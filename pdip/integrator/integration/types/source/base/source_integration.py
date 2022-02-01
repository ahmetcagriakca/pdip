from injector import inject

from pdip.dependency import IScoped
from pdip.integrator.connection.base import ConnectionSourceAdapterFactory
from pdip.integrator.domain.enums.events import EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE, EVENT_LOG
from pdip.integrator.integration.domain.base import IntegrationBase
from pdip.integrator.operation.domain import OperationIntegrationBase
from pdip.integrator.pubsub.base import ChannelQueue
from pdip.integrator.pubsub.domain import TaskMessage
from pdip.integrator.pubsub.publisher import Publisher
from ...base import IntegrationAdapter


class SourceIntegration(IntegrationAdapter, IScoped):
    @inject
    def __init__(self,
                 connection_source_adapter_factory: ConnectionSourceAdapterFactory
                 ):
        self.connection_adapter_factory = connection_source_adapter_factory

    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            channel: ChannelQueue
    ) -> int:
        publisher = Publisher(channel=channel)
        source_adapter = self.connection_adapter_factory.get_adapter(
            connection_type=operation_integration.Integration.TargetConnections.ConnectionType)
        order = operation_integration.Order
        row_count = source_adapter.get_source_data_count(integration=operation_integration.Integration)

        publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                              kwargs={
                                                  'data': operation_integration,
                                                  'message': f"{order} - source has {row_count}"
                                              }))
        return row_count

    def get_start_message(self, integration: IntegrationBase):
        message = f"Integration execute started."
        if integration.TargetConnections.Sql is not None:
            message = f"{integration.TargetConnections.Sql.Schema}.{integration.TargetConnections.Sql.ObjectName} integration execute started."
        elif integration.TargetConnections.BigData is not None:
            message = f"{integration.TargetConnections.BigData.Schema}.{integration.TargetConnections.BigData.ObjectName} integration execute started."
        elif integration.TargetConnections.WebService is not None:
            message = f"{integration.TargetConnections.WebService.Method} integration execute started."
        elif integration.TargetConnections.File is not None:
            message = f"{integration.TargetConnections.File.Folder}\\{integration.TargetConnections.File.FileName} integration execute started."
        elif integration.TargetConnections.Queue is not None:
            message = f"{integration.TargetConnections.Queue.TopicName} integration execute started."
        return message

    def get_finish_message(self, integration: IntegrationBase, data_count: int):
        message = f"Integration execute finished"
        if integration.TargetConnections.Sql is not None:
            message = f"{integration.TargetConnections.Sql.Schema}.{integration.TargetConnections.Sql.ObjectName} integration execute finished."
        elif integration.TargetConnections.BigData is not None:
            message = f"{integration.TargetConnections.BigData.Schema}.{integration.TargetConnections.BigData.ObjectName} integration execute finished."
        elif integration.TargetConnections.BigData is not None:
            message = f"{integration.TargetConnections.WebService.Method} integration execute finished."
        elif integration.TargetConnections.File is not None:
            message = f"{integration.TargetConnections.File.Folder}\\{integration.TargetConnections.File.FileName} integration execute finished."
        elif integration.TargetConnections.Queue is not None:
            message = f"{integration.TargetConnections.Queue.TopicName} integration execute finished."

        return message

    def get_error_message(self, integration: IntegrationBase):
        message = f"Integration execute getting error."
        if integration.TargetConnections.Sql is not None:
            message = f"{integration.TargetConnections.Sql.Schema}.{integration.TargetConnections.Sql.ObjectName} integration execute getting error."
        elif integration.TargetConnections.BigData is not None:
            message = f"{integration.TargetConnections.BigData.Schema}.{integration.TargetConnections.BigData.ObjectName} integration execute getting error."
        if integration.TargetConnections.WebService is not None:
            message = f"{integration.TargetConnections.WebService.Method} integration execute getting error."
        elif integration.TargetConnections.File is not None:
            message = f"{integration.TargetConnections.File.Folder}\\{integration.TargetConnections.File.FileName} integration execute getting error."
        elif integration.TargetConnections.Queue is not None:
            message = f"{integration.TargetConnections.Queue.TopicName} integration execute getting error."
        return message
