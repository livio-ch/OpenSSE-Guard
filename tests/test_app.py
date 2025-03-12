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
