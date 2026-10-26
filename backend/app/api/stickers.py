from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.sticker import StickerPack
from app.services.schema_upgrade import _seed_default_stickers

stickers_bp = Blueprint('stickers', __name__)


@stickers_bp.route('/packs', methods=['GET'])
@jwt_required()
def list_packs():
    _seed_default_stickers()
    packs = StickerPack.query.order_by(StickerPack.created_at.asc()).all()
    return jsonify({
        'packs': [p.to_dict(include_stickers=True) for p in packs]
    }), 200


@stickers_bp.route('/packs/<pack_id>', methods=['GET'])
@jwt_required()
def get_pack(pack_id):
    pack = StickerPack.query.get(pack_id)
    if not pack:
        return jsonify({'error': 'Sticker pack not found.'}), 404
    return jsonify({'pack': pack.to_dict(include_stickers=True)}), 200
