from datetime import datetime, timedelta
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from app import db
from app.models.chat import Chat, ChatMember
from app.models.message import Message, DeletedMessage
from app.models.user import User, BlockedUser
from app.services.chat_permissions import (
    is_admin_or_owner,
    can_manage_members,
    can_promote_admins,
    can_pin_in_chat,
)
from app.services.message_payloads import serialize_messages
from app.services.retention_maintenance import maybe_run_auto_retention
from app.services.timestamps import utc_iso

chats_bp = Blueprint('chats', __name__)

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,32}$')


def _escape_like(val: str) -> str:
    return val.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def _last_visible_message(chat_id: str, user_id: str):
    deleted_subq = db.session.query(DeletedMessage.message_id).filter_by(user_id=user_id)
    msg = (
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
        .first()
    )
    if not msg:
        return None
    items = serialize_messages([msg], viewer_id=user_id)
    return items[0] if items else None


@chats_bp.route('', methods=['GET'])
@chats_bp.route('/', methods=['GET'])
@jwt_required()
def get_chats():
    maybe_run_auto_retention()
    user_id = get_jwt_identity()
    me = User.query.filter_by(id=user_id, is_deleted=False).first()
    if me:
        me.touch_online()
        db.session.commit()

    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    only_archived = request.args.get('only_archived', 'false').lower() == 'true'

    all_memberships = ChatMember.query.filter_by(user_id=user_id, is_deleted=False).all()
    archived_count = sum(1 for m in all_memberships if m.is_archived and m.chat and not m.chat.is_deleted)

    memberships = []
    for m in all_memberships:
        if not m.chat or m.chat.is_deleted:
            continue
        if only_archived and not m.is_archived:
            continue
        if not only_archived and not include_archived and m.is_archived:
            continue
        memberships.append(m)

    chats_list = []
    for m in memberships:
        last_msg = _last_visible_message(m.chat.id, user_id)
        chat_dict = m.chat.to_dict(current_user_id=user_id, last_message=last_msg)
        chats_list.append(chat_dict)

    chats_list.sort(
        key=lambda c: (
            1 if c.get('is_pinned') else 0,
            c.get('pinned_at') or '',
            (c.get('last_message') or {}).get('created_at') or c.get('updated_at') or '',
        ),
        reverse=True,
    )

    return jsonify({
        'chats': chats_list,
        'archived_count': archived_count,
    }), 200


