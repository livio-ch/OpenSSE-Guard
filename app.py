import logging
import sqlite3
from flask import Flask, request, jsonify
import tldextract
import re
from urllib.parse import urlparse
import requests  # To make API calls to OTX
import json  # Ensure you import json at the top of your script
import os
import time
from log_db import LogDB
from flask_cors import CORS  # Import CORS

from dotenv import load_dotenv  # Import dotenv

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# Load environment variables from the .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


DB_PATH = "url_filter.db"  # Path to SQLite database

OTX_API_KEY = os.getenv('OTX_API_KEY')  # Retrieve the API key from the .env file
OTX_API_URL = 'https://otx.alienvault.com/api/v1/indicators/domain/{}/general'  # OTX API URL for domain check
log_db = LogDB()  # Create an instance of the LogDB class for logging

# Helper Functions
def get_domain(url):
    """Extracts the main domain from a URL (ignores subdomains)."""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def normalize_url(url):
    """Normalizes URL to remove query parameters and fragments."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def query_database(query, params=()):
    """Executes a database query and returns the first result."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return None

def get_block_status(url):
    """Checks if a URL is blocked based on database rules and OTX."""
    hostname = urlparse(url).netloc
    domain = get_domain(url)

    # Check against local database first
    checks = [
        ("SELECT value FROM blocked_urls WHERE type = 'url_prefix' AND ? LIKE value || '%'", (url,), 'Blocked by URL prefix'),
        ("SELECT value FROM blocked_urls WHERE type = 'hostname' AND value = ?", (hostname,), 'Blocked by exact hostname'),
        ("SELECT value FROM blocked_urls WHERE type = 'domain' AND value = ?", (domain,), 'Blocked by domain (includes subdomains)'),
    ]

    for query, params, message in checks:
        if query_database(query, params):
            return {'status': 'blocked', 'message': message}

    # Check OTX for IOC (Indicator of Compromise)
    ioc_status = check_otx_for_ioc(domain)
    logging.info(f"Domain {domain} isioc status {ioc_status}.")
    if ioc_status and ioc_status.get('verdict') != 'Whitelisted':
        # If it's an IOC and not whitelisted, block the request
        return {'status': 'blocked', 'message': 'Domain is an IOC (Indicator of Compromise)'}

    return None  # Not blocked


def check_otx_for_ioc(domain):
    """Check the domain against OTX and extract Facts & Verdict."""
    headers = {'X-OTX-API-KEY': OTX_API_KEY}
    response = requests.get(OTX_API_URL.format(domain), headers=headers)

    if response.status_code == 200:
        data = response.json()

        # Check if pulse_info count is 0
        pulse_info = data.get('pulse_info', {})
        pulse_count = pulse_info.get('count', 0)

        if pulse_count == 0:
            logging.info(f"Domain {domain} has pulse count 0, not blocking.")
            return None  # No pulses, so don't block

        # Extract the validation list that contains information about whitelist
        validations = data.get('validation', [])

        # Check if any of the validation sources are "whitelist"
        for validation in validations:
            if validation.get('source') == 'whitelist':
                logging.info(f"Domain {domain} is whitelisted. Not blocking.")
                return None  # Domain is whitelisted, so we don't block it

        # If it's not whitelisted, check for other IOC information (verdict)
        facts = data.get('facts', {})
        verdict = facts.get('verdict', 'Unknown')

        # Extract other relevant details from 'facts'
        ip_addresses = facts.get('current_ip_addresses', [])
        current_asns = facts.get('current_asns', [])
        current_nameservers = facts.get('current_nameservers', [])
        ssl_certificates = facts.get('ssl_certificates', [])

        # Logging the extracted information in a readable format
        logging.info(f"OTX Verdict for {domain}: {verdict}")
        logging.info(f"OTX IP Addresses for {domain}: {json.dumps(ip_addresses, indent=4)}")
        logging.info(f"OTX Current ASNs for {domain}: {json.dumps(current_asns, indent=4)}")
        logging.info(f"OTX Current Nameservers for {domain}: {json.dumps(current_nameservers, indent=4)}")
        logging.info(f"OTX SSL Certificates for {domain}: {json.dumps(ssl_certificates, indent=4)}")

        # Return the IOC info (but only if it's not whitelisted)
        return {
            'verdict': verdict,
            'ip_addresses': ip_addresses,
            'current_asns': current_asns,
            'current_nameservers': current_nameservers,
            'ssl_certificates': ssl_certificates
        }

    else:
        logging.error(f"OTX API call failed for domain {domain} with status code {response.status_code}")
        return None





