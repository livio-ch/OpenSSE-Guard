import logging
import mitmproxy
from mitmproxy import http, tls, ctx
import requests
import magic
import hashlib
import time
from typing import Iterable, Union


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

def get_real_file_type(chunk):
    """Detects the actual file type using magic."""
    return magic.from_buffer(chunk)


accumulated_data = bytearray()  # Initialize the accumulated data
first_round = True  # Flag to track if it's the first round of data
counter = 0
BUFFER_SIZE = 8192  # Size of each chunk sent to the client (adjust as needed)
DELAY = 0  # Time delay between each chunk (adjust to slow down download speed)
HASH_SHA256 =  hashlib.sha256()
HASH_MD5 =  hashlib.md5()

def responseheaders(flow: mitmproxy.http.HTTPFlow):
    """Check if the response is streamable and set stream response handler."""
    if "content-disposition" in flow.response.headers or "application/octet-stream" in flow.response.headers.get("content-type", ""):
        ctx.log.info("Setting response bodmd5tream")
        global first_round, HASH_SHA256
        HASH_SHA256  =  hashlib.sha256()
        HASH_MD5  =  hashlib.md5()
        first_round = True

        flow.response.stream = stream_response  # Set the stream_response function to handle the response

def stream_response(flow: bytes) -> Iterable[bytes]:
    global accumulated_data, first_round, counter, full_data, HASH_SHA256  # Access global variables
    accumulated_data.extend(flow)  # Add the new flow data to the accumulated data
    HASH_SHA256.update(flow)
    HASH_MD5.update(flow)

    if flow == b'':
        print("Stream finished (empty chunk received).")
        print(HASH_SHA256.hexdigest())
        print(HASH_MD5.hexdigest())
#TODO send request against API

        time.sleep(10)
        yield accumulated_data
    else:
        # First round, determine the file type
        if first_round:
            rtype = get_real_file_type(flow)
            print(f"File type detected: {rtype}")
            first_round = False  # Set flag to false after first round
        chunk = accumulated_data[:BUFFER_SIZE]
        accumulated_data = accumulated_data[BUFFER_SIZE:]
        yield chunk
