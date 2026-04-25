"""Unit tests for ``pdip.integrator.connection.base._async_extra``.

ADR-0032 §3 says the factories must raise a clear ``ImportError``
when ``is_async=True`` is asked for but the ``pdip[async]`` extra is
not installed. ``require_async_extra`` is the single helper both
factories call to enforce that contract; these tests pin its
behaviour so the per-factory tests can stub it out cleanly.
"""

import sys
from unittest import TestCase

from pdip.integrator.connection.base._async_extra import (
    ASYNC_EXTRA_INSTALL_HINT,
    require_async_extra,
)


class RequireAsyncExtraReturnsWhenMarkerImportable(TestCase):
    def setUp(self):
        # Inject a fake ``asyncpg`` so the marker import succeeds even
        # when the real package is not in this environment.
        self._saved = sys.modules.get("asyncpg")
        sys.modules["asyncpg"] = object()

    def tearDown(self):
        if self._saved is None:
            sys.modules.pop("asyncpg", None)
        else:
            sys.modules["asyncpg"] = self._saved

    def test_returns_none_when_marker_present(self):
        # Helper must NOT raise — the test asserts the silent
        # success path that lets the factory continue.
        self.assertIsNone(require_async_extra())


class RequireAsyncExtraRaisesWhenMarkerMissing(TestCase):
    def setUp(self):
        # Block ``asyncpg`` even if it happens to be installed.
        self._saved = sys.modules.get("asyncpg")
        sys.modules["asyncpg"] = None

    def tearDown(self):
        sys.modules.pop("asyncpg", None)
        if self._saved is not None:
            sys.modules["asyncpg"] = self._saved

    def test_raises_import_error_with_install_hint(self):
        with self.assertRaises(ImportError) as ctx:
            require_async_extra()
        self.assertIn(ASYNC_EXTRA_INSTALL_HINT, str(ctx.exception))
        self.assertIn("pdip[async]", ASYNC_EXTRA_INSTALL_HINT)
