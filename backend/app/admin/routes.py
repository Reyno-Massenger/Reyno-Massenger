"""Minimal Privacy-Preserving Web Admin Panel for Reyno Messenger Lite.

Strictly restricted to:
1. Adding a user (username + password)
2. Removing a user (by username)
3. Clearing server storage space (72h expired cleanup or full media/storage wipe)

Zero visibility into user profiles, online status, devices, chats, or messages.
"""
from datetime import datetime
from functools import wraps
import hmac
import os
import re
import secrets
from flask import (
    Blueprint,
    render_template_string,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from app import db
from app.admin.ui import ADMIN_CSS
from app.models.chat import ChatMember
from app.models.message import Message, DeletedMessage, MessageReaction
from app.models.user import User, BlockedUser
from app.services.rate_limiter import check_rate_limit
from app.services.retention_maintenance import clear_server_storage, get_storage_stats

admin_bp = Blueprint('admin', __name__)

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]{3,32}$')


def _get_admin_credentials() -> tuple[str, str]:
    username = os.getenv('ADMIN_USERNAME', 'admin').strip() or 'admin'
    password = os.getenv('ADMIN_PASSWORD', 'admin123').strip() or 'admin123'
    return username, password


def _csrf_token() -> str:
    token = session.get('_admin_csrf')
    if not token:
        token = secrets.token_hex(24)
        session['_admin_csrf'] = token
    return token


def _verify_csrf() -> bool:
    expected = session.get('_admin_csrf')
    provided = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token') or ''
    return bool(expected and provided and hmac.compare_digest(expected, provided))


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('reyno_admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


def permanently_remove_user(user: User):
    """Permanently delete a user and their memberships without exposing their data."""
    uid = user.id
    BlockedUser.query.filter(
        (BlockedUser.blocker_id == uid) | (BlockedUser.blocked_id == uid)
    ).delete(synchronize_session=False)
    MessageReaction.query.filter_by(user_id=uid).delete(synchronize_session=False)
    DeletedMessage.query.filter_by(user_id=uid).delete(synchronize_session=False)
    ChatMember.query.filter_by(user_id=uid).delete(synchronize_session=False)

    # Remove messages sent by this user
    user_msgs = Message.query.filter_by(sender_id=uid).all()
    user_msg_ids = [m.id for m in user_msgs]
    if user_msg_ids:
        MessageReaction.query.filter(MessageReaction.message_id.in_(user_msg_ids)).delete(synchronize_session=False)
        DeletedMessage.query.filter(DeletedMessage.message_id.in_(user_msg_ids)).delete(synchronize_session=False)
        Message.query.filter(Message.reply_to_id.in_(user_msg_ids)).update({'reply_to_id': None}, synchronize_session=False)
        for m in user_msgs:
            db.session.delete(m)

    db.session.delete(user)
    db.session.commit()


LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reyno Messenger Lite — Admin Sign In</title>
  <style>{{ css }}</style>
</head>
<body>
  <div class="container login-wrap">
    <div class="card">
      <div class="brand" style="margin-bottom: 20px;">
        <img src="/assets/icons/reyno_logo_dark.png" alt="Reyno">
        <div>
          <h1>Reyno Messenger Lite</h1>
          <p>Minimal Server Administration</p>
        </div>
      </div>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, msg in messages %}
          <div class="alert alert-{{ 'error' if category == 'error' else 'success' }}">{{ msg }}</div>
        {% endfor %}
      {% endwith %}
      <form method="POST" action="{{ url_for('admin.login') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div style="margin-bottom: 14px;">
          <label for="username">Admin Username</label>
          <input id="username" type="text" name="username" required autocomplete="username">
        </div>
        <div style="margin-bottom: 20px;">
          <label for="password">Admin Password</label>
          <input id="password" type="password" name="password" required autocomplete="current-password">
        </div>
        <button type="submit" class="btn btn-primary" style="width: 100%;">Sign In</button>
      </form>
    </div>
  </div>
