from injector import inject

from ..base import IntegrationAdapter
from ...domain.base import IntegrationBase
from ...factories import IntegrationExecuteStrategyFactory
from ....connection.factories import ConnectionAdapterFactory
from ....models.enums.events import EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE, \
    EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE, EVENT_LOG
from ....operation.domain import OperationIntegrationBase
from ....pubsub import EventChannel
from .....dependency import IScoped


class SourceIntegration(IntegrationAdapter, IScoped):
    @inject
    def __init__(self,
                 integration_execute_strategy_factory: IntegrationExecuteStrategyFactory,
                 connection_adapter_factory: ConnectionAdapterFactory
                 ):
        self.connection_adapter_factory = connection_adapter_factory
        self.integration_execute_strategy_factory = integration_execute_strategy_factory

    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            event_channel: EventChannel
    ) -> int:
        target_adapter = self.connection_adapter_factory.get_adapter(
            connection_type=operation_integration.Integration.TargetConnections.ConnectionType)
        if operation_integration.Integration.IsTargetTruncate:
            truncate_affected_row_count = target_adapter.clear_data(integration=operation_integration.Integration)
            event_channel.publish(event=EVENT_EXECUTION_INTEGRATION_EXECUTE_TRUNCATE, data=operation_integration,
                                  row_count=truncate_affected_row_count)
        order = operation_integration.Order
        process_count = operation_integration.ProcessCount
        limit = operation_integration.Limit
        execute_integration_strategy = self.integration_execute_strategy_factory.get(
            limit=limit,
            process_count=process_count)
        strategy_name = type(execute_integration_strategy).__name__
        event_channel.publish(
            event=EVENT_LOG,
            data=operation_integration,
            log=f"{order} - integration will execute on {strategy_name}. {process_count}-{limit}")
        affected_row_count = execute_integration_strategy.execute(
            operation_integration=operation_integration,
            event_channel=event_channel)
        event_channel.publish(
            event=EVENT_EXECUTION_INTEGRATION_EXECUTE_SOURCE,
            data=operation_integration,
            row_count=affected_row_count
        )
        return affected_row_count

    def get_start_message(self, integration: IntegrationBase):
        message = f"Integration execute started."
        if integration.TargetConnections.Sql is not None:
            message = f"{integration.TargetConnections.Sql.Schema}.{integration.TargetConnections.Sql.ObjectName} integration execute started."
        elif integration.TargetConnections.BigData is not None:
            message = f"{integration.TargetConnections.BigData.Schema}.{integration.TargetConnections.BigData.ObjectName} integration execute started."
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
        elif integration.TargetConnections.File is not None:
            message = f"{integration.TargetConnections.File.Folder}\\{integration.TargetConnections.File.FileName} integration execute getting error."
        elif integration.TargetConnections.Queue is not None:
            message = f"{integration.TargetConnections.Queue.TopicName} integration execute getting error."
        return message
