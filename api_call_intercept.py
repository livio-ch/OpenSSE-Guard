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
API_URL_HASH = "http://127.0.0.1:5000/checkHash"
API_URL_MIME = "http://127.0.0.1:5000/checkMimeType"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_and_check_token(flow=None):
    """Check if the auth token is present and handle redirect if not."""
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





def send_request_to_api(payload,header=None):
    """Helper function to send a request to the Flask API and handle responses."""
    try:
        ctx.log.error(f"Flask API: {API_URL}")
        ctx.log.error(f"Flask head: {header}")
        ctx.log.error(f"Flask head: {payload}")


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

    except requests.exceptions.RequestException as e:
        ctx.log.error(f"Error contacting Flask API: {e}")
        return {"status": "error", "details": "Request failed"}

        

def tls_clienthello(flow):
    """Handles TLS interception logic by checking with Flask API."""
    host = flow.client_hello.sni
    if not host:
        ctx.log.info("No SNI found; proceeding with TLS interception.")
        return
            # Directly ignore connection for specific hosts without token check
    if host in ["dev-qq26bf68b4ogkwa7.us.auth0.com", "localhost:3000", "192.168.182.1:3000"]:
        ctx.log.info(f"Directly excluding TLS decryption for {host} as it is a known host.")
        return
    token = get_and_check_token(flow)  # Use the function to get and check the token
    if not token:
        # The client has been redirected already, no need to do anything further here
        return

    # Token found, proceed with API request
    headers = {"Authorization": f"Bearer {token}",
            "Content-Type": "application/json"}

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

    if host in ["dev-qq26bf68b4ogkwa7.us.auth0.com", "localhost", "192.168.182.1"]:
        ctx.log.info(f"Directly excluding request for {host} as it is a known host.")
        #flow.ignore_connection = True
        return

    token = get_and_check_token(flow)  # Use the function to get and check the token
    if not token:
        # The client has been redirected already, no need to do anything further here
        return

    # Token found, proceed with API request
    headers = {"Authorization": f"Bearer {token}",
        "Content-Type": "application/json"}




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

def get_real_file_type(chunk):
    """Detects the actual file type using magic."""
    magic_obj = magic.Magic(mime=True)
    return magic_obj.from_buffer(chunk)


accumulated_data = bytearray()  # Initialize the accumulated data
first_round = True  # Flag to track if it's the first round of data
counter = 0
BUFFER_SIZE = 8192  # Size of each chunk sent to the client (adjust as needed)
DELAY = 1  # DELAYED starting of chunking
HASH_SHA256 =  hashlib.sha256()
HASH_MD5 =  hashlib.md5()
FLOWURL = ""



#TODO where we had a bug lets check that later.

def old_responseheaders(flow: mitmproxy.http.HTTPFlow):
    """Check if the response is streamable and set stream response handler."""
#    if "content-disposition" in flow.response.headers or "application/octet-stream" in flow.response.headers.get("content-type", ""):
#        ctx.log.info("Setting response bodmd5tream")
    global first_round, HASH_SHA256, FLOWURL, DELAY
    DELAY = 1
    HASH_SHA256  =  hashlib.sha256()
    HASH_MD5  =  hashlib.md5()
    first_round = True
    FLOWURL =  flow.request.url
    # Remove Content-Length header if present
    if "content-length" in flow.response.headers:
        del flow.response.headers["content-length"]
        flow.response.headers["transfer-encoding"] = "chunked"
        print(f"Removed Content-Length header for {FLOWURL}")

    flow.response.stream = stream_response  # Set the stream_response function to handle the response

import json

def response(flow: http.HTTPFlow):
    """Intercepts and processes responses from the Auth0 OAuth token endpoint."""
    url = flow.request.pretty_url
    ctx.log.info(f"Intercepted response: {url}")

    # Check if the response is from the Auth0 OAuth token endpoint
    if "https://dev-qq26bf68b4ogkwa7.us.auth0.com/oauth/token" in url:
        # Here you can log the response or modify it if necessary
        ctx.log.info(f"Intercepted OAuth token response: {url}")

        # Log the response status and body
        ctx.log.info(f"Response status code: {flow.response.status_code}")
        ctx.log.info(f"Response body: {flow.response.text}")

        # If the response is successful (status code 200), proceed
        if flow.response.status_code == 200:
            # Try to extract the JSON response
            try:
                response_data = flow.response.json()  # Get JSON body

                # Extract the access_token
                if "access_token" in response_data:
                    access_token = response_data["access_token"]
                    ctx.log.info(f"Access Token intercepted: {access_token}")

                    # Write only the access_token to the /tmp/mitm_token.txt file
                    with open("mitm_token.txt", "w") as f:
                        f.write(access_token)

            except json.JSONDecodeError as e:
                ctx.log.error(f"Failed to decode JSON response: {e}")

        # Optionally, you can modify the response here if necessary
        # Example: flow.response.set_text(str(response_data)) if you want to modify the response body


def stream_response(flow: bytes) -> Iterable[bytes]:
    global accumulated_data, first_round, counter, full_data, HASH_SHA256, FLOWURL, DELAY  # Access global variables
    accumulated_data.extend(flow)  # Add the new flow data to the accumulated data
    HASH_SHA256.update(flow)
    HASH_MD5.update(flow)

    if flow == b'':
        print("Stream finished (empty chunk received).")
        print(HASH_SHA256.hexdigest())
        print(HASH_MD5.hexdigest())
        data = {
            "file_hash": HASH_SHA256.hexdigest(),
            "url": FLOWURL
        }
        response = requests.post(API_URL_HASH, json=data)
        response_data = response.json()
        if response_data.get("status") == "blocked":
            print("Blocked:", response_data["message"])
            accumulated_data = bytearray()
            yield b''
        else:
            print("Allowed:", response_data["message"])

        yield accumulated_data
    else:
        # First round, determine the file type
        if first_round:
            rtype = get_real_file_type(flow)
            #print(f"File type detected: {rtype}")
            data = {
                "mime_type": rtype,
                "url": FLOWURL
            }
            response = requests.post(API_URL_MIME, json=data)
            response_data = response.json()
            if response_data.get("status") == "blocked":
                print("Blocked:", response_data["message"])
                accumulated_data = bytearray()
                yield b''
            else:
                print("Allowed:", response_data["message"])
            first_round = False  # Set flag to false after first round
            DELAY = DELAY - 1
            return ""
        if DELAY > 0: #yield chunks later wait 1 more round.
            DELAY = DELAY -1
            return ""
        chunk = accumulated_data[:BUFFER_SIZE]
        accumulated_data = accumulated_data[BUFFER_SIZE:]
        yield chunk
