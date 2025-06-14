import uuid
import os
import pyodbc
import argparse
from datetime import datetime, timedelta, time
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import hashlib
import secrets
import re
import shutil
from functools import wraps

app = Flask(__name__)
CORS(app)

# SQL Server connection configuration
SERVER = 'localhost\SQLEXPRESS'
DATABASE = 'system_hams_pie'
USERNAME = 'sa'
PASSWORD = 'sa123'
DRIVER = '{ODBC Driver 17 for SQL Server}'

# Connection string for SQL Server
connection_string = f'DRIVER={DRIVER};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}'

UPLOAD_FOLDER = r'C:\Putra\Proyek\Createch\PIE\Projects\people_counter_v2\people'
UPLOAD_FOLDER_BPJS = r'C:\Putra\Proyek\Createch\PIE\Projects\people_counter_v2\bpjs'
UPLOAD_FOLDER_MEDICAL_CHECKUP = r'C:\Putra\Proyek\Createch\PIE\Projects\people_counter_v2\medical_checkup'
UPLOAD_FOLDER_SKCK = r'C:\Putra\Proyek\Createch\PIE\Projects\people_counter_v2\skck'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_BPJS'] = UPLOAD_FOLDER_BPJS
app.config['UPLOAD_FOLDER_MEDICAL_CHECKUP'] = UPLOAD_FOLDER_MEDICAL_CHECKUP
app.config['UPLOAD_FOLDER_SKCK'] = UPLOAD_FOLDER_SKCK
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def handle_file_upload(file, upload_folder, uuid_prefix):
    if file and allowed_file(file.filename):
        # Create directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid_prefix}_{filename}"
        file.save(os.path.join(upload_folder, unique_filename))
        return unique_filename
    return None

def delete_file(file_path):
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

def get_db_connection():
    return pyodbc.connect(connection_string)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    return secrets.token_hex(32)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if the token is in the request headers
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        user_uuid = verify_token(token)
        if not user_uuid:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
            
        return f(*args, **kwargs)
    
    return decorated

