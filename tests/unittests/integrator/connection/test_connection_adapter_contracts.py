"""Unit tests for the abstract connection adapter contracts.

``ConnectionSourceAdapter`` and ``ConnectionTargetAdapter`` declare
``@abstractmethod`` stubs whose bodies are ``pass``. Hit the bodies
via a concrete subclass that calls ``super()`` so the contract lines
execute and regression risk on the abstract signatures is pinned.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.connection.base.connection_source_adapter import (  # noqa: E402
    ConnectionSourceAdapter,
)
from pdip.integrator.connection.base.connection_target_adapter import (  # noqa: E402
    ConnectionTargetAdapter,
)


class _ConcreteSourceAdapter(ConnectionSourceAdapter):
    def get_source_data_count(self, integration):
        return super().get_source_data_count(integration)

    def get_iterator(self, integration, limit):
        return super().get_iterator(integration, limit)

    def get_source_data_with_paging(self, integration, start, end):
        return super().get_source_data_with_paging(integration, start, end)


class _ConcreteTargetAdapter(ConnectionTargetAdapter):
    def clear_data(self, integration):
        return super().clear_data(integration)

    def write_data(self, integration, source_data):
        return super().write_data(integration, source_data)

    def do_target_operation(self, integration):
        return super().do_target_operation(integration)


class ConnectionSourceAdapterAbstractStubsReturnNone(TestCase):
    def test_get_source_data_count_stub_returns_none(self):
        adapter = _ConcreteSourceAdapter()

        result = adapter.get_source_data_count(integration=MagicMock())

        self.assertIsNone(result)

    def test_get_iterator_stub_returns_none(self):
        adapter = _ConcreteSourceAdapter()

        result = adapter.get_iterator(integration=MagicMock(), limit=10)

        self.assertIsNone(result)

    def test_get_source_data_with_paging_stub_returns_none(self):
        adapter = _ConcreteSourceAdapter()

        result = adapter.get_source_data_with_paging(
            integration=MagicMock(), start=0, end=5
        )

        self.assertIsNone(result)


class ConnectionTargetAdapterAbstractStubsReturnNone(TestCase):
    def test_clear_data_stub_returns_none(self):
        adapter = _ConcreteTargetAdapter()

        result = adapter.clear_data(integration=MagicMock())

        self.assertIsNone(result)

    def test_write_data_stub_returns_none(self):
        adapter = _ConcreteTargetAdapter()

        result = adapter.write_data(integration=MagicMock(), source_data=[1, 2])

        self.assertIsNone(result)

    def test_do_target_operation_stub_returns_none(self):
        adapter = _ConcreteTargetAdapter()

        result = adapter.do_target_operation(integration=MagicMock())

        self.assertIsNone(result)
