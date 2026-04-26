"""Unit tests for ``ParallelIntegrationExecute`` — the multiprocessing
source-to-target strategy ("parallelold").

These tests target the ADR-0033 §3 adapter-call-site span
instrumentation that the strategy emits at three call sites:

* ``start_source_data_operation`` — wraps the
  ``source_adapter.get_source_data_count`` call in a
  ``pdip.integrator.source.read`` span,
* ``start_execute_integration_with_source_data`` — wraps the
  ``target_adapter.write_data`` call in a
  ``pdip.integrator.target.write`` span,
* ``start_execute_integration_with_paging`` — wraps the
  ``source_adapter.get_source_data_with_paging`` call in a
  ``pdip.integrator.source.read`` span and the subsequent
  ``target_adapter.write_data`` call in a
  ``pdip.integrator.target.write`` span.

The strategy is otherwise covered by the integration-tests suite
because the orchestration paths boot ``multiprocessing.Manager`` /
``ProcessManager`` and require a real broker — see
``.coveragerc`` ``omit`` list. The span call sites do not require
any of that machinery and so are exercised here as plain unit
tests with mocked factories and a recording tracer.
"""

# Stub pandas/func_timeout before any ``pdip.integrator.*`` import.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock, patch  # noqa: E402

from pdip.integrator.integration.types.sourcetotarget.strategies.parallelold.base.parallel_integration_execute import (  # noqa: E402
    ParallelIntegrationExecute,
)
from pdip.integrator.pubsub.base import ChannelQueue  # noqa: E402


_MODULE_PATH = (
    "pdip.integrator.integration.types.sourcetotarget"
    ".strategies.parallelold.base"
    ".parallel_integration_execute.get_tracer"
)


class _SpanRecorder:
    def __init__(self):
        self.attributes = {}
        self.entered = 0
        self.exited = 0

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self.exited += 1
        return False

    def set_attribute(self, key, value):
        self.attributes[key] = value


class _TracerRecorder:
    def __init__(self):
        self.spans = []

    def start_as_current_span(self, name):
        span = _SpanRecorder()
        span.name = name
        self.spans.append(span)
        return span


def _build_subject(source_adapter=None, target_adapter=None):
    source_factory = MagicMock(name="source_factory")
    source_factory.get_adapter.return_value = (
        source_adapter if source_adapter is not None else MagicMock()
    )
    target_factory = MagicMock(name="target_factory")
    target_factory.get_adapter.return_value = (
        target_adapter if target_adapter is not None else MagicMock()
    )
    process_manager_factory = MagicMock(name="process_manager_factory")
    subject = ParallelIntegrationExecute(
        process_manager_factory=process_manager_factory,
        connection_source_adapter_factory=source_factory,
        connection_target_adapter_factory=target_factory,
    )
    return subject


def _build_operation(source_type="SQL", limit=10, process_count=1, data_count=0):
    operation = MagicMock(name="operation_integration")
    operation.Limit = limit
    operation.ProcessCount = process_count
    operation.Integration.SourceConnections.ConnectionType = source_type
    return operation


def _build_integration(source_type="SQL", target_type="SQL"):
    integration = MagicMock(name="integration")
    integration.SourceConnections.ConnectionType = source_type
    integration.TargetConnections.ConnectionType = target_type
    return integration


