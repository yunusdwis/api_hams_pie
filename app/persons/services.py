from config.database import get_db_connection
from config.directory import directory
from utils.file import handle_file_upload, delete_file
from flask import jsonify
import os
import uuid

def create_person(data, files):
    image = files.get('image')
    bpjs = files.get('bpjs')
    medical_checkup = files.get('medical_checkup')
    skck = files.get('skck')
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        person_uuid = str(uuid.uuid4())
        
        # Handle file uploads
        image_filename = handle_file_upload(image, f"{directory['people']}/{person_uuid}", person_uuid)
        bpjs_filename = handle_file_upload(bpjs, directory['bpjs'], person_uuid)
        medical_filename = handle_file_upload(medical_checkup, directory['medical_checkup'], person_uuid)
        skck_filename = handle_file_upload(skck, directory['skck'], person_uuid)
        
        query = """
        INSERT INTO persons (
            uuid, name, status, nik, birth_place, birth_date, gender, 
            address, company, compartment, departement, email, phone,
            bpjs, medical_checkup, skck, emergency_contact_name,
            emergency_contact_address, emergency_contact_relation,
            emergency_contact_phone, image
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            person_uuid,
            data.get('name'),
            data.get('status'),
            data.get('nik'),
            data.get('birth_place'),
            data.get('birth_date'),
            data.get('gender'),
            data.get('address'),
            data.get('company'),
            data.get('compartment'),
            data.get('departement'),
            data.get('email'),
            f"+62{data.get('phone')}",
            bpjs_filename,
            medical_filename,
            skck_filename,
            data.get('emergency_contact_name'),
            data.get('emergency_contact_address'),
            data.get('emergency_contact_relation'),
            f"+62{data.get('emergency_contact_phone')}",
            image_filename
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        return jsonify({
            'message': 'Person created successfully!',
            'uuid': person_uuid
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def update_person(person_uuid, data, files):
    image = files.get('image')
    bpjs = files.get('bpjs')
    medical_checkup = files.get('medical_checkup')
    skck = files.get('skck')
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get existing person data
        cursor.execute("SELECT * FROM persons WHERE uuid = %s", (person_uuid,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Handle file uploads
        image_filename = person['image']
        if image:
            # Delete old image if exists
            if person['image']:
                old_path = os.path.join(directory['people'], person['image'])
                delete_file(old_path)
            image_filename = handle_file_upload(image, directory['people'], person_uuid)

        bpjs_filename = person['bpjs']
        if bpjs:
            if person['bpjs']:
                old_path = os.path.join(directory['bpjs'], person['bpjs'])
                delete_file(old_path)
            bpjs_filename = handle_file_upload(bpjs, directory['bpjs'], person_uuid)

        medical_filename = person['medical_checkup']
        if medical_checkup:
            if person['medical_checkup']:
                old_path = os.path.join(directory['medical_checkup'], person['medical_checkup'])
                delete_file(old_path)
            medical_filename = handle_file_upload(medical_checkup, directory['medical_checkup'], person_uuid)

        skck_filename = person['skck']
        if skck:
            if person['skck']:
                old_path = os.path.join(directory['skck'], person['skck'])
                delete_file(old_path)
            skck_filename = handle_file_upload(skck, directory['skck'], person_uuid)
        
        # Update person
        query = """
        UPDATE persons 
        SET 
            name = %s, status = %s, nik = %s, birth_place = %s, 
            birth_date = %s, gender = %s, address = %s,
            company = %s, compartment = %s, departement = %s,
            email = %s, phone = %s, bpjs = %s,
            medical_checkup = %s, skck = %s,
            emergency_contact_name = %s, emergency_contact_address = %s,
            emergency_contact_relation = %s, emergency_contact_phone = %s,
            image = %s
        WHERE uuid = %s
        """
        values = (
            data.get('name', person['name']),
            data.get('status', person['status']),
            data.get('nik', person['nik']),
            data.get('birth_place', person['birth_place']),
            data.get('birth_date', person['birth_date']),
            data.get('gender', person['gender']),
            data.get('address', person['address']),
            data.get('company', person['company']),
            data.get('compartment', person['compartment']),
            data.get('departement', person['departement']),
            data.get('email', person['email']),
            f"+62{data.get('phone')}",
            bpjs_filename,
            medical_filename,
            skck_filename,
            data.get('emergency_contact_name', person['emergency_contact_name']),
            data.get('emergency_contact_address', person['emergency_contact_address']),
            data.get('emergency_contact_relation', person['emergency_contact_relation']),
            f"+62{data.get('emergency_contact_phone')}",
            image_filename,
            person_uuid
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        return jsonify({'message': 'Person updated successfully!'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def delete_person(person_uuid):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Get person data first to delete associated files
        cursor.execute("SELECT * FROM persons WHERE uuid = %s", (person_uuid,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Delete all associated files
        if person['image']:
            delete_file(os.path.join(f"{directory['people']}/{person['uuid']}", person['image']))
        if person['bpjs']:
            delete_file(os.path.join(directory['bpjs'], person['bpjs']))
        if person['medical_checkup']:
            delete_file(os.path.join(directory['medical_checkup'], person['medical_checkup']))
        if person['skck']:
            delete_file(os.path.join(directory['skck'], person['skck']))
        
        # Delete from database
        cursor.execute("DELETE FROM persons WHERE uuid = %s", (person_uuid,))
        connection.commit()
        
        return jsonify({'message': 'Person deleted successfully!'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_person(person_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = """
        SELECT 
            uuid, name, status, nik, birth_place, 
            DATE_FORMAT(birth_date, '%Y-%m-%d') as birth_date,
            gender, address, company, compartment, 
            departement, email, phone,
            bpjs, medical_checkup, skck,
            emergency_contact_name, emergency_contact_address,
            emergency_contact_relation, emergency_contact_phone,
            image
        FROM persons WHERE uuid = %s
        """
    try:
        cursor.execute(query, (person_id,))
        person = cursor.fetchone()

        
        if person:
            return jsonify(person)
        else:
            return jsonify({'error': f'Person dengan id {person_id} tidak ditemukan'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_persons():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM persons ORDER BY name ASC")
        persons = cursor.fetchall()
        return jsonify(persons)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_persons_paginate(page, limit, search):
    offset = (page - 1) * limit

    connection = get_db_connection()
    cursor = None

    try:
        # Build base query
        base_query = """
        SELECT 
            *,
            DATE_FORMAT(birth_date, '%Y-%m-%d') as birth_date,
            CONCAT(uuid, '/', image) as image_path
        FROM persons
        """
        count_query = "SELECT COUNT(*) AS total FROM persons"
        params = []
        count_params = []

        if search:
            base_query += " WHERE name LIKE %s OR nik LIKE %s"
            params.extend([f"%{search}%", f"%{search}%"])
            count_query += " WHERE name LIKE %s OR nik LIKE %s"
            count_params.extend([f"%{search}%", f"%{search}%"])

        base_query += " ORDER BY name ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor = connection.cursor(dictionary=True)
        cursor.execute(base_query, params)
        persons = cursor.fetchall()

        # Get total count
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

        print(persons)

        return jsonify({
            'data': persons,
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        connection.close()
