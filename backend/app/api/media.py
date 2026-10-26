from datetime import datetime, timedelta
import os
import re
import uuid
from PIL import Image
from flask import Blueprint, request, jsonify, current_app, Response, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.media import MediaFile
from app.models.user import User
from app.services.app_settings import VIDEO_MAX_BYTES, effective_limit_for, limits_payload_for_user
from app.services.retention_maintenance import RETENTION_HOURS

media_bp = Blueprint('media', __name__)

ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'webp'},
    'video': {'mp4', 'mov', 'webm'},
    'voice': {'ogg', 'mp3', 'wav', 'm4a', 'aac', 'webm', 'opus'},
    'sticker': {'webp', 'png'},
}

DISALLOWED_EXTENSIONS = {
    'gif': 'Sending GIFs is not supported in Reyno Messenger Lite.',
    'pdf': 'Sending files is not supported in Reyno Messenger Lite.',
    'doc': 'Sending files is not supported in Reyno Messenger Lite.',
    'docx': 'Sending files is not supported in Reyno Messenger Lite.',
    'xls': 'Sending files is not supported in Reyno Messenger Lite.',
    'xlsx': 'Sending files is not supported in Reyno Messenger Lite.',
    'zip': 'Sending files is not supported in Reyno Messenger Lite.',
    'rar': 'Sending files is not supported in Reyno Messenger Lite.',
    'txt': 'Sending files is not supported in Reyno Messenger Lite.',
    'apk': 'Sending files is not supported in Reyno Messenger Lite.',
    'exe': 'Sending files is not supported in Reyno Messenger Lite.',
}

_RANGE_RE = re.compile(r'bytes=(\d*)-(\d*)')


def _ext_of(filename: str) -> str:
    if not filename or '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower().strip()


def _strip_exif_and_verify_image(filepath: str, ext: str) -> tuple[int, int]:
    """Verify image integrity and strip all EXIF/GPS/camera metadata in-place."""
    with Image.open(filepath) as img:
        img.verify()
    with Image.open(filepath) as img:
        width, height = img.size
        # Re-encode without EXIF/info metadata for user privacy in high-risk regions
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA' if ext in ('png', 'webp') else 'RGB')
        clean = Image.new(img.mode, img.size)
        clean.putdata(list(img.getdata()))
        fmt = 'JPEG' if ext in ('jpg', 'jpeg') else ('WEBP' if ext == 'webp' else 'PNG')
        if fmt == 'JPEG' and clean.mode != 'RGB':
            clean = clean.convert('RGB')
        clean.save(filepath, format=fmt, quality=90, optimize=True)
        return width, height


@media_bp.route('/limits', methods=['GET'])
@jwt_required()
def get_my_upload_limits():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify(limits_payload_for_user(user)), 200


