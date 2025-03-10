from flask import Flask, request, jsonify
import tldextract
from urllib.parse import urlparse
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Define blocking lists
blocked_domains = {"blocked.com"}  # Blocks all subdomains
blocked_hostnames = {"www.example.com"}  # Exact hostnames only
blocked_url_prefixes = {"https://www.dhl.de/de/privatkunden/"}  # Blocks all sub-URLs under this prefix

# Define redirect lists
redirect_domains = {"whatismyip.com"}  # Now applies to all subdomains
redirect_hostnames = {"httpbin.org"}  # Exact hostnames for redirect
redirect_url_prefixes = {"https://www.redirectme.com"}  # URL prefixes for redirect
proxy_host = "http://localhost:8081"  # The proxy server to use in case of a redirect

def get_domain(url):
    """Extracts the main domain from a URL (ignores subdomains)."""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def normalize_url(url):
    """Normalizes URL to remove query parameters and fragments."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

@app.route('/checkUrl', methods=['POST'])
def check_url():
    # Print the full JSON payload received
    data = request.get_json()
    logging.info(f"Received data: {data}")

    # Get the URL from the posted data
    url = data.get('url')

    if not url:
        return jsonify({'status': 'error', 'message': 'Missing URL'}), 200

    url = normalize_url(url)
    domain = get_domain(url)
    hostname = urlparse(url).netloc  # More robust way to extract hostname

    logging.info(f"Checking URL: {url} (Domain: {domain}, Hostname: {hostname})")

    # 1️⃣ Blocked URL prefix check
    if any(url.startswith(prefix) for prefix in blocked_url_prefixes):
        logging.info(f"Blocked URL: {url} (matched prefix)")
        return jsonify({'status': 'blocked', 'message': 'Blocked by URL prefix'}), 200

    # 2️⃣ Blocked exact hostname
    if hostname in blocked_hostnames:
        logging.info(f"Blocked URL: {url} (matched hostname)")
        return jsonify({'status': 'blocked', 'message': 'Blocked by exact hostname'}), 200

    # 3️⃣ Blocked domain (includes subdomains)
    if domain in blocked_domains:
        logging.info(f"Blocked URL: {url} (matched domain)")
        return jsonify({'status': 'blocked', 'message': 'Blocked by domain (includes subdomains)'}), 200

    # 4️⃣ Redirected URL prefix
    if any(url.startswith(prefix) for prefix in redirect_url_prefixes):
        logging.info(f"Redirecting URL: {url} (matched prefix)")
        return jsonify({'status': 'redirected', 'message': 'Redirected by URL prefix', 'proxy': proxy_host}), 200

    # 5️⃣ Redirected exact hostname
    if hostname in redirect_hostnames:
        logging.info(f"Redirecting URL: {url} (matched hostname)")
        return jsonify({'status': 'redirected', 'message': 'Redirected by exact hostname', 'proxy': proxy_host}), 200

    # 6️⃣ Redirected domain (includes subdomains)
    if domain in redirect_domains:
        logging.info(f"Redirecting URL: {url} (matched domain)")
        return jsonify({'status': 'redirected', 'message': 'Redirected by domain (includes subdomains)', 'proxy': proxy_host}), 200

    logging.info(f"Allowed URL: {url}")
    return jsonify({'status': 'allowed', 'message': 'Access granted'}), 200

# Handle unexpected errors
@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unexpected error: {str(e)}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
