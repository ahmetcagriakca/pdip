"""Unit tests for ``pdip.dependency.provider.api.api_provider.ApiProvider``.

``ApiProvider`` wires Flask + flask_restx + flask_injector together
for a full ``Pdi`` boot. The ``basic_app*`` suites exercise the
happy path end-to-end via ``Pdi()``; these tests pin down the
branches those suites don't hit without booting the container —
the ``__del__`` path and the explicit ``base_url``/``doc_url``
branches plus the ``home_redirect`` route itself.
"""

from unittest import TestCase
from unittest.mock import MagicMock

from flask import Flask
from injector import Injector

from pdip.configuration.models.api import ApiConfig
from pdip.configuration.models.application import ApplicationConfig
from pdip.dependency.provider.api.api_provider import ApiProvider


def _api_config(base_url=None, doc_url=None, version="1.0"):
    return ApiConfig(
        base_url=base_url,
        doc_url=doc_url,
        is_debug=False,
        version=version,
        port=None,
        origins=None,
        authorizations=None,
        security=None,
    )


def _application_config(name="test-app"):
    return ApplicationConfig(
        root_directory="/tmp",
        name=name,
        environment="test",
        hostname=None,
        secret_key=None,
    )


class ApiProviderInitializeFlaskUsesConfiguredUrls(TestCase):
    def test_explicit_base_url_and_doc_url_are_applied(self):
        # Arrange — both base_url and doc_url explicitly set so the
        # ``if ...is not None`` branches for each take effect.
        provider = ApiProvider(
            modules=[],
            application_config=_application_config(),
            api_config=_api_config(base_url="/root", doc_url="/docs"),
            injector=Injector(),
        )

        # Act
        provider.initialize_flask()

        # Assert — the Flask app now has the ``/root`` rule installed
        # by ``@self.app.route(base_url)`` and the redirect returns 302
        # to ``/docs``.
        rules = {r.rule for r in provider.app.url_map.iter_rules()}
        self.assertIn("/root", rules)

        with provider.app.test_client() as client:
            response = client.get("/root")
            self.assertEqual(response.status_code, 302)
            self.assertIn("/docs", response.headers["Location"])


class ApiProviderInitializeFlaskUsesDefaultsWhenConfigIsBlank(TestCase):
    def test_defaults_base_url_and_doc_url_when_config_none(self):
        provider = ApiProvider(
            modules=[],
            application_config=_application_config(),
            api_config=_api_config(),
            injector=Injector(),
        )

        provider.initialize_flask()

        rules = {r.rule for r in provider.app.url_map.iter_rules()}
        # Default base_url is '/'.
        self.assertIn("/", rules)

        with provider.app.test_client() as client:
            response = client.get("/")
            self.assertEqual(response.status_code, 302)
            # Default doc_url.
            self.assertIn("/documentation", response.headers["Location"])


class ApiProviderDelReleasesOwnedResources(TestCase):
    def test_del_deletes_api_app_and_logger_attributes(self):
        # Arrange — build a provider but swap app/api/logger for
        # plain sentinels we can observe being released.
        provider = ApiProvider(
            modules=[],
            application_config=_application_config(),
            api_config=_api_config(),
            injector=Injector(),
        )
        provider.app = MagicMock(spec=Flask)
        provider.api = MagicMock()
        # logger is already set in __init__.
        self.assertTrue(hasattr(provider, "logger"))

        # Act
        provider.__del__()

        # Assert
        self.assertFalse(hasattr(provider, "api"))
        self.assertFalse(hasattr(provider, "app"))
        self.assertFalse(hasattr(provider, "logger"))

    def test_del_is_safe_when_logger_already_released(self):
        # Covers the ``if hasattr(self, 'logger')`` False branch.
        provider = ApiProvider(
            modules=[],
            application_config=_application_config(),
            api_config=_api_config(),
            injector=Injector(),
        )
        provider.app = MagicMock(spec=Flask)
        provider.api = MagicMock()
        del provider.logger

        provider.__del__()

        self.assertFalse(hasattr(provider, "logger"))