</body>
</html>
"""

PANEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reyno Messenger Lite — Admin Panel</title>
  <style>{{ css }}</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="brand">
        <img src="/assets/icons/reyno_logo_dark.png" alt="Reyno">
        <div>
          <h1>Reyno Messenger Lite — Admin Panel</h1>
          <p>Strictly limited to User Add/Remove &amp; Server Storage Cleanup</p>
        </div>
      </div>
      <form method="POST" action="{{ url_for('admin.logout') }}">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit" class="btn btn-outline">Sign Out</button>
      </form>
    </div>

    <div class="privacy-banner">
      <strong>Zero-Knowledge Privacy Enforcement:</strong> User profiles, online status, private chats, groups, channels, and messages are encrypted at rest and completely inaccessible from this panel.
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, msg in messages %}
        <div class="alert alert-{{ 'error' if category == 'error' else 'success' }}">{{ msg }}</div>
      {% endfor %}
    {% endwith %}

    <!-- 1. Add User -->
    <div class="card">
      <h2>Add User Account</h2>
      <p class="subtitle">Create a new user account with a username and password.</p>
      <form method="POST" action="{{ url_for('admin.add_user') }}" class="form-grid">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div>
          <label for="add-username">Username</label>
          <input id="add-username" type="text" name="username" placeholder="e.g. alice" required pattern="[a-zA-Z0-9_]{3,32}">
        </div>
        <div>
          <label for="add-password">Password</label>
          <input id="add-password" type="password" name="password" placeholder="Min 6 characters" required minlength="6">
        </div>
        <button type="submit" class="btn btn-primary">Add User</button>
      </form>
    </div>

    <!-- 2. Remove User -->
    <div class="card">
      <h2>Remove User Account</h2>
      <p class="subtitle">Permanently delete a user account by entering their username. User personal data and chat history are never displayed.</p>
      <form method="POST" action="{{ url_for('admin.remove_user') }}" class="form-grid" style="grid-template-columns: 1fr auto;">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <div>
          <label for="remove-username">Username to Remove</label>
          <input id="remove-username" type="text" name="username" placeholder="e.g. alice" required>
        </div>
        <button type="submit" class="btn btn-danger" onclick="return confirm('Permanently remove this user account?');">Remove User</button>
      </form>
    </div>

    <!-- 3. Clear Server Storage Space -->
    <div class="card">
      <h2>Server Storage &amp; Automatic 72-Hour Cleanup</h2>
      <p class="subtitle">Only uploaded media files (photos, videos, voice) are automatically removed every 72 hours — chats and messages are never deleted. You can also free server disk space manually below.</p>
      <div class="stats-row">
        <div class="stat-box">
          <div class="label">Media Upload Storage</div>
          <div class="value">{{ storage.upload_mb }} MB</div>
        </div>
        <div class="stat-box">
          <div class="label">Stored Media Files</div>
          <div class="value">{{ storage.upload_files_count }}</div>
        </div>
        <div class="stat-box">
          <div class="label">Auto-Retention Policy</div>
          <div class="value">{{ storage.retention_hours }} Hours</div>
        </div>
      </div>
      <div class="actions-row">
        <form method="POST" action="{{ url_for('admin.clear_storage') }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <input type="hidden" name="mode" value="expired">
          <button type="submit" class="btn btn-primary">Purge Expired Media (&gt; 72h)</button>
        </form>
        <form method="POST" action="{{ url_for('admin.clear_storage') }}">
          <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
          <input type="hidden" name="mode" value="all">
          <button type="submit" class="btn btn-danger" onclick="return confirm('Clear ALL server media files and message storage immediately?');">Clear All Server Storage Space</button>
        </form>
      </div>
    </div>
  </div>
</body>
</html>
"""


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        allowed, _retry = check_rate_limit('admin_login', max_requests=10, window_seconds=300)
        if not allowed:
            flash('Too many login attempts. Please try again later.', 'error')
            return render_template_string(LOGIN_HTML, css=ADMIN_CSS, csrf_token=_csrf_token()), 429

        if not _verify_csrf():
            flash('Invalid security token. Please try again.', 'error')
            return render_template_string(LOGIN_HTML, css=ADMIN_CSS, csrf_token=_csrf_token()), 400

        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        expected_user, expected_pass = _get_admin_credentials()

        if hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_pass):
            session.clear()
            session['reyno_admin_logged_in'] = True
            _csrf_token()
            return redirect(url_for('admin.index'))

        flash('Invalid admin credentials.', 'error')
        return render_template_string(LOGIN_HTML, css=ADMIN_CSS, csrf_token=_csrf_token()), 401

    return render_template_string(LOGIN_HTML, css=ADMIN_CSS, csrf_token=_csrf_token())


@admin_bp.route('/logout', methods=['POST'])
@admin_required
def logout():
    session.clear()
    return redirect(url_for('admin.login'))


@admin_bp.route('/', methods=['GET'])
@admin_required
def index():
    storage = get_storage_stats()
    return render_template_string(
        PANEL_HTML,
        css=ADMIN_CSS,
        csrf_token=_csrf_token(),
        storage=storage,
    )


@admin_bp.route('/users/add', methods=['POST'])
@admin_required
def add_user():
    if not _verify_csrf():
        flash('Invalid CSRF token.', 'error')
        return redirect(url_for('admin.index'))

    raw_username = (request.form.get('username') or '').strip().lstrip('@').lower()
    password = request.form.get('password') or ''

    if not USERNAME_RE.match(raw_username):
        flash('Username must be 3–32 characters using English letters, numbers, and underscores.', 'error')
        return redirect(url_for('admin.index'))

    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('admin.index'))

    if User.query.filter_by(username=raw_username).first():
        flash(f'User @{raw_username} already exists.', 'error')
        return redirect(url_for('admin.index'))

    user = User(
        username=raw_username,
        display_name=raw_username,
        is_online=False,
        last_seen=datetime.utcnow(),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash(f'User @{raw_username} created successfully.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/users/remove', methods=['POST'])
@admin_required
def remove_user():
    if not _verify_csrf():
        flash('Invalid CSRF token.', 'error')
        return redirect(url_for('admin.index'))

    raw_username = (request.form.get('username') or '').strip().lstrip('@').lower()
    if not raw_username:
        flash('Please enter a username to remove.', 'error')
        return redirect(url_for('admin.index'))

    user = User.query.filter_by(username=raw_username).first()
    if not user:
        flash(f'User @{raw_username} was not found.', 'error')
        return redirect(url_for('admin.index'))

    permanently_remove_user(user)
    flash(f'User @{raw_username} has been permanently removed.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/storage/clear', methods=['POST'])
@admin_required
def clear_storage():
    if not _verify_csrf():
        flash('Invalid CSRF token.', 'error')
        return redirect(url_for('admin.index'))

    mode = (request.form.get('mode') or 'all').strip().lower()
    if mode not in ('all', 'expired'):
        mode = 'all'

    result = clear_server_storage(mode=mode)
    freed_mb = round(result.get('freed_bytes', 0) / (1024 * 1024), 2)
    if mode == 'expired':
        flash(f'Expired media (>72h) cleared ({freed_mb} MB freed).', 'success')
    else:
        flash(f'Server storage space cleared ({freed_mb} MB freed).', 'success')
    return redirect(url_for('admin.index'))
