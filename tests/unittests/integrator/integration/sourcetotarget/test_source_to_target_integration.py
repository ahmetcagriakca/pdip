"""Unit tests for ``SourceToTargetIntegration`` — the source-to-target
integration adapter.

``SourceToTargetIntegration.execute`` orchestrates:
 1. optional target truncation (publishes ``EVENT_..._TRUNCATE``),
 2. strategy selection via ``IntegrationSourceToTargetExecuteStrategyFactory``,
 3. a single ``EVENT_LOG`` describing the chosen strategy,
 4. the strategy's own execute call,
 5. a final ``EVENT_..._EXECUTE_SOURCE`` with the affected row count.

The message-helper methods return strings built from the
``TargetConnections`` variant of the ``IntegrationBase`` dataclass.
"""

# Stub pandas/func_timeout before any ``pdip.integrator.*`` import.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.domain.enums.events import (  # noqa: E402
    EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE,
    EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
    EVENT_LOG,
)
from pdip.integrator.integration.domain.base import (  # noqa: E402
    IntegrationBase,
    IntegrationConnectionBase,
)
from pdip.integrator.integration.types.base import IntegrationAdapter  # noqa: E402, F401
from pdip.integrator.integration.types.sourcetotarget.base import (  # noqa: E402
    SourceToTargetIntegration,
)
from pdip.integrator.operation.domain import OperationIntegrationBase  # noqa: E402
from pdip.integrator.pubsub.base import ChannelQueue  # noqa: E402


def _build_integration(connection_type="SQL",
                       sql=None, bigdata=None, webservice=None,
                       file=None, queue_=None, is_truncate=False):
    """Build an ``IntegrationBase`` whose ``TargetConnections`` carries
    the selected variant. The ``SourceConnections`` side is irrelevant
    for the target-facing adapter under test."""
    target = IntegrationConnectionBase(
        ConnectionType=connection_type,
        Sql=sql,
        BigData=bigdata,
        WebService=webservice,
        File=file,
        Queue=queue_,
    )
    return IntegrationBase(
        SourceConnections=None,
        TargetConnections=target,
        IsTargetTruncate=is_truncate,
    )


def _build_operation(integration, order=2, process_count=1, limit=100):
    return OperationIntegrationBase(
        Id=1, Name="oi", Order=order, Integration=integration,
        Limit=limit, ProcessCount=process_count,
    )


def _build_subject(target_adapter, strategy):
    """Wire a subject with a stubbed target adapter and strategy."""
    target_factory = MagicMock(name="connection_target_adapter_factory")
    target_factory.get_adapter.return_value = target_adapter

    strategy_factory = MagicMock(name="strategy_factory")
    strategy_factory.get.return_value = strategy

    subject = SourceToTargetIntegration(
        integration_execute_strategy_factory=strategy_factory,
        connection_target_adapter_factory=target_factory,
    )
    return subject, target_factory, strategy_factory


def _drain(channel):
    messages = []
    while True:
        try:
            messages.append(channel.get_nowait())
        except queue.Empty:
            break
    return messages