def get_redirect_proxy(url):
    """Fetch the proxy for a redirected URL from the database."""
    hostname = urlparse(url).netloc
    domain = get_domain(url)

    queries = [
        ("SELECT proxy FROM redirect_urls WHERE type = 'url_prefix' AND ? LIKE value || '%'", (url,)),
        ("SELECT proxy FROM redirect_urls WHERE type = 'hostname' AND value = ?", (hostname,)),
        ("SELECT proxy FROM redirect_urls WHERE type = 'domain' AND value = ?", (domain,)),
    ]

    for query, params in queries:
        result = query_database(query, params)
        if result:
            return result[0]

    return None  # No redirect match found

def is_tls_excluded(hostname):
    """Checks if a hostname should be excluded from TLS interception."""
    return query_database("SELECT hostname FROM tls_excluded_hosts WHERE hostname = ?", (hostname,)) is not None


def check_otx_for_file_hash(file_hash):
    """Check the file hash against OTX and extract relevant threat information."""
    headers = {'X-OTX-API-KEY': OTX_API_KEY}
    response = requests.get(f"https://otx.alienvault.com/api/v1/indicators/file/{file_hash}/analysis", headers=headers)

    if response.status_code != 200:
        logging.error(f"OTX API request failed for hash {file_hash} with status code {response.status_code}")
        return None

    try:
        data = response.json()

        # Ensure 'pulse_info' exists in the response
        pulse_info = data.get("pulse_info", {})
        if not pulse_info or pulse_info.get("count", 0) == 0:
            logging.info(f"Hash {file_hash} is not found in OTX (no pulses).")
            return None  # No threats found

        # Extract threat details
        return {
            "verdict": "Malicious",
            "pulses": pulse_info.get("pulses", [])
        }

    except json.JSONDecodeError:
        logging.error(f"OTX API returned invalid JSON for hash {file_hash}")
        return None



def check_file_hash_in_db(file_hash):
    """Check if a file hash is blocked in the local database or flagged in OTX."""
    # First, check in the local database
    result = query_database("SELECT value FROM blocked_files WHERE file_hash = ?", (file_hash,))
    if result:
        return {'status': 'blocked', 'message': 'Blocked file hash (database)'}

    # If not found locally, check with AlienVault OTX
    otx_result = check_otx_for_file_hash(file_hash)
    if otx_result:
        return {'status': 'blocked', 'message': 'Malicious file hash detected in OTX', 'details': otx_result}

    return None  # Not blocked

@app.route('/checkHash', methods=['POST'])
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

def check_mime_type_in_db(mime_type):
    result = query_database("SELECT value FROM blocked_mimetypes WHERE value = ?", (mime_type,))
    if result:
        return {'status': 'blocked', 'message': 'Blocked MIME type'}
    return None

@app.route('/checkMimeType', methods=['POST'])
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
def get_logs():
    """Fetch all log entries from the log database."""
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
    }

    # Validate the requested table name
    if table_name not in table_columns:
        return jsonify({'status': 'error', 'message': f'Invalid table name: {table_name}'}), 400

    # Fetch the data from the specified table
    columns = table_columns[table_name]
    response, status_code = fetch_data_from_table(table_name, columns)
    return jsonify(response), status_code


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
# TODO add a ignore for the get all logs (or at least do not put the response data in ...)
    # Log the request and response data
    log_db.log(
        level='INFO',
        request=request_data,
        response=response_data if request.method != "GET" else "N/A",  # Empty response for GET        client_ip=str(request.remote_addr),
        user_agent=str(request.headers.get('User-Agent')),
        method=request.method,
        status_code=response.status_code,
        response_time=response_time,
        category=request.url  # Category can be dynamic based on the request URL
    )

    return response

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unexpected error: {str(e)}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
