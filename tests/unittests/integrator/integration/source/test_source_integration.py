"""Unit tests for ``SourceIntegration`` — the source-only integration
adapter.

``SourceIntegration.execute`` resolves a source adapter from a factory,
asks it for the source row count, and publishes a single ``EVENT_LOG``
message onto the channel. The ``get_*_message`` helpers format a
human-readable label from the ``SourceConnections`` variant of the
``IntegrationBase`` dataclass. All collaborators below the public
surface (factory, adapter, channel) are mocked at the boundary.
"""

# Stub pandas/func_timeout before any ``pdip.integrator.*`` import.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.domain.enums.events import EVENT_LOG  # noqa: E402
from pdip.integrator.integration.domain.base import (  # noqa: E402
    IntegrationBase,
    IntegrationConnectionBase,
)
from pdip.integrator.integration.types.base import IntegrationAdapter  # noqa: E402, F401
from pdip.integrator.integration.types.source.base import SourceIntegration  # noqa: E402
from pdip.integrator.operation.domain import OperationIntegrationBase  # noqa: E402
from pdip.integrator.pubsub.base import ChannelQueue  # noqa: E402


def _build_integration(connection_type="SQL",
                       sql=None, bigdata=None, webservice=None,
                       file=None, queue_=None, is_truncate=False):
    """Factory for an ``IntegrationBase`` with only its
    ``SourceConnections`` populated — targets are irrelevant for
    the source-only adapter."""
    source = IntegrationConnectionBase(
        ConnectionType=connection_type,
        Sql=sql,
        BigData=bigdata,
        WebService=webservice,
        File=file,
        Queue=queue_,
    )
    return IntegrationBase(
        SourceConnections=source,
        TargetConnections=None,
        IsTargetTruncate=is_truncate,
    )


def _build_operation(integration, order=3):
    return OperationIntegrationBase(
        Id=1, Name="oi", Order=order, Integration=integration,
    )


def _build_subject(adapter, connection_type="SQL"):
    """Return ``(subject, factory, adapter)`` wired so that the subject's
    ``ConnectionSourceAdapterFactory`` returns ``adapter``."""
    factory = MagicMock(name="connection_source_adapter_factory")
    factory.get_adapter.return_value = adapter
    subject = SourceIntegration(connection_source_adapter_factory=factory)
    return subject, factory


class SourceIntegrationExecutePublishesLogAndReturnsCount(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_execute_returns_source_row_count_from_adapter(self):
        adapter = MagicMock(name="source_adapter")
        adapter.get_source_data_count.return_value = 77
        integration = _build_integration(connection_type="SQL")
        operation = _build_operation(integration, order=5)
        subject, _factory = _build_subject(adapter)

        result = subject.execute(operation_integration=operation, channel=self.channel)

        self.assertEqual(result, 77)

    def test_execute_resolves_adapter_with_source_connection_type(self):
        adapter = MagicMock(name="source_adapter")
        adapter.get_source_data_count.return_value = 0
        integration = _build_integration(connection_type="BIGDATA")
        operation = _build_operation(integration)
        subject, factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        factory.get_adapter.assert_called_once_with(connection_type="BIGDATA")

    def test_execute_asks_adapter_for_source_count_with_integration(self):
        adapter = MagicMock(name="source_adapter")
        adapter.get_source_data_count.return_value = 3
        integration = _build_integration(connection_type="SQL")
        operation = _build_operation(integration)
        subject, _factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        adapter.get_source_data_count.assert_called_once_with(integration=integration)

    def test_execute_publishes_single_event_log_with_order_and_count(self):
        adapter = MagicMock(name="source_adapter")
        adapter.get_source_data_count.return_value = 9
        integration = _build_integration(connection_type="SQL")
        operation = _build_operation(integration, order=4)
        subject, _factory = _build_subject(adapter)

        subject.execute(operation_integration=operation, channel=self.channel)

        # Drain the channel and pin down exactly one EVENT_LOG message
        # with the order and row count baked into its text.
        messages = []
        while True:
            try:
                messages.append(self.channel.get_nowait())
            except queue.Empty:
                break
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].event, EVENT_LOG)
        self.assertIs(messages[0].kwargs["data"], operation)
        self.assertEqual(messages[0].kwargs["message"], "4 - source has 9")


