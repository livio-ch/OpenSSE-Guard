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


@app.route('/checkUrl', methods=['POST'])
def check_url():
    data = request.get_json()
    logging.info(f"Received data: {data}")

    if "host" in data:
        return process_host_check(data.get("host"))

    if "url" in data:
        return process_url_check(data.get("url"))

    return jsonify({'status': 'error', 'message': 'Missing URL or host'}), 400


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


@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unexpected error: {str(e)}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
