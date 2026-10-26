from app import db
from datetime import datetime
import uuid

class StickerPack(db.Model):
    __tablename__ = 'sticker_packs'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)  # slug like cute_cats
    title = db.Column(db.String(200), nullable=False)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    is_featured = db.Column(db.Boolean, default=True)
    is_animated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stickers = db.relationship('Sticker', backref='pack', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_stickers=False):
        data = {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'thumbnail_url': self.thumbnail_url,
            'is_featured': self.is_featured,
            'is_animated': self.is_animated,
            'stickers_count': self.stickers.filter_by(is_deleted=False).count() if hasattr(self, 'stickers') else 0,
            'created_at': self.created_at.isoformat() + 'Z' if self.created_at else None,
        }
        if include_stickers:
            data['stickers'] = [s.to_dict() for s in self.stickers.filter_by(is_deleted=False).order_by(Sticker.position.asc()).all()]
        return data


class Sticker(db.Model):
    __tablename__ = 'stickers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pack_id = db.Column(db.String(36), db.ForeignKey('sticker_packs.id'), nullable=False, index=True)
    # Either emoji representation or media file
    emoji = db.Column(db.String(20), nullable=True)  # associated emoji like 😀
    file_url = db.Column(db.String(500), nullable=True)  # URL to webp/png image
    media_id = db.Column(db.String(36), db.ForeignKey('media_files.id'), nullable=True)
    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)
    position = db.Column(db.Integer, default=0)

    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pack_id': self.pack_id,
            'emoji': self.emoji,
            'file_url': self.file_url,
            'media_id': self.media_id,
            'width': self.width,
            'height': self.height,
            'position': self.position,
        }
