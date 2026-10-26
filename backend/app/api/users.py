from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app import db
from app.models.user import User, BlockedUser
from app.models.chat import Chat
from app.services.app_settings import limits_payload_for_user

users_bp = Blueprint('users', __name__)


def _escape_like(val: str) -> str:
    return val.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


@users_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_profile():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, is_deleted=False).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    user.touch_online()
    db.session.commit()
    payload = user.to_dict(viewer_id=user.id)
    payload['upload_limits'] = limits_payload_for_user(user)
    return jsonify({'user': payload}), 200


@users_bp.route('/<target_id>', methods=['GET'])
@jwt_required()
def get_user(target_id):
    current_user_id = get_jwt_identity()
    user = User.query.filter_by(id=target_id, is_deleted=False).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    is_blocked = BlockedUser.query.filter_by(
        blocker_id=current_user_id, blocked_id=target_id, is_deleted=False
    ).first() is not None
    is_blocked_by = BlockedUser.query.filter_by(
        blocker_id=target_id, blocked_id=current_user_id, is_deleted=False
    ).first() is not None

    data = user.to_dict(viewer_id=current_user_id)
    data['is_blocked'] = is_blocked
    data['is_blocked_by'] = is_blocked_by
    return jsonify({'user': data}), 200


@users_bp.route('/by-username/<username>', methods=['GET'])
@jwt_required()
def get_by_username(username):
    current_user_id = get_jwt_identity()
    clean_u = username.strip().lstrip('@').lower()
    user = User.query.filter_by(username=clean_u, is_deleted=False).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    is_blocked = BlockedUser.query.filter_by(
        blocker_id=current_user_id, blocked_id=user.id, is_deleted=False
    ).first() is not None
    data = user.to_dict(viewer_id=current_user_id)
    data['is_blocked'] = is_blocked
    return jsonify({'user': data}), 200


@users_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    current_user_id = get_jwt_identity()
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'users': [], 'chats': []}), 200

    clean_q = q.lstrip('@').strip().lower()
    if not clean_q:
        return jsonify({'users': [], 'chats': []}), 200

    pattern = f'%{_escape_like(clean_q)}%'

    users = (
        User.query.filter(
            User.is_deleted.is_(False),
            User.is_active.is_(True),
            User.id != current_user_id,
            or_(
                User.username.ilike(pattern, escape='\\'),
                User.display_name.ilike(pattern, escape='\\'),
            ),
        )
        .limit(30)
        .all()
    )

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

    return jsonify({
        'users': [u.to_dict(viewer_id=current_user_id) for u in users],
        'chats': [c.to_dict(current_user_id=current_user_id) for c in chats],
    }), 200


@users_bp.route('/block/<target_id>', methods=['POST'])
@jwt_required()
def block_user(target_id):
    user_id = get_jwt_identity()
    if user_id == target_id:
        return jsonify({'error': 'You cannot block yourself.'}), 400

    target = User.query.filter_by(id=target_id, is_deleted=False).first()
    if not target:
        return jsonify({'error': 'User not found.'}), 404

    block = BlockedUser.query.filter_by(blocker_id=user_id, blocked_id=target_id).first()
    if block:
        block.is_deleted = False
        block.deleted_at = None
    else:
        block = BlockedUser(blocker_id=user_id, blocked_id=target_id)
        db.session.add(block)

    db.session.commit()
    return jsonify({'message': 'User blocked.', 'blocked_user_id': target_id}), 200


@users_bp.route('/unblock/<target_id>', methods=['POST'])
@jwt_required()
def unblock_user(target_id):
    user_id = get_jwt_identity()
    block = BlockedUser.query.filter_by(
        blocker_id=user_id, blocked_id=target_id, is_deleted=False
    ).first()
    if block:
        block.is_deleted = True
        block.deleted_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'message': 'User unblocked.', 'unblocked_user_id': target_id}), 200


@users_bp.route('/blocked', methods=['GET'])
@jwt_required()
def get_blocked_users():
    user_id = get_jwt_identity()
    blocks = BlockedUser.query.filter_by(blocker_id=user_id, is_deleted=False).all()
    users = []
    for b in blocks:
        u = User.query.filter_by(id=b.blocked_id, is_deleted=False).first()
        if u:
            users.append(u.to_dict(viewer_id=user_id))
    return jsonify({'blocked_users': users}), 200


@users_bp.route('/status', methods=['POST'])
@jwt_required()
def update_online_status():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, is_deleted=False).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    data = request.get_json(silent=True) or {}
    is_online = data.get('is_online', True)
    if not isinstance(is_online, bool):
        return jsonify({'error': 'Boolean fields must be true or false.'}), 400
    user.is_online = is_online
    user.last_seen = datetime.utcnow()
    db.session.commit()
    return jsonify({
        'is_online': user.effective_online,
        'last_seen': user.to_dict()['last_seen'],
    }), 200