class SourceToTargetExecuteDelegatesToStrategy(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_returns_affected_row_count_from_strategy(self):
        adapter = MagicMock(name="target_adapter")
        strategy = MagicMock(name="strategy")
        strategy.execute.return_value = 123
        integration = _build_integration(is_truncate=False)
        operation = _build_operation(integration)
        subject, _tf, _sf = _build_subject(adapter, strategy)

        result = subject.execute(operation_integration=operation, channel=self.channel)

        self.assertEqual(result, 123)

    def test_execute_resolves_target_adapter_with_connection_type(self):
        adapter = MagicMock(name="target_adapter")
        strategy = MagicMock(name="strategy", **{"execute.return_value": 0})
        integration = _build_integration(connection_type="BIGDATA")
        operation = _build_operation(integration)
        subject, target_factory, _sf = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        target_factory.get_adapter.assert_called_once_with(connection_type="BIGDATA")

    def test_execute_asks_strategy_factory_for_process_count(self):
        adapter = MagicMock(name="target_adapter")
        strategy = MagicMock(name="strategy", **{"execute.return_value": 0})
        integration = _build_integration()
        operation = _build_operation(integration, process_count=4, limit=50)
        subject, _tf, strategy_factory = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        strategy_factory.get.assert_called_once_with(process_count=4)

    def test_execute_invokes_strategy_with_operation_and_channel(self):
        adapter = MagicMock(name="target_adapter")
        strategy = MagicMock(name="strategy", **{"execute.return_value": 0})
        integration = _build_integration()
        operation = _build_operation(integration)
        subject, _tf, _sf = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        strategy.execute.assert_called_once_with(
            operation_integration=operation, channel=self.channel
        )


class SourceToTargetExecuteTruncatesOnlyWhenFlagSet(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_does_not_clear_target_when_truncate_flag_false(self):
        adapter = MagicMock(name="target_adapter")
        strategy = MagicMock(name="strategy", **{"execute.return_value": 0})
        integration = _build_integration(is_truncate=False)
        operation = _build_operation(integration)
        subject, _tf, _sf = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        adapter.clear_data.assert_not_called()

    def test_execute_clears_target_and_publishes_truncate_event(self):
        adapter = MagicMock(name="target_adapter")
        adapter.clear_data.return_value = 11
        strategy = MagicMock(name="strategy", **{"execute.return_value": 0})
        integration = _build_integration(is_truncate=True)
        operation = _build_operation(integration)
        subject, _tf, _sf = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        adapter.clear_data.assert_called_once_with(integration=integration)
        events = _drain(self.channel)
        # The first event must be the truncate event with the reported
        # affected row count.
        self.assertEqual(events[0].event, EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE)
        self.assertEqual(events[0].kwargs["row_count"], 11)
        self.assertIs(events[0].kwargs["data"], operation)


class SourceToTargetExecutePublishesEventsInOrder(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_event_sequence_without_truncate_is_log_then_execute_source(self):
        adapter = MagicMock(name="target_adapter")
        strategy = MagicMock(name="strategy")
        strategy.execute.return_value = 7
        integration = _build_integration(is_truncate=False)
        operation = _build_operation(integration, order=2, process_count=2, limit=10)
        subject, _tf, _sf = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        events = _drain(self.channel)
        self.assertEqual(
            [m.event for m in events],
            [EVENT_LOG, EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE],
        )
        self.assertEqual(events[-1].kwargs["row_count"], 7)

    def test_event_sequence_with_truncate_is_truncate_log_execute_source(self):
        adapter = MagicMock(name="target_adapter")
        adapter.clear_data.return_value = 4
        strategy = MagicMock(name="strategy")
        strategy.execute.return_value = 9
        integration = _build_integration(is_truncate=True)
        operation = _build_operation(integration)
        subject, _tf, _sf = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        events = _drain(self.channel)
        self.assertEqual(
            [m.event for m in events],
            [
                EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE,
                EVENT_LOG,
                EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE,
            ],
        )

    def test_log_event_mentions_strategy_name_order_process_count_and_limit(self):
        adapter = MagicMock(name="target_adapter")

        class FakeStrategy:  # name surfaces in the log string
            def execute(self, operation_integration, channel):
                return 0

        strategy = FakeStrategy()
        integration = _build_integration(is_truncate=False)
        operation = _build_operation(integration, order=5, process_count=3, limit=25)
        subject, _tf, _sf = _build_subject(adapter, strategy)

        subject.execute(operation_integration=operation, channel=self.channel)

        events = _drain(self.channel)
        log_event = [m for m in events if m.event == EVENT_LOG][0]
        self.assertEqual(
            log_event.kwargs["message"],
            "5 - integration will execute on FakeStrategy. 3-25",
        )


class SourceToTargetStartMessageDependsOnTargetVariant(TestCase):
    def test_start_message_uses_sql_schema_and_object_name(self):
        sql = MagicMock(Schema="S", ObjectName="T")
        integration = _build_integration(sql=sql)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "S.T integration execute started.")

    def test_start_message_uses_bigdata_schema_and_object_name(self):
        bigdata = MagicMock(Schema="BD", ObjectName="BT")
        integration = _build_integration(bigdata=bigdata)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "BD.BT integration execute started.")

    def test_start_message_uses_webservice_method(self):
        webservice = MagicMock(Method="GET")
        integration = _build_integration(webservice=webservice)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "GET integration execute started.")

    def test_start_message_uses_file_folder_and_name(self):
        file = MagicMock(Folder="/out", FileName="b.csv")
        integration = _build_integration(file=file)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "/out\\b.csv integration execute started.")

    def test_start_message_uses_queue_topic(self):
        q = MagicMock(TopicName="topicB")
        integration = _build_integration(queue_=q)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "topicB integration execute started.")

    def test_start_message_is_generic_when_no_variant_set(self):
        integration = _build_integration()
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "Integration execute started.")


