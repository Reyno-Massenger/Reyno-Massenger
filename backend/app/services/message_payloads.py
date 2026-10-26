"""Batch message serializer for Reyno Messenger Lite."""
from sqlalchemy.orm import selectinload

from app import db
from app.models.chat import Chat, ChatMember
from app.models.media import MediaFile
from app.models.message import Message, MessageReaction
from app.models.user import User
from app.services.timestamps import utc_iso

MAX_REPLY_SNIPPET = 120

MEDIA_LABELS = {
    'image': 'Photo',
    'video': 'Video',
    'voice': 'Voice message',
    'sticker': 'Sticker',
    'location': 'Location',
}


def user_in_chat(user_id, chat_id):
    return ChatMember.query.filter_by(
        chat_id=chat_id, user_id=user_id, is_deleted=False
    ).first() is not None


def _media_url_for(msg):
    if msg.media_expired or not msg.media_id:
        return None
    if msg.media and not msg.media.is_deleted:
        return f'/api/v1/media/{msg.media_id}'
    return None


def _reply_preview(msg, sender_name, viewer_id=None):
    if not msg or msg.is_deleted or msg.is_deleted_for_all:
        return None
    text = (msg.content or '').strip()
    if len(text) > MAX_REPLY_SNIPPET:
        text = f'{text[:MAX_REPLY_SNIPPET]}…'
    if not text:
        if msg.media_expired:
            text = 'Expired media'
        elif msg.message_type == 'location':
            text = msg.location_title or 'Static location'
        else:
            text = MEDIA_LABELS.get(msg.message_type, 'Message')

    thumb_url = None
    if msg.message_type == 'image' and not msg.media_expired and msg.media_id:
        thumb_url = f'/api/v1/media/{msg.media_id}'

    return {
        'id': msg.id,
        'sender_id': msg.sender_id,
        'sender_name': sender_name,
        'message_type': msg.message_type,
        'content': text,
        'media_id': None if msg.media_expired else msg.media_id,
        'thumb_url': thumb_url,
        'media_expired': bool(msg.media_expired),
    }


def serialize_messages(messages, viewer_id=None, chat=None):
    if not messages:
        return []

    reply_ids = {m.reply_to_id for m in messages if m.reply_to_id}
    forward_ids = {m.forwarded_from_id for m in messages if m.forwarded_from_id}
    msg_ids = {m.id for m in messages}

    reply_map = {}
    if reply_ids:
        reply_rows = (
            Message.query.options(
                selectinload(Message.sender),
                selectinload(Message.media),
            )
            .filter(Message.id.in_(reply_ids))
            .all()
        )
        reply_map = {m.id: m for m in reply_rows}

    user_ids = set(forward_ids)
    for m in messages:
        if m.sender_id:
            user_ids.add(m.sender_id)
    for m in reply_map.values():
        if m.sender_id:
            user_ids.add(m.sender_id)

    users = (
        {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()}
        if user_ids else {}
    )

    reactions_by_msg = {}
    if msg_ids:
        rx_rows = MessageReaction.query.filter(
            MessageReaction.message_id.in_(msg_ids),
            MessageReaction.is_deleted.is_(False),
        ).all()
        for r in rx_rows:
            reactions_by_msg.setdefault(r.message_id, []).append(r)

    result = []
    for msg in messages:
        sender = msg.sender or users.get(msg.sender_id)
        reply = reply_map.get(msg.reply_to_id) if msg.reply_to_id else None
        reply_sender = (
            (reply.sender or users.get(reply.sender_id)) if reply else None
        )
        forwarded_user = (
            users.get(msg.forwarded_from_id) if msg.forwarded_from_id else None
        )

        msg_reactions = reactions_by_msg.get(msg.id, [])
        rx_counts = {}
        rx_me = {}
        for r in msg_reactions:
            rx_counts[r.emoji] = rx_counts.get(r.emoji, 0) + 1
            if viewer_id and r.user_id == viewer_id:
                rx_me[r.emoji] = True
        reactions_list = [
            {'emoji': e, 'count': c, 'me': bool(rx_me.get(e))}
            for e, c in sorted(rx_counts.items(), key=lambda x: -x[1])
        ]

        media = msg.media if (msg.media_id and not msg.media_expired) else None
        media_url = _media_url_for(msg)

        payload = {
            'id': msg.id,
            'chat_id': msg.chat_id,
            'sender_id': msg.sender_id,
            'sender': sender.to_dict(viewer_id=viewer_id) if sender else None,
            'message_type': msg.message_type,
            'content': msg.content,
            'media_id': None if msg.media_expired else msg.media_id,
            'media_url': media_url,
            'media_expired': bool(msg.media_expired),
            'media_expired_at': utc_iso(msg.media_expired_at),
            'file_size': media.file_size if media else None,
            'mime_type': media.mime_type if media else None,
            'duration': media.duration if media else None,
            'width': media.width if media else None,
            'height': media.height if media else None,
            'reply_to_id': msg.reply_to_id,
            'reply_to': _reply_preview(
                reply,
                reply_sender.display_name if reply_sender else '',
                viewer_id=viewer_id,
            ),
            'forwarded_from_id': msg.forwarded_from_id,
            'forwarded_from': (
                {
                    'id': forwarded_user.id,
                    'username': forwarded_user.username,
                    'display_name': forwarded_user.display_name,
                }
                if forwarded_user else None
            ),
            'is_edited': bool(msg.is_edited),
            'edited_at': utc_iso(msg.edited_at),
            'is_pinned': bool(msg.is_pinned),
            'pinned_at': utc_iso(msg.pinned_at),
            'pinned_by': msg.pinned_by,
            'latitude': msg.latitude,
            'longitude': msg.longitude,
            'location_label': msg.location_title,
            'location_title': msg.location_title,
            'is_live_location': False,
            'status': msg.status,
            'reactions': reactions_list,
            'created_at': utc_iso(msg.created_at),
        }
        result.append(payload)

    return result
