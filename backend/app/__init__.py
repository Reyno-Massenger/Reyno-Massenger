import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy(); migrate = Migrate(); jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    secret = os.getenv('SECRET_KEY', 'dev-secret-change-me-32-chars-minimum!!')
    jwt_secret = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-me-32-chars!!')
    app.config.update(
        SECRET_KEY=secret, JWT_SECRET_KEY=jwt_secret,
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///reyno_lite.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=int(os.getenv('MAX_CONTENT_LENGTH', 26 * 1024 * 1024)),
        UPLOAD_FOLDER=os.getenv('UPLOAD_FOLDER', 'uploads'),
        SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true',
        JWT_ACCESS_TOKEN_EXPIRES=86400, JWT_REFRESH_TOKEN_EXPIRES=2592000,
    )
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    db.init_app(app); migrate.init_app(app, db); jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": os.getenv('CORS_ORIGINS', '*')}})

    from app.api.auth import auth_bp
    from app.api.users import users_bp
    from app.api.chats import chats_bp
    from app.api.messages import messages_bp
    from app.api.media import media_bp
    from app.api.admin_api import admin_api_bp
    from app.api.reactions import reactions_bp
    from app.api.stickers import stickers_bp
    from app.admin.routes import admin_bp
    from app.web.routes import web_bp

    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(chats_bp, url_prefix='/api/v1/chats')
    app.register_blueprint(messages_bp, url_prefix='/api/v1/messages')
    app.register_blueprint(media_bp, url_prefix='/api/v1/media')
    app.register_blueprint(admin_api_bp, url_prefix='/api/v1/admin')
    app.register_blueprint(reactions_bp, url_prefix='/api/v1/reactions')
    app.register_blueprint(stickers_bp, url_prefix='/api/v1/stickers')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(web_bp)

    with app.app_context():
        from app.services.schema_upgrade import upgrade_schema
        try:
            db.create_all(); upgrade_schema()
        except Exception:
            app.logger.exception('Schema init failed')

    # Point 6: HTTP is a fully supported mode (e.g. Iran "national network",
    # LAN, or IP-only hosting). HTTPS is recommended but NEVER forced unless
    # the operator explicitly sets FORCE_HTTPS=true. HSTS is only sent on
    # HTTPS responses (below), so plain-HTTP clients are never locked out.
    force_https = os.getenv('FORCE_HTTPS', 'false').lower() == 'true'

    @app.before_request
    def _maybe_force_https():
        if force_https and not request.is_secure and request.path != '/health':
            return jsonify({'error': 'HTTPS required on this server.'}), 426
        return None

    @app.after_request
    def _headers(resp):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
        resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        resp.headers['Permissions-Policy'] = 'camera=(self), microphone=(self), geolocation=(self)'
        if request.is_secure:
            resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        if request.path.startswith('/api/'):
            resp.headers['Cache-Control'] = 'no-store'
        return resp

    @app.errorhandler(404)
    def _404(e):
        return (jsonify({'error': 'Not found'}), 404) if request.path.startswith('/api/') else e
    @app.errorhandler(413)
    def _413(e):
        return jsonify({'error': 'File too large. Videos must be under 10 MB.'}), 413
    @jwt.unauthorized_loader
    def _unauth(r): return jsonify({'error': 'Authentication required', 'code': 'token_missing'}), 401
    @jwt.invalid_token_loader
    def _inv(r): return jsonify({'error': 'Invalid session', 'code': 'token_invalid'}), 401
    @jwt.expired_token_loader
    def _exp(h, p): return jsonify({'error': 'Session expired', 'code': 'token_expired'}), 401

    @app.route('/health')
    def health(): return {'status': 'ok', 'app': 'Reyno Messenger Lite'}, 200
    return app
