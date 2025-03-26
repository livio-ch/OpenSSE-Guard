import pytest
import subprocess
import sys
import os
from unittest.mock import patch
# Add the root directory to sys.path to make 'app' accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # Import your Flask app
from undecorated import undecorated



@pytest.fixture(autouse=True)
def undecorate_all_views():
    """Undecorate all view functions in the app before running tests."""
    # Loop through all registered views in the Flask app
    for rule, view_func in app.view_functions.items():
        # Replace each view function with its undecorated version
        app.view_functions[rule] = undecorated(view_func)
    yield  # Allow the test to run
    # No need to revert back since each test will start with the undecorated version



# Use pytest's fixture to set up the test client
@pytest.fixture(scope="module", autouse=True)
def run_pre_tests():
    """Run init_db.py and generatedb.py before starting the tests."""
    # Run init_db.py to initialize the database
    init_db_result = subprocess.run([sys.executable, 'init_db.py'], check=True)
    if init_db_result.returncode != 0:
        raise RuntimeError("init_db.py failed")

    # Run generatedb.py to populate the database with values
    generatedb_result = subprocess.run([sys.executable, 'generatedb.py'], check=True)
    if generatedb_result.returncode != 0:
        raise RuntimeError("generatedb.py failed")


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client



    # Mocking the decorators for testing

def test_missing_url(client):
    """Test when no URL is provided in the request."""
    response = client.post("/checkUrl", json={})
    assert response.status_code == 400
    assert response.json["status"] == "error"


def test_allowed_url(client):
    """Test an allowed URL (should return 'allowed')."""
    response = client.post("/checkUrl", json={"url": "https://example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"


def test_blocked_hostname(client):
    """Test a blocked exact hostname."""
    response = client.post("/checkUrl", json={"url": "https://www.example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"


def test_blocked_domain(client):
    """Test a blocked domain that includes subdomains."""
    response = client.post("/checkUrl", json={"url": "https://blocked.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"


def test_redirected_hostname(client):
    """Test a URL that should be redirected based on hostname."""
    response = client.post("/checkUrl", json={"url": "https://httpbin.org"})
    assert response.status_code == 200
    assert response.json["status"] == "redirected"
    assert "proxy" in response.json


def test_tls_excluded_hostname(client):
    """Test a URL that should be excluded from TLS interception."""
    response = client.post("/checkUrl", json={"url": "https://www.google.com", "host": "www.google.com"})
    assert response.status_code == 200
    assert response.json["status"] == "exclude-tls"


def test_invalid_url_format(client):
    """Test an invalid URL format."""
    response = client.post("/checkUrl", json={"url": "not_a_valid_url"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"  # If not explicitly blocked


def test_blocked_hostname_direct(client):
    """Test a blocked exact hostname (by `host` only)."""
    response = client.post("/checkUrl", json={"host": "www.example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"


def test_redirected_url(client):
    """Test a URL that should be redirected to a proxy based on the hostname."""
    response = client.post("/checkUrl", json={"url": "https://whatismyip.com"})
    assert response.status_code == 200
    assert response.json["status"] == "redirected"
    assert response.json["proxy"] == "http://localhost:8081"


def test_allowed_url_prefix(client):
    """Test a URL with an allowed prefix."""
    response = client.post("/checkUrl", json={"url": "https://allowed-url.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"

def test_blocked_url_prefix(client):
    """Test a URL with a blocked prefix."""
    response = client.post("/checkUrl", json={"url": "https://www.dhl.de/de/privatkunden/asdf"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"

def test_blocked_hostname_exact(client):
    """Test a blocked exact hostname."""
    response = client.post("/checkUrl", json={"host": "www.blockedsite.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"

def test_allowed_hostname_exact(client):
    """Test an allowed exact hostname."""
    response = client.post("/checkUrl", json={"host": "www.allowedsite.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"


def test_blocked_subdomain(client):
    """Test a blocked subdomain."""
    response = client.post("/checkUrl", json={"host": "sub.blockedsite.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"


def test_allowed_subdomain(client):
    """Test an allowed subdomain."""
    response = client.post("/checkUrl", json={"host": "sub.allowedsite.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"


def test_tls_exclusion_for_host(client):
    """Test a hostname excluded from TLS interception."""
    response = client.post("/checkUrl", json={"host": "www.google.com"})
    assert response.status_code == 200
    assert response.json["status"] == "exclude-tls"


def test_redirected_hostname(client):
    """Test a redirected hostname (based on `host`)."""
    response = client.post("/checkUrl", json={"host": "httpbin.org"})
    assert response.status_code == 200
    assert response.json["status"] == "redirected"
    assert "proxy" in response.json


def test_unmatched_hostname(client):
    """Test a hostname that doesn't match any entry."""
    response = client.post("/checkUrl", json={"host": "www.nonexistent.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"


def test_invalid_hostname_format(client):
    """Test an invalid hostname format."""
    response = client.post("/checkUrl", json={"host": "invalid-hostname"})
    assert response.status_code == 400
    assert response.json["status"] == "error"


def test_hostname_with_port(client):
    """Test a hostname with a port number."""
    response = client.post("/checkUrl", json={"host": "www.example.com:8080"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"


def test_multiple_hostnames(client):
    """Test multiple hostnames in the same request (should return error)."""
    # Send a request with a list of hostnames
    response = client.post("/checkUrl", json={"host": ["www.example.com", "www.blockedsite.com"]})

    # Assert that the response status code is 400 (Bad Request)
    assert response.status_code == 400

    # Assert that the response contains the correct error message
    assert response.json == {
        'status': 'error',
        'message': 'Multiple hostnames not allowed'
    }

def test_wildcard_hostname(client):
    """Test a wildcard hostname."""
    response = client.post("/checkUrl", json={"host": "sub.example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"  # Assuming *.example.com is allowed


def test_blocked_file_hash(client):
    """Test a file hash that is blocked in the database."""
    blocked_file_hash = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
    response = client.post("/checkHash", json={"file_hash": blocked_file_hash, "url": "https://example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"
    assert response.json["message"] == "Blocked file hash (database)"

def test_allowed_file_hash(client):
    """Test a file hash that is allowed (not blocked)."""
    allowed_file_hash = "allowedfilehash1234567890"
    response = client.post("/checkHash", json={"file_hash": allowed_file_hash, "url": "https://example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"
    assert response.json["message"] == "File and URL are allowed"



def test_blocked_mime_type(client):
    """Test a MIME type that is blocked."""
    blocked_mime_type = "application/x-dosexec"
    response = client.post("/checkMimeType", json={"mime_type": blocked_mime_type, "url": "https://example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"
    assert response.json["message"] == "Blocked MIME type"


def test_allowed_mime_type(client):
    """Test an allowed MIME type."""
    allowed_mime_type = "application/json"
    response = client.post("/checkMimeType", json={"mime_type": allowed_mime_type, "url": "https://example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"
    assert response.json["message"] == "MIME type allowed"
