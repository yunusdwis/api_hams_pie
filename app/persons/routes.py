from flask import Blueprint, request, jsonify
from .services import (
    create_person,
    update_person,
    delete_person,
    get_person,
    get_persons,
    get_persons_paginate
)
from app.auth.services import token_required

persons_bp = Blueprint('persons', __name__)

@persons_bp.route('/persons', methods=['POST'])
@token_required
def create_person_route():
    data = request.form
    files = {
        'image': request.files.get('image'),
        'bpjs': request.files.get('bpjs'),
        'medical_checkup': request.files.get('medical_checkup'),
        'skck': request.files.get('skck')
    }
    return create_person(data, files)

@persons_bp.route('/persons/<string:person_uuid>', methods=['PUT'])
@token_required
def update_person_route(person_uuid):
    data = request.form
    files = {
        'image': request.files.get('image'),
        'bpjs': request.files.get('bpjs'),
        'medical_checkup': request.files.get('medical_checkup'),
        'skck': request.files.get('skck')
    }
    return update_person(person_uuid, data, files)

@persons_bp.route('/persons/<string:person_uuid>', methods=['DELETE'])
@token_required
def delete_person_route(person_uuid):
    return delete_person(person_uuid)

@persons_bp.route('/persons/<string:person_uuid>', methods=['GET'])
@token_required
def get_person_route(person_uuid):
    return get_person(person_uuid)

@persons_bp.route('/persons', methods=['GET'])
@token_required
def get_persons_route():
    return get_persons()

@persons_bp.route('/persons-paginate', methods=['GET'])
@token_required
def get_persons_paginate_route():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    search = request.args.get('search', '')
    return get_persons_paginate(page, limit, search)