"""Media upload limits and runtime settings for Reyno Messenger Lite."""

MB = 1024 * 1024

# Reyno Messenger Lite strict media limits:
# Videos must be strictly under 10 MB.
VIDEO_MAX_BYTES = 10 * MB

DEFAULT_UPLOAD_LIMITS = {
    'image': 15 * MB,
    'video': VIDEO_MAX_BYTES,
    'voice': 10 * MB,
    'sticker': 5 * MB,
}


def get_category_limits() -> dict[str, int]:
    return dict(DEFAULT_UPLOAD_LIMITS)


def effective_limit_for(user, file_type: str) -> int:
    limits = get_category_limits()
    return limits.get(file_type, VIDEO_MAX_BYTES)


def limits_payload_for_user(user=None) -> dict:
    limits = get_category_limits()
    return {
        'bytes': limits,
        'mb': {k: round(v / MB, 2) for k, v in limits.items()},
        'video_max_bytes': VIDEO_MAX_BYTES,
        'video_max_mb': 10,
    }
