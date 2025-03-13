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
        return {"status": "error"}  # Ensure we always return a dictionary

def tls_clienthello(flow):
    """Handles TLS interception logic by checking with Flask API."""
    host = flow.client_hello.sni
    if not host:
        ctx.log.info("No SNI found; proceeding with TLS interception.")
        return

    data = send_request_to_api({"host": host})
    if data.get("status") == "exclude-tls":
        ctx.log.info(f"Excluding TLS decryption for {host} as per API response.")
        flow.ignore_connection = True

def request(flow: http.HTTPFlow):
    """Intercepts and processes requests based on API response."""
    url = flow.request.pretty_url
    ctx.log.info(f"Intercepted request: {url}")

    data = send_request_to_api({"url": url})
    status = data.get("status", "")

    if status == "allowed":
        ctx.log.info(f"Request allowed: {url}")
        return  # Let request proceed

    elif status == "blocked":
        ctx.log.info(f"Request blocked: {url}")
        send_blocked_response(flow)

    elif status == "redirected":
        handle_proxy_redirection(flow, data.get("proxy"))

    else:
        ctx.log.error(f"Unexpected API response for {url}: {data}")
        send_error_response(flow)

def handle_proxy_redirection(flow, proxy_url):
    """Handles request redirection through an alternative proxy."""
    if not proxy_url:
        ctx.log.error("Proxy URL missing for redirection.")
        send_error_response(flow)
        return

    try:
        proxy_host, proxy_port = proxy_url.replace("http://", "").split(":")
        proxy_port = int(proxy_port)
    except ValueError:
        ctx.log.error(f"Invalid proxy format: {proxy_url}")
        send_error_response(flow)
        return

    ctx.log.info(f"Redirecting request through proxy: {proxy_url}")

    original_host, original_scheme, original_path = flow.request.host, flow.request.scheme, flow.request.path
    flow.request.scheme, flow.request.host, flow.request.port = "http", proxy_host, proxy_port
    flow.request.path = f"{original_scheme}://{original_host}{original_path}"
    flow.request.headers["Host"] = original_host  # Maintain correct Host header

def send_blocked_response(flow):
    """Sets a blocked response for a request."""
    flow.response = http.Response.make(
        403, b"Request blocked by Flask API", {"Content-Type": "text/plain"}
    )

def send_error_response(flow):
    """Sets an error response for failed API communication or unexpected responses."""
    flow.response = http.Response.make(
        500, b"Proxy error", {"Content-Type": "text/plain"}
    )

def response(flow: http.HTTPFlow):
    """Logs intercepted responses."""
    ctx.log.info(f"Response from {flow.request.pretty_url}: {flow.response.status_code}")
    ctx.log.debug(f"Response body: {flow.response.content[:200]}")  # Log first 200 bytes for debugging
