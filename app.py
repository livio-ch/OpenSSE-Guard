import logging
import sqlite3
from flask import Flask, request, jsonify
import tldextract
import re
from urllib.parse import urlparse

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DB_PATH = "url_filter.db"  # Path to SQLite database

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
    """Checks if a URL is blocked based on database rules."""
    hostname = urlparse(url).netloc
    domain = get_domain(url)

    checks = [
        ("SELECT value FROM blocked_urls WHERE type = 'url_prefix' AND ? LIKE value || '%'", (url,), 'Blocked by URL prefix'),
        ("SELECT value FROM blocked_urls WHERE type = 'hostname' AND value = ?", (hostname,), 'Blocked by exact hostname'),
        ("SELECT value FROM blocked_urls WHERE type = 'domain' AND value = ?", (domain,), 'Blocked by domain (includes subdomains)'),
    ]

    for query, params, message in checks:
        if query_database(query, params):
            return {'status': 'blocked', 'message': message}

    return None  # Not blocked

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
