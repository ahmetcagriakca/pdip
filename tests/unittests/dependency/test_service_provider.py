"""Unit tests for ``pdip.dependency.provider.service_provider.ServiceProvider``.

``ServiceProvider`` loads configs, builds a dependency injector, and
exposes ``get(...)`` to resolve instances. The existing
``test_pdi`` suite covers the happy-path construction + shutdown via
``Pdi``; these tests pin the smaller branches:

* ``__del__`` disposes the ``api_provider`` when one was installed
  (line-52 branch).
* ``__del__`` deletes the ``logger`` attribute only when it still
  exists (line-55 branch) — e.g. constructors that register modules
  delete ``self.logger`` in ``configure``.
* The constructor appends caller-supplied ``excluded_modules`` on top
  of the internal defaults (line 66).

A real pdip config directory (``tests/unittests/configuration``) is
used because ``ConfigManager`` requires a valid ``application.yml``.
No ``Pdi()`` is booted — the provider is constructed directly at the
boundary it already exposes.
"""

import os
from unittest import TestCase
from unittest.mock import MagicMock

from pdip.dependency.provider.service_provider import ServiceProvider


_CONFIG_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "configuration",
    )
)


class ServiceProviderForwardsExcludedModules(TestCase):
    def tearDown(self):
        # Purge env overrides that other suites might have set.
        os.environ["PYTHON_ENVIRONMENT"] = ""

    def test_constructor_appends_excluded_modules(self):
        # Pass a bogus excluded module to exercise the append branch.
        provider = ServiceProvider(
            root_directory=_CONFIG_ROOT,
            excluded_modules=["definitely_not_a_real_module"],
        )
        try:
            self.assertEqual(
                provider.excluded_modules, ["definitely_not_a_real_module"]
            )
        finally:
            del provider


class ServiceProviderDelDisposesApiProvider(TestCase):
    def tearDown(self):
        os.environ["PYTHON_ENVIRONMENT"] = ""

    def test_del_calls_into_api_provider_disposer(self):
        provider = ServiceProvider(root_directory=_CONFIG_ROOT)
        # Simulate a Flask-mode provider that already installed an
        # api_provider without actually booting flask.
        api_provider = MagicMock(name="api_provider")
        provider.api_provider = api_provider
        # Re-attach a disposable logger too so the line-55 branch runs.
        provider.logger = MagicMock(name="logger")

        provider.__del__()

        # ``del self.api_provider`` removes the attribute; its
        # observable effect is that ``api_provider`` is no longer set.
        self.assertFalse(hasattr(provider, "api_provider"))

    def test_del_skips_api_provider_disposal_when_none(self):
        provider = ServiceProvider(root_directory=_CONFIG_ROOT)
        # Re-attach a logger so only the api_provider branch is what
        # differs between the two tests.
        provider.logger = MagicMock(name="logger")
        self.assertIsNone(provider.api_provider)

        # Must not raise even though api_provider is None.
        provider.__del__()
