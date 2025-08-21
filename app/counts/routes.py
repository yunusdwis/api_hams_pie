from flask import Blueprint, request
from app.auth.services import token_required
from .services import get_weekly_counts_service, count_gate_service

counts_bp = Blueprint('counts', __name__)

@counts_bp.route('/weekly-counts', methods=['GET'])
@token_required
def get_weekly_counts():
    building_uuid = request.args.get('building_uuid')
    return get_weekly_counts_service(building_uuid)

@counts_bp.route('/count-gate', methods=['GET'])
@token_required
def count_gate():
    return count_gate_service()
