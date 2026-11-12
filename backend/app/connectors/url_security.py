"""SSRF-resistant URL validation for explicitly allowlisted public sources.

This module validates destinations before a future connector opens a network
connection. It does not perform HTTP requests or follow redirects.
"""

import ipaddress
import socket
from urllib.parse import urlsplit


def _normalise_host(host: str) -> str:
    if not isinstance(host, str) or not host.strip():
        raise ValueError("A valid hostname is required")

    host = host.strip().rstrip(".").lower()

    try:
        normalised = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("Invalid international hostname") from exc

    if not normalised or len(normalised) > 253:
        raise ValueError("Invalid hostname length")

    return normalised


def validate_public_https_url(
    url: str,
    allowed_hosts,
    resolver=None,
) -> dict:
    """Validate HTTPS URL, exact hostname allowlist and public DNS addresses.

    DNS validation alone does not prevent DNS rebinding. A future HTTP
    transport must connect to the validated IP directly and preserve the
    original hostname for TLS SNI, certificate validation and Host header.
    Redirects must be disabled or independently revalidated.
    """
    if not isinstance(url, str) or not url.strip():
        raise ValueError("URL must be a non-empty string")

    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Malformed URL") from exc

    if parsed.scheme.lower() != "https":
        raise ValueError("Only HTTPS URLs are permitted")

    if not parsed.hostname or not parsed.netloc:
        raise ValueError("URL hostname is required")

    if parsed.username is not None or parsed.password is not None:
        raise ValueError("URL credentials are not permitted")

    if parsed.fragment:
        raise ValueError("URL fragments are not permitted")

    if port not in (None, 443):
        raise ValueError("Only HTTPS port 443 is permitted")

    host = _normalise_host(parsed.hostname)

    if host == "localhost" or host.endswith(
        (".localhost", ".local", ".internal", ".test", ".invalid", ".example")
    ):
        raise ValueError("Local or reserved hostname is not permitted")

    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError("IP-literal URLs are not permitted")

    if not isinstance(allowed_hosts, (list, tuple, set, frozenset)):
        raise TypeError("allowed_hosts must be a collection of hostnames")

    normalised_allowlist = {
        _normalise_host(item) for item in allowed_hosts
    }

    if host not in normalised_allowlist:
        raise ValueError("Hostname is not in the approved source allowlist")

    resolve = resolver or socket.getaddrinfo

    try:
        answers = resolve(host, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError("Hostname DNS resolution failed") from exc

    addresses = set()

    for answer in answers:
        try:
            address = ipaddress.ip_address(answer[4][0].split("%")[0])
        except (ValueError, IndexError, TypeError):
            raise ValueError("DNS returned an invalid address")

        if not address.is_global:
            raise ValueError("Hostname resolves to a non-public IP address")

        addresses.add(str(address))

    if not addresses:
        raise ValueError("Hostname has no usable DNS addresses")

    return {
        "url": url.strip(),
        "hostname": host,
        "port": 443,
        "resolved_addresses": sorted(addresses),
        "allowlisted": True,
        "public_dns": True,
    }