class SourceToTargetFinishMessageDependsOnTargetVariant(TestCase):
    def test_finish_message_uses_sql_schema_and_object_name(self):
        sql = MagicMock(Schema="S", ObjectName="T")
        integration = _build_integration(sql=sql)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_finish_message(integration, data_count=2)

        self.assertEqual(message, "S.T integration execute finished.")

    def test_finish_message_uses_bigdata_schema_and_object_name(self):
        bigdata = MagicMock(Schema="BD", ObjectName="BT")
        integration = _build_integration(bigdata=bigdata)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "BD.BT integration execute finished.")

    def test_finish_message_uses_file_folder_and_name(self):
        file = MagicMock(Folder="/out", FileName="b.csv")
        integration = _build_integration(file=file)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "/out\\b.csv integration execute finished.")

    def test_finish_message_uses_queue_topic(self):
        q = MagicMock(TopicName="topicB")
        integration = _build_integration(queue_=q)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "topicB integration execute finished.")

    def test_finish_message_is_generic_when_no_variant_set(self):
        integration = _build_integration()
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "Integration execute finished")


class SourceToTargetErrorMessageDependsOnTargetVariant(TestCase):
    def test_error_message_uses_sql_schema_and_object_name(self):
        sql = MagicMock(Schema="S", ObjectName="T")
        integration = _build_integration(sql=sql)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "S.T integration execute getting error.")

    def test_error_message_uses_bigdata_schema_and_object_name(self):
        bigdata = MagicMock(Schema="BD", ObjectName="BT")
        integration = _build_integration(bigdata=bigdata)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "BD.BT integration execute getting error.")

    def test_error_message_uses_webservice_method(self):
        webservice = MagicMock(Method="PATCH")
        integration = _build_integration(webservice=webservice)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "PATCH integration execute getting error.")

    def test_error_message_uses_file_folder_and_name(self):
        file = MagicMock(Folder="/out", FileName="b.csv")
        integration = _build_integration(file=file)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "/out\\b.csv integration execute getting error.")

    def test_error_message_uses_queue_topic(self):
        q = MagicMock(TopicName="topicB")
        integration = _build_integration(queue_=q)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "topicB integration execute getting error.")

    def test_error_message_is_generic_when_no_variant_set(self):
        integration = _build_integration()
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "Integration execute getting error.")

    def test_error_message_sql_wins_when_webservice_also_set(self):
        # After the if/elif fix, the first matching branch wins —
        # Sql comes before WebService, so a Sql+WebService combo keeps
        # the Sql label.
        sql = MagicMock(Schema="S", ObjectName="T")
        webservice = MagicMock(Method="PATCH")
        integration = _build_integration(sql=sql, webservice=webservice)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "S.T integration execute getting error.")


class SourceToTargetFinishMessageBranchCoverage(TestCase):
    def test_finish_message_uses_webservice_method(self):
        # After the duplicate-BigData fix, the WebService branch uses
        # the WebService method (not the old duplicate BigData guard).
        webservice = MagicMock(Method="GET")
        integration = _build_integration(webservice=webservice)
        subject, _tf, _sf = _build_subject(MagicMock(), MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "GET integration execute finished.")
