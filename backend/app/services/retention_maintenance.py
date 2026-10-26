"""Automatic 72-hour MEDIA retention & manual storage cleanup for Reyno Lite.

IMPORTANT (matches the original Reyno): this cleanup is for MEDIA ONLY.
- Only the uploaded file blobs (photos, videos, voice messages) attached to
  chat messages and older than 72 hours are removed from disk.
- Chats, message rows, text, captions, reactions and media metadata are
  NEVER deleted by retention. The message stays in the conversation and is
  flagged ``media_expired`` so clients show an "expired media" placeholder.
- Sticker assets are protected and never expired.
- The minimal Admin Panel storage cleanup follows the same rule: it frees
  media files only, never chats or messages.
"""
from datetime import datetime, timedelta
import os
import time
from flask import current_app

from app import db
from app.models.media import MediaFile
from app.models.message import DeletedMessage, Message, MessageReaction
from app.models.settings import AppSetting
from app.models.sticker import Sticker
from app.services.timestamps import utc_iso

RETENTION_HOURS = 72
_AUTO_CHECK_INTERVAL_SECONDS = 600  # Check at most once every 10 minutes per worker
_last_auto_check_monotonic = 0.0


def _protected_sticker_media_ids() -> set[str]:
    try:
        rows = (
            db.session.query(Sticker.media_id)
            .filter(Sticker.is_deleted.is_(False), Sticker.media_id.isnot(None))
            .all()
        )
        return {r[0] for r in rows if r[0]}
    except Exception:
        return set()


def _safe_unlink(file_path: str | None) -> int:
    """Delete a file from disk if it exists and return freed bytes."""
    if not file_path:
        return 0
    try:
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            os.remove(file_path)
            return size
    except OSError:
        pass
    return 0


def _record_last_cleanup(now: datetime):
    try:
        setting = db.session.get(AppSetting, 'last_retention_cleanup_at')
        iso_val = utc_iso(now)
        if setting is None:
            db.session.add(AppSetting(key='last_retention_cleanup_at', value=iso_val))
        else:
            setting.value = iso_val
        db.session.commit()
    except Exception:
        db.session.rollback()


def get_last_cleanup_iso() -> str | None:
    try:
        setting = db.session.get(AppSetting, 'last_retention_cleanup_at')
        return setting.value if setting else None
    except Exception:
        return None


# Message types whose *attached file* may expire. Text/location/sticker
# messages have no expirable blob and are untouched. (Original: CHAT_ATTACHMENT_TYPES)
CHAT_ATTACHMENT_TYPES = ('image', 'video', 'voice')


def run_retention_maintenance(now: datetime | None = None, retention_hours: int = RETENTION_HOURS) -> dict:
    """Expire media blobs older than `retention_hours` (default 72h).

    Media-only: chats and messages are never deleted here. Referencing
    messages keep their row/text and are flagged media_expired; the
    MediaFile row (metadata) is kept but marked deleted so the file can
    no longer be served.
    """
    now = now or datetime.utcnow()
    cutoff = now - timedelta(hours=retention_hours)
    protected_media = _protected_sticker_media_ids()

    # Media that is actually attached to a chat attachment message.
    attached_media_ids = {
        row[0]
        for row in db.session.query(Message.media_id).filter(
            Message.media_id.isnot(None),
            Message.message_type.in_(CHAT_ATTACHMENT_TYPES),
        ).all()
    }

    freed_bytes = 0
    purged_media_count = 0

    expired_media = MediaFile.query.filter(
        MediaFile.created_at.isnot(None),
        MediaFile.created_at <= cutoff,
        MediaFile.is_deleted.is_(False),
    ).all()

    for media in expired_media:
        if media.id in protected_media or media.id not in attached_media_ids:
            continue
        freed_bytes += _safe_unlink(media.file_path)
        media.is_deleted = True
        media.deleted_at = now
        purged_media_count += 1
        # Keep the message (and its text/caption); only flag its media gone.
        Message.query.filter_by(media_id=media.id).update(
            {'media_expired': True, 'media_expired_at': now},
            synchronize_session=False,
        )

    db.session.commit()
    _record_last_cleanup(now)

    return {
        'ok': True,
        'retention_hours': retention_hours,
        'purged_messages': 0,  # retention NEVER deletes messages/chats
        'purged_chats': 0,
        'purged_media_files': purged_media_count,
        'freed_bytes': freed_bytes,
        'cleaned_at': utc_iso(now),
    }