class StartSourceDataOperationEmitsSourceReadSpan(TestCase):
    """``start_source_data_operation`` opens one
    ``pdip.integrator.source.read`` span around ``get_source_data_count``.
    """

    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def _run(self, source, operation, data_queue=None, data_result_queue=None):
        subject = _build_subject(source_adapter=source)
        tracer = _TracerRecorder()
        # ``start_source_data_operation`` is wrapped by
        # ``@transactionhandler``, which calls
        # ``DependencyContainer.Instance.get(RepositoryProvider)`` for
        # commit/rollback/close. Replace the global container with a
        # mock so the decorator does not need a live DI graph.
        fake_container = MagicMock(name="dependency_container")
        with patch(
            "pdip.data.decorators.transaction_handler.DependencyContainer.Instance",
            fake_container,
        ), patch(_MODULE_PATH, return_value=tracer):
            subject.start_source_data_operation(
                sub_process_id=0,
                channel=self.channel,
                operation_integration=operation,
                data_queue=data_queue if data_queue is not None else queue.Queue(),
                data_result_queue=data_result_queue
                if data_result_queue is not None
                else queue.Queue(),
            )
        return tracer

    def test_opens_pdip_integrator_source_read_span_around_get_source_data_count(self):
        source = MagicMock(name="source_adapter")
        source.get_source_data_count.return_value = 0
        operation = _build_operation(source_type="SQL", limit=25, process_count=1)

        tracer = self._run(source, operation)

        read_spans = [s for s in tracer.spans if s.name == "pdip.integrator.source.read"]
        self.assertEqual(len(read_spans), 1)
        span = read_spans[0]
        self.assertEqual(span.entered, 1)
        self.assertEqual(span.exited, 1)
        self.assertEqual(span.attributes.get("pdip.connection.type"), "SQL")
        self.assertEqual(span.attributes.get("pdip.batch.size"), 25)
        # Best-effort driver — MagicMock chain falls back to "".
        self.assertEqual(span.attributes.get("pdip.connection.driver"), "")
        source.get_source_data_count.assert_called_once_with(
            integration=operation.Integration
        )

    def test_batch_size_is_zero_when_limit_is_none(self):
        source = MagicMock(name="source_adapter")
        source.get_source_data_count.return_value = 0
        operation = _build_operation(source_type="SQL", limit=None, process_count=1)

        tracer = self._run(source, operation)

        span = [s for s in tracer.spans if s.name == "pdip.integrator.source.read"][0]
        self.assertEqual(span.attributes.get("pdip.batch.size"), 0)

    def test_resolves_driver_from_sql_connector_type_when_present(self):
        from pdip.integrator.connection.domain.enums import (
            ConnectionTypes,
            ConnectorTypes,
        )

        source = MagicMock(name="source_adapter")
        source.get_source_data_count.return_value = 0
        operation = MagicMock(name="operation_integration")
        operation.Limit = 5
        operation.ProcessCount = 1
        operation.Integration.SourceConnections.ConnectionType = ConnectionTypes.Sql
        operation.Integration.SourceConnections.Sql.Connection.ConnectorType = (
            ConnectorTypes.POSTGRESQL
        )
        operation.Integration.SourceConnections.BigData = None
        operation.Integration.SourceConnections.WebService = None

        tracer = self._run(source, operation)

        span = [s for s in tracer.spans if s.name == "pdip.integrator.source.read"][0]
        self.assertEqual(span.attributes.get("pdip.connection.type"), "Sql")
        self.assertEqual(span.attributes.get("pdip.connection.driver"), "POSTGRESQL")


class StartExecuteIntegrationWithSourceDataEmitsTargetWriteSpan(TestCase):
    """``start_execute_integration_with_source_data`` opens one
    ``pdip.integrator.target.write`` span around ``write_data``.
    """

    def test_opens_target_write_span_with_rows_written_matching_source_data_length(self):
        target = MagicMock(name="target_adapter")
        subject = _build_subject(target_adapter=target)
        integration = _build_integration(target_type="QUEUE")
        source_data = [1, 2, 3, 4]

        tracer = _TracerRecorder()
        with patch(_MODULE_PATH, return_value=tracer):
            result = subject.start_execute_integration_with_source_data(
                integration=integration,
                source_data=source_data,
            )

        self.assertEqual(result, 4)
        write_spans = [
            s for s in tracer.spans if s.name == "pdip.integrator.target.write"
        ]
        self.assertEqual(len(write_spans), 1)
        span = write_spans[0]
        self.assertEqual(span.entered, 1)
        self.assertEqual(span.exited, 1)
        self.assertEqual(span.attributes.get("pdip.connection.type"), "QUEUE")
        self.assertEqual(span.attributes.get("pdip.connection.driver"), "")
        self.assertEqual(span.attributes.get("pdip.batch.size"), 4)
        self.assertEqual(span.attributes.get("pdip.rows.written"), 4)
        target.write_data.assert_called_once_with(
            integration=integration, source_data=source_data
        )

    def test_resolves_driver_from_target_connector_type_when_present(self):
        from pdip.integrator.connection.domain.enums import (
            ConnectionTypes,
            ConnectorTypes,
        )

        target = MagicMock(name="target_adapter")
        subject = _build_subject(target_adapter=target)
        integration = MagicMock(name="integration")
        integration.TargetConnections.ConnectionType = ConnectionTypes.Sql
        integration.TargetConnections.Sql.Connection.ConnectorType = (
            ConnectorTypes.MYSQL
        )
        integration.TargetConnections.BigData = None
        integration.TargetConnections.WebService = None

        tracer = _TracerRecorder()
        with patch(_MODULE_PATH, return_value=tracer):
            subject.start_execute_integration_with_source_data(
                integration=integration,
                source_data=[1, 2],
            )

        span = [
            s for s in tracer.spans if s.name == "pdip.integrator.target.write"
        ][0]
        self.assertEqual(span.attributes.get("pdip.connection.driver"), "MYSQL")


