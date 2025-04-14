import logging
from urllib.parse import urlparse
import tldextract

from category_check import check_category_action
from api_interfaces.otx_api import OTXAPI
from utils.url_utils import get_domain
from .db_utils import query_database  # Hilfsfunktion, siehe unten

# Instanz der OTX API
api_provider = OTXAPI()

def get_block_status(url):
    """
    Checks if a URL should be blocked based on local database rules, OTX verdicts, and category rules.
    """
    hostname = urlparse(url).netloc
    domain = get_domain(url)

    # Check against local DB blocklists
    checks = [
        ("SELECT value FROM blocked_urls WHERE type = 'url_prefix' AND ? LIKE value || '%'", (url,), 'Blocked by URL prefix'),
        ("SELECT value FROM blocked_urls WHERE type = 'hostname' AND value = ?", (hostname,), 'Blocked by exact hostname'),
        ("SELECT value FROM blocked_urls WHERE type = 'domain' AND value = ?", (domain,), 'Blocked by domain (includes subdomains)'),
    ]

    for query, params, message in checks:
        if query_database(query, params):
            return {'status': 'blocked', 'message': message}

    # Check OTX verdict
    ioc_status = api_provider.check_domain(hostname)
    logging.info(f"Domain {hostname} OTX status: {ioc_status}")
    if ioc_status and ioc_status.get('verdict') != 'Whitelisted':
        return {'status': 'blocked', 'message': 'Domain is an IOC (Indicator of Compromise)'}

    # Check via category
    category_status = check_category_action(hostname)
    if category_status:
        return category_status

    return None  # Allowed