@chats_bp.route('', methods=['POST'])
@chats_bp.route('/', methods=['POST'])
@jwt_required()
def create_chat():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    chat_type = (data.get('chat_type') or 'private').strip().lower()

    if chat_type not in ('private', 'group', 'channel'):
        return jsonify({'error': 'Invalid chat type. Allowed: private, group, channel.'}), 400

    if chat_type == 'private':
        target_user_id = (data.get('target_user_id') or '').strip()
        target_username = (data.get('username') or '').strip().lstrip('@').lower()

        target_user = None
        if target_user_id:
            target_user = User.query.filter_by(id=target_user_id, is_deleted=False).first()
        elif target_username:
            target_user = User.query.filter_by(username=target_username, is_deleted=False).first()

        if not target_user:
            return jsonify({'error': 'Target user not found.'}), 404
        if target_user.id == user_id:
            return jsonify({'error': 'You cannot start a private chat with yourself.'}), 400

        # Check if blocked
        blocked = BlockedUser.query.filter(
            or_(
                db.and_(BlockedUser.blocker_id == user_id, BlockedUser.blocked_id == target_user.id),
                db.and_(BlockedUser.blocker_id == target_user.id, BlockedUser.blocked_id == user_id),
            ),
            BlockedUser.is_deleted.is_(False),
        ).first()
        if blocked:
            return jsonify({'error': 'Cannot start a chat with a blocked user.'}), 403

        # Check existing private chat
        my_chats = (
            db.session.query(ChatMember.chat_id)
            .join(Chat, Chat.id == ChatMember.chat_id)
            .filter(
                ChatMember.user_id == user_id,
                Chat.chat_type == 'private',
                Chat.is_deleted.is_(False),
            )
            .subquery()
        )
        existing_member = ChatMember.query.filter(
            ChatMember.chat_id.in_(my_chats),
            ChatMember.user_id == target_user.id,
        ).first()

        if existing_member:
            chat = Chat.query.get(existing_member.chat_id)
            for uid in (user_id, target_user.id):
                cm = ChatMember.query.filter_by(chat_id=chat.id, user_id=uid).first()
                if cm and cm.is_deleted:
                    cm.is_deleted = False
                    cm.deleted_at = None
            db.session.commit()
            last_msg = _last_visible_message(chat.id, user_id)
            return jsonify({'chat': chat.to_dict(current_user_id=user_id, last_message=last_msg)}), 200

        chat = Chat(chat_type='private', created_by=user_id, is_public=False)
        db.session.add(chat)
        db.session.flush()

        db.session.add(ChatMember(chat_id=chat.id, user_id=user_id, role='member'))
        db.session.add(ChatMember(chat_id=chat.id, user_id=target_user.id, role='member'))
        db.session.commit()

        return jsonify({'chat': chat.to_dict(current_user_id=user_id)}), 201

    # Group or Channel creation
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': f'{chat_type.capitalize()} name is required.'}), 400
    if len(name) > 100:
        return jsonify({'error': 'Name cannot exceed 100 characters.'}), 400

    description = (data.get('description') or '').strip() or None
    raw_username = (data.get('username') or '').strip().lstrip('@').lower() or None

    if raw_username:
        if not USERNAME_RE.match(raw_username):
            return jsonify({
                'error': 'Public handle (@username) must be 3–32 characters using English letters, numbers, and underscores.'
            }), 400
        if Chat.query.filter_by(username=raw_username).first() or User.query.filter_by(username=raw_username).first():
            return jsonify({'error': 'This @username handle is already taken.'}), 409

    is_public = data.get('is_public', True)
    if not isinstance(is_public, bool):
        is_public = True

    chat = Chat(
        chat_type=chat_type,
        name=name,
        description=description,
        username=raw_username,
        created_by=user_id,
        is_public=is_public,
    )
    db.session.add(chat)
    db.session.flush()

    db.session.add(ChatMember(chat_id=chat.id, user_id=user_id, role='owner'))

    # Optional initial members (by user_ids or usernames)
    member_ids = data.get('member_ids') or []
    member_usernames = data.get('member_usernames') or []
    added_ids = {user_id}

    if isinstance(member_ids, list):
        for mid in member_ids:
            if not isinstance(mid, str) or mid in added_ids:
                continue
            u = User.query.filter_by(id=mid, is_deleted=False).first()
            if u:
                db.session.add(ChatMember(chat_id=chat.id, user_id=u.id, role='member'))
                added_ids.add(u.id)

    if isinstance(member_usernames, list):
        for uname in member_usernames:
            if not isinstance(uname, str):
                continue
            clean_u = uname.strip().lstrip('@').lower()
            if not clean_u:
                continue
            u = User.query.filter_by(username=clean_u, is_deleted=False).first()
            if u and u.id not in added_ids:
                db.session.add(ChatMember(chat_id=chat.id, user_id=u.id, role='member'))
                added_ids.add(u.id)

    db.session.commit()
    return jsonify({'chat': chat.to_dict(current_user_id=user_id)}), 201


@chats_bp.route('/search', methods=['GET'])
@jwt_required()
def search_chats():
    user_id = get_jwt_identity()
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'chats': []}), 200

    clean_q = q.lstrip('@').strip().lower()
    if not clean_q:
        return jsonify({'chats': []}), 200

    pattern = f'%{_escape_like(clean_q)}%'
    chats = (
        Chat.query.filter(
            Chat.is_deleted.is_(False),
            Chat.chat_type.in_(['group', 'channel']),
            Chat.is_public.is_(True),
            or_(
                Chat.username.ilike(pattern, escape='\\'),
                Chat.name.ilike(pattern, escape='\\'),
            ),
        )
        .limit(30)
        .all()
    )
    return jsonify({'chats': [c.to_dict(current_user_id=user_id) for c in chats]}), 200


