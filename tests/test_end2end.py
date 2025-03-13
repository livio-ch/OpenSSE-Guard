import pytest
import subprocess
import time
import requests
import os
from requests.exceptions import RequestException

# Path to your app.py and api_call_intercept.py scripts
APP_PATH = os.path.join(os.getcwd(), "app.py")
MITMPROXY_SCRIPT_PATH = os.path.join(os.getcwd(), "api_call_intercept.py")

# Start services function to launch the Flask app and mitmproxy
@pytest.fixture(scope="module")
def start_services():
    # Start the Flask app in a subprocess
    flask_process = subprocess.Popen(["python", APP_PATH])

    # Start mitmproxy in the background with the script api_call_intercept.py on port 8080
    mitmproxy_process = subprocess.Popen(
        ["mitmdump", "-p", "8080", "-s", MITMPROXY_SCRIPT_PATH]
    )


    mitmproxy_process = subprocess.Popen(
        ["mitmdump", "-p", "8081"]
    )

    # Wait for the services to start (you might need to adjust the timing based on your system)
    time.sleep(5)  # Adjust if necessary to give time for Flask and mitmproxy to start

    yield  # The test will run after this point

    # Cleanup: terminate both processes after the tests are done
    flask_process.terminate()
    mitmproxy_process.terminate()
    flask_process.wait()
    mitmproxy_process.wait()

# Test cases to test the proxy routing and Flask API
test_cases = [
    ("https://www.google.com", 200),
#    ("http://whatismyip.com", 200),
    ("http://httpbin.org", 200),
#    ("https://www.redirectme.com", 200),
    ("http://blocked.com", 403),
    ("http://blockedsite.com", 403),
    ("http://www.example.com", 403),
    ("https://www.dhl.de/de/privatkunden/", 403)
]

@pytest.mark.parametrize("url, expected_status", test_cases)
def test_proxy_routing(start_services, url, expected_status):
    """Test that requests are routed through the proxy and return the expected status codes."""

    # Ensure the proxy is available before making requests (optional, to avoid race conditions)
    retries = 5
    for attempt in range(retries):
        try:
            # Check if the proxy server is reachable
            response = requests.get("http://localhost:8080", timeout=5)
            if response.status_code == 200:
                break
        except RequestException:
            if attempt == retries - 1:
                pytest.fail("Proxy server is not reachable after multiple attempts.")
            time.sleep(2)  # Wait before retrying

    # Making the actual request through the proxy, ignoring SSL certificate verification
    proxies = {
        'http': 'http://localhost:8080',
        'https': 'http://localhost:8080',
    }

    try:
        response = requests.get(url, proxies=proxies, verify=False, timeout=10)
        assert response.status_code == expected_status, f"Expected {expected_status} but got {response.status_code} for {url}"
    except RequestException as e:
        pytest.fail(f"Request failed for {url}: {e}")