def clear_server_storage(mode: str = 'all') -> dict:
    """Admin manual storage cleanup (MEDIA ONLY, like the original).

    - mode='expired': expire media blobs older than 72 hours.
    - mode='all': delete all non-sticker uploaded media blobs now and flag
      referencing messages media_expired.
    Chats, messages, reactions and users are never touched by either mode.
    """
    now = datetime.utcnow()
    if mode == 'expired':
        return run_retention_maintenance(now=now, retention_hours=RETENTION_HOURS)

    protected_media = _protected_sticker_media_ids()
    freed_bytes = 0
    purged_media_count = 0

    all_media = MediaFile.query.filter(MediaFile.is_deleted.is_(False)).all()
    for media in all_media:
        if media.id in protected_media:
            continue
        freed_bytes += _safe_unlink(media.file_path)
        media.is_deleted = True
        media.deleted_at = now
        purged_media_count += 1
        Message.query.filter_by(media_id=media.id).update(
            {'media_expired': True, 'media_expired_at': now},
            synchronize_session=False,
        )

    # Also sweep any orphan files inside UPLOAD_FOLDER
    upload_folder = current_app.config.get('UPLOAD_FOLDER') if current_app else None
    if upload_folder and os.path.isdir(upload_folder):
        for entry in os.listdir(upload_folder):
            if entry.startswith('.'):
                continue
            full_path = os.path.join(upload_folder, entry)
            if os.path.isfile(full_path):
                freed_bytes += _safe_unlink(full_path)

    db.session.commit()
    _record_last_cleanup(now)

    return {
        'ok': True,
        'mode': 'all',
        'purged_messages': 0,  # storage cleanup NEVER deletes messages/chats
        'purged_chats': 0,
        'purged_media_files': purged_media_count,
        'freed_bytes': freed_bytes,
        'cleaned_at': utc_iso(now),
    }


def get_storage_stats() -> dict:
    """Return aggregate storage metrics without exposing any user/chat data."""
    upload_folder = current_app.config.get('UPLOAD_FOLDER') if current_app else None
    upload_bytes = 0
    upload_files_count = 0
    if upload_folder and os.path.isdir(upload_folder):
        for root, _dirs, files in os.walk(upload_folder):
            for f in files:
                if f.startswith('.'):
                    continue
                fp = os.path.join(root, f)
                try:
                    upload_bytes += os.path.getsize(fp)
                    upload_files_count += 1
                except OSError:
                    pass

    db_bytes = 0
    try:
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '') if current_app else ''
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '', 1)
            if not os.path.isabs(db_path) and current_app:
                candidates = [
                    db_path,
                    os.path.join(current_app.instance_path, db_path),
                    os.path.join(os.path.dirname(current_app.root_path), db_path),
                ]
                for c in candidates:
                    if os.path.isfile(c):
                        db_bytes = os.path.getsize(c)
                        break
            elif os.path.isfile(db_path):
                db_bytes = os.path.getsize(db_path)
    except Exception:
        pass

    return {
        'upload_files_count': upload_files_count,
        'upload_bytes': upload_bytes,
        'upload_mb': round(upload_bytes / (1024 * 1024), 2),
        'db_bytes': db_bytes,
        'db_mb': round(db_bytes / (1024 * 1024), 2),
        'total_bytes': upload_bytes + db_bytes,
        'total_mb': round((upload_bytes + db_bytes) / (1024 * 1024), 2),
        'retention_hours': RETENTION_HOURS,
        'last_cleanup_at': get_last_cleanup_iso(),
    }


def maybe_run_auto_retention():
    """Lightweight hook called during requests to trigger 72h cleanup periodically."""
    global _last_auto_check_monotonic
    now_mono = time.monotonic()
    if (now_mono - _last_auto_check_monotonic) < _AUTO_CHECK_INTERVAL_SECONDS:
        return
    _last_auto_check_monotonic = now_mono
    try:
        run_retention_maintenance(retention_hours=RETENTION_HOURS)
    except Exception:
        db.session.rollback()
