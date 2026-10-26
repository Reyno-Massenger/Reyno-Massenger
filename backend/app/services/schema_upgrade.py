"""Idempotent database initialization and default sticker pack seeding for Reyno Messenger Lite."""
from sqlalchemy import inspect, text
from app import db


DEFAULT_STICKER_PACKS = [
    {
        'name': 'reyno_classics',
        'title': 'Reyno Classics',
        'emojis': ['😀', '😂', '🥰', '😎', '🤩', '🥳', '🤔', '😴', '😭', '🤯', '🔥', '❤️', '👍', '🙏', '🎉', '🚀'],
    },
    {
        'name': 'vibes_reactions',
        'title': 'Vibes & Reactions',
        'emojis': ['👋', '🙌', '👏', '🤝', '✌️', '🫶', '💯', '⚡', '🌟', '💎', '☕', '🍕', '🎵', '🏆', '🛡️', '🌈'],
    },
]


def upgrade_schema():
    additions = {
        'chat_members': {
            'is_archived': 'BOOLEAN NOT NULL DEFAULT 0',
            'archived_at': 'DATETIME NULL',
            'pinned_at': 'DATETIME NULL',
        },
        'messages': {
            'latitude': 'FLOAT NULL',
            'longitude': 'FLOAT NULL',
            'location_title': 'VARCHAR(512) NULL',
        },
    }
    with db.engine.begin() as connection:
        for table, columns in additions.items():
            inspector = inspect(connection)
            if not inspector.has_table(table):
                continue
            existing = {column['name'] for column in inspector.get_columns(table)}
            for column, definition in columns.items():
                if column not in existing:
                    connection.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {definition}'))

    from app.models.sticker import StickerPack, Sticker  # noqa: F401
    from app.models.message import MessageReaction  # noqa: F401
    from app.models.settings import AppSetting  # noqa: F401

    db.metadata.create_all(bind=db.engine)
    _seed_default_stickers()


def _seed_default_stickers():
    from app.models.sticker import StickerPack, Sticker

    try:
        if StickerPack.query.count() > 0:
            return
        for pack_def in DEFAULT_STICKER_PACKS:
            pack = StickerPack(
                name=pack_def['name'],
                title=pack_def['title'],
                is_featured=True,
                is_animated=False,
            )
            db.session.add(pack)
            db.session.flush()
            for idx, emoji in enumerate(pack_def['emojis']):
                db.session.add(
                    Sticker(
                        pack_id=pack.id,
                        emoji=emoji,
                        position=idx,
                    )
                )
        db.session.commit()
    except Exception:
        db.session.rollback()
