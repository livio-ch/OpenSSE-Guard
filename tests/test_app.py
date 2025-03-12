import pytest
import requests
import sys
import os

# Add the root directory to sys.path to make 'app' accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # Import your Flask app

# Use pytest's fixture to set up the test client
@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_missing_url(client):
    """Test when no URL is provided in the request."""
    response = client.post("/checkUrl", json={})
    assert response.status_code == 400
    assert response.json["status"] == "error"

def test_blocked_url_prefix(client):
    """Test a URL that starts with a blocked prefix."""
    response = client.post("/checkUrl", json={"url": "https://www.dhl.de/de/privatkunden/somepage"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"
    assert response.json["message"] == "Blocked by URL prefix"

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


def test_allowed_url_with_query_params(client):
    """Test an allowed URL with query parameters."""
    response = client.post("/checkUrl", json={"url": "https://example.com/search?q=test"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"
    assert response.json["message"] == "Access granted"

def test_blocked_url_with_query_params(client):
    """Test a blocked URL with query parameters."""
    response = client.post("/checkUrl", json={"url": "https://www.dhl.de/de/privatkunden/?param=value"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"
    assert response.json["message"] == "Blocked by URL prefix"


def test_redirected_url_prefix(client):
    """Test a URL that should be redirected based on a prefix."""
    response = client.post("/checkUrl", json={"url": "https://www.redirectme.com/somepath"})
    assert response.status_code == 200
    assert response.json["status"] == "redirected"
    assert response.json["message"] == "Redirected by database rule"
    assert "proxy" in response.json

def test_redirected_domain(client):
    """Test a URL that should be redirected based on the domain."""
    response = client.post("/checkUrl", json={"url": "https://whatismyip.com"})
    assert response.status_code == 200
    assert response.json["status"] == "redirected"
    assert response.json["message"] == "Redirected by database rule"
    assert "proxy" in response.json

def test_blocked_subdomain(client):
    """Test a subdomain of a blocked domain."""
    response = client.post("/checkUrl", json={"url": "https://sub.blocked.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"
    assert response.json["message"] == "Blocked by domain (includes subdomains)"

def test_valid_url_format(client):
    """Test a valid URL that should be allowed."""
    response = client.post("/checkUrl", json={"url": "https://allowedurl.com"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"
    assert response.json["message"] == "Access granted"

def test_invalid_url_format(client):
    """Test an invalid URL format."""
    response = client.post("/checkUrl", json={"url": "not_a_valid_url"})
    assert response.status_code == 200
    assert response.json["status"] == "allowed"  # If not explicitly blocked
    assert response.json["message"] == "Access granted"  # Assuming non-blocked invalid URLs pass

def test_blocked_hostname_direct(client):
    """Test a blocked exact hostname."""
    response = client.post("/checkUrl", json={"host": "www.example.com"})
    assert response.status_code == 200
    assert response.json["status"] == "blocked"
    assert response.json["message"] == "Blocked by exact hostname"

def test_redirected_host_with_proxy(client):
    """Test a hostname that should be redirected to a proxy."""
    response = client.post("/checkUrl", json={"url": "https://httpbin.org"})
    assert response.status_code == 200
    assert response.json["status"] == "redirected"
    assert response.json["message"] == "Redirected by database rule"
    assert response.json["proxy"] == "http://proxy2.com:8080"  # Make sure proxy is correct
