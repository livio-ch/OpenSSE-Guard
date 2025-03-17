import logging
import sqlite3
from flask import Flask, request, jsonify
import tldextract
import re
from urllib.parse import urlparse
import requests  # To make API calls to OTX
import json  # Ensure you import json at the top of your script
import os
from dotenv import load_dotenv  # Import dotenv

app = Flask(__name__)


# Load environment variables from the .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DB_PATH = "url_filter.db"  # Path to SQLite database

OTX_API_KEY = os.getenv('OTX_API_KEY')  # Retrieve the API key from the .env file
OTX_API_URL = 'https://otx.alienvault.com/api/v1/indicators/domain/{}/general'  # OTX API URL for domain check


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

def check_file_hash_in_db(file_hash):
    """Check if a file hash is blocked in the database."""
    result = query_database("SELECT value FROM blocked_files WHERE file_hash = ?", (file_hash,))
    if result:
        return {'status': 'blocked', 'message': 'Blocked file hash'}
    return None  # Not blocked

@app.route('/checkHash', methods=['POST'])
def check_file_and_url():
    """Check both file hash and URL for block status."""
    data = request.get_json()

    if "file_hash" not in data or "url" not in data:
        return jsonify({'status': 'error', 'message': 'Missing file_hash or url'}), 400

    file_status = check_file_hash_in_db(data['file_hash'])
    if file_status:
        return jsonify(file_status), 200

    url_status = get_block_status(data['url'])
    if url_status:
        return jsonify(url_status), 200

    return jsonify({'status': 'allowed', 'message': 'File and URL are allowed'}), 200

@app.route('/checkUrl', methods=['POST'])
def check_url():
    data = request.get_json()
    logging.info(f"Received data: {data}")

    if "host" in data:
        return process_host_check(data["host"])
    if "url" in data:
        return process_url_check(data["url"])

    return jsonify({'status': 'error', 'message': 'Missing URL or host'}), 400

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
        return jsonify({'status': 'error', 'message': 'Missing mime_type or url'}), 400

    mime_status = check_mime_type_in_db(data["mime_type"])
    if mime_status:
        return jsonify(mime_status), 200

    return jsonify({'status': 'allowed', 'message': 'MIME type allowed'}), 200

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unexpected error: {str(e)}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
