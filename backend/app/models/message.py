from datetime import datetime
import uuid
from sqlalchemy.types import TypeDecorator, Text, String
from app import db
from app.services.crypto_at_rest import encrypt_text, decrypt_text
from app.services.timestamps import utc_iso


class EncryptedText(TypeDecorator):
    """Transparently encrypts text with Fernet before writing to DB and decrypts on read."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_text(value)

    def process_result_value(self, value, dialect):
        return decrypt_text(value)


class EncryptedString(TypeDecorator):
    """Transparently encrypts string with Fernet before writing to DB and decrypts on read."""
    impl = String(512)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt_text(value)

    def process_result_value(self, value, dialect):
        return decrypt_text(value)


ALLOWED_MESSAGE_TYPES = {
    'text',
    'image',
    'video',
    'voice',
    'sticker',
    'location',
    'system',
}


class Message(db.Model):
    __tablename__ = 'messages'
    __table_args__ = (
        db.Index('ix_messages_chat_created_id', 'chat_id', 'created_at', 'id'),
        db.Index('ix_messages_chat_sender_created', 'chat_id', 'sender_id', 'created_at'),
    )

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_id = db.Column(db.String(36), db.ForeignKey('chats.id'), nullable=False, index=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)

    # Allowed in Lite: 'text', 'image', 'video', 'voice', 'sticker', 'location', 'system'
    message_type = db.Column(db.String(20), default='text')
    content = db.Column(EncryptedText, nullable=True)
    media_id = db.Column(db.String(36), db.ForeignKey('media_files.id'), nullable=True)

    # 72-hour automatic media retention tracking
    media_expired = db.Column(db.Boolean, default=False)
    media_expired_at = db.Column(db.DateTime, nullable=True)

    # Reply & Forward
    reply_to_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=True)
    forwarded_from_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    # Edit
    is_edited = db.Column(db.Boolean, default=False)
    edited_at = db.Column(db.DateTime, nullable=True)

    # Pin
    is_pinned = db.Column(db.Boolean, default=False)
    pinned_at = db.Column(db.DateTime, nullable=True)
    pinned_by = db.Column(db.String(36), nullable=True)

    # Static location sharing only (no live location)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_title = db.Column(EncryptedString, nullable=True)

    # Delivery status: 'sent', 'delivered', 'read'
    status = db.Column(db.String(20), default='sent')

    # Soft delete / Two-way delete
    is_deleted = db.Column(db.Boolean, default=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    deleted_by = db.Column(db.String(36), nullable=True)
    is_deleted_for_all = db.Column(db.Boolean, default=False)
    deleted_for_all_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    media = db.relationship('MediaFile', backref='message', uselist=False)
    reply_to = db.relationship('Message', remote_side=[id], backref='replies')

    def to_dict(self):
        from app.services.message_payloads import serialize_messages
        items = serialize_messages([self])
        return items[0] if items else {}


class DeletedMessage(db.Model):
    """Tracks messages deleted only for a specific user (one-sided delete)."""
    __tablename__ = 'deleted_messages'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', name='uq_deleted_msg_user'),
    )


class MessageReaction(db.Model):
    __tablename__ = 'message_reactions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = db.Column(db.String(36), db.ForeignKey('messages.id'), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    emoji = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('message_id', 'user_id', 'emoji', name='uq_msg_user_emoji'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'user_id': self.user_id,
            'emoji': self.emoji,
            'created_at': utc_iso(self.created_at),
        }
