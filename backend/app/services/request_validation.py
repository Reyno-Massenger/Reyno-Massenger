"""Strict JSON payload validation for Reyno Messenger Lite."""
from flask import request, jsonify

BOOLEAN_FIELDS = {
    'for_all',
    'delete_for_all',
    'is_public',
    'is_muted',
    'is_online',
    'is_pinned',
    'is_archived',
}


def validate_object_body():
    if request.method not in ('POST', 'PUT', 'PATCH') or not request.is_json:
        return None
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected a JSON object.'}), 400
    if any(key in data and type(data[key]) is not bool for key in BOOLEAN_FIELDS):
        return jsonify({'error': 'Boolean fields must be true or false.'}), 400
    return None
