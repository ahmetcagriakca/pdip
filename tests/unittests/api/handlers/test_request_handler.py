"""Unit tests for ``pdip.api.handlers.request_handler.RequestHandler``.

``set_headers`` walks the configured origin allow-list and copies the
request ``Origin`` onto the response when it matches. ``after_request``
also drives the repository-provider close via the service provider.
``flask.request`` is stubbed through a test request context so no
real HTTP stack is involved.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from flask import Flask

from pdip.api.handlers.request_handler import RequestHandler


def _build_handler(origins):
    api_config = MagicMock()
    api_config.origins = origins
    service_provider = MagicMock()
    return (
        RequestHandler(api_config=api_config, service_provider=service_provider),
        api_config,
        service_provider,
    )


class RequestHandlerSetHeadersAllowsConfiguredOrigins(TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_wildcard_origin_copies_request_origin_onto_response(self):
        handler, _, _ = _build_handler(origins="*")
        with self.app.test_request_context(
            "/", headers={"Origin": "https://client.test"}
        ):
            response = MagicMock()
            response.headers = {}

            result = handler.set_headers(response)

        self.assertEqual(
            result.headers["Access-Control-Allow-Origin"], "https://client.test"
        )
        self.assertEqual(result.headers["Server"], "")

    def test_explicit_origin_in_list_copies_request_origin(self):
        handler, _, _ = _build_handler(
            origins="https://a.test,https://b.test"
        )
        with self.app.test_request_context(
            "/", headers={"Origin": "https://b.test"}
        ):
            response = MagicMock()
            response.headers = {}

            handler.set_headers(response)

        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"], "https://b.test"
        )

    def test_origin_not_in_allow_list_does_not_set_cors_header(self):
        handler, _, _ = _build_handler(origins="https://a.test")
        with self.app.test_request_context(
            "/", headers={"Origin": "https://c.test"}
        ):
            response = MagicMock()
            response.headers = {}

            handler.set_headers(response)

        self.assertNotIn("Access-Control-Allow-Origin", response.headers)
        self.assertEqual(response.headers["Server"], "")

    def test_missing_origins_config_skips_header_copy(self):
        handler, _, _ = _build_handler(origins=None)
        with self.app.test_request_context(
            "/", headers={"Origin": "https://any.test"}
        ):
            response = MagicMock()
            response.headers = {}

            handler.set_headers(response)

        self.assertNotIn("Access-Control-Allow-Origin", response.headers)


class RequestHandlerAfterRequestClosesRepository(TestCase):
    def setUp(self):
        self.app = Flask(__name__)

    def test_after_request_delegates_to_set_headers_and_closes_provider(self):
        handler, _, service_provider = _build_handler(origins="*")
        repo_provider = MagicMock(name="RepositoryProvider")
        service_provider.get.return_value = repo_provider

        with self.app.test_request_context(
            "/", headers={"Origin": "https://client.test"}
        ):
            response = MagicMock()
            response.headers = {}

            result = handler.after_request(response)

        self.assertIs(result, response)
        repo_provider.close.assert_called_once()
