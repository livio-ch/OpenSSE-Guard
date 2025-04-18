import logging
import mitmproxy
from mitmproxy import http, tls, ctx
import requests
import magic
import hashlib
import time
from typing import Iterable, Union
import json

# Replace with your Flask API endpoint
API_URL = "http://127.0.0.1:5000/checkUrl"
API_URL_HASH = "http://127.0.0.1:5000/checkHash"
API_URL_MIME = "http://127.0.0.1:5000/checkMimeType"


EXCLUDED_HOSTS_TLS = {"dev-qq26bf68b4ogkwa7.us.auth0.com", "cdn.auth0.com", "localhost:3000", "192.168.182.1:3000"}
EXCLUDED_HOSTS_REQUEST = {"dev-qq26bf68b4ogkwa7.us.auth0.com", "cdn.auth0.com", "localhost", "192.168.182.1"}
EXCLUDED_STREAM_URLS = {"https://dev-qq26bf68b4ogkwa7.us.auth0.com/oauth/token"}


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")




_cached_token = None
_token_timestamp = 0
TOKEN_TTL = 300  # seconds

def get_and_check_token(flow=None):
    """Check if the auth token is present and handle redirect if not."""
    global _cached_token, _token_timestamp
    now = time.time()
    if _cached_token and (now - _token_timestamp < TOKEN_TTL):
        return _cached_token
    try:
        # Try to read token from a file or other source
        with open("mitm_token.txt", "r") as f:
            token = f.read().strip()
            if token:
                return token  # Token found, return it
            else:
                ctx.log.info("No token found. Redirecting to localhost:3000.")
    except FileNotFoundError:
        ctx.log.info("Token file not found. Redirecting to localhost:3000.")

    # No token found, redirect the client to the login page (localhost:3000)
    if flow:  # If this is a request flow, we can redirect
        flow.response = http.Response.make(
            302,  # HTTP status for redirect
            b"",  # Empty body for redirect
            {"Location": "http://localhost:3000"}  # Redirect location
        )
    return None  # Return None if no token


def get_auth_headers(flow):
    token = get_and_check_token(flow)
    if not token:
        return None
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def send_request_to_api(payload,header=None):
    """Helper function to send a request to the Flask API and handle responses."""
    try:
        ctx.log.debug(f"Flask API: {API_URL}")
        ctx.log.debug(f"Flask head: {header}")
        ctx.log.debug(f"Flask head: {payload}")

        response = requests.post(API_URL, json=payload, headers=header, timeout=5)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        status_code = str(e.response.status_code)
        ctx.log.error(f"Error contacting Flask API: {e}")
        if status_code.startswith("401"):
            ctx.log.error("Unauthorized access - maybe token expired?")

            # If token expired, delete token file (optional)
            try:
                import os
                os.remove("mitm_token.txt")
            except Exception as remove_err:
                ctx.log.error(f"Failed to delete token file: {remove_err}")

            # If we have a flow context, redirect the user
            if flow:
                ctx.log.info("Redirecting user to re-auth at http://localhost:3000")
                flow.response = http.Response.make(
                    302,
                    b"",
                    {"Location": "http://localhost:3000"}
                )

        return {"status": "error", "details": f"HTTP error {status_code}"}





def tls_clienthello(flow):
    """Handles TLS interception logic by checking with Flask API."""
    host = flow.client_hello.sni
    if not host:
        ctx.log.info("No SNI found; proceeding with TLS interception.")
        return
            # Directly ignore connection for specific hosts without token check
    if host in EXCLUDED_HOSTS_TLS:
        ctx.log.info(f"Directly excluding TLS decryption for {host} as it is a known host.")
        return
    token = get_and_check_token(flow)  # Use the function to get and check the token
    if not token:
        # The client has been redirected already, no need to do anything further here
        return

    # Token found, proceed with API request
    headers = get_auth_headers(flow)

    data = send_request_to_api({"host": host},headers)
    if data.get("status") == "exclude-tls":
        ctx.log.info(f"Excluding TLS decryption for {host} as per API response.")
        flow.ignore_connection = True

def request(flow: http.HTTPFlow):
    """Intercepts and processes requests based on API response."""
    url = flow.request.pretty_url
    ctx.log.info(f"Intercepted request: {url}")

    # Extract host from URL
    host = flow.request.host

    # Directly ignore connection for specific hosts without token check

    if host in EXCLUDED_HOSTS_REQUEST:
        ctx.log.info(f"Directly excluding request for {host} as it is a known host.")
        #flow.ignore_connection = True
        return

    token = get_and_check_token(flow)  # Use the function to get and check the token
    if not token:
        # The client has been redirected already, no need to do anything further here
        return

    # Token found, proceed with API request

    headers = get_auth_headers(flow)




    data = send_request_to_api({"url": url},headers)
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

MAGIC_MIME = magic.Magic(mime=True)
def get_real_file_type(chunk):
    """Detects the actual file type using magic."""
    return MAGIC_MIME.from_buffer(chunk)


accumulated_data = bytearray()  # Initialize the accumulated data
first_round = True  # Flag to track if it's the first round of data
counter = 0
BUFFER_SIZE = 8192  # Size of each chunk sent to the client (adjust as needed)
DELAY = 1  # DELAYED starting of chunking
HASH_SHA256 =  hashlib.sha256()
HASH_MD5 =  hashlib.md5()
FLOWURL = ""



