from time import time

from injector import inject

from ..base import IntegrationExecuteStrategy
from ....connection.factories import ConnectionAdapterFactory
from ....models.enums.events import EVENT_LOG
from ....operation.domain.operation import OperationIntegrationBase
from ....pubsub import EventChannel
from .....dependency import IScoped


class SingleProcessIntegrationExecute(IntegrationExecuteStrategy, IScoped):
    @inject
    def __init__(self,
                 connection_adapter_factory: ConnectionAdapterFactory
                 ):
        self.connection_adapter_factory = connection_adapter_factory

    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            event_channel: EventChannel
    ) -> int:
        try:
            source_adapter = self.connection_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.SourceConnections.ConnectionType)
            target_adapter = self.connection_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.TargetConnections.ConnectionType)
            integration = operation_integration.Integration
            data_count = source_adapter.get_source_data_count(integration=integration)
            if data_count > 0:
                limit = operation_integration.Limit
                end = limit
                start = 0
                id = 0
                while True:
                    if end != limit and end - data_count >= limit:
                        break
                    start_time = time()
                    id = id + 1
                    task_id = id
                    event_channel.publish(
                        event=EVENT_LOG,
                        data=operation_integration,
                        log=f"0 - data :{task_id}-{start}-{end} process got a new task")

                    source_data = source_adapter.get_source_data_with_paging(
                        integration=integration, start=start, end=end)
                    event_channel.publish(
                        event=EVENT_LOG,
                        data=operation_integration,
                        log=f"0 - data :{task_id}-{start}-{end} readed from db")
                    prepared_data = target_adapter.prepare_data(integration=integration, source_data=source_data)
                    target_adapter.write_target_data(integration=integration, prepared_data=prepared_data)
                    end_time = time()
                    event_channel.publish(
                        event=EVENT_LOG,
                        data=operation_integration,
                        log=f"0 - data :{task_id}-{start}-{end} process finished task. time:{end_time - start_time}")
                    end += limit
                    start += limit
            return data_count
        except Exception as ex:
            event_channel.publish(
                event=EVENT_LOG,
                data=operation_integration,
                log=f"Integration getting error.",
                exception=ex)
            raise
