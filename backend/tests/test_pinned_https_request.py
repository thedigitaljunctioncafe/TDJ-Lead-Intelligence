import socket
import unittest
from unittest.mock import Mock, patch

from app.connectors.pinned_https import request_public_https


URL = "https://feeds.example.org/rss"


def public_resolver(host, port, type):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))
    ]


class TestPinnedHTTPSRequest(unittest.TestCase):

    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_query_string_is_preserved(self, connection_class):
        connection = Mock()
        response = Mock()
        response.status = 200
        response.getheaders.return_value = []
        response.read.return_value = b"ok"
        connection.getresponse.return_value = response
        connection_class.return_value = connection

        request_public_https(
            URL + "?page=2",
            {"feeds.example.org"},
            resolver=public_resolver,
        )

        self.assertEqual(
            connection.request.call_args.args[1],
            "/rss?page=2",
        )
        connection.close.assert_called_once()

    @patch("app.connectors.pinned_https._PinnedHTTPSConnection")
    def test_host_header_uses_original_hostname(self, connection_class):
        connection = Mock()
        response = Mock()
        response.status = 200
        response.getheaders.return_value = []
        response.read.return_value = b"ok"
        connection.getresponse.return_value = response
        connection_class.return_value = connection

        request_public_https(
            URL,
            {"feeds.example.org"},
            resolver=public_resolver,
        )

        headers = connection.request.call_args.kwargs["headers"]
        self.assertEqual(headers["Host"], "feeds.example.org")



    def test_control_characters_in_url_are_rejected_before_connection(self):
        unsafe_urls = [
            URL + "\r\nInjected: yes",
            URL + "?page=2\nInjected: yes",
            URL + "\t",
            URL + " ",
        ]

        for unsafe_url in unsafe_urls:
            with self.subTest(url=repr(unsafe_url)):
                with patch("app.connectors.pinned_https._PinnedHTTPSConnection") as factory:
                    with self.assertRaises(ValueError):
                        request_public_https(
                            unsafe_url,
                            {"feeds.example.org"},
                            resolver=public_resolver,
                        )
                    factory.assert_not_called()

    def test_query_string_is_preserved_after_validation(self):
        with patch("app.connectors.pinned_https._PinnedHTTPSConnection") as factory:
            connection = Mock()
            response = Mock()
            response.status = 200
            response.getheaders.return_value = []
            response.read.return_value = b"ok"
            connection.getresponse.return_value = response
            factory.return_value = connection

            request_public_https(
                URL + "?page=2&limit=10",
                {"feeds.example.org"},
                resolver=public_resolver,
            )

            self.assertEqual(
                connection.request.call_args.args[1],
                "/rss?page=2&limit=10",
            )
            connection.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
