from datetime import datetime, timedelta
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app import db
from app.models.chat import Chat, ChatMember
from app.models.media import MediaFile
from app.models.message import Message, DeletedMessage, ALLOWED_MESSAGE_TYPES
from app.models.user import User, BlockedUser
from app.services.app_settings import VIDEO_MAX_BYTES
from app.services.chat_permissions import ensure_can_send
from app.services.message_payloads import serialize_messages, user_in_chat
from app.services.retention_maintenance import maybe_run_auto_retention

messages_bp = Blueprint('messages', __name__)


@messages_bp.route('/chat/<chat_id>', methods=['GET'])
@jwt_required()
def get_messages(chat_id):
    maybe_run_auto_retention()
    user_id = get_jwt_identity()

    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat:
        return jsonify({'error': 'Chat not found.'}), 404

    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member and not (chat.is_public and chat.chat_type in ('group', 'channel')):
        return jsonify({'error': 'You do not have access to this chat.'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    # No age cutoff: messages/chats are never expired — only media blobs are.

    deleted_subq = db.session.query(DeletedMessage.message_id).filter_by(user_id=user_id)

    messages_q = (
        Message.query.options(
            selectinload(Message.sender),
            selectinload(Message.media),
        )
        .filter(
            Message.chat_id == chat_id,
            Message.is_deleted.is_(False),
            Message.is_deleted_for_all.is_(False),
            ~Message.id.in_(deleted_subq),
        )
        .order_by(Message.created_at.desc(), Message.id.desc())
    )

    paginated = messages_q.paginate(page=page, per_page=per_page, error_out=False)

    if member:
        now = datetime.utcnow()
        member.unread_count = 0
        member.last_read_at = now
        Message.query.filter(
            Message.chat_id == chat_id,
            Message.sender_id != user_id,
            Message.status != 'read',
        ).update({'status': 'read', 'updated_at': now}, synchronize_session=False)
        db.session.commit()

    ordered_items = list(reversed(paginated.items))
    return jsonify({
        'messages': serialize_messages(ordered_items, viewer_id=user_id, chat=chat),
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
    }), 200


@messages_bp.route('/chat/<chat_id>', methods=['POST'])
@jwt_required()
def send_message(chat_id):
    maybe_run_auto_retention()
    user_id = get_jwt_identity()

    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat:
        return jsonify({'error': 'Chat not found.'}), 404

    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'You are not a member of this chat.'}), 403

    data = request.get_json(silent=True) or {}

    # Reject features explicitly excluded from Reyno Messenger Lite
    if data.get('is_view_once') or data.get('view_duration'):
        return jsonify({'error': 'Self-destructing or timed messages are not supported in Reyno Messenger Lite.'}), 400
    if data.get('is_spoiler'):
        return jsonify({'error': 'Spoiler messages are not supported in Reyno Messenger Lite.'}), 400
    if data.get('is_encrypted') or data.get('encryption_hint'):
        return jsonify({'error': 'Password-protected messages are not supported in Reyno Messenger Lite.'}), 400
    if data.get('scheduled_at') or data.get('is_scheduled'):
        return jsonify({'error': 'Scheduled messages are not supported in Reyno Messenger Lite.'}), 400
    if data.get('is_live') or data.get('live_duration') or data.get('live_until'):
        return jsonify({
            'error': 'Live location sharing is not supported in Reyno Messenger Lite. Only static location sharing is allowed.'
        }), 400

    msg_type = (data.get('message_type') or 'text').strip().lower()
    if msg_type in ('file', 'document', 'audio', 'music'):
        return jsonify({'error': 'Sending files is not supported in Reyno Messenger Lite.'}), 400
    if msg_type == 'gif':
        return jsonify({'error': 'Sending GIFs is not supported in Reyno Messenger Lite.'}), 400
    if msg_type == 'poll':
        return jsonify({'error': 'Polls and quizzes are not supported in Reyno Messenger Lite.'}), 400
    if msg_type in ('video_note', 'round_video'):
        return jsonify({'error': 'Video messages (circular video notes) are not supported in Reyno Messenger Lite.'}), 400

    if msg_type not in ALLOWED_MESSAGE_TYPES or msg_type == 'system':
        return jsonify({'error': f'Unsupported message type: {msg_type}.'}), 400

    media_id = data.get('media_id')
    perm_err = ensure_can_send(chat, member, message_type=msg_type, has_media=bool(media_id))
    if perm_err:
        return jsonify({'error': perm_err}), 403

    # Check block in private chat
    if chat.chat_type == 'private':
        other_member = ChatMember.query.filter(
            ChatMember.chat_id == chat_id,
            ChatMember.user_id != user_id,
            ChatMember.is_deleted.is_(False),
        ).first()
        if other_member:
            blocked = BlockedUser.query.filter(
                or_(
                    db.and_(BlockedUser.blocker_id == other_member.user_id, BlockedUser.blocked_id == user_id),
                    db.and_(BlockedUser.blocker_id == user_id, BlockedUser.blocked_id == other_member.user_id),
                ),
                BlockedUser.is_deleted.is_(False),
            ).first()
            if blocked:
                return jsonify({'error': 'Cannot send messages because a block is active between users.'}), 403

    content = (data.get('content') or '').strip() if isinstance(data.get('content'), str) else ''
    reply_to_id = data.get('reply_to_id')

    media_obj = None
    if media_id:
        media_obj = MediaFile.query.filter_by(id=media_id, is_deleted=False).first()
        if not media_obj:
            return jsonify({'error': 'Attached media file was not found or has expired.'}), 404
        if media_obj.file_type == 'video' and (media_obj.file_size or 0) >= VIDEO_MAX_BYTES:
            return jsonify({'error': 'Video file size must be under 10 MB.'}), 413

    latitude = None
    longitude = None
    location_title = None

    if msg_type == 'location':
        try:
            latitude = float(data.get('latitude'))
            longitude = float(data.get('longitude'))
        except (TypeError, ValueError):
            return jsonify({'error': 'Valid latitude and longitude coordinates are required for location sharing.'}), 400

        if not (-90.0 <= latitude <= 90.0 and -180.0 <= longitude <= 180.0):
            return jsonify({'error': 'Coordinates are out of valid geographic bounds.'}), 400

        raw_label = data.get('location_label') or data.get('location_title') or content
        if isinstance(raw_label, str) and raw_label.strip():
            location_title = raw_label.strip()[:200]
        else:
            location_title = f'{latitude:.5f}, {longitude:.5f}'
        if not content:
            content = location_title

    elif msg_type == 'text':
        if not content:
            return jsonify({'error': 'Message text cannot be empty.'}), 400
        if len(content) > 4096:
            return jsonify({'error': 'Message text cannot exceed 4096 characters.'}), 400

    elif msg_type in ('image', 'video', 'voice'):
        if not media_obj:
            return jsonify({'error': f'A media attachment is required for {msg_type} messages.'}), 400

    elif msg_type == 'sticker':
        if not content and not media_obj:
            return jsonify({'error': 'Sticker emoji or media is required.'}), 400

    if reply_to_id:
        reply_msg = Message.query.filter_by(
            id=reply_to_id, chat_id=chat_id, is_deleted=False, is_deleted_for_all=False
        ).first()
        if not reply_msg:
            reply_to_id = None

    msg = Message(
        chat_id=chat_id,
        sender_id=user_id,
        message_type=msg_type,
        content=content or None,
        media_id=media_obj.id if media_obj else None,
        reply_to_id=reply_to_id,
        latitude=latitude,
        longitude=longitude,
        location_title=location_title,
        status='sent',
    )
    db.session.add(msg)

    now = datetime.utcnow()
    chat.updated_at = now

    other_members = ChatMember.query.filter(
        ChatMember.chat_id == chat_id,
        ChatMember.user_id != user_id,
        ChatMember.is_deleted.is_(False),
    ).all()
    for m in other_members:
        m.unread_count = (m.unread_count or 0) + 1

    sender_user = User.query.get(user_id)
    if sender_user:
        sender_user.touch_online()

    db.session.commit()
    return jsonify({
        'message': serialize_messages([msg], viewer_id=user_id, chat=chat)[0]
    }), 201


