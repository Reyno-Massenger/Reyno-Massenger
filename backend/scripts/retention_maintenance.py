#!/usr/bin/env python3
"""CLI script to run the 72-hour MEDIA retention cleanup (cron/systemd). Media only: chats/messages are kept."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.services.retention_maintenance import run_retention_maintenance


def main():
    app = create_app()
    with app.app_context():
        result = run_retention_maintenance()
        print(
            f"[Reyno Lite Retention] Expired {result['purged_media_files']} media files "
            f"({result['freed_bytes']} bytes freed). Chats and messages are never deleted."
        )


if __name__ == '__main__':
    main()
