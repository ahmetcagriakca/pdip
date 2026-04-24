"""Unit tests for ``pdip.data.repository.RepositoryProvider``.

The ``basic_app_with_cqrs`` suite exercises ``get`` / ``create`` /
``commit`` end-to-end through a live ``Pdi`` container; these tests
pin down the branches that path doesn't reach without booting
``Pdi``: the ``query`` pass-through, ``rollback``, ``reconnect``,
and the ``None``-manager fast-paths.
"""

from dataclasses import dataclass
from typing import Optional
from unittest import TestCase
from unittest.mock import MagicMock

from pdip.data.repository.repository_provider import RepositoryProvider


@dataclass
class _DbConfigStub:
    type: Optional[str] = None
    connection_string: str = ""


class RepositoryProviderDelegatesToSessionManager(TestCase):
    def setUp(self):
        # Arrange — a mock session manager lets us assert call
        # propagation without a real database.
        self.mgr = MagicMock()
        self.provider = RepositoryProvider(
            database_config=_DbConfigStub(),
            database_session_manager=self.mgr,
        )

    def test_query_returns_session_query_for_entities(self):
        sentinel_query = object()
        self.mgr.session.query.return_value = sentinel_query

        result = self.provider.query("a", "b", filter_by="x")

        self.assertIs(result, sentinel_query)
        self.mgr.session.query.assert_called_once_with("a", "b", filter_by="x")

    def test_commit_delegates_to_session_manager(self):
        self.provider.commit()

        self.mgr.commit.assert_called_once_with()

    def test_rollback_delegates_to_session_manager(self):
        self.provider.rollback()

        self.mgr.rollback.assert_called_once_with()

    def test_reconnect_closes_and_reopens_session_manager(self):
        self.provider.reconnect()

        self.mgr.close.assert_called_once_with()
        self.mgr.connect.assert_called_once_with()

    def test_close_delegates_to_session_manager(self):
        self.provider.close()

        self.mgr.close.assert_called_once_with()


class RepositoryProviderIsSafeWhenManagerIsNone(TestCase):
    """Every mutating method guards on ``is not None`` before
    delegating; those False branches must be a no-op rather than a
    crash. This pins down lines 43-44, 47-48, 51-53, 56-57 ``False``
    branches."""

    def setUp(self):
        self.provider = RepositoryProvider(
            database_config=_DbConfigStub(),
            database_session_manager=None,
        )

    def test_commit_is_noop_when_manager_absent(self):
        # Contract: the method returns None (no raise, no side effect).
        self.assertIsNone(self.provider.commit())
        self.assertIsNone(self.provider.database_session_manager)

    def test_rollback_is_noop_when_manager_absent(self):
        self.assertIsNone(self.provider.rollback())
        self.assertIsNone(self.provider.database_session_manager)

    def test_reconnect_is_noop_when_manager_absent(self):
        self.assertIsNone(self.provider.reconnect())
        self.assertIsNone(self.provider.database_session_manager)

    def test_close_is_noop_when_manager_absent(self):
        self.assertIsNone(self.provider.close())
        # Contract: manager is still None (nothing was created).
        self.assertIsNone(self.provider.database_session_manager)