@chats_bp.route('/<chat_id>', methods=['GET'])
@jwt_required()
def get_chat(chat_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat:
        return jsonify({'error': 'Chat not found.'}), 404

    my_member = ChatMember.query.filter_by(
        chat_id=chat_id, user_id=user_id, is_deleted=False
    ).first()
    if not my_member and not (chat.is_public and chat.chat_type in ('group', 'channel')):
        return jsonify({'error': 'You do not have access to this chat.'}), 403

    members = ChatMember.query.filter_by(chat_id=chat_id, is_deleted=False).all()
    members_data = []
    for m in members:
        u = User.query.filter_by(id=m.user_id, is_deleted=False).first()
        if u:
            members_data.append({
                'user': u.to_dict(viewer_id=user_id),
                'role': m.role,
                'joined_at': utc_iso(m.joined_at),
            })

    # Sort members: owner first, then admin, then member
    role_priority = {'owner': 0, 'admin': 1, 'member': 2}
    members_data.sort(key=lambda item: (role_priority.get(item['role'], 3), item['user']['username']))

    last_msg = _last_visible_message(chat.id, user_id) if my_member else None
    chat_data = chat.to_dict(current_user_id=user_id, last_message=last_msg)
    chat_data['members'] = members_data
    return jsonify({'chat': chat_data}), 200


@chats_bp.route('/<chat_id>', methods=['PUT'])
@jwt_required()
def update_chat(chat_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat:
        return jsonify({'error': 'Chat not found.'}), 404
    if chat.chat_type == 'private':
        return jsonify({'error': 'Private chats cannot be edited.'}), 400

    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not is_admin_or_owner(member):
        return jsonify({'error': 'Only group or channel admins can update info.'}), 403

    data = request.get_json(silent=True) or {}
    if 'name' in data:
        new_name = (data.get('name') or '').strip()
        if not new_name:
            return jsonify({'error': 'Name cannot be empty.'}), 400
        chat.name = new_name[:100]

    if 'description' in data:
        desc = (data.get('description') or '').strip()
        chat.description = desc[:500] if desc else None

    if 'username' in data:
        raw_u = (data.get('username') or '').strip().lstrip('@').lower() or None
        if raw_u and raw_u != chat.username:
            if not USERNAME_RE.match(raw_u):
                return jsonify({
                    'error': 'Public handle (@username) must be 3–32 characters using English letters, numbers, and underscores.'
                }), 400
            conflict = Chat.query.filter(Chat.username == raw_u, Chat.id != chat.id).first()
            user_conflict = User.query.filter_by(username=raw_u).first()
            if conflict or user_conflict:
                return jsonify({'error': 'This @username handle is already taken.'}), 409
        chat.username = raw_u

    chat.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'chat': chat.to_dict(current_user_id=user_id)}), 200


@chats_bp.route('/<chat_id>/join', methods=['POST'])
@jwt_required()
def join_chat(chat_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat or chat.chat_type not in ('group', 'channel'):
        return jsonify({'error': 'Group or channel not found.'}), 404
    if not chat.is_public:
        return jsonify({'error': 'This chat is private.'}), 403

    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id).first()
    if member:
        if not member.is_deleted:
            return jsonify({'message': 'Already a member.', 'chat': chat.to_dict(current_user_id=user_id)}), 200
        member.is_deleted = False
        member.deleted_at = None
        member.role = 'member'
        member.joined_at = datetime.utcnow()
    else:
        member = ChatMember(chat_id=chat_id, user_id=user_id, role='member')
        db.session.add(member)

    db.session.commit()
    return jsonify({'message': 'Joined successfully.', 'chat': chat.to_dict(current_user_id=user_id)}), 200


@chats_bp.route('/<chat_id>/leave', methods=['POST'])
@jwt_required()
def leave_chat(chat_id):
    user_id = get_jwt_identity()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'You are not a member of this chat.'}), 404

    member.is_deleted = True
    member.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'You left the chat.'}), 200