@media_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()

    if 'file' not in request.files:
        return jsonify({'error': 'No file was provided.'}), 400

    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'No file was selected.'}), 400

    requested_type = (request.form.get('type') or '').strip().lower()
    if requested_type in ('file', 'document', 'audio', 'music'):
        return jsonify({'error': 'Sending files is not supported in Reyno Messenger Lite.'}), 400
    if requested_type == 'gif':
        return jsonify({'error': 'Sending GIFs is not supported in Reyno Messenger Lite.'}), 400
    if requested_type in ('video_note', 'round_video'):
        return jsonify({'error': 'Video notes are not supported in Reyno Messenger Lite.'}), 400

    ext = _ext_of(file.filename)
    if ext in DISALLOWED_EXTENSIONS:
        return jsonify({'error': DISALLOWED_EXTENSIONS[ext]}), 400

    # Determine file_type
    file_type = None
    if requested_type in ALLOWED_EXTENSIONS and ext in ALLOWED_EXTENSIONS[requested_type]:
        file_type = requested_type
    elif requested_type == 'voice' and ext in ALLOWED_EXTENSIONS['voice']:
        file_type = 'voice'
    else:
        for ftype, exts in ALLOWED_EXTENSIONS.items():
            if ext in exts:
                # Note: .webm can be voice or video; respect requested_type if given
                if ext == 'webm' and requested_type == 'voice':
                    file_type = 'voice'
                else:
                    file_type = ftype
                break

    if not file_type:
        return jsonify({
            'error': 'Unsupported file format. Only photos (JPG/PNG/WebP), videos (<10 MB MP4/WebM/MOV), voice messages, and stickers are allowed.'
        }), 400

    # Measure file size before saving
    try:
        file.stream.seek(0, os.SEEK_END)
        stream_size = file.stream.tell()
        file.stream.seek(0)
    except Exception:
        stream_size = 0

    if stream_size <= 0:
        return jsonify({'error': 'Uploaded file is empty.'}), 400

    user = User.query.get(user_id)
    if file_type == 'video':
        if stream_size >= VIDEO_MAX_BYTES:
            return jsonify({
                'error': 'Video file size must be under 10 MB.',
                'code': 'video_too_large',
                'limit_bytes': VIDEO_MAX_BYTES,
                'limit_mb': 10,
            }), 413
    else:
        max_bytes = effective_limit_for(user, file_type)
        if stream_size > max_bytes:
            return jsonify({
                'error': f'File size exceeds the maximum allowed limit ({max_bytes // (1024 * 1024)} MB).',
                'code': 'file_too_large',
                'limit_bytes': max_bytes,
            }), 413

    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    unique_name = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(upload_dir, unique_name)
    file.save(filepath)

    actual_size = os.path.getsize(filepath)
    if file_type == 'video' and actual_size >= VIDEO_MAX_BYTES:
        try:
            os.remove(filepath)
        except OSError:
            pass
        return jsonify({
            'error': 'Video file size must be under 10 MB.',
            'code': 'video_too_large',
            'limit_bytes': VIDEO_MAX_BYTES,
            'limit_mb': 10,
        }), 413

    width = None
    height = None
    if file_type in ('image', 'sticker'):
        try:
            width, height = _strip_exif_and_verify_image(filepath, ext)
            actual_size = os.path.getsize(filepath)
        except Exception:
            try:
                os.remove(filepath)
            except OSError:
                pass
            return jsonify({'error': 'Invalid or corrupted image file.'}), 400

    duration = request.form.get('duration', type=float)
    mime_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
        'mp4': 'video/mp4',
        'mov': 'video/quicktime',
        'webm': 'audio/webm' if file_type == 'voice' else 'video/webm',
        'ogg': 'audio/ogg',
        'opus': 'audio/ogg',
        'm4a': 'audio/mp4',
        'aac': 'audio/aac',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
    }
    mime_type = mime_map.get(ext, file.mimetype or 'application/octet-stream')

    media = MediaFile(
        uploaded_by=user_id,
        filename=unique_name,
        original_name=None,  # Never store user's original device filename for privacy
        file_path=filepath,
        file_type=file_type,
        mime_type=mime_type,
        file_size=actual_size,
        width=width,
        height=height,
        duration=duration,
    )
    db.session.add(media)
    db.session.commit()

    return jsonify({'media': media.to_dict()}), 201


@media_bp.route('/<media_id>', methods=['GET'])
def serve_media(media_id):
    media = MediaFile.query.filter_by(id=media_id, is_deleted=False).first()
    if not media:
        return jsonify({'error': 'Media file not found or has expired.'}), 404

    cutoff = datetime.utcnow() - timedelta(hours=RETENTION_HOURS)
    if media.created_at and media.created_at <= cutoff and media.file_type != 'sticker':
        return jsonify({'error': 'This media file has expired after 72 hours.'}), 410

    if not media.file_path or not os.path.isfile(media.file_path):
        return jsonify({'error': 'Media file is no longer available on disk.'}), 404

    file_size = os.path.getsize(media.file_path)
    mime = media.mime_type or 'application/octet-stream'
    range_header = request.headers.get('Range')

    if range_header:
        m = _RANGE_RE.match(range_header.strip())
        if m:
            start_str, end_str = m.groups()
            if start_str == '':
                suffix = int(end_str) if end_str else 0
                start = max(0, file_size - suffix)
                end = file_size - 1
            else:
                start = int(start_str)
                end = int(end_str) if end_str else file_size - 1
            if start >= file_size or start > end:
                resp = Response(status=416)
                resp.headers['Content-Range'] = f'bytes */{file_size}'
                return resp
            end = min(end, file_size - 1)
            length = end - start + 1
            with open(media.file_path, 'rb') as f:
                f.seek(start)
                chunk = f.read(length)
            resp = Response(chunk, status=206, mimetype=mime, direct_passthrough=True)
            resp.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            resp.headers['Accept-Ranges'] = 'bytes'
            resp.headers['Content-Length'] = str(length)
            resp.headers['Cache-Control'] = 'private, max-age=3600'
            resp.headers['X-Content-Type-Options'] = 'nosniff'
            return resp

    response = send_file(media.file_path, mimetype=mime, conditional=True)
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Cache-Control'] = 'private, max-age=3600'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response
