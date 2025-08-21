from flask import jsonify
from datetime import datetime, timedelta, time
from config.database import get_db_connection

def get_weekly_counts_service(building_uuid=None):
    try:
        # Get the last 7 days (including today)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Common WHERE clause
        where_clause = """
        WHERE entry_time BETWEEN %s AND %s
        {building_condition}
        """.format(
            building_condition="AND building_uuid = %s" if building_uuid else ""
        )

        params = [start_date, end_date]
        if building_uuid:
            params.append(building_uuid)

        # Entry count query
        entry_query = f"""
        SELECT DATE(entry_time) AS date, COUNT(*) AS count
        FROM building_persons
        {where_clause}
        GROUP BY DATE(entry_time)
        """

        # Exit count query
        exit_query = f"""
        SELECT DATE(exit_time) AS date, COUNT(*) AS count
        FROM building_persons
        {where_clause}
        GROUP BY DATE(exit_time)
        """

        # Execute entry query
        cursor.execute(entry_query, params)
        entry_results = cursor.fetchall()

        # Execute exit query
        cursor.execute(exit_query, params)
        exit_results = cursor.fetchall()

        # Generate all dates in the range
        date_range = [start_date + timedelta(days=x) for x in range(7)]
        date_strings = [date.strftime('%d/%m/%Y') for date in date_range]
        weekday_names = [date.strftime('%A') for date in date_range]

        # Initialize counts with 0
        internal_date_format = {date.strftime('%Y-%m-%d'): 0 for date in date_range}
        entry_counts = internal_date_format.copy()
        exit_counts = internal_date_format.copy()

        # Populate counts from query results
        for row in entry_results:
            entry_counts[str(row['date'])] = row['count']

        for row in exit_results:
            exit_counts[str(row['date'])] = row['count']

        response_data = {
            'start_date': start_date.strftime('%d/%m/%Y'),
            'end_date': end_date.strftime('%d/%m/%Y'),
            'dates': date_strings,
            'weekdays': weekday_names,
            'entry': [entry_counts[date.strftime('%Y-%m-%d')] for date in date_range],
            'exit': [
                exit_counts[date.strftime('%Y-%m-%d')]
                if entry_counts[date.strftime('%Y-%m-%d')] > 0 else 0
                for date in date_range
            ]
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()


def count_gate_service():
    count = {
        'total': 0,
        'entry': 0,
        'exit': 0,
        'registered': 0,
        'undefined': 0
    }

    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)

        # Reset counters if current time is between 23:59:50 and 23:59:59
        now = datetime.now().time()
        if time(23, 59, 50) <= now <= time(23, 59, 59):
            cursor.execute("UPDATE buildings SET entry = 0, `exit` = 0, total = 0")
            connection.commit()

        # Get gate info
        cursor.execute("SELECT * FROM buildings WHERE name = 'Gerbang'")
        gate = cursor.fetchone()

        if gate:
            count['total'] = gate['total']
            count['entry'] = gate['entry']
            count['exit'] = gate['exit']

        # Get the registered count
        cursor.execute("""
            SELECT COUNT(*) AS registered 
            FROM building_persons 
            WHERE exit_time IS NULL 
              AND person_uuid IS NOT NULL 
              AND DATE(entry_time) = CURDATE()
        """)
        result = cursor.fetchone()
        if result:
            count['registered'] = result['registered']

        # Get the undefined count
        cursor.execute("""
            SELECT COUNT(*) AS undefined 
            FROM building_persons 
            WHERE exit_time IS NULL 
              AND person_uuid IS NULL 
              AND DATE(entry_time) = CURDATE()
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
