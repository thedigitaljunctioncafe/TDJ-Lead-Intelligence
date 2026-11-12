"""Controlled HTTPS request API with DNS-pinned connections."""

import ipaddress
import socket
import ssl
from http.client import HTTPSConnection
from urllib.parse import urlsplit

from app.connectors.url_security import validate_public_https_url


class _PinnedHTTPSConnection(HTTPSConnection):
    """Internal connection that uses a previously validated public IP."""

    def __init__(self, hostname, pinned_ip, timeout=10):
        address = ipaddress.ip_address(pinned_ip)
        if not address.is_global:
            raise ValueError("Connection IP must be globally routable")

        self._pinned_ip = str(address)
        super().__init__(
            host=hostname,
            port=443,
            timeout=timeout,
            context=ssl.create_default_context(),
        )

    def connect(self):
        if self._tunnel_host:
            raise ValueError("HTTPS tunnelling is not permitted")

        raw_socket = socket.create_connection(
            (self._pinned_ip, self.port),
            self.timeout,
            self.source_address,
        )
        try:
            self.sock = self._context.wrap_socket(
                raw_socket,
                server_hostname=self.host,
            )
        except Exception:
            raw_socket.close()
            raise


def _validate_request_target(url):
    """Reject whitespace and control characters in an HTTP request URL."""
    if not isinstance(url, str) or not url:
        raise ValueError("URL must be a non-empty string")

    if any(ord(char) <= 0x20 or ord(char) == 0x7F for char in url):
        raise ValueError("URL contains whitespace or control characters")

    parsed = urlsplit(url)
    request_path = parsed.path or "/"

    if parsed.query:
        request_path += "?" + parsed.query

    if not request_path.startswith("/"):
        raise ValueError("Invalid HTTP request target")

    if any(ord(char) < 0x21 or ord(char) > 0x7E for char in request_path):
        raise ValueError("HTTP request target must contain printable ASCII only")

    return request_path


def _connect_with_ip_fallback(hostname, addresses, timeout):
    """Connect to the first working IP from an already validated address list."""
    last_error = None

    for pinned_ip in addresses:
        connection = _PinnedHTTPSConnection(
            hostname=hostname,
            pinned_ip=pinned_ip,
            timeout=timeout,
        )

        try:
            connection.connect()
            return connection, pinned_ip
        except OSError as exc:
            last_error = exc
            try:
                connection.close()
            except OSError:
                pass

    if last_error is not None:
        raise last_error

    raise OSError("No validated IP addresses were available")


def request_public_https(
    url,
    allowed_hosts,
    *,
    resolver=None,
    timeout=10,
    max_response_bytes=2_000_000,
):
    """Validate, pin and request one allowlisted public HTTPS URL.

    Redirects are never followed. The caller must explicitly validate any
    redirect destination as a new request.
    """
    if not isinstance(max_response_bytes, int) or not 1 <= max_response_bytes <= 10_000_000:
        raise ValueError("max_response_bytes must be between 1 and 10000000")

    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("timeout must be positive")

    request_path = _validate_request_target(url)

    validation = validate_public_https_url(
        url,
        allowed_hosts,
        resolver=resolver,
    )

    connection, connected_ip = _connect_with_ip_fallback(
        hostname=validation["hostname"],
        addresses=validation["resolved_addresses"],
        timeout=timeout,
    )

    try:
        connection.request(
            "GET",
            request_path,
            headers={
                "Host": validation["hostname"],
                "User-Agent": "TDJ-Lead-Intelligence/1.0",
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
                "Connection": "close",
            },
        )
        response = connection.getresponse()
        body = response.read(max_response_bytes + 1)

        if len(body) > max_response_bytes:
            raise ValueError("Response exceeds configured size limit")

        status = response.status
        return {
            "status": status,
            "headers": dict(response.getheaders()),
            "body": body,
            "redirected": status in (301, 302, 303, 307, 308),
            "final_url": url,
            "hostname": validation["hostname"],
            "connected_ip": connected_ip,
        }
    finally:
        connection.close()
