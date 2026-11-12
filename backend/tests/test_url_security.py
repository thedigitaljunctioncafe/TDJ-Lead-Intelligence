import socket
import unittest

from app.connectors.url_security import validate_public_https_url


def public_resolver(host, port, type):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))
    ]


def private_resolver(host, port, type):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", port))
    ]


def mixed_resolver(host, port, type):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
    ]


class TestURLSecurity(unittest.TestCase):

    def test_allowlisted_public_https_url_passes(self):
        result = validate_public_https_url(
            "https://feeds.example.org/news",
            {"feeds.example.org"},
            resolver=public_resolver,
        )
        self.assertTrue(result["public_dns"])
        self.assertEqual(result["hostname"], "feeds.example.org")

    def test_non_allowlisted_host_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://other.example.org/feed",
                {"feeds.example.org"},
                resolver=public_resolver,
            )

    def test_http_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "http://feeds.example.org/feed",
                {"feeds.example.org"},
                resolver=public_resolver,
            )

    def test_url_credentials_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://user:pass@feeds.example.org/feed",
                {"feeds.example.org"},
                resolver=public_resolver,
            )

    def test_nonstandard_port_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://feeds.example.org:8443/feed",
                {"feeds.example.org"},
                resolver=public_resolver,
            )

    def test_localhost_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://localhost/feed",
                {"localhost"},
                resolver=public_resolver,
            )

    def test_private_ip_literal_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://192.168.1.10/feed",
                {"192.168.1.10"},
                resolver=public_resolver,
            )

    def test_private_dns_address_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://feeds.example.org/feed",
                {"feeds.example.org"},
                resolver=private_resolver,
            )

    def test_mixed_public_and_private_dns_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://feeds.example.org/feed",
                {"feeds.example.org"},
                resolver=mixed_resolver,
            )

    def test_dns_failure_rejected(self):
        def failed_resolver(host, port, type):
            raise socket.gaierror("DNS failure")

        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://feeds.example.org/feed",
                {"feeds.example.org"},
                resolver=failed_resolver,
            )

    def test_empty_dns_result_rejected(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://feeds.example.org/feed",
                {"feeds.example.org"},
                resolver=lambda host, port, type: [],
            )

    def test_subdomain_requires_its_own_allowlist_entry(self):
        with self.assertRaises(ValueError):
            validate_public_https_url(
                "https://sub.feeds.example.org/feed",
                {"feeds.example.org"},
                resolver=public_resolver,
            )


if __name__ == "__main__":
    unittest.main()
