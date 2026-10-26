from datetime import datetime
import re
from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from app import db
from app.models.user import User
from app.services.rate_limiter import check_rate_limit

auth_bp = Blueprint('auth', __name__)

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,32}$')


def _attach_media_cookie(response, access_token: str):
    response.set_cookie(
        'reyno_media_token',
        access_token,
        httponly=True,
        samesite='Lax',
        secure=request.is_secure,
        max_age=30 * 24 * 3600,
        path='/api/v1/media',
    )
    return response


@auth_bp.route('/register', methods=['POST'])
def register():
    allowed, retry_after = check_rate_limit('auth_register', max_requests=10, window_seconds=300)
    if not allowed:
        return jsonify({
            'error': 'Too many registration attempts. Please try again later.',
            'retry_after_seconds': retry_after,
        }), 429

    data = request.get_json(silent=True) or {}
    raw_username = (data.get('username') or '').strip().lstrip('@').lower()
    password = data.get('password') or ''
    display_name = (data.get('display_name') or '').strip()

    if not raw_username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    if not USERNAME_RE.match(raw_username):
        return jsonify({
            'error': 'Username must be 3–32 characters using only English letters, numbers, and underscores.'
        }), 400

    if not isinstance(password, str) or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400
    if len(password) > 128:
        return jsonify({'error': 'Password cannot exceed 128 characters.'}), 400

    if not display_name:
        display_name = raw_username
    elif len(display_name) > 80:
        display_name = display_name[:80]

    existing = User.query.filter_by(username=raw_username).first()
    if existing:
        return jsonify({'error': 'This username is already taken.'}), 409

    user = User(
        username=raw_username,
        display_name=display_name,
        is_online=True,
        last_seen=datetime.utcnow(),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    resp = make_response(jsonify({
        'message': 'Registration successful.',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(viewer_id=user.id),
    }), 201)
    return _attach_media_cookie(resp, access_token)


@auth_bp.route('/login', methods=['POST'])
def login():
    allowed, retry_after = check_rate_limit('auth_login', max_requests=15, window_seconds=300)
    if not allowed:
        return jsonify({
            'error': 'Too many login attempts. Please wait before trying again.',
            'retry_after_seconds': retry_after,
        }), 429

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip().lstrip('@').lower()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': 'Username and password are required.'}), 400

    user = User.query.filter_by(username=username, is_deleted=False).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password.'}), 401

    if not user.is_active:
        return jsonify({'error': 'This account has been deactivated.'}), 403

    user.touch_online()
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    resp = make_response(jsonify({
        'message': 'Signed in successfully.',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(viewer_id=user.id),
    }), 200)
    return _attach_media_cookie(resp, access_token)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, is_deleted=False, is_active=True).first()
    if not user:
        return jsonify({'error': 'Invalid session.'}), 401
    user.touch_online()
    db.session.commit()
    access_token = create_access_token(identity=user_id)
    resp = make_response(jsonify({'access_token': access_token}), 200)
    return _attach_media_cookie(resp, access_token)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if user:
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.session.commit()
    resp = make_response(jsonify({'message': 'Signed out successfully.'}), 200)
    resp.delete_cookie('reyno_media_token', path='/api/v1/media')
    return resp


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, is_deleted=False).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    user.touch_online()
    db.session.commit()
    return jsonify({'user': user.to_dict(viewer_id=user.id)}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id, is_deleted=False).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    data = request.get_json(silent=True) or {}
    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''

    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect.'}), 400
    if not isinstance(new_password, str) or len(new_password) < 6:
        return jsonify({'error': 'New password must be at least 6 characters long.'}), 400
    if len(new_password) > 128:
        return jsonify({'error': 'New password cannot exceed 128 characters.'}), 400

    user.set_password(new_password)
    db.session.commit()
    return jsonify({'message': 'Password updated successfully.'}), 200
