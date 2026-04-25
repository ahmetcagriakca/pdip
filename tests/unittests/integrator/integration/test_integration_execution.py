"""Unit tests for ``IntegrationExecution.start``.

The method wraps the integration adapter and publishes a strict three
event sequence: ``INITIALIZED`` -> ``STARTED`` -> ``FINISHED``. These
tests pin down that ordering and the payload shape, without requiring
a multiprocessing broker.
"""

# Stub pandas/func_timeout before the pdip.integrator.* import chain pulls
# them in via the connection-adapter __init__ tree.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.domain.enums.events import (  # noqa: E402
    EVENT_EXECUTION_INTEGRATION_FINISHED,
    EVENT_EXECUTION_INTEGRATION_INITIALIZED,
    EVENT_EXECUTION_INTEGRATION_STARTED,
)
from pdip.integrator.integration.base.integration_execution import (  # noqa: E402
    IntegrationExecution,
)
from pdip.integrator.operation.domain import OperationIntegrationBase  # noqa: E402
from pdip.integrator.pubsub.base import ChannelQueue  # noqa: E402


def _build_execution(adapter):
    adapter_factory = MagicMock(name="adapter_factory")
    adapter_factory.get.return_value = adapter

    initializer = MagicMock(name="initializer")
    # The initializer is a passthrough so downstream asserts can compare
    # against the object the caller passed in.
    initializer.initialize.side_effect = lambda op: op
    initializer_factory = MagicMock(name="initializer_factory")
    initializer_factory.get.return_value = initializer

    return (
        IntegrationExecution(
            integration_adapter_factory=adapter_factory,
            operation_integration_execution_initializer_factory=initializer_factory,
        ),
        initializer,
    )


def _drain(channel):
    """Pull every message off ``channel`` non-blockingly via the
    public ``ChannelQueue.get_nowait`` API."""
    events = []
    while True:
        try:
            events.append(channel.get_nowait())
        except queue.Empty:
            break
    return events


class IntegrationExecutionPublishesLifecycleEvents(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())
        self.operation_integration = OperationIntegrationBase(
            Id=1, Name="oi", Order=0, Integration=MagicMock(name="integration_cfg")
        )

    def test_start_publishes_initialized_started_finished_in_order(self):
        adapter = MagicMock(name="adapter")
        adapter.get_start_message.return_value = "start!"
        adapter.get_finish_message.return_value = "done!"
        adapter.execute.return_value = 42

        execution, _init = _build_execution(adapter)
        execution.start(
            operation_integration=self.operation_integration, channel=self.channel
        )

        events = _drain(self.channel)
        self.assertEqual(
            [m.event for m in events],
            [
                EVENT_EXECUTION_INTEGRATION_INITIALIZED,
                EVENT_EXECUTION_INTEGRATION_STARTED,
                EVENT_EXECUTION_INTEGRATION_FINISHED,
            ],
        )
        # ``data_count`` travels on the finished payload.
        self.assertEqual(events[-1].kwargs["data_count"], 42)

    def test_start_invokes_adapter_execute_with_operation_and_channel(self):
        adapter = MagicMock(name="adapter")
        adapter.get_start_message.return_value = "s"
        adapter.get_finish_message.return_value = "f"
        adapter.execute.return_value = 0

        execution, _init = _build_execution(adapter)
        execution.start(
            operation_integration=self.operation_integration, channel=self.channel
        )

        adapter.execute.assert_called_once_with(
            operation_integration=self.operation_integration, channel=self.channel
        )

    def test_start_emits_finished_with_exception_when_execute_raises(self):
        adapter = MagicMock(name="adapter")
        adapter.get_start_message.return_value = "s"
        adapter.get_error_message.return_value = "oh no"
        error = RuntimeError("kaput")
        adapter.execute.side_effect = error

        execution, _init = _build_execution(adapter)
        with self.assertRaises(RuntimeError):
            execution.start(
                operation_integration=self.operation_integration, channel=self.channel
            )

        events = _drain(self.channel)
        # Should be INITIALIZED, STARTED, then FINISHED-with-exception.
        self.assertEqual(events[-1].event, EVENT_EXECUTION_INTEGRATION_FINISHED)
        self.assertIs(events[-1].kwargs["exception"], error)
        self.assertEqual(events[-1].kwargs["data_count"], 0)
        self.assertEqual(events[-1].kwargs["message"], "oh no")

    def test_start_passes_operation_integration_through_initializer(self):
        adapter = MagicMock(name="adapter")
        adapter.get_start_message.return_value = "s"
        adapter.get_finish_message.return_value = "f"
        adapter.execute.return_value = 1

        execution, initializer = _build_execution(adapter)
        execution.start(
            operation_integration=self.operation_integration, channel=self.channel
        )

        initializer.initialize.assert_called_once_with(self.operation_integration)
