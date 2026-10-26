from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.message import Message, MessageReaction
from app.models.user import User
from app.services.message_payloads import user_in_chat

reactions_bp = Blueprint('reactions', __name__)


def normalize_emoji(value):
    if not isinstance(value, str):
        return None
    e = value.strip()
    if not e or len(e) > 20:
        return None
    if ' ' in e and len(e) > 4:
        return None
    return e


@reactions_bp.route('/<message_id>/reaction', methods=['POST'])
@jwt_required()
def toggle_reaction(message_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    emoji = normalize_emoji(data.get('emoji') or data.get('reaction') or '')
    if not emoji:
        return jsonify({'error': 'Invalid emoji.'}), 400

    msg = Message.query.filter_by(id=message_id, is_deleted=False, is_deleted_for_all=False).first()
    if not msg:
        return jsonify({'error': 'Message not found.'}), 404
    if not user_in_chat(user_id, msg.chat_id):
        return jsonify({'error': 'Access denied.'}), 403

    existing_others = MessageReaction.query.filter_by(
        message_id=message_id, user_id=user_id, is_deleted=False
    ).all()

    for r in existing_others:
        if r.emoji == emoji:
            r.is_deleted = True
            r.deleted_at = datetime.utcnow()
            db.session.commit()
            return jsonify({
                'ok': True,
                'action': 'removed',
                'emoji': emoji,
                **reaction_summary(message_id, user_id),
            }), 200

    for r in existing_others:
        r.is_deleted = True
        r.deleted_at = datetime.utcnow()

    existing_deleted = MessageReaction.query.filter_by(
        message_id=message_id, user_id=user_id, emoji=emoji
    ).first()
    if existing_deleted:
        existing_deleted.is_deleted = False
        existing_deleted.deleted_at = None
        existing_deleted.created_at = datetime.utcnow()
    else:
        db.session.add(MessageReaction(message_id=message_id, user_id=user_id, emoji=emoji))

    db.session.commit()
    return jsonify({
        'ok': True,
        'action': 'added',
        'emoji': emoji,
        **reaction_summary(message_id, user_id),
    }), 200


@reactions_bp.route('/<message_id>/reactions', methods=['GET'])
@jwt_required()
def list_reactions(message_id):
    user_id = get_jwt_identity()
    msg = Message.query.filter_by(id=message_id).first()
    if not msg or not user_in_chat(user_id, msg.chat_id):
        return jsonify({'error': 'Access denied.'}), 403
    return jsonify(reaction_summary(message_id, user_id)), 200


@reactions_bp.route('/<message_id>/reaction', methods=['DELETE'])
@jwt_required()
def remove_reaction(message_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    emoji = normalize_emoji(data.get('emoji') or '') if data else None
    query = MessageReaction.query.filter_by(
        message_id=message_id, user_id=user_id, is_deleted=False
    )
    if emoji:
        query = query.filter_by(emoji=emoji)
    reactions = query.all()
    for r in reactions:
        r.is_deleted = True
        r.deleted_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        'ok': True,
        'removed': len(reactions),
        **reaction_summary(message_id, user_id),
    }), 200


def reaction_summary(message_id, viewer_id=None):
    reactions = MessageReaction.query.filter_by(message_id=message_id, is_deleted=False).all()
    counts = {}
    user_reacted = {}
    for r in reactions:
        counts[r.emoji] = counts.get(r.emoji, 0) + 1
        if r.user_id == viewer_id:
            user_reacted[r.emoji] = True
    summary = [
        {'emoji': e, 'count': c, 'me': bool(user_reacted.get(e))}
        for e, c in sorted(counts.items(), key=lambda x: -x[1])
    ]
    details = []
    for item in summary:
        emoji = item['emoji']
        users = [u for u in reactions if u.emoji == emoji][:3]
        user_infos = []
        for rr in users:
            u = User.query.get(rr.user_id)
            if u:
                user_infos.append({
                    'id': u.id,
                    'display_name': u.display_name,
                    'username': u.username,
                })
        details.append({**item, 'users': user_infos})
    return {'reactions': details, 'total': len(reactions)}