class StartExecuteIntegrationWithPagingEmitsBothSpans(TestCase):
    """``start_execute_integration_with_paging`` opens a
    ``pdip.integrator.source.read`` span around the paged read and a
    ``pdip.integrator.target.write`` span around the subsequent write.
    """

    def test_opens_source_read_then_target_write_in_order(self):
        source = MagicMock(name="source_adapter")
        source.get_source_data_with_paging.return_value = [1, 2, 3]
        target = MagicMock(name="target_adapter")
        subject = _build_subject(source_adapter=source, target_adapter=target)
        integration = _build_integration(source_type="SQL", target_type="SQL")

        tracer = _TracerRecorder()
        with patch(_MODULE_PATH, return_value=tracer):
            result = subject.start_execute_integration_with_paging(
                integration=integration, start=10, end=40
            )

        self.assertEqual(result, 3)
        # Span ordering matters: read first, then write.
        names = [s.name for s in tracer.spans]
        self.assertEqual(
            names,
            ["pdip.integrator.source.read", "pdip.integrator.target.write"],
        )

    def test_source_read_span_carries_paging_window_as_batch_size(self):
        source = MagicMock(name="source_adapter")
        source.get_source_data_with_paging.return_value = []
        target = MagicMock(name="target_adapter")
        subject = _build_subject(source_adapter=source, target_adapter=target)
        integration = _build_integration(source_type="SQL", target_type="SQL")

        tracer = _TracerRecorder()
        with patch(_MODULE_PATH, return_value=tracer):
            subject.start_execute_integration_with_paging(
                integration=integration, start=20, end=70
            )

        read_span = [
            s for s in tracer.spans if s.name == "pdip.integrator.source.read"
        ][0]
        # batch.size mirrors the paging window (end - start) per the
        # parallelthread reference implementation.
        self.assertEqual(read_span.attributes.get("pdip.batch.size"), 50)
        self.assertEqual(read_span.attributes.get("pdip.connection.type"), "SQL")
        self.assertEqual(read_span.attributes.get("pdip.connection.driver"), "")

    def test_target_write_span_records_rows_written_from_returned_page(self):
        source = MagicMock(name="source_adapter")
        source.get_source_data_with_paging.return_value = [1, 2]
        target = MagicMock(name="target_adapter")
        subject = _build_subject(source_adapter=source, target_adapter=target)
        integration = _build_integration(source_type="SQL", target_type="QUEUE")

        tracer = _TracerRecorder()
        with patch(_MODULE_PATH, return_value=tracer):
            subject.start_execute_integration_with_paging(
                integration=integration, start=0, end=10
            )

        write_span = [
            s for s in tracer.spans if s.name == "pdip.integrator.target.write"
        ][0]
        self.assertEqual(write_span.attributes.get("pdip.connection.type"), "QUEUE")
        self.assertEqual(write_span.attributes.get("pdip.batch.size"), 2)
        self.assertEqual(write_span.attributes.get("pdip.rows.written"), 2)
        target.write_data.assert_called_once_with(
            integration=integration, source_data=[1, 2]
        )
