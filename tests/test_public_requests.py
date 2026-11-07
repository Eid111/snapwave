import unittest
from unittest.mock import Mock, patch

import requests
from fastapi import HTTPException

from backend.core.security import _PinnedAddressAdapter, request_public_url
from backend.services.resolvers.drama_resolver import resolve_drama_site
from backend.services.resolvers.vidaraa import resolve_vidaraa


class PublicRequestTests(unittest.TestCase):
    @staticmethod
    def _response(status_code, headers=None):
        response = Mock(spec=requests.Response)
        response.status_code = status_code
        response.headers = headers or {}
        return response

    def test_redirect_to_private_address_is_rejected(self):
        redirect = self._response(302, {"Location": "http://127.0.0.1/admin"})
        with patch.object(requests.Session, "request", return_value=redirect) as send:
            with self.assertRaises(HTTPException):
                request_public_url("GET", "http://8.8.8.8/video")

        send.assert_called_once()
        redirect.close.assert_called_once()

    def test_public_redirect_is_validated_and_followed_manually(self):
        redirect = self._response(302, {"Location": "https://1.1.1.1/video"})
        final = self._response(200)
        with patch.object(
            requests.Session, "request", side_effect=[redirect, final]
        ) as send:
            response = request_public_url("GET", "http://8.8.8.8/start")

        self.assertIs(response, final)
        self.assertEqual(
            [call.args[1] for call in send.call_args_list],
            ["http://8.8.8.8/start", "https://1.1.1.1/video"],
        )
        redirect.close.assert_called_once()

    def test_https_connection_is_pinned_and_keeps_hostname_verification(self):
        prepared = requests.Request("GET", "https://media.example/video").prepare()
        adapter = _PinnedAddressAdapter()
        address_info = [
            (2, 1, 6, "", ("8.8.8.8", 443)),
        ]
        with patch("backend.core.security.socket.getaddrinfo", return_value=address_info):
            pool = adapter.get_connection_with_tls_context(
                prepared, verify=True, proxies=None, cert=None
            )

        self.assertEqual(pool.host, "8.8.8.8")
        self.assertEqual(pool.assert_hostname, "media.example")
        self.assertEqual(pool.conn_kw["server_hostname"], "media.example")
        adapter.close()

    def test_dns_results_containing_private_address_are_rejected(self):
        address_info = [
            (2, 1, 6, "", ("8.8.8.8", 443)),
            (2, 1, 6, "", ("10.0.0.5", 443)),
        ]
        with patch("backend.core.security.socket.getaddrinfo", return_value=address_info):
            with self.assertRaises(requests.exceptions.InvalidURL):
                _PinnedAddressAdapter().get_connection_with_tls_context(
                    requests.Request(
                        "GET", "https://media.example/video"
                    ).prepare(),
                    verify=True,
                )

    def test_private_embedded_server_is_not_contacted(self):
        page = Mock()
        page.text = '<iframe src="http://127.0.0.1/vidaraa/abc"></iframe>'
        with patch.object(requests.Session, "request", return_value=page) as send:
            result = resolve_drama_site("http://8.8.8.8/drama")

        self.assertFalse(result["resolved"])
        send.assert_called_once()

    def test_private_stream_url_is_not_returned(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "streaming_url": "http://127.0.0.1/private-video"
        }
        with patch(
            "backend.services.resolvers.vidaraa.request_public_url",
            return_value=response,
        ):
            stream_url, title = resolve_vidaraa("https://8.8.8.8/embed/abc")

        self.assertIsNone(stream_url)
        self.assertIsNone(title)


if __name__ == "__main__":
    unittest.main()
