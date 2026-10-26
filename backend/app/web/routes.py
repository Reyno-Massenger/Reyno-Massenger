"""Serves the Reyno Messenger Lite browser web application and static assets."""
import os
from flask import Blueprint, send_from_directory, Response, jsonify

web_bp = Blueprint(
    'web',
    __name__,
    template_folder='templates',
)

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
ASSETS_DIR = os.path.join(REPO_ROOT, 'assets')


@web_bp.route('/', methods=['GET'])
def index():
    tpl = os.path.join(os.path.dirname(__file__), 'templates', 'index.html')
    with open(tpl, encoding='utf-8') as f:
        return Response(f.read(), mimetype='text/html')


@web_bp.route('/manifest.json', methods=['GET'])
def manifest():
    return jsonify({
        'name': 'Reyno Messenger Lite',
        'short_name': 'Reyno Lite',
        'description': 'Fast, secure, browser-based messenger with 72-hour automatic data retention.',
        'start_url': '/',
        'display': 'standalone',
        'background_color': '#0F172A',
        'theme_color': '#0088CC',
        'icons': [
            {
                'src': '/assets/icons/app_icon.png',
                'sizes': '192x192',
                'type': 'image/png',
            },
            {
                'src': '/assets/icons/reyno_logo.png',
                'sizes': '512x512',
                'type': 'image/png',
            },
        ],
    })


@web_bp.route('/assets/<path:filename>', methods=['GET'])
def serve_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)
