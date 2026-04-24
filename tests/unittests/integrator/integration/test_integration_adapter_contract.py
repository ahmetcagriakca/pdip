"""Unit tests for the abstract ``IntegrationAdapter`` contract.

``IntegrationAdapter`` declares four ``@abstractmethod`` stubs whose
bodies are a single ``pass`` used only to document the contract for
subclasses that choose to call ``super()``. We invoke them through a
concrete subclass so the ``pass`` lines execute.
"""

from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.integration.types.base.integration_adapter import (  # noqa: E402
    IntegrationAdapter,
)


class _ConcreteIntegrationAdapter(IntegrationAdapter):
    def execute(self, operation_integration, channel):
        return super().execute(operation_integration, channel)

    def get_start_message(self, integration):
        return super().get_start_message(integration)

    def get_finish_message(self, integration, data_count):
        return super().get_finish_message(integration, data_count)

    def get_error_message(self, integration):
        return super().get_error_message(integration)


class IntegrationAdapterAbstractStubsReturnNone(TestCase):
    def test_execute_stub_returns_none(self):
        adapter = _ConcreteIntegrationAdapter()

        result = adapter.execute(operation_integration=MagicMock(), channel=MagicMock())

        self.assertIsNone(result)

    def test_get_start_message_stub_returns_none(self):
        adapter = _ConcreteIntegrationAdapter()

        result = adapter.get_start_message(integration=MagicMock())

        self.assertIsNone(result)

    def test_get_finish_message_stub_returns_none(self):
        adapter = _ConcreteIntegrationAdapter()

        result = adapter.get_finish_message(integration=MagicMock(), data_count=3)

        self.assertIsNone(result)

    def test_get_error_message_stub_returns_none(self):
        adapter = _ConcreteIntegrationAdapter()

        result = adapter.get_error_message(integration=MagicMock())

        self.assertIsNone(result)
