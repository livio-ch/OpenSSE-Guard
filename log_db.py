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
                    user TEXT,
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
                cursor.execute("SELECT id, level, user, request, response, client_ip, user_agent, method, status_code, response_time, category, timestamp FROM logs ORDER BY timestamp DESC")
                logs = cursor.fetchall()
                logging.info(f"Retrieved {len(logs)} logs from the database")

                # Convert the logs into a more readable format (a list of dictionaries)
                log_entries = []
                for log in logs:
                    log_entry = {
                        'id': log[0],
                        'level': log[1],
                        'user' : log[2],
                        'request': log[3],
                        'response': log[4],
                        'client_ip': log[5],
                        'user_agent': log[6],
                        'method': log[7],
                        'status_code': log[8],
                        'response_time': log[9],
                        'category': log[10],
                        'timestamp': log[11]
                    }

                    # Deserialize 'request', 'response', and 'client_ip' if in JSON format
                    for field in ['request', 'response']:
                        if log_entry[field]:
                            try:
                                log_entry[field] = json.loads(log_entry[field])
                            except json.JSONDecodeError as e:
                        #        logging.warning(f"Failed to decode '{field}' field as JSON: {e}")
                                pass

                    log_entries.append(log_entry)

                return {'logs': log_entries, 'status': 'success'}
        except sqlite3.Error as e:
            logging.error(f"SQLite error retrieving logs: {e}")
            return {'logs': [], 'status': 'error'}
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return {'logs': [], 'status': 'error'}


    def log(self, level, user, request, response, client_ip=None, user_agent=None, method=None,
            status_code=None, response_time=None, category=None, error_message=None):
        """Insert a log entry into the database."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO logs (timestamp, level, user, request, response, client_ip,
                                                   user_agent, method, status_code, response_time,
                                                   category, error_message)
                                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                               (timestamp, level, user, request, response, client_ip, user_agent, method,
                                status_code, response_time, category, error_message))
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Error inserting log entry: {e}")
