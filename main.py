import uuid
import os
import mysql.connector
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from mysql.connector import pooling
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Create MySQL connection pool
db_pool = pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    host="localhost",
    user="root",
    password="",
    database="pie",
    autocommit=True
)

UPLOAD_FOLDER = r'C:\Putra\Proyek\Createch\PIE\Projects\people_counter_v2\people'
UPLOAD_FOLDER_BPJS = r'C:\Putra\Proyek\Createch\PIE\Projects\people_counter_v2\bpjs'
UPLOAD_FOLDER_MEDICAL_HISTORY = r'C:\Putra\Proyek\Createch\PIE\Projects\people_counter_v2\medical_history'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_BPJS'] = UPLOAD_FOLDER_BPJS
app.config['UPLOAD_FOLDER_MEDICAL_HISTORY'] = UPLOAD_FOLDER_MEDICAL_HISTORY
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to unregistered persons
@app.route('/unregistered', methods=['POST'])
def unregistered():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON or missing Content-Type header'}), 400

        image = data.get('image')
        name = data.get('name')
        nik = data.get('nik')
        email = data.get('email')
        address = data.get('address')
        emergency_contact = data.get('emergency_contact')
        building_uuid = data.get('building_uuid')
        building_person_uuid = data.get('building_person_uuid')
        insert = data.get('insert')

        if not all([name, nik, email, address, emergency_contact]):
            return jsonify({'error': 'All fields are required'}), 400

        person_uuid = str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO persons (uuid, image, name, nik, email, address, emergency_contact)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (person_uuid, image, name, nik, email, address, f"+62{emergency_contact}"))

        if insert == 1:
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
            cursor.execute("""
                UPDATE building_persons SET person_uuid = %s WHERE uuid = %s
            """, (person_uuid, building_person_uuid))

        connection.commit()
        return jsonify({'message': 'Entry person successfully!'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if connection: connection.close()


@app.route('/registered', methods=['POST'])
def registered():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON or missing Content-Type header'}), 400

        person_uuid = data.get('person_uuid')
        image = data.get('image')
        building_uuid = data.get('building_uuid')
        building_person_uuid = data.get('building_person_uuid')
        insert = data.get('insert')

        if not all([person_uuid]):
            return jsonify({'error': 'All fields are required'}), 400

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
            cursor.execute("""
                UPDATE building_persons SET person_uuid = %s WHERE uuid = %s
            """, (person_uuid, building_person_uuid))

        connection.commit()
        return jsonify({'message': 'Entry person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

@app.route('/exit', methods=['POST'])
def exit():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)

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
                exit_time = %s
                WHERE uuid = %s
        """, (exit_time, uuid))

        building_uuid = 'e1b6c9e7-4b8d-4e16-9d17-297c9816b64e'

        cursor.execute("""
            UPDATE buildings 
            SET `exit` = `exit` + 1, total = total - 1 
            WHERE uuid = %s
        """, (building_uuid,))

        connection.commit()
        return jsonify({'message': 'Exit person successfully!'}), 200

    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        if cursor: cursor.close()
        if connection: connection.close()

# Route to get persons
@app.route('/persons', methods=['GET'])
def get_persons():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM persons")
        persons = cursor.fetchall()
        return jsonify(persons)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to create a new person with UUID
@app.route('/persons', methods=['POST'])
def create_person():
    data = request.form
    image = request.files.get('image')
    bpjs = request.files.get('bpjs')
    medical_history = request.files.get('medical_history')
    
    try:
        connection = db_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Generate UUID for the new person
        person_uuid = str(uuid.uuid4())
        
        # Handle image upload
        image_filename = None

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_filename = f"{person_uuid}_{filename}"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        bpjs_filename = None

        if bpjs and allowed_file(bpjs.filename):
            filename = secure_filename(bpjs.filename)
            bpjs_filename = f"{person_uuid}_{filename}"
            bpjs.save(os.path.join(app.config['UPLOAD_FOLDER_BPJS'], bpjs_filename))

        medical_history_filename = None

        if medical_history and allowed_file(medical_history.filename):
            filename = secure_filename(medical_history.filename)
            medical_history_filename = f"{person_uuid}_{filename}"
            medical_history.save(os.path.join(app.config['UPLOAD_FOLDER_MEDICAL_HISTORY'], medical_history_filename))
        
        # Insert new person with UUID
        query = """
        INSERT INTO persons (uuid, name, status, departement, nik, address, contact, emergency_contact, email, image, bpjs, medical_history)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            person_uuid,
            data.get('name'),
            data.get('status'),
            data.get('departement'),
            data.get('nik'),
            data.get('address'),
            f"+62{data.get('contact')}",
            f"+62{data.get('emergency_contact')}",
            data.get('email'),
            image_filename,
            bpjs_filename,
            medical_history_filename
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
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Route to get a single person by UUID
@app.route('/persons/<string:person_uuid>', methods=['GET'])
def get_person(person_uuid):
    try:
        connection = db_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM persons WHERE uuid = %s"
        cursor.execute(query, (person_uuid,))
        person = cursor.fetchone()
        
        if not person:
            return jsonify({'error': 'Person not found'}), 404
            
        return jsonify(person)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Route to update a person by UUID
@app.route('/persons/<string:person_uuid>', methods=['PUT'])
def update_person(person_uuid):
    data = request.form
    image = request.files.get('image')
    bpjs = request.files.get('bpjs')
    medical_history = request.files.get('medical_history')
    
    try:
        connection = db_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Check if person exists
        cursor.execute("SELECT * FROM persons WHERE uuid = %s", (person_uuid,))
        person = cursor.fetchone()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Handle image upload if new image provided
        image_filename = person['image']
        if image and allowed_file(image.filename):
            # Delete old image if exists
            if person['image']:
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], person['image'])
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image with UUID prefix
            filename = secure_filename(image.filename)
            image_filename = f"{person_uuid}_{filename}"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # Handle file upload if new bpjs provided
        bpjs_filename = person['bpjs']
        if bpjs and allowed_file(bpjs.filename):
            # Delete old bpjs if exists
            if person['bpjs']:
                old_bpjs_path = os.path.join(app.config['UPLOAD_FOLDER_BPJS'], person['bpjs'])
                if os.path.exists(old_bpjs_path):
                    os.remove(old_bpjs_path)
            
            # Save new bpjs with UUID prefix
            filename = secure_filename(bpjs.filename)
            bpjs_filename = f"{person_uuid}_{filename}"
            bpjs.save(os.path.join(app.config['UPLOAD_FOLDER_BPJS'], bpjs_filename))

        # Handle file upload if new medical_history provided
        medical_history_filename = person['medical_history']
        if medical_history and allowed_file(medical_history.filename):
            # Delete old medical_history if exists
            if person['medical_history']:
                old_medical_history_path = os.path.join(app.config['UPLOAD_FOLDER_MEDICAL_HISTORY'], person['medical_history'])
                if os.path.exists(old_medical_history_path):
                    os.remove(old_medical_history_path)
            
            # Save new medical_history with UUID prefix
            filename = secure_filename(medical_history.filename)
            medical_history_filename = f"{person_uuid}_{filename}"
            medical_history.save(os.path.join(app.config['UPLOAD_FOLDER_MEDICAL_HISTORY'], medical_history_filename))
        
        # Update person
        query = """
        UPDATE persons 
        SET name = %s, status = %s, departement = %s, nik = %s, address = %s, contact = %s, 
            emergency_contact = %s, email = %s, image = %s, bpjs = %s, medical_history = %s
        WHERE uuid = %s
        """
        values = (
            data.get('name', person['name']),
            data.get('status', person['status']),
            data.get('departement', person['departement']),
            data.get('nik', person['nik']),
            data.get('address', person['address']),
            data.get('contact', f"+62{person['contact']}"),
            data.get('emergency_contact', f"+62{person['emergency_contact']}"),
            data.get('email', person['email']),
            image_filename,
            bpjs_filename,
            medical_history_filename,
            person_uuid
        )
        
        cursor.execute(query, values)
        connection.commit()
        
        return jsonify({'message': 'Person updated successfully!'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Route to delete a person by UUID
@app.route('/persons/<string:person_uuid>', methods=['DELETE'])
def delete_person(person_uuid):
    try:
        connection = db_pool.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # First get person to delete their image
        cursor.execute("SELECT * FROM persons WHERE uuid = %s", (person_uuid,))
        person = cursor.fetchone()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
        
        # Delete image file if exists
        if person['image']:
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], person['image'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Delete person from database
        cursor.execute("DELETE FROM persons WHERE uuid = %s", (person_uuid,))
        connection.commit()
        
        return jsonify({'message': 'Person deleted successfully!'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Route to get persons paginate
@app.route('/persons-paginate', methods=['GET'])
def get_persons_paginate():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    offset = (page - 1) * limit
    search = request.args.get('search')

    connection = db_pool.get_connection()
    cursor = None  # Initialize cursor to avoid UnboundLocalError

    try:
        # Build base query
        base_query = "SELECT * FROM persons"
        params = []

        if search:
            base_query += " AND persons.name LIKE %s"
            params.append(f"%{search}%")
        base_query += " ORDER BY name ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor = connection.cursor(dictionary=True)
        cursor.execute(base_query, params)
        persons = cursor.fetchall()

        # Count total (with search if provided)
        count_query = "SELECT COUNT(*) AS total FROM persons"
        count_params = []
        if search:
            count_query += " AND persons.name LIKE %s"
            count_params.append(f"%{search}%")

        cursor.execute(count_query, count_params)
        total = cursor.fetchone()['total']

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
def get_buildings():
    connection = db_pool.get_connection()
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

# Route to get buildings detail
@app.route('/buildings-detail', methods=['GET'])
def get_buildings_detail():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        uuid = request.args.get('uuid')
        if not uuid:
            return jsonify({'error': 'UUID parameter is required'}), 400

        cursor.execute("SELECT * FROM buildings WHERE uuid = %s LIMIT 1", (uuid,))
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

# Route to building persons not today
@app.route('/building-persons-not-today', methods=['GET'])
def get_building_persons_not_today():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
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
                WHERE DATE(entry_time) = CURDATE() AND
                exit_time IS NULL AND
                person_uuid IS NOT NULL AND
                building_uuid = %s
            )
        """, (building_uuid,))

        building_persons_not_today = cursor.fetchall()

        return jsonify(building_persons_not_today)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to get building persons today
@app.route('/building-persons-today', methods=['GET'])
def get_building_persons_today():
    connection = db_pool.get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        building_uuid = request.args.get('building_uuid')

        cursor.execute("""
            SELECT 
                building_persons.uuid, 
                persons.name, 
                persons.image
            FROM building_persons
            INNER JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE DATE(entry_time) = CURDATE() AND 
            exit_time IS NULL AND
            building_uuid = %s
        """, (building_uuid,))

        building_persons_today = cursor.fetchall()

        return jsonify(building_persons_today)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

# Route to get building-persons
@app.route('/building-persons', methods=['GET'])
def get_building_persons():
    building_uuid = request.args.get('building_uuid')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    offset = (page - 1) * limit
    search = request.args.get('search')

    if not building_uuid:
        return jsonify({'error': 'building_uuid is required'}), 400

    connection = db_pool.get_connection()
    try:
        # Build base query
        base_query = """
            SELECT 
                building_persons.uuid,
                building_persons.image,
                persons.uuid AS person_uuid,
                persons.image AS person_image,
                persons.name AS person_name,
                persons.nik AS person_nik,
                persons.address AS person_address,
                persons.emergency_contact AS person_emergency_contact,
                persons.email AS person_email,
                entry_time,
                exit_time
            FROM building_persons 
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE building_uuid = %s AND
            DATE(entry_time) = CURDATE() AND
            exit_time IS NULL
        """

        # Add search if provided
        params = [building_uuid]
        if search:
            base_query += " AND persons.name LIKE %s"
            params.append(f"%{search}%")
        base_query += " ORDER BY entry_time DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor = connection.cursor(dictionary=True)
        cursor.execute(base_query, params)
        building_persons = cursor.fetchall()

        # Count total (with search if provided)
        count_query = """
            SELECT COUNT(*) AS total
            FROM building_persons
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            WHERE building_uuid = %s AND
            DATE(entry_time) = CURDATE() AND
            exit_time IS NULL
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

# Route to get building-persons
@app.route('/building-persons-history', methods=['GET'])
def get_building_persons_history():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 5))
    offset = (page - 1) * limit
    search = request.args.get('search')

    connection = db_pool.get_connection()
    try:
        # Build base query
        base_query = """
            SELECT 
                building_persons.uuid,
                building_persons.image,
                buildings.name AS building_name,
                persons.uuid AS person_uuid,
                persons.image AS person_image,
                persons.name AS person_name,
                persons.nik AS person_nik,
                persons.address AS person_address,
                persons.emergency_contact AS person_emergency_contact,
                persons.email AS person_email,
                entry_time,
                exit_time
            FROM building_persons 
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            INNER JOIN buildings ON buildings.uuid = building_persons.building_uuid
        """

        # Add search if provided
        params = []
        if search:
            base_query += " WHERE persons.name LIKE %s"
            params.append(f"%{search}%")
        base_query += " ORDER BY entry_time DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor = connection.cursor(dictionary=True)
        cursor.execute(base_query, params)
        building_persons_history = cursor.fetchall()

        # Count total (with search if provided)
        count_query = """
            SELECT COUNT(*) AS total
            FROM building_persons
            LEFT JOIN persons ON persons.uuid = building_persons.person_uuid
            INNER JOIN buildings ON buildings.uuid = building_persons.building_uuid
        """
        count_params = []
        if search:
            count_query += " WHERE AND persons.name LIKE %s"
            count_params.append(f"%{search}%")

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


# Route to count gate info
@app.route('/count-gate', methods=['GET'])
def count_gate():
    count = {
        'total': 0,
        'entry': 0,
        'exit': 0,
        'registered': 0,
        'undefined': 0
    }

    connection = db_pool.get_connection()
    try:
        # Get gate info (Gerbang)
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM buildings WHERE name = 'Gerbang' LIMIT 1")
        gate = cursor.fetchone()

        if gate:
            count['total'] = gate['total']
            count['entry'] = gate['entry']
            count['exit'] = gate['exit']

        # Get the registered count
        cursor.execute("""
            SELECT COUNT(*) AS registered 
            FROM building_persons 
            WHERE exit_time IS NULL AND person_uuid IS NOT NULL
        """)
        result = cursor.fetchone()
        if result:
            count['registered'] = result['registered']

        # Get the undefined count
        cursor.execute("""
            SELECT COUNT(*) AS undefined 
            FROM building_persons 
            WHERE exit_time IS NULL AND person_uuid IS NULL
        """)
        result = cursor.fetchone()
        if result:
            count['undefined'] = result['undefined']

        return jsonify(count)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)