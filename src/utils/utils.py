from typing import List
from urllib.parse import urlparse


def string_to_list(s) -> List[str]:
    """
    Parses a string that represents a list, e.g., "[item1, item2]".
    """
    s = s.strip("[]")
    return [item.strip() for item in s.split(",") if item.strip()]


def url_matches_domain(url: str, domain: str) -> bool:
    """
    Returns True if the URL's hostname matches the configured domain,
    including subdomains (e.g. 'www.facebook.com' matches 'facebook.com').

    Uses exact hostname matching instead of substring matching to avoid
    false positives such as 'notexample.com' matching 'example.com'.
    """
    hostname = (urlparse(url).hostname or "").lower()
    domain = domain.strip().lower()
    return bool(domain) and (hostname == domain or hostname.endswith("." + domain))