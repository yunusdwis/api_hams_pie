from flask import request, jsonify
from config.database import get_db_connection
from functools import wraps

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
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
        cursor = conn.cursor(dictionary=True)
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        cursor.execute("SELECT uuid FROM `user` WHERE token = %s", (token,))
        user = cursor.fetchone()
        return user['uuid'] if user else None
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()