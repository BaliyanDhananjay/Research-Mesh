"""Fetch URL checks that do not require network access."""

import ipaddress
from urllib.parse import urlparse


def validate_fetch_url(url: str) -> None:
    """Reject URL forms that should never be fetched by the retrieval service."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are supported")
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in {"localhost", "metadata.google.internal"}:
        raise ValueError("Local and cloud metadata hosts are not allowed")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
        raise ValueError("Private, loopback, link-local, and reserved IPs are not allowed")