def verify_token(token):
    if not token:
        return None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if token starts with 'Bearer ' and remove it if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        cursor.execute("""
            SELECT uuid 
            FROM [user] 
            WHERE token = ?
        """, (token,))
        user = cursor.fetchone()
        
        return user.uuid
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    hashed_password = hash_password(password)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT uuid, password, token FROM [user] WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user or user.password != hashed_password:
            return jsonify({'error': 'Invalid username or password'}), 401

        token = user.token
        
        if user.token is None:
            # Generate new token
            token = generate_token()

            cursor.execute(
                "UPDATE [user] SET token = ? WHERE uuid = ?",
                (token, user.uuid)
            )
            conn.commit()


        return jsonify({
            'message': 'Login successful',
            'token': token,
            'uuid': user.uuid
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# Route to unregistered persons
@app.route('/unregistered', methods=['POST'])
@token_required
def unregistered():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        person_uuid = str(uuid.uuid4())

        # Handle file uploads
        bpjs = request.files.get('bpjs')
        medical_checkup = request.files.get('medical_checkup')
        skck = request.files.get('skck')

        bpjs_filename = handle_file_upload(bpjs, app.config['UPLOAD_FOLDER_BPJS'], person_uuid)
        medical_filename = handle_file_upload(medical_checkup, app.config['UPLOAD_FOLDER_MEDICAL_CHECKUP'], person_uuid)
        skck_filename = handle_file_upload(skck, app.config['UPLOAD_FOLDER_SKCK'], person_uuid)

        # Get form data
        image = request.form.get('image')
        name = request.form.get('name')
        nik = request.form.get('nik')
        email = request.form.get('email')
        address = request.form.get('address')
        emergency_contact_name = request.form.get('emergency_contact_name')
        emergency_contact_address = request.form.get('emergency_contact_address')
        emergency_contact_relation = request.form.get('emergency_contact_relation')
        emergency_contact_phone = request.form.get('emergency_contact_phone')
        company = request.form.get('company')
        compartment = request.form.get('compartment')
        departement = request.form.get('departement')
        birth_place = request.form.get('birth_place')

        birth_date = request.form.get('birth_date')

        gender = request.form.get('gender')
        phone = request.form.get('phone')
        building_uuid = request.form.get('building_uuid')
        insert = request.form.get('insert')

        if insert == '1':
            person_uuid = str(uuid.uuid4())
            # Insert person data
            cursor.execute("""
                INSERT INTO persons (uuid, image, name, nik, email, address, 
                                emergency_contact_name, emergency_contact_address,
                                emergency_contact_relation, emergency_contact_phone,
                                birth_place, birth_date, gender, phone,
                                bpjs, medical_checkup, skck, company, compartment, departement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (person_uuid, image, name, nik, email, address,
                emergency_contact_name, emergency_contact_address,
                emergency_contact_relation, f"+62{emergency_contact_phone}",
                birth_place, birth_date, gender, f"+62{phone}",
                bpjs_filename, medical_filename, skck_filename, company, compartment, departement))
        
            building_person_uuid = str(uuid.uuid4())
            entry_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                INSERT INTO building_persons (uuid, building_uuid, person_uuid, entry_time)
                VALUES (?, ?, ?, ?)
            """, (building_person_uuid, building_uuid, person_uuid, entry_time))

            cursor.execute("""
                UPDATE buildings 
                SET entry = entry + 1, 
                    total = total + 1 
                WHERE uuid = ?
            """, (building_uuid,))
        else:
            person_uuid = image.split('.')[0]

            src_file = f"{UPLOAD_FOLDER}/undefined/{person_uuid}.jpg"
            dst_dir = f"{UPLOAD_FOLDER}/{person_uuid}"
            
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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (person_uuid, image, name, nik, email, address,
                emergency_contact_name, emergency_contact_address,
                emergency_contact_relation, f"+62{emergency_contact_phone}",
                birth_place, birth_date, gender, f"+62{phone}",
                bpjs_filename, medical_filename, skck_filename, company, compartment, departement))

            building_person_uuid = request.form.get('building_person_uuid')
            cursor.execute("""
                UPDATE building_persons SET person_uuid = ?, image = ? WHERE uuid = ?
            """, (person_uuid, image, building_person_uuid))

        connection.commit()
        return jsonify({'message': 'Entry person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/registered', methods=['POST'])
@token_required
def registered():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        data = request.get_json()
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
                VALUES (?, ?, ?, ?, ?)
            """, (building_person_uuid, building_uuid, person_uuid, image, entry_time))

            cursor.execute("""
                UPDATE buildings 
                SET entry = entry + 1, total = total + 1 
                WHERE uuid = ?
            """, (building_uuid,))
        else:
            src_file = f"{UPLOAD_FOLDER}/undefined/{image}"
            dst_dir = f"{UPLOAD_FOLDER}/{person_uuid}"

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
                UPDATE building_persons SET person_uuid = ?, image = ? WHERE uuid = ?
            """, (person_uuid, image, building_person_uuid))

        connection.commit()
        return jsonify({'message': 'Entry person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/exit', methods=['POST'])
@token_required
def exit():
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON or missing Content-Type header'}), 400

        uuid = data.get('uuid')

        if not all([uuid]):
            return jsonify({'error': 'All fields are required'}), 400

        exit_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
            UPDATE building_persons SET
                exit_time = ?
                WHERE uuid = ?
        """, (exit_time, uuid))

        building_uuid = 'e1b6c9e7-4b8d-4e16-9d17-297c9816b64e'

        cursor.execute("""
            UPDATE buildings 
            SET [exit] = [exit] + 1, total = CASE WHEN total > 0 THEN total - 1 ELSE 0 END
            WHERE uuid = ?
        """, (building_uuid,))

        connection.commit()
        return jsonify({'message': 'Exit person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        cursor.close()
        connection.close()

@app.route('/persons/<string:person_uuid>', methods=['GET'])
@token_required
def get_person(person_uuid):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        query = """
        SELECT 
            uuid, name, status, nik, birth_place, 
            CONVERT(varchar, birth_date, 23) as birth_date,
            gender, address, company, compartment, 
            departement, email, phone,
            bpjs, medical_checkup, skck,
            emergency_contact_name, emergency_contact_address,
            emergency_contact_relation, emergency_contact_phone,
            image
        FROM persons WHERE uuid = ?
        """
        cursor.execute(query, (person_uuid,))
        columns = [column[0] for column in cursor.description]
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
            
        person_dict = dict(zip(columns, person))
        return jsonify(person_dict)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to get persons
@app.route('/persons', methods=['GET'])
@token_required
def get_persons():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM persons ORDER BY name ASC")
        columns = [desc[0] for desc in cursor.description]  # get column names
        persons = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in persons]  # convert to list of dicts
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()
        
@app.route('/persons', methods=['POST'])
@token_required
def create_person():
    data = request.form
    image = request.files.get('image')
    bpjs = request.files.get('bpjs')
    medical_checkup = request.files.get('medical_checkup')
    skck = request.files.get('skck')
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        person_uuid = str(uuid.uuid4())
        
        # Handle file uploads
        image_filename = handle_file_upload(image, f"{app.config['UPLOAD_FOLDER']}/{person_uuid}", person_uuid)
        bpjs_filename = handle_file_upload(bpjs, app.config['UPLOAD_FOLDER_BPJS'], person_uuid)
        medical_filename = handle_file_upload(medical_checkup, app.config['UPLOAD_FOLDER_MEDICAL_CHECKUP'], person_uuid)
        skck_filename = handle_file_upload(skck, app.config['UPLOAD_FOLDER_SKCK'], person_uuid)
        
        query = """
        INSERT INTO persons (
            uuid, name, status, nik, birth_place, birth_date, gender, 
            address, company, compartment, departement, email, phone,
            bpjs, medical_checkup, skck, emergency_contact_name,
            emergency_contact_address, emergency_contact_relation,
            emergency_contact_phone, image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

@app.route('/persons/<string:person_uuid>', methods=['PUT'])
@token_required
def update_person(person_uuid):
    data = request.form
    image = request.files.get('image')
    bpjs = request.files.get('bpjs')
    medical_checkup = request.files.get('medical_checkup')
    skck = request.files.get('skck')
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get existing person data
        cursor.execute("SELECT * FROM persons WHERE uuid = ?", (person_uuid,))
        columns = [column[0] for column in cursor.description]
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        person_dict = dict(zip(columns, person))
        
        # Handle file uploads
        image_filename = person_dict['image']
        if image:
            # Delete old image if exists
            if person_dict['image']:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], person_dict['image'])
                delete_file(old_path)
            image_filename = handle_file_upload(image, app.config['UPLOAD_FOLDER'], person_uuid)

        bpjs_filename = person_dict['bpjs']
        if bpjs:
            if person_dict['bpjs']:
                old_path = os.path.join(app.config['UPLOAD_FOLDER_BPJS'], person_dict['bpjs'])
                delete_file(old_path)
            bpjs_filename = handle_file_upload(bpjs, app.config['UPLOAD_FOLDER_BPJS'], person_uuid)

        medical_filename = person_dict['medical_checkup']
        if medical_checkup:
            if person_dict['medical_checkup']:
                old_path = os.path.join(app.config['UPLOAD_FOLDER_MEDICAL_CHECKUP'], person_dict['medical_checkup'])
                delete_file(old_path)
            medical_filename = handle_file_upload(medical_checkup, app.config['UPLOAD_FOLDER_MEDICAL_CHECKUP'], person_uuid)

        skck_filename = person_dict['skck']
        if skck:
            if person_dict['skck']:
                old_path = os.path.join(app.config['UPLOAD_FOLDER_SKCK'], person_dict['skck'])
                delete_file(old_path)
            skck_filename = handle_file_upload(skck, app.config['UPLOAD_FOLDER_SKCK'], person_uuid)
        
        # Update person
        query = """
        UPDATE persons 
        SET 
            name = ?, status = ?, nik = ?, birth_place = ?, 
            birth_date = ?, gender = ?, address = ?,
            company = ?, compartment = ?, departement = ?,
            email = ?, phone = ?, bpjs = ?,
            medical_checkup = ?, skck = ?,
            emergency_contact_name = ?, emergency_contact_address = ?,
            emergency_contact_relation = ?, emergency_contact_phone = ?,
            image = ?
        WHERE uuid = ?
        """
        values = (
            data.get('name', person_dict['name']),
            data.get('status', person_dict['status']),
            data.get('nik', person_dict['nik']),
            data.get('birth_place', person_dict['birth_place']),
            data.get('birth_date', person_dict['birth_date']),
            data.get('gender', person_dict['gender']),
            data.get('address', person_dict['address']),
            data.get('company', person_dict['company']),
            data.get('compartment', person_dict['compartment']),
            data.get('departement', person_dict['departement']),
            data.get('email', person_dict['email']),
            f"+62{data.get('phone')}",
            bpjs_filename,
            medical_filename,
            skck_filename,
            data.get('emergency_contact_name', person_dict['emergency_contact_name']),
            data.get('emergency_contact_address', person_dict['emergency_contact_address']),
            data.get('emergency_contact_relation', person_dict['emergency_contact_relation']),
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

@app.route('/persons/<string:person_uuid>', methods=['DELETE'])
def delete_person(person_uuid):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Get person data first to delete associated files
        cursor.execute("SELECT * FROM persons WHERE uuid = ?", (person_uuid,))
        columns = [column[0] for column in cursor.description]
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        person_dict = dict(zip(columns, person))
        
        # Delete all associated files
        if person_dict['image']:
            delete_file(os.path.join(f"{app.config['UPLOAD_FOLDER']}/{person_dict['uuid']}", person_dict['image']))
        if person_dict['bpjs']:
            delete_file(os.path.join(app.config['UPLOAD_FOLDER_BPJS'], person_dict['bpjs']))
        if person_dict['medical_checkup']:
            delete_file(os.path.join(app.config['UPLOAD_FOLDER_MEDICAL_CHECKUP'], person_dict['medical_checkup']))
        if person_dict['skck']:
            delete_file(os.path.join(app.config['UPLOAD_FOLDER_SKCK'], person_dict['skck']))
        
        # Delete from database
        cursor.execute("DELETE FROM persons WHERE uuid = ?", (person_uuid,))
        connection.commit()
        
        return jsonify({'message': 'Person deleted successfully!'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/persons-paginate', methods=['GET'])
@token_required
def get_persons_paginate():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    offset = (page - 1) * limit
    search = request.args.get('search', '')

    connection = get_db_connection()
    cursor = None

    try:
        # Build base query
        base_query = """
        SELECT 
            *,
            CONVERT(varchar, birth_date, 23) as birth_date,
            uuid + '/' + image as image_path
        FROM persons
        """
        count_query = "SELECT COUNT(*) AS total FROM persons"
        params = []
        count_params = []

        if search:
            base_query += " WHERE name LIKE ? OR nik LIKE ?"
            params.extend([f"%{search}%", f"%{search}%"])
            count_query += " WHERE name LIKE ? OR nik LIKE ?"
            count_params.extend([f"%{search}%", f"%{search}%"])

        base_query += " ORDER BY name ASC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])

        cursor = connection.cursor()
        cursor.execute(base_query, params)
        columns = [column[0] for column in cursor.description]
        persons = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Get total count
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]

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

# Route to get buildings
@app.route('/buildings', methods=['GET'])
@token_required
def get_buildings():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM buildings")
        columns = [column[0] for column in cursor.description]
        buildings = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return jsonify(buildings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to get buildings detail
@app.route('/buildings-detail', methods=['GET'])
@token_required
def get_buildings_detail():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        uuid = request.args.get('uuid')
        if not uuid:
            return jsonify({'error': 'UUID parameter is required'}), 400

        cursor.execute("SELECT * FROM buildings WHERE uuid = ?", (uuid,))
        columns = [column[0] for column in cursor.description]
        building = cursor.fetchone()

        if building:
            return jsonify(dict(zip(columns, building)))
        else:
            return jsonify({'error': 'Building not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to building persons not today
@app.route('/building-persons-not-today', methods=['GET'])
@token_required
def get_building_persons_not_today():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        building_uuid = request.args.get('building_uuid')

        cursor.execute("""
            SELECT
                uuid,
                name,
                image
            FROM persons
            WHERE uuid NOT IN (
                SELECT person_uuid
                FROM building_persons
                WHERE CONVERT(DATE, entry_time) = CONVERT(DATE, GETDATE()) AND
                exit_time IS NULL AND
                person_uuid IS NOT NULL AND
                building_uuid = ?
            )
        """, (building_uuid,))

        columns = [column[0] for column in cursor.description]
        building_persons_not_today = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(building_persons_not_today)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to get building persons today
@app.route('/building-persons-today', methods=['GET'])
@token_required
def get_building_persons_today():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        building_uuid = request.args.get('building_uuid')

        cursor.execute("""
            SELECT 
                building_persons.uuid AS building_person_uuid, 
                persons.name, 
                persons.image
            FROM building_persons
            INNER JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE CONVERT(DATE, entry_time) = CONVERT(DATE, GETDATE()) AND 
            exit_time IS NULL AND
            building_uuid = ?
        """, (building_uuid,))

        columns = [column[0] for column in cursor.description]
        building_persons_today = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify(building_persons_today)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to get building-persons
@app.route('/building-persons', methods=['GET'])
@token_required
def get_building_persons():
    building_uuid = request.args.get('building_uuid')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    offset = (page - 1) * limit
    search = request.args.get('search')

    if not building_uuid:
        return jsonify({'error': 'building_uuid is required'}), 400

    connection = get_db_connection()
    try:
        # Build base query
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
                    WHEN person_uuid IS NULL THEN 'undefined/' + building_persons.image
                    ELSE CONVERT(varchar(36), person_uuid) + '/' + building_persons.image
                END AS image_path
            FROM building_persons 
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE building_uuid = ? AND
            CONVERT(DATE, entry_time) = CONVERT(DATE, GETDATE()) AND
            exit_time IS NULL
        """

        # Add search if provided
        params = [building_uuid]
        if search:
            base_query += " AND persons.name LIKE ?"
            params.append(f"%{search}%")
        base_query += " ORDER BY entry_time DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])

        cursor = connection.cursor()
        cursor.execute(base_query, params)
        columns = [column[0] for column in cursor.description]
        building_persons = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Count total (with search if provided)
        count_query = """
            SELECT COUNT(*) AS total
            FROM building_persons
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE building_uuid = ? AND
            CONVERT(DATE, entry_time) = CONVERT(DATE, GETDATE()) AND
            exit_time IS NULL
        """
        count_params = [building_uuid]
        if search:
            count_query += " AND persons.name LIKE ?"
            count_params.append(f"%{search}%")

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]

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

# Route to get building-persons
@app.route('/building-persons-history', methods=['GET'])
@token_required
def get_building_persons_history():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    offset = (page - 1) * limit
    search = request.args.get('search')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    sort_param = request.args.get('sort', 'entry_time,desc')
    sort_parts = sort_param.split(',')
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
    try:
        # Build base query
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
                    WHEN person_uuid IS NULL THEN 'undefined/' + building_persons.image
                    ELSE CAST(person_uuid AS VARCHAR(36)) + '/' + building_persons.image
                END AS image_path
            FROM building_persons 
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            INNER JOIN buildings ON buildings.uuid = building_persons.building_uuid
        """

        # Add conditions based on parameters
        conditions = []
        params = []
        count_params = []

        if search:
            conditions.append("persons.name LIKE ?")
            params.append(f"%{search}%")
            count_params.append(f"%{search}%")

        if start_date and end_date:
            conditions.append("CONVERT(DATE, entry_time) BETWEEN ? AND ?")
            params.extend([start_date, end_date])
            count_params.extend([start_date, end_date])
        elif start_date:
            conditions.append("CONVERT(DATE, entry_time) >= ?")
            params.append(start_date)
            count_params.append(start_date)
        elif end_date:
            conditions.append("CONVERT(DATE, entry_time) <= ?")
            params.append(end_date)
            count_params.append(end_date)

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        order_by = f" ORDER BY {column_mapping[sort_column]} {sort_direction.upper()} "
        base_query += order_by
        base_query += " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])

        cursor = connection.cursor()
        cursor.execute(base_query, params)
        columns = [column[0] for column in cursor.description]
        building_persons_history = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Count total (with same conditions)
        count_query = """
            SELECT COUNT(*) AS total
            FROM building_persons
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            INNER JOIN buildings ON buildings.uuid = building_persons.building_uuid
        """
        if conditions:
            count_query += " WHERE " + " AND ".join(conditions)

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]

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

@app.route('/building-persons/<string:building_person_uuid>', methods=['DELETE'])
@token_required
def delete_building_person(building_person_uuid):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # First, get the record to determine if it's an exit or entry
        cursor.execute("""
            SELECT building_uuid, exit_time 
            FROM building_persons 
            WHERE uuid = ?
        """, (building_person_uuid,))
        record = cursor.fetchone()
        
        if not record:
            return jsonify({'error': 'Record not found'}), 404
            
        building_uuid = record.building_uuid
        exit_time = record.exit_time
        
        # Delete the record
        cursor.execute("DELETE FROM building_persons WHERE uuid = ?", (building_person_uuid,))
        
        # Update building counts
        if exit_time is None:
            # This was an active entry - decrement entry and total
            cursor.execute("""
                UPDATE buildings 
                SET entry = entry - 1, 
                    total = total - 1 
                WHERE uuid = ?
            """, (building_uuid,))
        else:
            # This was an exit - decrement exit count
            cursor.execute("""
                UPDATE buildings 
                SET [exit] = [exit] - 1 
                WHERE uuid = ?
            """, (building_uuid,))
        
        connection.commit()
        return jsonify({'message': 'Record deleted successfully!'}), 200
        
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/weekly-counts', methods=['GET'])
@token_required
def get_weekly_counts():
    try:
        building_uuid = request.args.get('building_uuid')

        # Get the last 7 days (including today)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)

        connection = get_db_connection()
        cursor = connection.cursor()

        # Common WHERE clause
        where_clause = """
        WHERE entry_time BETWEEN ? AND ?
        {building_condition}
        """.format(
            building_condition="AND building_uuid = ?" if building_uuid else ""
        )

        params = [start_date, end_date]
        if building_uuid:
            params.append(building_uuid)

        # Entry count query
        entry_query = f"""
        SELECT CAST(entry_time AS DATE) AS date, COUNT(*) AS count
        FROM building_persons
        {where_clause}
        GROUP BY CAST(entry_time AS DATE)
        """

        # Exit count query
        exit_query = f"""
        SELECT CAST(exit_time AS DATE) AS date, COUNT(*) AS count
        FROM building_persons
        {where_clause}
        GROUP BY CAST(exit_time AS DATE)
        """

        # Execute entry query
        cursor.execute(entry_query, params)
        entry_results = cursor.fetchall()

        # Execute exit query
        cursor.execute(exit_query, params)
        exit_results = cursor.fetchall()

        # Generate all dates in the range
        date_range = [start_date + timedelta(days=x) for x in range(7)]
        date_strings = [date.strftime('%d/%m/%Y') for date in date_range]  # Changed to dd/mm/yyyy
        weekday_names = [date.strftime('%A') for date in date_range]

        # Initialize counts with 0 - using original format for internal matching
        internal_date_format = {date.strftime('%Y-%m-%d'): 0 for date in date_range}
        entry_counts = internal_date_format.copy()
        exit_counts = internal_date_format.copy()

        # Populate counts from query results
        for row in entry_results:
            entry_counts[str(row.date)] = row.count

        for row in exit_results:
            exit_counts[str(row.date)] = row.count

        response_data = {
            'start_date': start_date.strftime('%d/%m/%Y'),  # Changed to dd/mm/yyyy
            'end_date': end_date.strftime('%d/%m/%Y'),    # Changed to dd/mm/yyyy
            'dates': date_strings,
            'weekdays': weekday_names,
            'entry': [entry_counts[date.strftime('%Y-%m-%d')] for date in date_range],
            'exit': [exit_counts[date.strftime('%Y-%m-%d')] if entry_counts[date.strftime('%Y-%m-%d')] > 0 else 0 for date in date_range]
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# Route to count gate info
@app.route('/count-gate', methods=['GET'])
@token_required
def count_gate():
    count = {
        'total': 0,
        'entry': 0,
        'exit': 0,
        'registered': 0,
        'undefined': 0
    }

    connection = get_db_connection()
    try:
        cursor = connection.cursor()

        # Reset counters if current time is between 23:59:50 and 23:59:59
        now = datetime.now().time()
        if time(23, 59, 50) <= now <= time(23, 59, 59):
            cursor.execute("UPDATE [buildings] SET [entry] = 0, [exit] = 0, [total] = 0")
            connection.commit()

        # Get gate info (Gerbang)
        cursor.execute("SELECT * FROM buildings WHERE name = 'Gerbang'")
        columns = [column[0] for column in cursor.description]
        gate = cursor.fetchone()

        if gate:
            gate_dict = dict(zip(columns, gate))
            count['total'] = gate_dict['total']
            count['entry'] = gate_dict['entry']
            count['exit'] = gate_dict['exit']

        # Get the registered count
        cursor.execute("""
            SELECT COUNT(*) AS registered 
            FROM building_persons 
            WHERE exit_time IS NULL AND person_uuid IS NOT NULL AND
            CONVERT(DATE, entry_time) = CONVERT(DATE, GETDATE())
        """)
        result = cursor.fetchone()
        if result:
            count['registered'] = result[0]

        # Get the undefined count
        cursor.execute("""
            SELECT COUNT(*) AS undefined 
            FROM building_persons 
            WHERE exit_time IS NULL AND person_uuid IS NULL AND
            CONVERT(DATE, entry_time) = CONVERT(DATE, GETDATE())
        """)
        result = cursor.fetchone()
        if result:
            count['undefined'] = result[0]

        return jsonify(count)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run the Flask application')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the application on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the application on')
    args = parser.parse_args()
    
    app.run(host=args.host, port=args.port, debug=True)