class SourceIntegrationStartMessageDependsOnConnectionVariant(TestCase):
    def test_start_message_uses_sql_schema_and_object_name(self):
        sql = MagicMock(Schema="S1", ObjectName="T1")
        integration = _build_integration(sql=sql)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "S1.T1 integration execute started.")

    def test_start_message_uses_bigdata_schema_when_bigdata_present(self):
        bigdata = MagicMock(Schema="BD", ObjectName="BT")
        integration = _build_integration(bigdata=bigdata)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "BD.BT integration execute started.")

    def test_start_message_uses_webservice_method(self):
        webservice = MagicMock(Method="POST")
        integration = _build_integration(webservice=webservice)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "POST integration execute started.")

    def test_start_message_uses_file_folder_and_name(self):
        file = MagicMock(Folder="/in", FileName="a.csv")
        integration = _build_integration(file=file)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "/in\\a.csv integration execute started.")

    def test_start_message_uses_queue_topic(self):
        q = MagicMock(TopicName="topicA")
        integration = _build_integration(queue_=q)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "topicA integration execute started.")

    def test_start_message_is_generic_when_no_variant_set(self):
        integration = _build_integration()
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_start_message(integration)

        self.assertEqual(message, "Integration execute started.")


class SourceIntegrationFinishMessageDependsOnConnectionVariant(TestCase):
    def test_finish_message_uses_sql_schema_and_object_name(self):
        sql = MagicMock(Schema="S1", ObjectName="T1")
        integration = _build_integration(sql=sql)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_finish_message(integration, data_count=5)

        self.assertEqual(message, "S1.T1 integration execute finished.")

    def test_finish_message_uses_bigdata_schema_when_bigdata_present(self):
        bigdata = MagicMock(Schema="BD", ObjectName="BT")
        integration = _build_integration(bigdata=bigdata)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "BD.BT integration execute finished.")

    def test_finish_message_uses_file_folder_and_name(self):
        file = MagicMock(Folder="/in", FileName="a.csv")
        integration = _build_integration(file=file)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "/in\\a.csv integration execute finished.")

    def test_finish_message_uses_queue_topic(self):
        q = MagicMock(TopicName="topicA")
        integration = _build_integration(queue_=q)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "topicA integration execute finished.")

    def test_finish_message_is_generic_when_no_variant_set(self):
        integration = _build_integration()
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_finish_message(integration, data_count=0)

        self.assertEqual(message, "Integration execute finished")


class SourceIntegrationErrorMessageDependsOnConnectionVariant(TestCase):
    def test_error_message_uses_sql_schema_and_object_name(self):
        # The branch order here lets WebService override a Sql-only
        # setup (see the bug note): Sql alone keeps the Sql label.
        sql = MagicMock(Schema="S1", ObjectName="T1")
        integration = _build_integration(sql=sql)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "S1.T1 integration execute getting error.")

    def test_error_message_uses_file_folder_and_name(self):
        file = MagicMock(Folder="/in", FileName="a.csv")
        integration = _build_integration(file=file)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "/in\\a.csv integration execute getting error.")

    def test_error_message_uses_queue_topic(self):
        q = MagicMock(TopicName="topicA")
        integration = _build_integration(queue_=q)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "topicA integration execute getting error.")

    def test_error_message_is_generic_when_no_variant_set(self):
        integration = _build_integration()
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "Integration execute getting error.")

    def test_error_message_webservice_wins_when_set_alongside_sql(self):
        # The production code uses a separate ``if`` (not ``elif``) for
        # the WebService branch, so WebService can override an earlier
        # Sql match. Pin this behaviour down — see the notes at the end
        # of the PR description about the likely bug here.
        sql = MagicMock(Schema="S1", ObjectName="T1")
        webservice = MagicMock(Method="PUT")
        integration = _build_integration(sql=sql, webservice=webservice)
        subject, _factory = _build_subject(MagicMock())

        message = subject.get_error_message(integration)

        self.assertEqual(message, "PUT integration execute getting error.")
