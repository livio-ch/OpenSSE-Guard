import logging
import sqlite3
from flask import Flask, request, jsonify, g
import tldextract
import re
from urllib.parse import urlparse
import json  # Ensure you import json at the top of your script
import os
import time
from log_db import LogDB
from flask_cors import CORS  # Import CORS
import jwt
from jwt.exceptions import PyJWTError
from os import environ as env
from dotenv import load_dotenv, find_dotenv
from authlib.integrations.flask_oauth2 import ResourceProtector
from validator import Auth0JWTBearerTokenValidator
from functools import wraps
import base64
import cache  # Import your cache module
from filter_checks.block_check import get_block_status
from filter_checks.hash_check import check_file_hash_in_db
from filter_checks.mime_check import check_mime_type_in_db
from filter_checks.db_utils import query_database
from filter_checks.redirects import get_redirect_proxy, is_tls_excluded
# Load environment variables from the .env file
load_dotenv()
require_auth = ResourceProtector()
auth0_domain = os.getenv("AUTH0_DOMAIN")
auth0_audience = os.getenv("AUTH0_AUDIENCE")
if not auth0_domain or not auth0_audience:
    raise ValueError("AUTH0_DOMAIN and AUTH0_AUDIENCE must be set in the environment variables.")
validator = Auth0JWTBearerTokenValidator(auth0_domain, auth0_audience)
require_auth.register_token_validator(validator)
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
DB_PATH = "url_filter.db"  # Path to SQLite database
log_db = LogDB()  # Create an instance of the LogDB class for logging

def require_roles(roles):
    """ A decorator to check if the user has the required roles in the token """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization", "").split("Bearer ")[-1]
            if not token:
                return jsonify({"status": "error", "message": "Token missing"}), 401
            # Split the token by the dots
            token_parts = token.split('.')
            # Check if the token is well-formed and has three parts
            if len(token_parts) >= 3:
                payload = token_parts[1]  # The second part (index 1) is the payload
                # Decode the Base64 payload
                decoded_payload = base64.urlsafe_b64decode(payload + "==")  # Adding '==' to pad the Base64 string if necessary
                decoded_payload = decoded_payload.decode('utf-8')  # Decode bytes to string
                # Parse the decoded payload into a dictionary
                payload_data = json.loads(decoded_payload)
                # Get the roles from the payload (make sure the key exists)
                user_roles = payload_data.get("https://yourdomain.com/claims/roles", [])
                g.sub = payload_data.get("sub", [])
                print(f"User {g.sub} Roles: {user_roles}")
                # Check if the required role(s) exist in the token's roles
                if not set(roles).issubset(set(user_roles)):
                    return jsonify({"status": "error", "message": "Insufficient permissions"}), 403
            else:
                return jsonify({"status": "error", "message": "Invalid token format"}), 400
            return func(*args, **kwargs)
        return wrapper
    return decorator

