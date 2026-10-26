from datetime import datetime, timedelta
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.services.timestamps import utc_iso

ONLINE_WINDOW_SECONDS = 300


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Online status (always visible in Lite — no Ghost Mode)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    is_active = db.Column(db.Boolean, default=True)
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def touch_online(self):
        self.is_online = True
        self.last_seen = datetime.utcnow()

    @property
    def effective_online(self) -> bool:
        if not self.is_online:
            return False
        if not self.last_seen:
            return True
        return (datetime.utcnow() - self.last_seen) <= timedelta(seconds=ONLINE_WINDOW_SECONDS)

    def to_dict(self, viewer_id=None):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'is_online': self.effective_online,
            'last_seen': utc_iso(self.last_seen),
            'created_at': utc_iso(self.created_at),
        }


class BlockedUser(db.Model):
    __tablename__ = 'blocked_users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    blocker_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    blocked_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('blocker_id', 'blocked_id', name='uq_blocker_blocked'),
    )
