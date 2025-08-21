from datetime import datetime
from time import mktime
from config.database import get_db_connection
from dotenv import load_dotenv
import os

load_dotenv()

DANGER_CODE = os.getenv('DANGER_CODE')

def get_danger_status():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT 
                COALESCE(danger_mode, FALSE) AS danger_mode,
                danger_start_time 
            FROM settings 
            LIMIT 1
        """)
        settings = cursor.fetchone()

        if not settings:
            return {
                'danger_mode': False,
                'danger_time_elapsed': "00:00:00"
            }
        
        start_time = settings.get('danger_start_time')
        if start_time:
            now = datetime.now()
            elapsed = now - start_time
            total_seconds = int(elapsed.total_seconds())

            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            formatted_time = "00:00:00"

        return {
            'danger_mode': bool(settings.get('danger_mode', False)),
            'danger_time_elapsed': formatted_time
        }
    finally:
        cursor.close()
        conn.close()


def update_danger_mode(danger_mode: bool, code: str):
    if code != DANGER_CODE:
        return {'error': 'Invalid danger code'}, 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT 1 FROM settings LIMIT 1")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings (danger_mode) VALUES (FALSE)")

        if danger_mode:
            cursor.execute("""
                UPDATE settings 
                SET danger_mode = TRUE, 
                    danger_start_time = CURRENT_TIMESTAMP 
                LIMIT 1
            """)
        else:
            cursor.execute("""
                UPDATE settings 
                SET danger_mode = FALSE, 
                    danger_start_time = NULL 
                LIMIT 1
            """)
        conn.commit()

        cursor.execute("""
            SELECT 
                COALESCE(danger_mode, FALSE) AS danger_mode,
                danger_start_time 
            FROM settings 
            LIMIT 1
        """)
        updated = cursor.fetchone()
        start_time = updated.get('danger_start_time')
        start_timestamp = mktime(start_time.timetuple()) if start_time else None

        return {
            'message': 'Danger mode updated successfully',
            'danger_mode': bool(updated.get('danger_mode', False)),
            'danger_start_time': start_timestamp
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
