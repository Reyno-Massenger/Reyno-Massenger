from app import db
from datetime import datetime


class AppSetting(db.Model):
    """Tiny key/value store for operator-controlled runtime settings.

    The admin panel writes here (upload limits, per-user overrides, feature
    toggles) so behaviour can change on shared hosting without redeploying
    code or editing ``.env``. Values are plain text; structured settings are
    stored as JSON by the service layer.
    """

    __tablename__ = 'app_settings'

    key = db.Column(db.String(120), primary_key=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
