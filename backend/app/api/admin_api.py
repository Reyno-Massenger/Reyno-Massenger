"""Minimal Privacy-Preserving JSON Admin API for Reyno Messenger Lite.

Strictly limited to:
- POST /api/v1/admin/login (admin authentication)
- POST /api/v1/admin/users (add user)
- DELETE /api/v1/admin/users/<username_or_id> (remove user)
- GET /api/v1/admin/storage (aggregate storage usage only)
- POST /api/v1/admin/storage/clear (clear server storage space)

Zero endpoints for reading user profiles, chats, messages, or activity.
"""
from datetime import datetime, timedelta
from functools import wraps
import hmac
import os
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    verify_jwt_in_request,
    get_jwt,
)
from app import db
from app.admin.routes import permanently_remove_user
from app.models.user import User
from app.services.rate_limiter import check_rate_limit
from app.services.retention_maintenance import clear_server_storage, get_storage_stats

admin_api_bp = Blueprint('admin_api', __name__)

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,32}$')


def _get_admin_credentials() -> tuple[str, str]:
    username = os.getenv('ADMIN_USERNAME', 'admin').strip() or 'admin'
    password = os.getenv('ADMIN_PASSWORD', 'admin123').strip() or 'admin123'
    return username, password


def admin_jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('is_admin'):
                return jsonify({'error': 'Admin privileges required.'}), 403
        except Exception:
            return jsonify({'error': 'Admin authentication required.'}), 401
        return fn(*args, **kwargs)
    return wrapper


@admin_api_bp.route('/login', methods=['POST'])
def admin_login():
    allowed, retry_after = check_rate_limit('admin_api_login', max_requests=10, window_seconds=300)
    if not allowed:
        return jsonify({
            'error': 'Too many login attempts. Please wait before trying again.',
            'retry_after_seconds': retry_after,
        }), 429

    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    expected_user, expected_pass = _get_admin_credentials()

    if not (hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_pass)):
        return jsonify({'error': 'Invalid admin credentials.'}), 401

    token = create_access_token(
        identity='__reyno_admin__',
        additional_claims={'is_admin': True},
        expires_delta=timedelta(hours=12),
    )
    return jsonify({
        'access_token': token,
        'admin': {'username': expected_user},
    }), 200


@admin_api_bp.route('/users', methods=['POST'])
@admin_jwt_required
def add_user():
    data = request.get_json(silent=True) or {}
    raw_username = (data.get('username') or '').strip().lstrip('@').lower()
    password = data.get('password') or ''
    display_name = (data.get('display_name') or '').strip() or raw_username

    if not USERNAME_RE.match(raw_username):
        return jsonify({
            'error': 'Username must be 3–32 characters using English letters, numbers, and underscores.'
        }), 400
    if not isinstance(password, str) or len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    if User.query.filter_by(username=raw_username).first():
        return jsonify({'error': 'This username is already taken.'}), 409

    user = User(
        username=raw_username,
        display_name=display_name[:80],
        is_online=False,
        last_seen=datetime.utcnow(),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully.',
        'user': {
            'id': user.id,
            'username': user.username,
        },
    }), 201


@admin_api_bp.route('/users/<identifier>', methods=['DELETE'])
@admin_jwt_required
def remove_user(identifier):
    clean = identifier.strip().lstrip('@').lower()
    user = User.query.filter(
        (User.id == identifier) | (User.username == clean)
    ).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    removed_username = user.username
    permanently_remove_user(user)
    return jsonify({
        'message': 'User removed permanently.',
        'username': removed_username,
    }), 200


@admin_api_bp.route('/storage', methods=['GET'])
@admin_jwt_required
def storage_stats():
    return jsonify({'storage': get_storage_stats()}), 200


@admin_api_bp.route('/storage/clear', methods=['POST'])
@admin_jwt_required
def clear_storage():
    data = request.get_json(silent=True) or {}
    mode = (data.get('mode') or 'all').strip().lower()
    if mode not in ('all', 'expired'):
        return jsonify({'error': 'Mode must be "all" or "expired".'}), 400

    result = clear_server_storage(mode=mode)
    result['storage'] = get_storage_stats()
    return jsonify(result), 200
