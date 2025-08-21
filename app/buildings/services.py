from config.database import get_db_connection
from config.directory import directory
from datetime import datetime
from utils.file import handle_file_upload
from flask import jsonify
import os
import re
import uuid
import shutil

def register_unregistered(data, files):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        person_uuid = str(uuid.uuid4())

        # Handle file uploads
        bpjs = files.get('bpjs')
        medical_checkup = files.get('medical_checkup')
        skck = files.get('skck')

        bpjs_filename = handle_file_upload(bpjs, directory['bpjs'], person_uuid) if (bpjs) else None
        skck_filename = handle_file_upload(skck, directory['skck'], person_uuid) if (medical_checkup) else None
        medical_filename = handle_file_upload(medical_checkup, directory['medical_checkup'], person_uuid) if (skck) else None

        # Get form data
        image = data.get('image')
        name = data.get('name')
        nik = data.get('nik')
        email = data.get('email')
        address = data.get('address')
        emergency_contact_name = data.get('emergency_contact_name')
        emergency_contact_address = data.get('emergency_contact_address')
        emergency_contact_relation = data.get('emergency_contact_relation')
        emergency_contact_phone = data.get('emergency_contact_phone')
        company = data.get('company')
        compartment = data.get('compartment')
        departement = data.get('departement')
        birth_place = data.get('birth_place')
        birth_date = data.get('birth_date')
        gender = data.get('gender')
        phone = data.get('phone')
        building_uuid = data.get('building_uuid')
        insert = data.get('insert')

        if insert == '1':
            person_uuid = str(uuid.uuid4())
            # Insert person data
            cursor.execute("""
                INSERT INTO persons (uuid, image, name, nik, email, address, 
                                emergency_contact_name, emergency_contact_address,
                                emergency_contact_relation, emergency_contact_phone,
                                birth_place, birth_date, gender, phone,
                                bpjs, medical_checkup, skck, company, compartment, departement)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (person_uuid, image, name, nik, email, address,
                emergency_contact_name, emergency_contact_address,
                emergency_contact_relation, f"+62{emergency_contact_phone}",
                birth_place, birth_date, gender, f"+62{phone}",
                bpjs_filename, medical_filename, skck_filename, company, compartment, departement))
        
            building_person_uuid = str(uuid.uuid4())
            entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                INSERT INTO building_persons (uuid, building_uuid, person_uuid, entry_time)
                VALUES (%s, %s, %s, %s)
            """, (building_person_uuid, building_uuid, person_uuid, entry_time))

            cursor.execute("""
                UPDATE buildings 
                SET entry = entry + 1, 
                    total = total + 1 
                WHERE uuid = %s
            """, (building_uuid,))
        else:
            person_uuid = image.split('.')[0]

            src_file = f"{directory['people']}/undefined/{person_uuid}.jpg"
            dst_dir = f"{directory['people']}/{person_uuid}"
            
            os.makedirs(dst_dir, exist_ok=True)

            existing_files = [f for f in os.listdir(dst_dir) if re.match(r'^\d+\.jpg$', f)]

            if existing_files:
                numbers = [int(re.match(r'^(\d+)\.jpg$', f).group(1)) for f in existing_files]
                next_number = max(numbers) + 1
            else:
                next_number = 1

            image = f"{next_number}.jpg"

            dst_file = os.path.join(dst_dir, image)

            if os.path.exists(src_file):
                shutil.move(src_file, dst_file)

            cursor.execute("""
                INSERT INTO persons (uuid, image, name, nik, email, address, 
                                emergency_contact_name, emergency_contact_address,
                                emergency_contact_relation, emergency_contact_phone,
                                birth_place, birth_date, gender, phone,
                                bpjs, medical_checkup, skck, company, compartment, departement)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (person_uuid, image, name, nik, email, address,
                emergency_contact_name, emergency_contact_address,
                emergency_contact_relation, f"+62{emergency_contact_phone}",
                birth_place, birth_date, gender, f"+62{phone}",
                bpjs_filename, medical_filename, skck_filename, company, compartment, departement))

            building_person_uuid = data.get('building_person_uuid')
            cursor.execute("""
                UPDATE building_persons SET person_uuid = %s, image = %s WHERE uuid = %s
            """, (person_uuid, image, building_person_uuid))

        connection.commit()
        return jsonify({'message': 'Entry person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def register_registered(data):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not data:
            return jsonify({'error': 'Invalid JSON or missing Content-Type header'}), 400

        person_uuid = data.get('person_uuid')
        image = data.get('image')
        building_uuid = data.get('building_uuid')
        building_person_uuid = data.get('building_person_uuid')
        insert = data.get('insert')

        if insert == 1:
            building_person_uuid = str(uuid.uuid4())
            entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO building_persons (uuid, building_uuid, person_uuid, image, entry_time)
                VALUES (%s, %s, %s, %s, %s)
            """, (building_person_uuid, building_uuid, person_uuid, image, entry_time))

            cursor.execute("""
                UPDATE buildings 
                SET entry = entry + 1, total = total + 1 
                WHERE uuid = %s
            """, (building_uuid,))
        else:
            src_file = f"{directory['people']}/undefined/{image}"
            dst_dir = f"{directory['people']}/{person_uuid}"

            os.makedirs(dst_dir, exist_ok=True)

            existing_files = [f for f in os.listdir(dst_dir) if re.match(r'^\d+\.jpg$', f)]

            if existing_files:
                numbers = [int(re.match(r'^(\d+)\.jpg$', f).group(1)) for f in existing_files]
                next_number = max(numbers) + 1
            else:
                next_number = 1

            image = f"{next_number}.jpg"

            dst_file = os.path.join(dst_dir, image)

            if os.path.exists(src_file):
                shutil.move(src_file, dst_file)
        
            cursor.execute("""
                UPDATE building_persons SET person_uuid = %s, image = %s WHERE uuid = %s
            """, (person_uuid, image, building_person_uuid))

        connection.commit()
        return jsonify({'message': 'Entry person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

def exit_building(data):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if not data:
            return jsonify({'error': 'Invalid JSON or missing Content-Type header'}), 400

        person_uuid = data.get('person_uuid')

        if not all([person_uuid]):
            return jsonify({'error': 'All fields are required'}), 400

        exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            UPDATE building_persons SET
                exit_time = %s
                WHERE uuid = %s
        """, (exit_time, person_uuid))

        building_uuid = 'e1b6c9e7-4b8d-4e16-9d17-297c9816b64e'

        cursor.execute("""
            UPDATE buildings 
            SET `exit` = `exit` + 1, total = CASE WHEN total > 0 THEN total - 1 ELSE 0 END
            WHERE uuid = %s
        """, (building_uuid,))

        connection.commit()
        return jsonify({'message': 'Exit person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

def get_buildings_service():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM buildings")
        buildings = cursor.fetchall()
        return jsonify(buildings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_building_detail_service(uuid):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if not uuid:
            return jsonify({'error': 'UUID parameter is required'}), 400

        cursor.execute("SELECT * FROM buildings WHERE uuid = %s", (uuid,))
        building = cursor.fetchone()

        if building:
            return jsonify(building)
        else:
            return jsonify({'error': 'Building not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_building_persons_not_today_service(building_uuid):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT uuid, name, image
            FROM persons
            WHERE uuid NOT IN (
                SELECT person_uuid
                FROM building_persons
                WHERE DATE(entry_time) = CURDATE() 
                AND exit_time IS NULL 
                AND person_uuid IS NOT NULL 
                AND building_uuid = %s
            )
        """, (building_uuid,))
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_building_persons_today_service(building_uuid):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                building_persons.uuid AS building_person_uuid, 
                persons.uuid AS uuid,
                persons.name, 
                persons.image
            FROM building_persons
            INNER JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE DATE(entry_time) = CURDATE() 
                AND exit_time IS NULL 
                AND building_uuid = %s
        """, (building_uuid,))
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_building_persons_service(building_uuid, page, limit, search):
    if not building_uuid:
        return jsonify({'error': 'building_uuid is required'}), 400

    offset = (page - 1) * limit
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        base_query = """
            SELECT 
                building_persons.uuid AS building_person_uuid,
                building_persons.building_uuid AS building_person_building_uuid,
                building_persons.person_uuid AS building_person_person_uuid,
                building_persons.image AS building_person_image,
                persons.*,
                persons.uuid AS person_uuid,
                persons.image AS person_image,
                persons.name AS person_name,
                entry_time,
                exit_time,
                CASE 
                    WHEN person_uuid IS NULL THEN CONCAT('undefined/', building_persons.image)
                    ELSE CONCAT(person_uuid, '/', building_persons.image)
                END AS image_path
            FROM building_persons 
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE building_uuid = %s AND DATE(entry_time) = CURDATE() AND exit_time IS NULL
        """

        params = [building_uuid]
        if search:
            base_query += " AND persons.name LIKE %s"
            params.append(f"%{search}%")
        base_query += " ORDER BY entry_time DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        building_persons = cursor.fetchall()

        count_query = """
            SELECT COUNT(*) AS total
            FROM building_persons
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE building_uuid = %s AND DATE(entry_time) = CURDATE() AND exit_time IS NULL
        """
        count_params = [building_uuid]
        if search:
            count_query += " AND persons.name LIKE %s"
            count_params.append(f"%{search}%")

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

        return jsonify({
            'data': building_persons,
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def get_building_persons_history_service(page, limit, search, start_date, end_date, sort):
    offset = (page - 1) * limit
    sort_parts = sort.split(',')
    sort_column = sort_parts[0]
    sort_direction = sort_parts[1] if len(sort_parts) > 1 else 'desc'

    column_mapping = {
        'name': 'persons.name',
        'building': 'buildings.name',
        'entry_time': 'entry_time',
        'exit_time': 'exit_time'
    }
    if sort_column not in column_mapping:
        sort_column = 'entry_time'
        sort_direction = 'desc'

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        base_query = """
            SELECT 
                building_persons.uuid AS building_person_uuid,
                building_persons.image AS building_person_image,
                buildings.name AS building_name,
                persons.*,
                persons.uuid AS person_uuid,
                persons.image AS person_image,
                persons.name AS person_name,
                entry_time,
                exit_time,
                CASE 
                    WHEN person_uuid IS NULL THEN CONCAT('undefined/', building_persons.image)
                    ELSE CONCAT(person_uuid, '/', building_persons.image)
                END AS image_path
            FROM building_persons 
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            INNER JOIN buildings ON buildings.uuid = building_persons.building_uuid
        """

        conditions = []
        params = []
        count_params = []

        if search:
            conditions.append("persons.name LIKE %s")
            params.append(f"%{search}%")
            count_params.append(f"%{search}%")

        if start_date and end_date:
            conditions.append("DATE(entry_time) BETWEEN %s AND %s")
            params.extend([start_date, end_date])
            count_params.extend([start_date, end_date])
        elif start_date:
            conditions.append("DATE(entry_time) >= %s")
            params.append(start_date)
            count_params.append(start_date)
        elif end_date:
            conditions.append("DATE(entry_time) <= %s")
            params.append(end_date)
            count_params.append(end_date)

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        base_query += f" ORDER BY {column_mapping[sort_column]} {sort_direction.upper()} LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        building_persons_history = cursor.fetchall()

        count_query = """
            SELECT COUNT(*) AS total
            FROM building_persons
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            INNER JOIN buildings ON buildings.uuid = building_persons.building_uuid
        """
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

        return jsonify({
            'data': building_persons_history,
            'page': page,
            'limit': limit,
            'total': total,
            'pages': (total + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

def delete_building_person_service(building_person_uuid):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT building_uuid, exit_time 
            FROM building_persons 
            WHERE uuid = %s
        """, (building_person_uuid,))
        record = cursor.fetchone()
        if not record:
            return jsonify({'error': 'Record not found'}), 404

        building_uuid = record['building_uuid']
        exit_time = record['exit_time']

        cursor.execute("DELETE FROM building_persons WHERE uuid = %s", (building_person_uuid,))
        if exit_time is None:
            cursor.execute("""
                UPDATE buildings 
                SET entry = entry - 1, total = total - 1 
                WHERE uuid = %s
            """, (building_uuid,))
        else:
            cursor.execute("""
                UPDATE buildings 
                SET `exit` = `exit` - 1 
                WHERE uuid = %s
            """, (building_uuid,))

        connection.commit()
        return jsonify({'message': 'Record deleted successfully!'}), 200
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()