def normalize_url(url):
    """Normalizes URL to remove query parameters and fragments."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

@app.route('/checkHash', methods=['POST'])
@require_auth(["user"])
@require_roles(["user"])
def check_file_and_url():
    """Check both file hash and URL for block status (local database + OTX)."""

    data = request.get_json()
    if "file_hash" not in data or "url" not in data:
        response =  jsonify({'status': 'error', 'message': 'Missing file_hash or url'}), 400
        return response
    # Check file hash (local DB + OTX)
    file_status = check_file_hash_in_db(data['file_hash'])
    if file_status:
        response =  jsonify(file_status), 200
        return response
    # Check URL
    url_status = get_block_status(data['url'])
    if url_status:
        response = jsonify(url_status), 200
        return response
    response = jsonify({'status': 'allowed', 'message': 'File and URL are allowed'}), 200
    return response

@app.route('/checkUrl', methods=['POST'])
@require_auth(["user"])
@require_roles(["user"])
def check_url():
    data = request.get_json()
    logging.info(f"Received data: {data}")
    if "host" in data:
        response = process_host_check(data["host"])
        return response
    if "url" in data:
        response = process_url_check(data["url"])
        return response
    response = jsonify({'status': 'error', 'message': 'Missing URL or host'}), 400
    return response

def process_host_check(hostname):
    if isinstance(hostname, list):
        return jsonify({'status': 'error', 'message': 'Multiple hostnames not allowed'}), 400
    if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(:\d+)?$', hostname):
        return jsonify({'status': 'error', 'message': 'Invalid hostname format'}), 400
    if block_status := get_block_status(f"https://{hostname}"):
        return jsonify(block_status), 200
    if is_tls_excluded(hostname):
        return jsonify({'status': 'exclude-tls', 'message': 'TLS excluded hostname'}), 200
    if proxy := get_redirect_proxy(f"https://{hostname}"):
        return jsonify({'status': 'redirected', 'message': 'Redirected by database rule', 'proxy': proxy}), 200
    return jsonify({'status': 'allowed', 'message': 'TLS allowed'}), 200

def process_url_check(url):
    if not url:
        return jsonify({'status': 'error', 'message': 'Missing URL'}), 400
    url = normalize_url(url)
    logging.info(f"Checking URL: {url}")
    if block_status := get_block_status(url):
        return jsonify(block_status), 200
    if proxy := get_redirect_proxy(url):
        return jsonify({'status': 'redirected', 'message': 'Redirected by database rule', 'proxy': proxy}), 200
    return jsonify({'status': 'allowed', 'message': 'Access granted'}), 200

@app.route('/checkMimeType', methods=['POST'])
@require_auth(["user"])
@require_roles(["user"])
def check_mime_type():
    data = request.get_json()
    if "mime_type" not in data or "url" not in data:
        response = jsonify({'status': 'error', 'message': 'Missing mime_type or url'}), 400
        return response
    mime_status = check_mime_type_in_db(data["mime_type"])
    if mime_status:
        response = jsonify(mime_status), 200
        return response
    response = jsonify({'status': 'allowed', 'message': 'MIME type allowed'}), 200
    return response

@app.route('/logs', methods=['GET'])
@require_auth(["admin"])
@require_roles(["admin"])
def get_logs():
    try:
        # Get all logs from the database using LogDB class
        logs = log_db.get_all_logs()  # Make sure to implement this method in your log_db.py
        if not logs:
            return jsonify({'status': 'error', 'message': 'No logs found'}), 404
        # Return the logs in a JSON format
        return jsonify({'status': 'success', 'logs': logs}), 200
    except Exception as e:
        logging.error(f"Error fetching logs: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch logs'}), 500

@app.route('/cache', methods=['GET'])
@require_auth(["admin"])
@require_roles(["admin"])
def get_cache():
    try:
        # Assumes your cache module has a get_all_cache() function
        cached_items = cache.get_all_cache()
        if not cached_items:
            return jsonify({'status': 'error', 'message': 'No cache found'}), 404
        return jsonify({'status': 'success', 'cache': cached_items}), 200
    except Exception as e:
        logging.error(f"Error fetching cache: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Failed to fetch cache'}), 500


def fetch_data_from_table(table_name, columns):
    """General function to fetch data from any table."""
    try:
        # Connect to the database
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            query = f"SELECT {', '.join(columns)} FROM {table_name}"
            cursor.execute(query)
            data = cursor.fetchall()
        if not data:
            return {'status': 'error', 'message': f'No data found in {table_name}'}, 404
        return {'status': 'success', 'data': data}, 200
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return {'status': 'error', 'message': 'Failed to fetch data from the database'}, 500

@app.route('/get_policy', methods=['GET'])
@require_auth(["admin"])
@require_roles(["user"])
def get_policy():
    """Fetch the current blocklist data based on the table specified in the query parameters."""
    # Get the table name from the query parameters
    table_name = request.args.get('table', None)
    if not table_name:
        return jsonify({'status': 'error', 'message': 'Table name is required'}), 400
    # Define the available tables and their respective columns
    table_columns = {
        'blocked_urls': ['value', 'type'],
        'blocked_files': ['file_hash', 'value'],
        'blocked_mimetypes': ['value'],
        'redirect_urls': ['type', 'value' , 'proxy'],
        'tls_excluded_hosts': ['hostname'],
        'category_policy': ['category_id','name','action'],
    }

    # Validate the requested table name
    if table_name not in table_columns:
        return jsonify({'status': 'error', 'message': f'Invalid table name: {table_name}'}), 400

    # Fetch the data from the specified table
    columns = table_columns[table_name]
    response, status_code = fetch_data_from_table(table_name, columns)
    return jsonify(response), status_code

@app.route('/set_policy', methods=['POST'])
@require_auth(["admin"])
@require_roles(["admin"])
def set_policy():
    """
    Adds a policy entry to a specified table in the database.
    The data should include the table name and the relevant entry data.
    Expected JSON: {"table": "blocked_urls", "data": {"url": "www.google.com", "type": "domain"}}
    """
    data = request.get_json()
    logging.error(f"INPUT: {data}")
    # Check if the required data is present in the request
    if "table" not in data or "data" not in data or not isinstance(data.get("data"), dict):
        return jsonify({'status': 'error', 'message': 'Missing table or values'}), 400

    table_name = data["table"]
    input_values = data["data"]

    # Define the available tables, their DB columns, and a mapping from JSON key to DB column
    table_columns = {
        'blocked_urls': ['value', 'type'],
        'blocked_files': ['file_hash', 'value'],
        'blocked_mimetypes': ['value'],
        'redirect_urls': ['type', 'value', 'proxy'],
        'tls_excluded_hosts': ['hostname'],
    }
    # Mapping: for each table, map DB column name to the key expected in the incoming JSON.
    mapping = {
        'blocked_urls': {'value': 'url', 'type': 'type'},
        'blocked_files': {'file_hash': 'file_hash', 'value': 'file_name'},
        'blocked_mimetypes': {'value': 'mime_type'},
        'redirect_urls': {'type': 'type', 'value': 'source_url', 'proxy': 'proxy'},
        'tls_excluded_hosts': {'hostname': 'hostname'},
    }

    # Validate the requested table name
    if table_name not in table_columns:
        return jsonify({'status': 'error', 'message': f'Invalid table name: {table_name}'}), 400
    columns = table_columns[table_name]
    key_mapping = mapping[table_name]
    # Build the list of values in the correct order based on the mapping.
    ordered_values = []
    for col in columns:
        json_key = key_mapping.get(col, col)  # Default to col if no mapping exists
        value = input_values.get(json_key)
        if value is None:
            return jsonify({'status': 'error', 'message': 'Missing values for one or more columns'}), 400
        ordered_values.append(value)
    # Create the SQL query for inserting the data
    placeholders = ', '.join(['?'] * len(ordered_values))
    query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    try:
        # Insert the data into the specified table
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(ordered_values))
            conn.commit()
        return jsonify({'status': 'success', 'message': 'Policy entry added successfully'}), 201
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}, query: {query}, values: {ordered_values}")
        return jsonify({'status': 'error', 'message': 'Failed to add policy entry'}), 500

@app.route('/delete_policy', methods=['DELETE'])
@require_auth(["admin"])
@require_roles(["admin"])
def delete_policy():
    """
    Deletes a policy entry from a specified table in the database.
    The data should include the table name and the condition string for deletion.
    """
    data = request.get_json()
    # Check if the required data is present in the request
    if "table" not in data or "condition" not in data:
        return jsonify({'status': 'error', 'message': 'Missing table or condition'}), 400
    table_name = data["table"]
    condition = data["condition"]  # Now condition is a string, not a dictionary
    # Define the available tables and their columns
    table_columns = {
        'blocked_urls': ['value', 'type'],
        'blocked_files': ['file_hash', 'value'],
        'blocked_mimetypes': ['value'],
        'redirect_urls': ['type', 'value', 'proxy'],
        'tls_excluded_hosts': ['hostname'],
    }
    # Validate the requested table name
    if table_name not in table_columns:
        return jsonify({'status': 'error', 'message': f'Invalid table name: {table_name}'}), 400
    # Ensure the condition string is not empty or unsafe
    if not condition.strip():
        return jsonify({'status': 'error', 'message': 'Condition is empty'}), 400
    # Assume that the condition string corresponds to the first column if no column is specified
    columns = table_columns.get(table_name)
    # If the condition doesn't have a column name, assume the first column (e.g., "value")
    if len(condition.split('= ')) == 1:
        condition = f"{columns[0]} = '{condition.strip()}'"
    # Build the SQL query for deletion using parameterized queries
    query = f"DELETE FROM {table_name} WHERE {condition}"
    logging.error(f"Query: {query}")
    try:
        # Execute the SQL query with parameterized values to prevent SQL injection
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query)  # Execute the query
            conn.commit()

        return jsonify({'status': 'success', 'message': 'Policy entry deleted successfully'}), 200

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to delete policy entry'}), 500


@app.before_request
def start_time():
    request.start_time = time.time()


@app.after_request
def log_response(response):
    """Log the request and response data."""
    # Calculate the response time
    response_time = time.time() - getattr(request, 'start_time', time.time())
    # Ensure that request and response are serialized correctly
    request_data = json.dumps(request.get_json() if request.is_json else {}, ensure_ascii=False)
    if response.is_json:
        response_data = json.dumps(response.get_json(), ensure_ascii=False)
    else:
        response_data = response.get_data(as_text=True)
    # Log the request and response data
    if hasattr(g, 'sub'):
        myuser = g.sub
    else:
        myuser = "unknown"
    log_db.log(
        level='INFO',
        user=myuser,
        request=request_data if request.method != "GET" else str(json.dumps(request.args.to_dict())) ,
        response=response_data if request.method != "GET" else "N/A",  # Empty response for GET
        client_ip=str(request.remote_addr),
        user_agent=str(request.headers.get('User-Agent')),
        method=request.method,
        status_code=response.status_code,
        response_time=response_time,
        category=request.path  # Category can be dynamic based on the request URL
    )
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    if str(e).startswith("401"):
            return jsonify({'status': 'Unauthorized', 'message': '401 Unauthorized'}), 401
    logging.error(f"Unexpected error: {e}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