@chats_bp.route('/<chat_id>/members', methods=['POST'])
@jwt_required()
def add_member(chat_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat or chat.chat_type not in ('group', 'channel'):
        return jsonify({'error': 'Group or channel not found.'}), 404

    my_member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not can_manage_members(chat, my_member):
        return jsonify({'error': 'Only group or channel admins can add members.'}), 403

    data = request.get_json(silent=True) or {}
    target_ids = []
    if data.get('user_id'):
        target_ids.append(str(data['user_id']).strip())
    if isinstance(data.get('user_ids'), list):
        target_ids.extend(str(uid).strip() for uid in data['user_ids'] if uid)

    raw_username = (data.get('username') or '').strip().lstrip('@').lower()
    if raw_username:
        u_by_name = User.query.filter_by(username=raw_username, is_deleted=False).first()
        if not u_by_name:
            return jsonify({'error': f'User @{raw_username} not found.'}), 404
        target_ids.append(u_by_name.id)

    if not target_ids:
        return jsonify({'error': 'Provide user_id, user_ids, or username to add.'}), 400

    added = []
    for tid in dict.fromkeys(target_ids):
        target_user = User.query.filter_by(id=tid, is_deleted=False).first()
        if not target_user:
            continue

        # Check block
        blocked = BlockedUser.query.filter_by(
            blocker_id=tid, blocked_id=user_id, is_deleted=False
        ).first()
        if blocked:
            continue

        existing = ChatMember.query.filter_by(chat_id=chat_id, user_id=tid).first()
        if existing:
            if existing.is_deleted:
                existing.is_deleted = False
                existing.deleted_at = None
                existing.role = 'member'
                existing.joined_at = datetime.utcnow()
                added.append(target_user.to_dict(viewer_id=user_id))
            else:
                added.append(target_user.to_dict(viewer_id=user_id))
        else:
            db.session.add(ChatMember(chat_id=chat_id, user_id=tid, role='member'))
            added.append(target_user.to_dict(viewer_id=user_id))

    chat.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        'message': 'Member(s) added.',
        'added_members': added,
    }), 200


@chats_bp.route('/<chat_id>/members/<target_user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(chat_id, target_user_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat or chat.chat_type not in ('group', 'channel'):
        return jsonify({'error': 'Group or channel not found.'}), 404

    my_member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not can_manage_members(chat, my_member):
        return jsonify({'error': 'Only admins can remove members.'}), 403

    target_member = ChatMember.query.filter_by(
        chat_id=chat_id, user_id=target_user_id, is_deleted=False
    ).first()
    if not target_member:
        return jsonify({'error': 'Member not found.'}), 404

    if target_member.role == 'owner':
        return jsonify({'error': 'The owner cannot be removed.'}), 403

    if target_member.role == 'admin' and my_member.role != 'owner':
        return jsonify({'error': 'Only the owner can remove an admin.'}), 403

    target_member.is_deleted = True
    target_member.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Member removed.'}), 200


@chats_bp.route('/<chat_id>/admins/<target_user_id>', methods=['POST'])
@chats_bp.route('/<chat_id>/members/<target_user_id>', methods=['PUT'])
@jwt_required()
def set_member_role(chat_id, target_user_id):
    """Promote a member to admin or demote an admin to member (simple role assignment)."""
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat or chat.chat_type not in ('group', 'channel'):
        return jsonify({'error': 'Group or channel not found.'}), 404

    my_member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not can_promote_admins(chat, my_member):
        return jsonify({'error': 'Only admins can assign or remove admin roles.'}), 403

    target_member = ChatMember.query.filter_by(
        chat_id=chat_id, user_id=target_user_id, is_deleted=False
    ).first()
    if not target_member:
        return jsonify({'error': 'Member not found in this chat.'}), 404

    if target_member.role == 'owner':
        return jsonify({'error': 'Cannot change the role of the owner.'}), 400

    data = request.get_json(silent=True) or {}
    requested_role = (data.get('role') or 'admin').strip().lower()
    if requested_role not in ('admin', 'member'):
        return jsonify({'error': 'Role must be either "admin" or "member".'}), 400

    if target_member.role == 'admin' and requested_role == 'member' and my_member.role != 'owner':
        return jsonify({'error': 'Only the owner can demote an existing admin.'}), 403

    target_member.role = requested_role
    db.session.commit()
    return jsonify({
        'message': f'Member role updated to {requested_role}.',
        'user_id': target_user_id,
        'role': target_member.role,
    }), 200


@chats_bp.route('/<chat_id>/archive', methods=['POST'])
@jwt_required()
def toggle_archive_chat(chat_id):
    user_id = get_jwt_identity()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'Chat not found.'}), 404

    data = request.get_json(silent=True) or {}
    if 'is_archived' in data:
        if not isinstance(data['is_archived'], bool):
            return jsonify({'error': 'Boolean fields must be true or false.'}), 400
        member.is_archived = data['is_archived']
    else:
        member.is_archived = not bool(member.is_archived)

    member.archived_at = datetime.utcnow() if member.is_archived else None
    db.session.commit()
    return jsonify({
        'chat_id': chat_id,
        'is_archived': bool(member.is_archived),
    }), 200


