from flask import Blueprint, request, jsonify
from config.database import get_db_connection
from utils.hash import hash_password, generate_token
from .services import token_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    hashed_password = hash_password(password)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        
        cursor.execute("SELECT uuid, password, token FROM `user` WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user or user['password'] != hashed_password:
            return jsonify({'error': 'Invalid username or password'}), 401

        token = user['token']
        
        if user['token'] is None:
            token = generate_token()
            cursor.execute("UPDATE `user` SET token = %s WHERE uuid = %s", (token, user['uuid']))
            conn.commit()

        return jsonify({
            'message': 'Login successful',
            'token': token,
            'uuid': user['uuid']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Token is missing'}), 401
    
    if token.startswith('Bearer '):
        token = token[7:]

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        
        cursor.execute("UPDATE `user` SET token = NULL WHERE token = %s", (token,))
        conn.commit()
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()