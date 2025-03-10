import logging
import mitmproxy
from mitmproxy import http, tls

# Replace with your Flask API endpoint
API_URL = "http://127.0.0.1:5000/checkUrl"

# Set up logging
logging.basicConfig(level=logging.INFO)

#def tls_clienthello(flow):



def request(flow: http.HTTPFlow):
    """
    This function intercepts requests, sends them to the Flask API for validation,
    and handles the response (allowed, blocked, or redirected).
    """
    url = flow.request.pretty_url
    logging.info(f"Intercepted request: {url}")  # Log intercepted URL
    try:
        # Send intercepted URL to Flask API
        response = requests.post(API_URL, json={"url": url}, timeout=5)
        logging.info(f"Sent request to Flask API: {API_URL} with URL: {url}")

        # Parse the response from the Flask API
        response_data = response.json()
        logging.info(f"Received response from Flask API: {response_data}")

        if response.status_code == 200:
            status = response_data.get("status", "")
            logging.info(f"API Response status: {status}")

            if status == "allowed":
                logging.info(f"Request allowed: {url}")
                return  # Let the request proceed normally

            elif status == "blocked":
                logging.info(f"Request blocked: {url}")
                # Block the request
                flow.response = http.Response.make(
                    403,  # HTTP status code for blocked
                    b"Request blocked by Flask API",  # Response body
                    {"Content-Type": "text/plain"}  # Headers
                )
                return

            elif status == "redirected":
                logging.info(f"Request redirected: {url}")
                proxy_url = response_data.get("proxy")
                if proxy_url:
                    logging.info(f"Redirecting request through proxy: {proxy_url}")
                    # Extract proxy details
                    proxy_host, proxy_port = proxy_url.replace("http://", "").split(":")
                    proxy_port = int(proxy_port)

                    # Preserve original request destination and set proxy
                    original_host = flow.request.host
                    original_port = flow.request.port
                    original_scheme = flow.request.scheme

                    # Set new proxy for request
                    flow.request.headers["Proxy-Authorization"] = "Basic fakeproxy"  # Optional auth
                    flow.request.scheme = "http"
                    flow.request.host = proxy_host
                    flow.request.port = proxy_port
                    flow.request.path = f"{original_scheme}://{original_host}{flow.request.path}"

                    logging.info(f"Request now routed through proxy: {proxy_host}:{proxy_port}")

        else:
            logging.error(f"Flask API responded with an unexpected status code: {response.status_code}")
            flow.response = http.Response.make(
                500,  # Internal Server Error
                b"Proxy error",
                {"Content-Type": "text/plain"}
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Error contacting Flask API: {str(e)}")
        flow.response = http.Response.make(
            500,  # Internal Server Error
            b"Error contacting Flask API",
            {"Content-Type": "text/plain"}
        )

def response(flow: http.HTTPFlow):
    """
    This function intercepts responses from the server and can be modified if needed.
    """
    # Example of logging responses if needed for debugging purposes.
    logging.info(f"Response from {flow.request.pretty_url}: {flow.response.status_code}")
    logging.debug(f"Response body: {flow.response.content[:200]}")  # Print the first 200 bytes of the response body
