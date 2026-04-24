"""Unit tests for ``OperationExecution.start``.

The method is wrapped in ``@transactionhandler`` which reaches into
``DependencyContainer.Instance`` for a ``RepositoryProvider``. We patch
that container access so the test stays in-process and does not require
a real SQLAlchemy session.
"""

# Stub pandas/func_timeout before the pdip.integrator.* import chain pulls
# them in via the connection-adapter __init__ tree.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.domain.enums.events import (  # noqa: E402
    EVENT_EXECUTION_FINISHED,
    EVENT_EXECUTION_INITIALIZED,
    EVENT_EXECUTION_STARTED,
)
from pdip.integrator.operation.base.operation_execution import (  # noqa: E402
    OperationExecution,
)
from pdip.integrator.operation.domain import (  # noqa: E402
    OperationBase,
    OperationIntegrationBase,
)
from pdip.integrator.pubsub.base import ChannelQueue  # noqa: E402


def _drain(channel):
    """Pull every message off ``channel`` by reaching through to the
    underlying ``queue.Queue``; ``ChannelQueue.get`` blocks forever."""
    events = []
    while not channel.channel_queue.empty():
        events.append(channel.channel_queue.get_nowait())
    return events


def _build_execution(integration_execution=None):
    integration_execution = integration_execution or MagicMock(name="integration_execution")
    initializer = MagicMock(name="initializer")
    initializer.initialize.side_effect = lambda op: op
    initializer_factory = MagicMock(name="initializer_factory")
    initializer_factory.get.return_value = initializer

    return OperationExecution(
        integration_execution=integration_execution,
        operation_execution_initializer_factory=initializer_factory,
    ), integration_execution


class _TxContainerPatch:
    """Context manager that installs a mock ``DependencyContainer`` so the
    ``@transactionhandler`` decorator does not hit real SQLAlchemy."""

    def __enter__(self):
        from pdip.dependency.container import DependencyContainer

        self._previous_instance = DependencyContainer.Instance
        self._mock_instance = MagicMock(name="container")
        self._mock_instance.get.return_value = MagicMock(name="repository_provider")
        DependencyContainer.Instance = self._mock_instance
        return self._mock_instance

    def __exit__(self, exc_type, exc_val, exc_tb):
        from pdip.dependency.container import DependencyContainer

        DependencyContainer.Instance = self._previous_instance
        return False


class OperationExecutionDrivesIntegrations(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_start_iterates_integrations_in_declared_order(self):
        integration_execution = MagicMock(name="integration_execution")
        execution, _ = _build_execution(integration_execution)

        oi1 = OperationIntegrationBase(Id=1, Name="first", Order=0)
        oi2 = OperationIntegrationBase(Id=2, Name="second", Order=1)
        oi3 = OperationIntegrationBase(Id=3, Name="third", Order=2)
        operation = OperationBase(Id=1, Name="op", Integrations=[oi1, oi2, oi3])

        with _TxContainerPatch():
            execution.start(operation=operation, channel=self.channel)

        observed = [
            call.kwargs.get("operation_integration") or call.args[0]
            for call in integration_execution.start.call_args_list
        ]
        self.assertEqual(observed, [oi1, oi2, oi3])

    def test_start_publishes_initialized_started_finished(self):
        execution, _ = _build_execution()
        operation = OperationBase(Id=1, Name="op", Integrations=[])

        with _TxContainerPatch():
            execution.start(operation=operation, channel=self.channel)

        events = _drain(self.channel)
        self.assertEqual(
            [m.event for m in events],
            [EVENT_EXECUTION_INITIALIZED, EVENT_EXECUTION_STARTED, EVENT_EXECUTION_FINISHED],
        )
        # The terminal event is flagged ``is_finished=True`` so subscribers
        # know to tear down.
        self.assertTrue(events[-1].is_finished)

    def test_start_emits_finished_with_exception_when_integration_fails(self):
        integration_execution = MagicMock(name="integration_execution")
        err = RuntimeError("integration blew up")
        integration_execution.start.side_effect = err

        execution, _ = _build_execution(integration_execution)
        operation = OperationBase(
            Id=1, Name="op", Integrations=[OperationIntegrationBase(Id=1, Name="x")]
        )

        with _TxContainerPatch():
            with self.assertRaises(RuntimeError):
                execution.start(operation=operation, channel=self.channel)

        events = _drain(self.channel)
        self.assertEqual(events[-1].event, EVENT_EXECUTION_FINISHED)
        self.assertTrue(events[-1].is_finished)
        self.assertIs(events[-1].kwargs["exception"], err)

    def test_start_commits_transaction_on_success(self):
        execution, _ = _build_execution()
        operation = OperationBase(Id=1, Name="op", Integrations=[])

        with _TxContainerPatch() as container:
            execution.start(operation=operation, channel=self.channel)
            provider = container.get.return_value
            provider.commit.assert_called_once_with()
            provider.rollback.assert_not_called()