@chats_bp.route('/<chat_id>/mute', methods=['POST'])
@jwt_required()
def toggle_mute_chat(chat_id):
    user_id = get_jwt_identity()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'Chat not found.'}), 404

    data = request.get_json(silent=True) or {}
    if 'is_muted' in data:
        if not isinstance(data['is_muted'], bool):
            return jsonify({'error': 'Boolean fields must be true or false.'}), 400
        member.is_muted = data['is_muted']
    else:
        member.is_muted = not bool(member.is_muted)

    db.session.commit()
    return jsonify({
        'chat_id': chat_id,
        'is_muted': bool(member.is_muted),
    }), 200


@chats_bp.route('/<chat_id>/pin', methods=['POST'])
@jwt_required()
def toggle_pin_chat(chat_id):
    user_id = get_jwt_identity()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'Chat not found.'}), 404

    data = request.get_json(silent=True) or {}
    if 'is_pinned' in data:
        if not isinstance(data['is_pinned'], bool):
            return jsonify({'error': 'Boolean fields must be true or false.'}), 400
        pin = data['is_pinned']
    else:
        pin = member.pinned_at is None

    member.pinned_at = datetime.utcnow() if pin else None
    db.session.commit()
    return jsonify({
        'chat_id': chat_id,
        'is_pinned': bool(member.pinned_at is not None),
        'pinned_at': utc_iso(member.pinned_at),
    }), 200


@chats_bp.route('/<chat_id>/pins', methods=['GET'])
@jwt_required()
def list_pinned_messages(chat_id):
    user_id = get_jwt_identity()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'Access denied.'}), 403

    deleted_subq = db.session.query(DeletedMessage.message_id).filter_by(user_id=user_id)
    pinned = (
        Message.query.options(
            selectinload(Message.sender),
            selectinload(Message.media),
        )
        .filter(
            Message.chat_id == chat_id,
            Message.is_pinned.is_(True),
            Message.is_deleted.is_(False),
            Message.is_deleted_for_all.is_(False),
            ~Message.id.in_(deleted_subq),
        )
        .order_by(Message.pinned_at.desc(), Message.created_at.desc())
        .all()
    )
    items = serialize_messages(pinned, viewer_id=user_id)
    return jsonify({
        'pinned_messages': items,
        'pinned_message': items[0] if items else None,
    }), 200


