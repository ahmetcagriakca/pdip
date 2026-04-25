"""Unit tests for ``SingleProcessIntegrationExecute`` — the
single-process source-to-target strategy.

The strategy is wired with a source-adapter factory and a target-
adapter factory (both injected). ``execute(operation_integration,
channel)``:

 * resolves the source and target adapters from the factories using
   the per-connection ``ConnectionType``,
 * iterates the source adapter's page iterator (``get_iterator``),
 * publishes a ``EVENT_LOG`` read message per page, writes the page
   through ``write_target_data``, then publishes a finish-log message,
 * returns the total row count (sum of ``len(results)`` across pages),
 * on exception, publishes a ``EVENT_LOG`` with the ``exception``
   kwarg and re-raises.

Tests exercise ``execute`` directly with mock factories, a fake
``OperationIntegrationBase``, and a real ``ChannelQueue`` so we can
observe the published events.
"""

# Stub pandas/func_timeout before any ``pdip.integrator.*`` import.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.domain.enums.events import EVENT_LOG  # noqa: E402
from pdip.integrator.integration.types.sourcetotarget.strategies.singleprocess.base.single_process_integration_execute import (  # noqa: E402
    SingleProcessIntegrationExecute,
)
from pdip.integrator.pubsub.base import ChannelQueue  # noqa: E402


def _build_operation(source_type="SQL", target_type="SQL", limit=10):
    """Fake ``OperationIntegrationBase`` built with MagicMock so the
    attribute chain ``Integration.SourceConnections.ConnectionType``
    (and the target counterpart) works without pulling real dataclasses."""
    operation = MagicMock(name="operation_integration")
    operation.Limit = limit
    operation.Integration.SourceConnections.ConnectionType = source_type
    operation.Integration.TargetConnections.ConnectionType = target_type
    return operation


def _build_subject(source_adapter, target_adapter):
    source_factory = MagicMock(name="source_factory")
    source_factory.get_adapter.return_value = source_adapter
    target_factory = MagicMock(name="target_factory")
    target_factory.get_adapter.return_value = target_adapter
    subject = SingleProcessIntegrationExecute(
        connection_source_adapter_factory=source_factory,
        connection_target_adapter_factory=target_factory,
    )
    return subject, source_factory, target_factory


def _drain(channel):
    messages = []
    while True:
        try:
            messages.append(channel.get_nowait())
        except queue.Empty:
            break
    return messages