@messages_bp.route('/<message_id>', methods=['PUT'])
@jwt_required()
def edit_message(message_id):
    user_id = get_jwt_identity()
    msg = Message.query.filter_by(id=message_id, is_deleted=False, is_deleted_for_all=False).first()
    if not msg:
        return jsonify({'error': 'Message not found.'}), 404

    if msg.sender_id != user_id:
        return jsonify({'error': 'You can only edit your own messages.'}), 403

    if msg.message_type == 'location' or msg.message_type == 'voice' or msg.message_type == 'sticker':
        return jsonify({'error': 'This message type cannot be edited.'}), 400

    data = request.get_json(silent=True) or {}
    new_content = (data.get('content') or '').strip() if isinstance(data.get('content'), str) else ''
    if msg.message_type == 'text' and not new_content:
        return jsonify({'error': 'Message content cannot be empty.'}), 400
    if len(new_content) > 4096:
        return jsonify({'error': 'Message content cannot exceed 4096 characters.'}), 400

    msg.content = new_content
    msg.is_edited = True
    msg.edited_at = datetime.utcnow()
    msg.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'message': serialize_messages([msg], viewer_id=user_id)[0]}), 200


@messages_bp.route('/<message_id>', methods=['DELETE'])
@jwt_required()
def delete_message(message_id):
    user_id = get_jwt_identity()
    msg = Message.query.filter_by(id=message_id, is_deleted=False).first()
    if not msg:
        return jsonify({'error': 'Message not found.'}), 404

    chat = Chat.query.filter_by(id=msg.chat_id, is_deleted=False).first()
    member = ChatMember.query.filter_by(chat_id=msg.chat_id, user_id=user_id, is_deleted=False).first()
    if not chat or not member:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}
    # POINT 1: Reyno Lite only supports one-sided deletion ("Delete for me").
    # Deleting for everyone is a Full-version feature and is rejected here,
    # even for the sender or group/channel admins. Editing, however, stays
    # two-sided: an edited message shows as edited for everyone.
    wants_for_all = bool(
        data.get('delete_for_all') or data.get('for_all')
        or (request.args.get('for_all') or '').lower() in ('true', '1', 'yes')
    )
    if wants_for_all:
        return jsonify({
            'error': 'Deleting for everyone is not available in Reyno Messenger Lite. You can only delete a message for yourself.',
            'code': 'delete_for_everyone_unavailable',
        }), 403

    existing = DeletedMessage.query.filter_by(message_id=message_id, user_id=user_id).first()
    if not existing:
        db.session.add(DeletedMessage(message_id=message_id, user_id=user_id))

    db.session.commit()
    return jsonify({
        'message': 'Message deleted.',
        'message_id': message_id,
        'delete_for_all': False,
    }), 200