#TODO where we had a bug lets check that later.

def responseheaders(flow: mitmproxy.http.HTTPFlow):
    """Check if the response is streamable and set stream response handler."""
#    if "content-disposition" in flow.response.headers or "application/octet-stream" in flow.response.headers.get("content-type", ""):
##        ctx.log.info("Setting response bodmd5tream")

    if any(excluded_url in flow.request.url for excluded_url in EXCLUDED_STREAM_URLS):
        # If the URL is excluded, do not set the streaming handler
        ctx.log.info(f"Skipping stream for URL: {flow.request.url}")
        return  # Skip setting the stream handler


    flow.metadata["DELAY"] = 1
    flow.metadata["HASH_SHA256"] = hashlib.sha256()
    flow.metadata["HASH_MD5"] = hashlib.md5()
    flow.metadata["first_round"] = True
    flow.metadata["FLOWURL"] = flow.request.url
    flow.metadata["accumulated_data"] = bytearray()
    # Remove Content-Length header if present
    if flow.response.http_version == "HTTP/1.1":
        if "content-length" in flow.response.headers:
            del flow.response.headers["content-length"]
        flow.response.headers["transfer-encoding"] = "chunked"



    def modify_with_flow(data: bytes) -> Iterable[bytes]:
        return modify(flow, data)
    flow.response.stream = modify_with_flow  # Set the stream_response function to handle the response


def response(flow: http.HTTPFlow):
    """Intercepts and processes responses from the Auth0 OAuth token endpoint."""
    url = flow.request.pretty_url
    ctx.log.info(f"Intercepted response: {url}")

    # Check if the response is from the Auth0 OAuth token endpoint
    # Check if the response is from the Auth0 OAuth token endpoint
    if "https://dev-qq26bf68b4ogkwa7.us.auth0.com/oauth/token" in url:
        ctx.log.info(f"Intercepted OAuth token response: {url}")
        ctx.log.info(f"Response status code: {flow.response.status_code}")
        ctx.log.info(f"Response content: {flow.response.content}")

        # Try to directly access the content if it's available
        if flow.response.content:
            try:
                response_data = json.loads(flow.response.content.decode('utf-8'))
                if "access_token" in response_data:
                    access_token = response_data["access_token"]
                    ctx.log.info(f"Access Token intercepted: {access_token}")
                    with open("mitm_token.txt", "w") as f:
                        f.write(access_token)
            except json.JSONDecodeError as e:
                ctx.log.error(f"Failed to decode JSON response: {e}")
        # Optionally, you can modify the response here if necessary
        # Example: flow.response.set_text(str(response_data)) if you want to modify the response body


def modify(flow: http.HTTPFlow, data: bytes) -> Iterable[bytes]:
#    flow = ctx.flow  # Get the current flow object

    # Accessing flow metadata to track state
    accumulated_data = flow.metadata["accumulated_data"]
    HASH_SHA256 = flow.metadata["HASH_SHA256"]
    HASH_MD5 = flow.metadata["HASH_MD5"]
    first_round = flow.metadata["first_round"]
    FLOWURL = flow.metadata["FLOWURL"]
    DELAY = flow.metadata["DELAY"]

    url = flow.request.pretty_url


    accumulated_data.extend(data)  # Add the new flow data to the accumulated data
    HASH_SHA256.update(data)
    HASH_MD5.update(data)
    print(f"First 10 bytes: {data[:10]}")
    if data == b'':
        print("Stream finished (empty chunk received).")
        print(HASH_SHA256.hexdigest())
        print(HASH_MD5.hexdigest())
        datajson = {
            "file_hash": HASH_SHA256.hexdigest(),
            "url": FLOWURL
        }
        token = get_and_check_token(flow)
        headers = get_auth_headers(flow)

        try:
            response = requests.post(API_URL_HASH, json=datajson, headers=headers)
            response_data = response.json()
        except requests.RequestException as e:
            ctx.log.error(f"Error in hash API call: {e}")
            yield accumulated_data  # fallback to letting it through
            return
        if response_data.get("status") == "blocked":
            print("Blocked:", response_data["message"])
            accumulated_data = bytearray()
            yield b''
        else:
            print("Allowed:", response_data["message"])
            yield accumulated_data
        accumulated_data = bytearray()  # Reset accumulated data after yielding
    else:
        # First round, determine the file type
        if first_round:
            rtype = get_real_file_type(data)
            #print(f"File type detected: {rtype}")
            datajson = {
                "mime_type": rtype,
                "url": FLOWURL
            }
            token = get_and_check_token(flow)
            headers = get_auth_headers(flow)

            response = requests.post(API_URL_MIME, json=datajson, headers=headers)
            response_data = response.json()
            if response_data.get("status") == "blocked":
                print("Blocked:", response_data["message"])
                accumulated_data = bytearray()
                yield b''
            else:
                print("Allowed:", response_data["message"])
            first_round = False  # Set flag to false after first round
            flow.metadata["first_round"] = False
            DELAY -= 1
            flow.metadata["DELAY"] = DELAY
            #yield b''
        elif DELAY > 0: #yield chunks later wait 1 more round.
            DELAY -= 1
            flow.metadata["DELAY"] = DELAY
            #yield b''
        else:
            chunk = accumulated_data[:BUFFER_SIZE]
            flow.metadata["accumulated_data"] = accumulated_data[BUFFER_SIZE:]
            yield chunk
