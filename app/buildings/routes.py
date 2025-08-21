from flask import Blueprint, request
from app.auth.services import token_required
from .services import (
    register_unregistered,
    register_registered,
    exit_building,
    get_buildings_service,
    get_building_detail_service,
    get_building_persons_not_today_service,
    get_building_persons_today_service,
    get_building_persons_service,
    get_building_persons_history_service,
    delete_building_person_service,
)

buildings_bp = Blueprint('buildings', __name__)

@buildings_bp.route('/unregistered', methods=['POST'])
@token_required
def unregistered():
    return register_unregistered(request.form, request.files)

@buildings_bp.route('/registered', methods=['POST'])
@token_required
def registered():
    return register_registered(request.get_json())

@buildings_bp.route('/exit', methods=['POST'])
@token_required
def exit():
    return exit_building(request.get_json())

@buildings_bp.route('/buildings', methods=['GET'])
@token_required
def get_buildings():
    return get_buildings_service()

@buildings_bp.route('/building-detail', methods=['GET'])
@token_required
def get_building_detail():
    return get_building_detail_service(request.args.get('uuid'))

@buildings_bp.route('/building-persons-not-today', methods=['GET'])
@token_required
def get_building_persons_not_today():
    return get_building_persons_not_today_service(request.args.get('building_uuid'))

@buildings_bp.route('/building-persons-today', methods=['GET'])
@token_required
def get_building_persons_today():
    return get_building_persons_today_service(request.args.get('building_uuid'))

@buildings_bp.route('/building-persons', methods=['GET'])
@token_required
def get_building_persons():
    return get_building_persons_service(
        building_uuid=request.args.get('building_uuid'),
        page=int(request.args.get('page', 1)),
        limit=int(request.args.get('limit', 5)),
        search=request.args.get('search')
    )

@buildings_bp.route('/building-persons-history', methods=['GET'])
@token_required
def get_building_persons_history():
    return get_building_persons_history_service(
        page=int(request.args.get('page', 1)),
        limit=int(request.args.get('limit', 5)),
        search=request.args.get('search'),
        start_date=request.args.get('start_date'),
        end_date=request.args.get('end_date'),
        sort=request.args.get('sort', 'entry_time,desc')
    )

@buildings_bp.route('/building-persons/<string:building_person_uuid>', methods=['DELETE'])
@token_required
def delete_building_person(building_person_uuid):
    return delete_building_person_service(building_person_uuid)
