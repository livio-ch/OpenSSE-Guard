from urllib.parse import urlparse
from .db_utils import query_database
from utils.url_utils import get_domain

def get_redirect_proxy(url):
    """
    Prüft, ob für die gegebene URL ein Redirect-Proxy in der Datenbank definiert ist.
    """
    hostname = urlparse(url).netloc
    domain = get_domain(url)

    queries = [
        ("SELECT proxy FROM redirect_urls WHERE type = 'url_prefix' AND ? LIKE value || '%'", (url,)),
        ("SELECT proxy FROM redirect_urls WHERE type = 'hostname' AND value = ?", (hostname,)),
        ("SELECT proxy FROM redirect_urls WHERE type = 'domain' AND value = ?", (domain,)),
    ]

    for query, params in queries:
        result = query_database(query, params)
        if result:
            return result[0]

    return None  # Kein Redirect gefunden

def is_tls_excluded(hostname):
    """
    Prüft, ob ein Hostname von TLS-Interception ausgeschlossen ist.
    """
    return query_database(
        "SELECT hostname FROM tls_excluded_hosts WHERE hostname = ?",
        (hostname,)
    ) is not None