@chats_bp.route('/<chat_id>/pins/<message_id>', methods=['POST'])
@jwt_required()
def pin_message(chat_id, message_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not chat or not can_pin_in_chat(chat, member):
        return jsonify({'error': 'You do not have permission to pin messages.'}), 403

    msg = Message.query.filter_by(
        id=message_id, chat_id=chat_id, is_deleted=False, is_deleted_for_all=False
    ).first()
    if not msg:
        return jsonify({'error': 'Message not found.'}), 404

    msg.is_pinned = True
    msg.pinned_at = datetime.utcnow()
    msg.pinned_by = user_id
    db.session.commit()
    return jsonify({'message': serialize_messages([msg], viewer_id=user_id)[0]}), 200


@chats_bp.route('/<chat_id>/pins/<message_id>', methods=['DELETE'])
@jwt_required()
def unpin_message(chat_id, message_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not chat or not can_pin_in_chat(chat, member):
        return jsonify({'error': 'You do not have permission to unpin messages.'}), 403

    msg = Message.query.filter_by(id=message_id, chat_id=chat_id).first()
    if not msg:
        return jsonify({'error': 'Message not found.'}), 404

    msg.is_pinned = False
    msg.pinned_at = None
    msg.pinned_by = None
    db.session.commit()
    return jsonify({'ok': True, 'message_id': message_id}), 200


@chats_bp.route('/<chat_id>', methods=['DELETE'])
@jwt_required()
def delete_chat(chat_id):
    user_id = get_jwt_identity()
    chat = Chat.query.filter_by(id=chat_id, is_deleted=False).first()
    if not chat:
        return jsonify({'error': 'Chat not found.'}), 404

    member = ChatMember.query.filter_by(chat_id=chat_id, user_id=user_id, is_deleted=False).first()
    if not member:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}
    for_all = bool(data.get('for_all', False))

    if chat.chat_type in ('group', 'channel') and member.role == 'owner':
        chat.is_deleted = True
        chat.deleted_at = datetime.utcnow()
        for m in ChatMember.query.filter_by(chat_id=chat_id).all():
            m.is_deleted = True
            m.deleted_at = datetime.utcnow()
    elif chat.chat_type == 'private' and for_all:
        chat.is_deleted = True
        chat.deleted_at = datetime.utcnow()
        for m in ChatMember.query.filter_by(chat_id=chat_id).all():
            m.is_deleted = True
            m.deleted_at = datetime.utcnow()
    else:
        member.is_deleted = True
        member.deleted_at = datetime.utcnow()

    db.session.commit()
    return jsonify({'message': 'Chat deleted.'}), 200


@chats_bp.route('/poll', methods=['GET'])
@jwt_required()
def poll_updates():
    maybe_run_auto_retention()
    user_id = get_jwt_identity()
    me = User.query.filter_by(id=user_id, is_deleted=False).first()
    if me:
        me.touch_online()
        db.session.commit()

    since_str = request.args.get('since')
    now = datetime.utcnow()

    since_dt = None
    if since_str:
        try:
            clean = since_str.replace('Z', '+00:00')
            parsed = datetime.fromisoformat(clean)
            if parsed.tzinfo is not None:
                parsed = parsed.utctimetuple()
                since_dt = datetime(*parsed[:6])
            else:
                since_dt = parsed
        except ValueError:
            since_dt = None

    if not since_dt:
        since_dt = now - timedelta(seconds=30)

    memberships = ChatMember.query.filter_by(user_id=user_id, is_deleted=False).all()
    chat_ids = [m.chat_id for m in memberships if m.chat and not m.chat.is_deleted]

    if not chat_ids:
        return jsonify({
            'messages': [],
            'deleted_message_ids': [],
            'server_time': utc_iso(now),
        }), 200

    deleted_subq = db.session.query(DeletedMessage.message_id).filter_by(user_id=user_id)
    new_or_updated = (
        Message.query.options(
            selectinload(Message.sender),
            selectinload(Message.media),
        )
        .filter(
            Message.chat_id.in_(chat_ids),
            Message.is_deleted.is_(False),
            Message.is_deleted_for_all.is_(False),
            ~Message.id.in_(deleted_subq),
            or_(Message.created_at >= since_dt, Message.updated_at >= since_dt),
        )
        .order_by(Message.created_at.asc())
        .limit(200)
        .all()
    )

    deleted_for_all = (
        db.session.query(Message.id)
        .filter(
            Message.chat_id.in_(chat_ids),
            or_(Message.is_deleted_for_all.is_(True), Message.is_deleted.is_(True)),
            or_(Message.deleted_for_all_at >= since_dt, Message.deleted_at >= since_dt),
        )
        .all()
    )

    return jsonify({
        'messages': serialize_messages(new_or_updated, viewer_id=user_id),
        'deleted_message_ids': [r[0] for r in deleted_for_all],
        'server_time': utc_iso(now),
    }), 200
