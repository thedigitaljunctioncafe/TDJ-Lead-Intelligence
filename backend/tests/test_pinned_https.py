import socket
import unittest
from unittest.mock import Mock, patch

from app.connectors.pinned_https import request_public_https


URL = "https://feeds.example.org/rss"


def public_resolver(host, port, type):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))
    ]


class TestControlledPinnedHTTPS(unittest.TestCase):

    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_successful_request(self, connection_class):
        connection = Mock()
        response = Mock()
        response.status = 200
        response.getheaders.return_value = [("Content-Type", "application/rss+xml")]
        response.read.return_value = b"<rss>test</rss>"
        connection.getresponse.return_value = response
        connection_class.return_value = connection

        result = request_public_https(
            URL,
            {"feeds.example.org"},
            resolver=public_resolver,
        )

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["body"], b"<rss>test</rss>")
        self.assertEqual(result["connected_ip"], "93.184.216.34")
        self.assertFalse(result["redirected"])
        connection_class.assert_called_once_with(
            hostname="feeds.example.org",
            pinned_ip="93.184.216.34",
            timeout=10,
        )
        connection.close.assert_called_once()

    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_redirect_is_reported_not_followed(self, connection_class):
        connection = Mock()
        response = Mock()
        response.status = 302
        response.getheaders.return_value = [
            ("Location", "https://other.example.org/")
        ]
        response.read.return_value = b""
        connection.getresponse.return_value = response
        connection_class.return_value = connection

        result = request_public_https(
            URL,
            {"feeds.example.org"},
            resolver=public_resolver,
        )

        self.assertTrue(result["redirected"])
        self.assertEqual(result["status"], 302)
        connection.request.assert_called_once()
        connection.close.assert_called_once()

    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_oversized_response_rejected(self, connection_class):
        connection = Mock()
        response = Mock()
        response.status = 200
        response.getheaders.return_value = []
        response.read.return_value = b"x" * 11
        connection.getresponse.return_value = response
        connection_class.return_value = connection

        with self.assertRaises(ValueError):
            request_public_https(
                URL,
                {"feeds.example.org"},
                resolver=public_resolver,
                max_response_bytes=10,
            )

        connection.close.assert_called_once()

    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_network_error_closes_connection(self, connection_class):
        connection = Mock()
        connection.request.side_effect = OSError("simulated network error")
        connection_class.return_value = connection

        with self.assertRaises(OSError):
            request_public_https(
                URL,
                {"feeds.example.org"},
                resolver=public_resolver,
            )

        connection.close.assert_called_once()

    def test_non_allowlisted_host_rejected_before_connection(self):
        with patch("app.connectors.pinned_https._PinnedHTTPSConnection") as factory:
            with self.assertRaises(ValueError):
                request_public_https(
                    URL,
                    {"other.example.org"},
                    resolver=public_resolver,
                )
            factory.assert_not_called()

    def test_private_dns_rejected_before_connection(self):
        def private_resolver(host, port, type):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", port))
            ]

        with patch("app.connectors.pinned_https._PinnedHTTPSConnection") as factory:
            with self.assertRaises(ValueError):
                request_public_https(
                    URL,
                    {"feeds.example.org"},
                    resolver=private_resolver,
                )
            factory.assert_not_called()

    def test_invalid_response_limit_rejected(self):
        with self.assertRaises(ValueError):
            request_public_https(
                URL,
                {"feeds.example.org"},
                resolver=public_resolver,
                max_response_bytes=0,
            )

    def test_timeout_must_be_positive(self):
        with self.assertRaises(ValueError):
            request_public_https(
                URL,
                {"feeds.example.org"},
                resolver=public_resolver,
                timeout=0,
            )

    def test_public_api_does_not_accept_validation_dictionary(self):
        # The public request API accepts allowlisted hosts, not caller-made
        # DNS validation dictionaries.
        with self.assertRaises(TypeError):
            request_public_https(
                URL,
                {"feeds.example.org"},
                validation={"allowlisted": True},
            )



    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_falls_back_to_next_validated_ip_on_connection_error(self, connection_class):
        first_connection = Mock()
        first_connection.connect.side_effect = OSError("first IP unavailable")

        second_connection = Mock()
        response = Mock()
        response.status = 200
        response.getheaders.return_value = []
        response.read.return_value = b"<rss>fallback</rss>"
        second_connection.getresponse.return_value = response

        connection_class.side_effect = [first_connection, second_connection]

        def multiple_public_resolver(host, port, type):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port)),
            ]

        result = request_public_https(
            URL,
            {"feeds.example.org"},
            resolver=multiple_public_resolver,
        )

        self.assertEqual(result["status"], 200)
        self.assertEqual(result["connected_ip"], "93.184.216.34")
        self.assertEqual(result["body"], b"<rss>fallback</rss>")
        first_connection.close.assert_called_once()
        second_connection.close.assert_called_once()
        self.assertEqual(connection_class.call_count, 2)

    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_all_connection_attempts_fail(self, connection_class):
        first_connection = Mock()
        first_connection.connect.side_effect = OSError("first IP unavailable")
        second_connection = Mock()
        second_connection.connect.side_effect = OSError("second IP unavailable")
        connection_class.side_effect = [first_connection, second_connection]

        def multiple_public_resolver(host, port, type):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", port)),
            ]

        with self.assertRaisesRegex(OSError, "second IP unavailable"):
            request_public_https(
                URL,
                {"feeds.example.org"},
                resolver=multiple_public_resolver,
            )

        first_connection.close.assert_called_once()
        second_connection.close.assert_called_once()
        self.assertEqual(connection_class.call_count, 2)


if __name__ == "__main__":
    unittest.main()
