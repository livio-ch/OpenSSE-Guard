import sqlite3
import logging
import time
import json

class LogDB:
    def __init__(self, db_path='log_database.db'):
        self.db_path = db_path
        self._create_table()

    def _create_table(self):
        """Create the log table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    level TEXT,
                    request TEXT,
                    response TEXT,
                    client_ip TEXT,
                    user_agent TEXT,
                    method TEXT,
                    status_code INTEGER,
                    response_time REAL,
                    category TEXT,
                    error_message TEXT
                )''')
        except sqlite3.Error as e:
            logging.error(f"Error creating log table: {e}")

    def get_all_logs(self):
        """Retrieve all log entries from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id,level,request,response,client_ip,user_agent,method,status_code,response_time,category,timestamp FROM logs ORDER BY timestamp DESC")  # Retrieve logs ordered by timestamp
                logs = cursor.fetchall()

                # Convert the logs into a more readable format (a list of dictionaries)
                log_entries = []
                for log in logs:
                    log_entry = {
                        'id': log[0],
                        'level': log[1],
                        'request': log[2],
                        'response': log[3],
                        'client_ip': log[4],
                        'user_agent': log[5],
                        'method': log[6],
                        'status_code': log[7],
                        'response_time': log[8],
                        'category': log[9],
                        'timestamp': log[10]
                    }

                    # Deserialize 'request' and 'response' fields if they are in JSON format
                    try:
                        log_entry['request'] = json.loads(log_entry['request'])
                    except json.JSONDecodeError:
                        pass  # Ignore if it's not a valid JSON string

                    try:
                        log_entry['response'] = json.loads(log_entry['response'])
                    except json.JSONDecodeError:
                        pass  # Ignore if it's not a valid JSON string

                    # Optionally: Deserialize 'client_ip' if it's in JSON format (if stored like this)
                    try:
                        log_entry['client_ip'] = json.loads(log_entry['client_ip'])
                    except json.JSONDecodeError:
                        pass  # Ignore if it's not a valid JSON string

                    log_entries.append(log_entry)

                return {'logs': log_entries, 'status': 'success'}
        except sqlite3.Error as e:
            logging.error(f"Error retrieving logs: {e}")
            return {'logs': [], 'status': 'error'}

    def log(self, level, request, response, client_ip=None, user_agent=None, method=None,
            status_code=None, response_time=None, category=None, error_message=None):
        """Insert a log entry into the database."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO logs (timestamp, level, request, response, client_ip,
                                                   user_agent, method, status_code, response_time,
                                                   category, error_message)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (timestamp, level, request, response, client_ip, user_agent, method,
                                status_code, response_time, category, error_message))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error inserting log entry: {e}")
