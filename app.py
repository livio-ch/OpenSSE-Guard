import logging
from flask import Flask, request, jsonify
import tldextract
from urllib.parse import urlparse

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Hosts for which TLS interception should be excluded.
tls_excluded_hostnames = {"www.google.com"}  # Example: exclude www.google.com

# Define blocking lists
blocked_domains = {"blocked.com"}  # Blocks all subdomains
blocked_hostnames = {"www.example.com"}  # Exact hostnames only
blocked_url_prefixes = {"https://www.dhl.de/de/privatkunden/"}  # Blocks all sub-URLs under this prefix

# Define redirect lists
redirect_domains = {"whatismyip.com"}  # Applies to all subdomains
redirect_hostnames = {"httpbin.org"}  # Exact hostnames for redirect
redirect_url_prefixes = {"https://www.redirectme.com"}  # URL prefixes for redirect
proxy_host = "http://localhost:8081"  # Proxy server to use for redirects

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
    data = request.get_json()
    logging.info(f"Received data: {data}")

    # 1. If payload contains 'host', treat it as a TLS handshake check.
    if "host" in data:
        sni_hostname = data.get("host")
        if sni_hostname in tls_excluded_hostnames:
            logging.info(f"TLS excluded hostname: {sni_hostname} (matched hostname)")
            return jsonify({'status': 'exclude-tls', 'message': 'TLS excluded hostname'}), 200
        else:
            logging.info(f"TLS allowed for hostname: {sni_hostname}")
            return jsonify({'status': 'allowed', 'message': 'TLS allowed'}), 200

    # 2. Otherwise, process the payload as a full URL check.
    url = data.get('url')
    if not url:
        return jsonify({'status': 'error', 'message': 'Missing URL or host'}), 200

    url = normalize_url(url)
    domain = get_domain(url)
    hostname = urlparse(url).netloc  # Extract the hostname robustly

    logging.info(f"Checking URL: {url} (Domain: {domain}, Hostname: {hostname})")

    # Check if URL starts with a blocked prefix.
    if any(url.startswith(prefix) for prefix in blocked_url_prefixes):
        logging.info(f"Blocked URL: {url} (matched prefix)")
        return jsonify({'status': 'blocked', 'message': 'Blocked by URL prefix'}), 200

    # Check for blocked exact hostname.
    if hostname in blocked_hostnames:
        logging.info(f"Blocked URL: {url} (matched hostname)")
        return jsonify({'status': 'blocked', 'message': 'Blocked by exact hostname'}), 200

    # Check if domain (including subdomains) is blocked.
    if domain in blocked_domains:
        logging.info(f"Blocked URL: {url} (matched domain)")
        return jsonify({'status': 'blocked', 'message': 'Blocked by domain (includes subdomains)'}), 200

    # Check for redirected URL prefix.
    if any(url.startswith(prefix) for prefix in redirect_url_prefixes):
        logging.info(f"Redirecting URL: {url} (matched prefix)")
        return jsonify({'status': 'redirected', 'message': 'Redirected by URL prefix', 'proxy': proxy_host}), 200

    # Check for redirected exact hostname.
    if hostname in redirect_hostnames:
        logging.info(f"Redirecting URL: {url} (matched hostname)")
        return jsonify({'status': 'redirected', 'message': 'Redirected by exact hostname', 'proxy': proxy_host}), 200

    # Check if domain (including subdomains) should be redirected.
    if domain in redirect_domains:
        logging.info(f"Redirecting URL: {url} (matched domain)")
        return jsonify({'status': 'redirected', 'message': 'Redirected by domain (includes subdomains)', 'proxy': proxy_host}), 200

    logging.info(f"Allowed URL: {url}")
    return jsonify({'status': 'allowed', 'message': 'Access granted'}), 200

@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f"Unexpected error: {str(e)}")
    return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
