import requests
from mitmproxy import http
import logging

# Local Flask API URL
API_URL = "http://127.0.0.1:5000/checkUrl"

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def request(flow: http.HTTPFlow):
    url = flow.request.pretty_url
    logging.info(f"Intercepted request: {url}")

    try:
        # Send request to Flask API
        response = requests.get(API_URL, params={"url": url}, timeout=5)
        response_data = response.json()

        if response.status_code == 200:
            status = response_data.get("status", "")

            if status == "allowed":
                logging.info(f"Request allowed: {url}")
                return  # Let request proceed normally

            elif status == "blocked":
                logging.info(f"Request blocked: {url}")
                flow.response = http.Response.make(
                    400,  # HTTP status code
                    b"Request blocked",  # Response body
                    {"Content-Type": "text/plain"}  # Headers
                )
                return

            elif status == "redirected":
                proxy_url = response_data.get("proxy")
                if proxy_url:
                    logging.info(f"Redirecting request through proxy: {proxy_url}")

                    # Extract host and port from proxy URL
                    proxy_host, proxy_port = proxy_url.replace("http://", "").split(":")
                    proxy_port = int(proxy_port)

                    # Preserve original request destination
                    original_host = flow.request.host
                    original_port = flow.request.port
                    original_scheme = flow.request.scheme

                    # Set upstream proxy manually
                    flow.request.headers["Proxy-Authorization"] = "Basic fakeproxy"  # Optional auth
                    flow.request.scheme = "http"
                    flow.request.host = proxy_host
                    flow.request.port = proxy_port
                    flow.request.path = f"{original_scheme}://{original_host}{flow.request.path}"

                    logging.info(f"Request is now routed through proxy: {proxy_host}:{proxy_port}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error contacting API: {str(e)}")
        flow.response = http.Response.make(
            500,  # Internal Server Error
            b"Proxy error",
            {"Content-Type": "text/plain"}
        )