@messages_bp.route('/forward', methods=['POST'])
@jwt_required()
def forward_message():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    message_id = data.get('message_id')
    target_chat_id = data.get('target_chat_id')

    if not message_id or not target_chat_id:
        return jsonify({'error': 'Both message_id and target_chat_id are required.'}), 400

    original = Message.query.filter_by(
        id=message_id, is_deleted=False, is_deleted_for_all=False
    ).first()
    if not original:
        return jsonify({'error': 'Original message not found.'}), 404

    if not user_in_chat(user_id, original.chat_id):
        return jsonify({'error': 'You do not have access to the source chat.'}), 403

    target_chat = Chat.query.filter_by(id=target_chat_id, is_deleted=False).first()
    target_member = ChatMember.query.filter_by(
        chat_id=target_chat_id, user_id=user_id, is_deleted=False
    ).first()
    if not target_chat or not target_member:
        return jsonify({'error': 'Target chat not found.'}), 404

    perm_err = ensure_can_send(
        target_chat,
        target_member,
        message_type=original.message_type,
        has_media=bool(original.media_id),
    )
    if perm_err:
        return jsonify({'error': perm_err}), 403

    forwarded = Message(
        chat_id=target_chat_id,
        sender_id=user_id,
        message_type=original.message_type,
        content=original.content,
        media_id=original.media_id if not original.media_expired else None,
        forwarded_from_id=original.sender_id,
        latitude=original.latitude,
        longitude=original.longitude,
        location_title=original.location_title,
        status='sent',
    )
    db.session.add(forwarded)

    target_chat.updated_at = datetime.utcnow()
    other_members = ChatMember.query.filter(
        ChatMember.chat_id == target_chat_id,
        ChatMember.user_id != user_id,
        ChatMember.is_deleted.is_(False),
    ).all()
    for m in other_members:
        m.unread_count = (m.unread_count or 0) + 1

    db.session.commit()
    return jsonify({
        'message': serialize_messages([forwarded], viewer_id=user_id, chat=target_chat)[0]
    }), 201


@messages_bp.route('/read/<chat_id>', methods=['POST'])
@jwt_required()
def mark_read(chat_id):
    user_id = get_jwt_identity()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'Access denied.'}), 403

    now = datetime.utcnow()
    member.unread_count = 0
    member.last_read_at = now
    Message.query.filter(
        Message.chat_id == chat_id,
        Message.sender_id != user_id,
        Message.status != 'read',
    ).update({'status': 'read', 'updated_at': now}, synchronize_session=False)
    db.session.commit()
    return jsonify({'message': 'Messages marked as read.'}), 200
