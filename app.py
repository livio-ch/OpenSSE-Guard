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

# Check if URL is blocked
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

# Get Proxy for Redirected URL
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

# Check if Hostname is excluded from TLS interception
def is_tls_excluded(hostname):
    """Checks if a hostname should be excluded from TLS interception."""
    return query_database("SELECT hostname FROM tls_excluded_hosts WHERE hostname = ?", (hostname,)) is not None

# Check if file hash is blocked
def check_file_hash_in_db(file_hash):
    """Check if a file hash is blocked in the database."""
    result = query_database("SELECT value FROM blocked_files WHERE file_hash = ?", (file_hash,))
    if result:
        return {'status': 'blocked', 'message': 'Blocked file hash'}
    return None  # Not blocked

# New route to check both file hash and URL
@app.route('/checkHash', methods=['POST'])
def check_file_and_url():
    """Check both file hash and URL for block status."""
    data = request.get_json()

    if "file_hash" not in data or "url" not in data:
        return jsonify({'status': 'error', 'message': 'Missing file_hash or url'}), 400

    file_hash = data['file_hash']
    url = data['url']

    # Check file hash in the database
    file_status = check_file_hash_in_db(file_hash)
    if file_status:
        return jsonify(file_status), 200

    # Check URL in the database
    url_status = get_block_status(url)
    if url_status:
        return jsonify(url_status), 200

    # If neither the file nor the URL are blocked
    return jsonify({'status': 'allowed', 'message': 'File and URL are allowed'}), 200

# Existing endpoint for checking URL or Hostname
@app.route('/checkUrl', methods=['POST'])
def check_url():
    data = request.get_json()
    logging.info(f"Received data: {data}")

    if "host" in data:
        return process_host_check(data.get("host"))

    if "url" in data:
        return process_url_check(data.get("url"))

    return jsonify({'status': 'error', 'message': 'Missing URL or host'}), 400

# Handle Hostname Check
def process_host_check(hostname):
    """Handles TLS hostname checking logic."""
    if isinstance(hostname, list):
        logging.error("Multiple hostnames not allowed")
        return jsonify({'status': 'error', 'message': 'Multiple hostnames not allowed'}), 400

    if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(:\d+)?$', hostname):
        logging.error(f"Invalid hostname format: {hostname}")
        return jsonify({'status': 'error', 'message': 'Invalid hostname format'}), 400

    if block_status := get_block_status(f"https://{hostname}"):
        logging.info(f"Blocked hostname: {hostname}")
        return jsonify(block_status), 200

    if is_tls_excluded(hostname):
        logging.info(f"TLS excluded hostname: {hostname}")
        return jsonify({'status': 'exclude-tls', 'message': 'TLS excluded hostname'}), 200

    if proxy := get_redirect_proxy(f"https://{hostname}"):
        logging.info(f"Redirecting hostname: {hostname} to {proxy}")
        return jsonify({'status': 'redirected', 'message': 'Redirected by database rule', 'proxy': proxy}), 200

    logging.info(f"TLS allowed for hostname: {hostname}")
    return jsonify({'status': 'allowed', 'message': 'TLS allowed'}), 200

# Handle URL Check
def process_url_check(url):
    """Handles full URL checking logic."""
    if not url:
        return jsonify({'status': 'error', 'message': 'Missing URL'}), 400

    url = normalize_url(url)
    logging.info(f"Checking URL: {url}")

    if block_status := get_block_status(url):
        logging.info(f"Blocked: {block_status}")
        return jsonify(block_status), 200

    if proxy := get_redirect_proxy(url):
        logging.info(f"Redirecting URL: {url} to {proxy}")
        return jsonify({'status': 'redirected', 'message': 'Redirected by database rule', 'proxy': proxy}), 200

    logging.info(f"Allowed URL: {url}")
    return jsonify({'status': 'allowed', 'message': 'Access granted'}), 200

# Global error handler for unexpected exceptions
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unexpected error: {str(e)}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

# Main entry point
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
