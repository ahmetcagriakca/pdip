"""Unit tests for ``TargetIntegration`` — the target-only integration
adapter.

``TargetIntegration.execute`` resolves a target adapter from a factory,
optionally asks it to clear existing data (publishing an
``EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE`` message), then runs
the target operation (publishing an
``EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET`` message) and returns
the affected row count. The three ``get_*_message`` helpers return
constant strings — one assertion each pins that contract down.

All collaborators below the public surface (factory, adapter,
channel) are mocked at the boundary.
"""

# Stub pandas/func_timeout before any ``pdip.integrator.*`` import.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.domain.enums.events import (  # noqa: E402
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET,
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
)
from pdip.integrator.integration.domain.base import (  # noqa: E402
    IntegrationBase,
    IntegrationConnectionBase,
)
# Import the package tree that owns ``IntegrationAdapterFactory``
# before reaching into the target-base package. Direct import of
# ``target.base`` hits a circular-import race with
# ``integration_adapter_factory``; resolving the parent first avoids it.
import pdip.integrator.integration.types.base  # noqa: F401, E402
from pdip.integrator.integration.types.target.base import (  # noqa: E402
    TargetIntegration,
)
from pdip.integrator.operation.domain import OperationIntegrationBase  # noqa: E402
from pdip.integrator.pubsub.base import ChannelQueue  # noqa: E402


def _build_integration(connection_type="SQL", is_truncate=False):
    target = IntegrationConnectionBase(ConnectionType=connection_type)
    return IntegrationBase(
        SourceConnections=None,
        TargetConnections=target,
        IsTargetTruncate=is_truncate,
    )


def _build_operation(integration, order=2):
    return OperationIntegrationBase(
        Id=1, Name="oi", Order=order, Integration=integration,
    )


def _build_subject(adapter):
    """Return ``(subject, factory)`` so that the subject's
    ``ConnectionTargetAdapterFactory`` returns ``adapter``."""
    factory = MagicMock(name="connection_target_adapter_factory")
    factory.get_adapter.return_value = adapter
    subject = TargetIntegration(connection_target_adapter_factory=factory)
    return subject, factory


def _drain(channel):
    messages = []
    while True:
        try:
            messages.append(channel.get_nowait())
        except queue.Empty:
            return messages


class TargetIntegrationExecuteWithoutTruncate(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_returns_affected_row_count_from_target_operation(self):
        adapter = MagicMock(name="target_adapter")
        adapter.do_target_operation.return_value = 12
        integration = _build_integration(is_truncate=False)
        operation = _build_operation(integration)
        subject, _factory = _build_subject(adapter)

        result = subject.execute(
            operation_integration=operation, channel=self.channel
        )

        self.assertEqual(result, 12)

    def test_execute_resolves_adapter_with_target_connection_type(self):
        adapter = MagicMock(name="target_adapter")
        adapter.do_target_operation.return_value = 0
        integration = _build_integration(connection_type="MSSQL")
        operation = _build_operation(integration)
        subject, factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        factory.get_adapter.assert_called_once_with(connection_type="MSSQL")

    def test_execute_runs_target_operation_once_with_integration(self):
        adapter = MagicMock(name="target_adapter")
        adapter.do_target_operation.return_value = 4
        integration = _build_integration()
        operation = _build_operation(integration)
        subject, _factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        adapter.do_target_operation.assert_called_once_with(
            integration=integration
        )
        adapter.clear_data.assert_not_called()

    def test_execute_publishes_only_target_event_when_truncate_is_false(self):
        adapter = MagicMock(name="target_adapter")
        adapter.do_target_operation.return_value = 3
        integration = _build_integration(is_truncate=False)
        operation = _build_operation(integration, order=7)
        subject, _factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        messages = _drain(self.channel)
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            messages[0].event, EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET
        )
        self.assertIs(messages[0].kwargs["data"], operation)
        self.assertEqual(messages[0].kwargs["row_count"], 3)


class TargetIntegrationExecuteWithTruncate(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_calls_clear_data_before_target_operation(self):
        adapter = MagicMock(name="target_adapter")
        adapter.clear_data.return_value = 99
        adapter.do_target_operation.return_value = 4
        integration = _build_integration(is_truncate=True)
        operation = _build_operation(integration)
        subject, _factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        adapter.clear_data.assert_called_once_with(integration=integration)
        adapter.do_target_operation.assert_called_once_with(
            integration=integration
        )

    def test_execute_publishes_truncate_event_with_clear_data_count(self):
        adapter = MagicMock(name="target_adapter")
        adapter.clear_data.return_value = 50
        adapter.do_target_operation.return_value = 1
        integration = _build_integration(is_truncate=True)
        operation = _build_operation(integration)
        subject, _factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        messages = _drain(self.channel)
        # First message is the truncate event; second is the target event.
        self.assertEqual(len(messages), 2)
        self.assertEqual(
            messages[0].event, EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE
        )
        self.assertEqual(messages[0].kwargs["row_count"], 50)
        self.assertEqual(
            messages[1].event, EVENT_EXECUTION_INTEGRATION_EXECUTE_TARGET
        )
        self.assertEqual(messages[1].kwargs["row_count"], 1)


class TargetIntegrationLabelHelpers(TestCase):
    def setUp(self):
        adapter = MagicMock(name="target_adapter")
        self.subject, _factory = _build_subject(adapter)
        self.integration = _build_integration()

    def test_get_start_message_returns_started_sentinel(self):
        self.assertEqual(
            self.subject.get_start_message(self.integration),
            "Target integration started.",
        )

    def test_get_finish_message_returns_finished_sentinel(self):
        self.assertEqual(
            self.subject.get_finish_message(self.integration, data_count=42),
            "Target integration finished.",
        )

    def test_get_error_message_returns_error_sentinel(self):
        self.assertEqual(
            self.subject.get_error_message(self.integration),
            "Target integration getting error.",
        )
