"""Privacy-preserving in-memory rate limiter.

Client IPs are hashed with a secret salt (SHA-256) so raw IP addresses are
never stored in memory or logs.
"""
import hashlib
import os
import threading
import time
from collections import defaultdict, deque
from flask import current_app, request

_lock = threading.Lock()
_buckets: dict[str, deque[float]] = defaultdict(deque)


def _anonymized_client_key(scope: str) -> str:
    ip = (
        request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        or request.remote_addr
        or 'unknown'
    )
    salt = (
        current_app.config.get('SECRET_KEY')
        if current_app
        else os.getenv('SECRET_KEY', 'reyno-salt')
    )
    digest = hashlib.sha256(f'{scope}:{salt}:{ip}'.encode('utf-8')).hexdigest()[:24]
    return f'{scope}:{digest}'


def check_rate_limit(scope: str, max_requests: int, window_seconds: int) -> tuple[bool, int]:
    """Return (allowed, retry_after_seconds)."""
    if current_app and current_app.config.get('TESTING') and not current_app.config.get('ENABLE_RATE_LIMIT_IN_TESTS'):
        return True, 0

    now = time.monotonic()
    key = _anonymized_client_key(scope)
    cutoff = now - window_seconds

    with _lock:
        dq = _buckets[key]
        while dq and dq[0] <= cutoff:
            dq.popleft()
        if len(dq) >= max_requests:
            retry_after = max(1, int(window_seconds - (now - dq[0])))
            return False, retry_after
        dq.append(now)
        if len(_buckets) > 4096:
            # Periodic prune of idle keys
            stale_keys = [k for k, v in _buckets.items() if not v or v[-1] <= cutoff]
            for k in stale_keys:
                _buckets.pop(k, None)
        return True, 0


def reset_rate_limits():
    with _lock:
        _buckets.clear()
