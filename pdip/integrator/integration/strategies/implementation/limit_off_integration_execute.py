from time import time

from func_timeout import func_set_timeout
from injector import inject

from ..base import IntegrationExecuteStrategy
from ....connection.factories import ConnectionAdapterFactory
from ....models.enums.events import EVENT_LOG
from ....operation.domain.operation import OperationIntegrationBase
from ....pubsub import EventChannel
from .....dependency import IScoped


class LimitOffIntegrationExecute(IntegrationExecuteStrategy, IScoped):
    @inject
    def __init__(self,
                 connection_adapter_factory: ConnectionAdapterFactory
                 ):
        self.connection_adapter_factory = connection_adapter_factory

    @func_set_timeout(3600)
    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            event_channel: EventChannel
    ) -> int:
        start_time = time()
        try:
            event_channel.publish(
                event=EVENT_LOG,
                data=operation_integration,
                log=f"0 - process got a new task")
            source_adapter = self.connection_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.SourceConnections.ConnectionType)
            source_data = source_adapter.get_source_data(
                integration=operation_integration.Integration)
            data_count = len(source_data)
            event_channel.publish(
                event=EVENT_LOG,
                data=operation_integration,
                log=f"0 - {data_count} readed from db")
            target_adapter = self.connection_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.TargetConnections.ConnectionType)
            prepared_data = target_adapter.prepare_data(integration=operation_integration.Integration,
                                                        source_data=source_data)
            target_adapter.write_target_data(
                integration=operation_integration.Integration, prepared_data=prepared_data)
            end_time = time()
            event_channel.publish(
                event=EVENT_LOG,
                data=operation_integration,
                log=f"0 - {data_count} process finished task. time:{end_time - start_time}")
            return data_count
        except Exception as ex:
            end_time = time()
            event_channel.publish(
                event=EVENT_LOG,
                data=operation_integration,
                log=f"Integration getting error. time:{end_time - start_time}", exception=ex)
            raise
