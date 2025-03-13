import logging
import mitmproxy
from mitmproxy import http, tls, ctx
import requests

# Replace with your Flask API endpoint
API_URL = "http://127.0.0.1:5000/checkUrl"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_request_to_api(payload):
    """Helper function to send a request to the Flask API and handle responses."""
    try:
        response = requests.post(API_URL, json=payload, timeout=5)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        ctx.log.error(f"Error contacting Flask API: {e}")
        return None

def tls_clienthello(flow):
    """Handles TLS interception logic by checking with Flask API."""
    host = flow.client_hello.sni
    if not host:
        ctx.log.info("No SNI found; proceeding with TLS interception.")
        return

    data = send_request_to_api({"host": host})
    if data and data.get("status") == "exclude-tls":
        ctx.log.info(f"Excluding TLS decryption for {host} as per API response.")
        flow.ignore_connection = True

def request(flow: http.HTTPFlow):
    """Intercepts and processes requests based on API response."""
    url = flow.request.pretty_url
    logging.info(f"Intercepted request: {url}")

    data = send_request_to_api({"url": url})
    if not data:
        flow.response = http.Response.make(500, b"Proxy error", {"Content-Type": "text/plain"})
        return

    status = data.get("status", "")
    logging.info(f"API Response status: {status}")

    if status == "allowed":
        return  # Allow request

    elif status == "blocked":
        logging.info(f"Request blocked: {url}")
        flow.response = http.Response.make(403, b"Request blocked by Flask API", {"Content-Type": "text/plain"})

    elif status == "redirected":
        handle_proxy_redirection(flow, data.get("proxy"))

def handle_proxy_redirection(flow, proxy_url):
    """Handles request redirection through an alternative proxy."""
    if not proxy_url:
        logging.error("Proxy URL missing for redirection.")
        flow.response = http.Response.make(500, b"Proxy error", {"Content-Type": "text/plain"})
        return

    logging.info(f"Redirecting request through proxy: {proxy_url}")
    proxy_host, proxy_port = proxy_url.replace("http://", "").split(":")
    proxy_port = int(proxy_port)

    original_host, original_scheme, original_path = flow.request.host, flow.request.scheme, flow.request.path
    flow.request.scheme, flow.request.host, flow.request.port = "http", proxy_host, proxy_port
    flow.request.path = f"{original_scheme}://{original_host}{original_path}"
    flow.request.headers["Host"] = original_host  # Maintain correct Host header

def response(flow: http.HTTPFlow):
    """Logs intercepted responses."""
    logging.info(f"Response from {flow.request.pretty_url}: {flow.response.status_code}")
    logging.debug(f"Response body: {flow.response.content[:200]}")  # Log first 200 bytes for debugging
