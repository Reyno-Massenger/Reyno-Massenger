"""Transparent server-side encryption at rest for message content & location labels.

Protects database files on disk (SQLite / MySQL) so private message text and
static location labels are never stored in plaintext at rest.
"""
import base64
import hashlib
import os
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app, has_app_context

_PREFIX = 'enc:v1:'


def _get_fernet() -> Fernet:
    secret = None
    if has_app_context():
        secret = current_app.config.get('SECRET_KEY')
    if not secret:
        secret = os.getenv('SECRET_KEY', 'reyno-lite-default-key')
    digest = hashlib.sha256(f'reyno-at-rest::{secret}'.encode('utf-8')).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_text(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    if not isinstance(plaintext, str):
        plaintext = str(plaintext)
    if plaintext == '':
        return ''
    if plaintext.startswith(_PREFIX):
        return plaintext
    token = _get_fernet().encrypt(plaintext.encode('utf-8')).decode('ascii')
    return f'{_PREFIX}{token}'


def decrypt_text(stored: str | None) -> str | None:
    if stored is None:
        return None
    if not isinstance(stored, str):
        return str(stored)
    if not stored.startswith(_PREFIX):
        return stored
    token = stored[len(_PREFIX):]
    try:
        return _get_fernet().decrypt(token.encode('ascii')).decode('utf-8')
    except (InvalidToken, ValueError, Exception):
        return '[Encrypted message]'
