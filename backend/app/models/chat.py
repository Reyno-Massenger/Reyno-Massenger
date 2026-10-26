from datetime import datetime
import uuid
from app import db
from app.services.timestamps import utc_iso


class Chat(db.Model):
    __tablename__ = 'chats'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_type = db.Column(db.String(20), nullable=False)  # 'private', 'group', 'channel'
    name = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    is_public = db.Column(db.Boolean, default=True)

    is_deleted = db.Column(db.Boolean, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members = db.relationship('ChatMember', backref='chat', lazy='dynamic')
    messages = db.relationship('Message', backref='chat', lazy='dynamic')

    def to_dict(self, current_user_id=None, last_message=None):
        active_members_q = self.members.filter_by(is_deleted=False)
        members_count = active_members_q.count()
        data = {
            'id': self.id,
            'chat_type': self.chat_type,
            'name': self.name,
            'description': self.description,
            'username': self.username,
            'is_public': bool(self.is_public),
            'created_by': self.created_by,
            'members_count': members_count,
            'created_at': utc_iso(self.created_at),
            'updated_at': utc_iso(self.updated_at),
        }

        if current_user_id:
            my_member = active_members_q.filter_by(user_id=current_user_id).first()
            data['my_role'] = my_member.role if my_member else None
            data['unread_count'] = my_member.unread_count if my_member else 0
            data['is_muted'] = bool(my_member.is_muted) if my_member else False
            data['is_archived'] = bool(my_member.is_archived) if my_member else False
            data['is_pinned'] = bool(my_member and my_member.pinned_at is not None)
            data['pinned_at'] = utc_iso(my_member.pinned_at) if my_member else None

            if self.chat_type == 'private':
                other_member = active_members_q.filter(
                    ChatMember.user_id != current_user_id
                ).first()
                if other_member:
                    from app.models.user import User, BlockedUser
                    other_user = User.query.get(other_member.user_id)
                    if other_user and not other_user.is_deleted:
                        data['other_user'] = other_user.to_dict(viewer_id=current_user_id)
                        data['name'] = other_user.display_name or other_user.username
                        data['username'] = other_user.username
                        is_blocked = BlockedUser.query.filter_by(
                            blocker_id=current_user_id,
                            blocked_id=other_user.id,
                            is_deleted=False,
                        ).first() is not None
                        is_blocked_by = BlockedUser.query.filter_by(
                            blocker_id=other_user.id,
                            blocked_id=current_user_id,
                            is_deleted=False,
                        ).first() is not None
                        data['is_blocked'] = is_blocked
                        data['is_blocked_by'] = is_blocked_by

        if last_message is not None:
            data['last_message'] = last_message

        return data


class ChatMember(db.Model):
    __tablename__ = 'chat_members'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = db.Column(db.String(36), db.ForeignKey('chats.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(20), default='member')  # 'owner', 'admin', 'member'
    is_muted = db.Column(db.Boolean, default=False)
    is_archived = db.Column(db.Boolean, default=False, index=True)
    archived_at = db.Column(db.DateTime, nullable=True)
    pinned_at = db.Column(db.DateTime, nullable=True, index=True)
    unread_count = db.Column(db.Integer, default=0)
    last_read_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('chat_id', 'user_id', name='uq_chat_user'),
        db.Index('ix_chat_members_user_chat', 'user_id', 'chat_id'),
    )
