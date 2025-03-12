import logging
import sqlite3
from flask import Flask, request, jsonify
import tldextract
import re
from urllib.parse import urlparse


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

DB_PATH = "url_filter.db"  # Path to SQLite database

def get_domain(url):
    """Extracts the main domain from a URL (ignores subdomains)."""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def normalize_url(url):
    """Normalizes URL to remove query parameters and fragments."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def get_block_status(url):
    """Checks if a URL is blocked based on database rules."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    hostname = urlparse(url).netloc
    domain = get_domain(url)

    # Check blocked URL prefixes
    cursor.execute("SELECT value FROM blocked_urls WHERE type = 'url_prefix' AND ? LIKE value || '%'", (url,))
    if cursor.fetchone():
        conn.close()
        return {'status': 'blocked', 'message': 'Blocked by URL prefix'}

    # Check blocked hostnames
    cursor.execute("SELECT value FROM blocked_urls WHERE type = 'hostname' AND value = ?", (hostname,))
    if cursor.fetchone():
        conn.close()
        return {'status': 'blocked', 'message': 'Blocked by exact hostname'}

    # Check blocked domains
    cursor.execute("SELECT value FROM blocked_urls WHERE type = 'domain' AND value = ?", (domain,))
    if cursor.fetchone():
        conn.close()
        return {'status': 'blocked', 'message': 'Blocked by domain (includes subdomains)'}

    conn.close()
    return None  # Not blocked

def get_redirect_proxy(url):
    """Fetch the proxy for a redirected URL from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    hostname = urlparse(url).netloc
    domain = get_domain(url)

    # Check for redirected URL prefix
    cursor.execute("SELECT proxy FROM redirect_urls WHERE type = 'url_prefix' AND ? LIKE value || '%'", (url,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]

    # Check for redirected hostname
    cursor.execute("SELECT proxy FROM redirect_urls WHERE type = 'hostname' AND value = ?", (hostname,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]

    # Check for redirected domain
    cursor.execute("SELECT proxy FROM redirect_urls WHERE type = 'domain' AND value = ?", (domain,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return row[0]

    conn.close()
    return None  # No redirect match found

def is_tls_excluded(hostname):
    """Checks if a hostname should be excluded from TLS interception."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT hostname FROM tls_excluded_hosts WHERE hostname = ?", (hostname,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

@app.route('/checkUrl', methods=['POST'])
def check_url():
    data = request.get_json()
    logging.info(f"Received data: {data}")

    # Handle the request for a single hostname only
    if "host" in data:
        hosts = data.get("host")

        # If it's a list of hosts, return an error
        if isinstance(hosts, list):
            logging.error("Multiple hostnames not allowed")
            return jsonify({
                'status': 'error',
                'message': 'Multiple hostnames are not allowed in the request'
            }), 400

        # If it's a single hostname, proceed with validation
        sni_hostname = hosts
        # Validate hostname format
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(:\d+)?$', sni_hostname):
            logging.error(f"Invalid hostname format: {sni_hostname}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid hostname format'
            }), 400

        block_status = get_block_status(f"https://{sni_hostname}")

        if block_status:
            logging.info(f"Blocked hostname: {sni_hostname}")
            return jsonify(block_status), 200

        if is_tls_excluded(sni_hostname):
            logging.info(f"TLS excluded hostname: {sni_hostname}")
            return jsonify({'status': 'exclude-tls', 'message': 'TLS excluded hostname'}), 200

        proxy = get_redirect_proxy(f"https://{sni_hostname}")
        if proxy:
            logging.info(f"Redirected hostname: {sni_hostname} to {proxy}")
            return jsonify({
                'status': 'redirected',
                'message': 'Redirected by database rule',
                'proxy': proxy
            }), 200

        logging.info(f"TLS allowed for hostname: {sni_hostname}")
        return jsonify({'status': 'allowed', 'message': 'TLS allowed'}), 200

    # Process the full URL check
    url = data.get('url')
    if not url:
        return jsonify({'status': 'error', 'message': 'Missing URL or host'}), 400

    url = normalize_url(url)
    logging.info(f"Checking URL: {url}")

    # Check if the URL is blocked
    block_status = get_block_status(url)
    if block_status:
        logging.info(f"Blocked: {block_status}")
        return jsonify(block_status), 200

    # Check if the URL should be redirected
    proxy = get_redirect_proxy(url)
    if proxy:
        logging.info(f"Redirecting URL: {url} to {proxy}")
        return jsonify({
            'status': 'redirected',
            'message': 'Redirected by database rule',
            'proxy': proxy
        }), 200

    logging.info(f"Allowed URL: {url}")
    return jsonify({'status': 'allowed', 'message': 'Access granted'}), 200


@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unexpected error: {str(e)}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
