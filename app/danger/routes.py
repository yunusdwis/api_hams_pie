from flask import Blueprint, jsonify, request
from app.auth.services import token_required
from .services import get_danger_status, update_danger_mode

danger_bp = Blueprint('danger', __name__)

@danger_bp.route('/danger-mode', methods=['GET'])
@token_required
def get_danger_mode_route():
    try:
        return jsonify(get_danger_status())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@danger_bp.route('/danger-mode', methods=['POST'])
@token_required
def set_danger_mode_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        danger_mode = data.get('danger_mode', False)
        code = data.get('code', '')
        result = update_danger_mode(danger_mode, code)

        if isinstance(result, tuple):  # case: error with status code
            return jsonify(result[0]), result[1]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