class SingleProcessExecuteSumsRowsAcrossPages(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_returns_total_row_count_across_pages(self):
        source = MagicMock(name="source_adapter")
        source.get_iterator.return_value = iter([[1, 2, 3], [4, 5]])
        target = MagicMock(name="target_adapter")
        operation = _build_operation(limit=10)
        subject, _s, _t = _build_subject(source, target)

        result = subject.execute(operation_integration=operation, channel=self.channel)

        self.assertEqual(result, 5)

    def test_execute_returns_zero_when_iterator_is_empty(self):
        source = MagicMock(name="source_adapter")
        source.get_iterator.return_value = iter([])
        target = MagicMock(name="target_adapter")
        operation = _build_operation()
        subject, _s, _t = _build_subject(source, target)

        result = subject.execute(operation_integration=operation, channel=self.channel)

        self.assertEqual(result, 0)


class SingleProcessExecuteResolvesAdaptersByConnectionType(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_resolves_source_adapter_with_source_connection_type(self):
        source = MagicMock()
        source.get_iterator.return_value = iter([])
        target = MagicMock()
        operation = _build_operation(source_type="BIGDATA", target_type="SQL")
        subject, source_factory, _t = _build_subject(source, target)

        subject.execute(operation_integration=operation, channel=self.channel)

        source_factory.get_adapter.assert_called_once_with(connection_type="BIGDATA")

    def test_execute_resolves_target_adapter_with_target_connection_type(self):
        source = MagicMock()
        source.get_iterator.return_value = iter([])
        target = MagicMock()
        operation = _build_operation(source_type="SQL", target_type="QUEUE")
        subject, _s, target_factory = _build_subject(source, target)

        subject.execute(operation_integration=operation, channel=self.channel)

        target_factory.get_adapter.assert_called_once_with(connection_type="QUEUE")

    def test_execute_passes_limit_and_integration_to_source_iterator(self):
        source = MagicMock()
        source.get_iterator.return_value = iter([])
        target = MagicMock()
        operation = _build_operation(limit=50)
        subject, _s, _t = _build_subject(source, target)

        subject.execute(operation_integration=operation, channel=self.channel)

        source.get_iterator.assert_called_once_with(
            integration=operation.Integration, limit=50,
        )


class SingleProcessExecuteWritesEachPageToTarget(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_forwards_each_page_to_target_write_data(self):
        source = MagicMock()
        page_a = [{"r": 1}]
        page_b = [{"r": 2}, {"r": 3}]
        source.get_iterator.return_value = iter([page_a, page_b])
        target = MagicMock()
        operation = _build_operation()
        subject, _s, _t = _build_subject(source, target)

        subject.execute(operation_integration=operation, channel=self.channel)

        # Each page routed through write_target_data -> target.write_data.
        self.assertEqual(target.write_data.call_count, 2)
        kwargs_list = [c.kwargs for c in target.write_data.call_args_list]
        self.assertEqual(kwargs_list[0]["source_data"], page_a)
        self.assertEqual(kwargs_list[1]["source_data"], page_b)
        self.assertIs(kwargs_list[0]["integration"], operation.Integration)


class SingleProcessExecutePublishesLogEventsPerPage(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_publishes_two_log_events_per_page(self):
        source = MagicMock()
        source.get_iterator.return_value = iter([[1], [2]])
        target = MagicMock()
        operation = _build_operation()
        subject, _s, _t = _build_subject(source, target)

        subject.execute(operation_integration=operation, channel=self.channel)

        events = _drain(self.channel)
        # two pages * (read-log + write-log) = 4 EVENT_LOG messages.
        self.assertEqual(len(events), 4)
        for ev in events:
            self.assertEqual(ev.event, EVENT_LOG)

    def test_execute_log_messages_include_task_id_start_and_end_markers(self):
        source = MagicMock()
        source.get_iterator.return_value = iter([[1]])
        target = MagicMock()
        operation = _build_operation(limit=5)
        subject, _s, _t = _build_subject(source, target)

        subject.execute(operation_integration=operation, channel=self.channel)

        events = _drain(self.channel)
        read_msg = events[0].kwargs["message"]
        # Format: "0 - data :<task_id>-<start>-<end> readed from db"
        self.assertIn("1-0-5", read_msg)
        self.assertIn("readed from db", read_msg)


class SingleProcessExecuteReraisesAndLogsOnAdapterError(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_reraises_exception_from_source_iterator(self):
        boom = RuntimeError("source exploded")
        source = MagicMock()
        source.get_iterator.side_effect = boom
        target = MagicMock()
        operation = _build_operation()
        subject, _s, _t = _build_subject(source, target)

        with self.assertRaises(RuntimeError) as ctx:
            subject.execute(operation_integration=operation, channel=self.channel)

        self.assertIs(ctx.exception, boom)

    def test_execute_publishes_error_log_with_exception_kwarg(self):
        boom = RuntimeError("source exploded")
        source = MagicMock()
        source.get_iterator.side_effect = boom
        target = MagicMock()
        operation = _build_operation()
        subject, _s, _t = _build_subject(source, target)

        with self.assertRaises(RuntimeError):
            subject.execute(operation_integration=operation, channel=self.channel)

        events = _drain(self.channel)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event, EVENT_LOG)
        self.assertIs(events[0].kwargs["exception"], boom)
        self.assertIs(events[0].kwargs["data"], operation)


class SingleProcessWriteTargetDataDelegatesToAdapter(TestCase):
    def test_write_target_data_calls_adapter_write_data_with_integration_and_source(self):
        subject = SingleProcessIntegrationExecute(
            connection_source_adapter_factory=MagicMock(),
            connection_target_adapter_factory=MagicMock(),
        )
        target = MagicMock(name="target_adapter")
        integration = MagicMock(name="integration")
        data = [{"r": 1}]

        subject.write_target_data(
            target_adapter=target, integration=integration, source_data=data,
        )

        target.write_data.assert_called_once_with(
            integration=integration, source_data=data,
        )
