from time import time

from injector import inject

from ..base import IntegrationExecuteStrategy
from ....connection.factories import ConnectionAdapterFactory
from ....domain.enums.events import EVENT_LOG
from ....operation.domain.operation import OperationIntegrationBase
from ....pubsub.base import ChannelQueue
from ....pubsub.domain import TaskMessage
from ....pubsub.publisher import Publisher
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
            channel: ChannelQueue
    ) -> int:
        publisher = Publisher(channel=channel)
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
                    publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                          kwargs={
                                                              'data': operation_integration,
                                                              'message': f"0 - data :{task_id}-{start}-{end} process got a new task"
                                                          }))
                    source_data = source_adapter.get_source_data_with_paging(
                        integration=integration, start=start, end=end)
                    publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                          kwargs={
                                                              'data': operation_integration,
                                                              'message': f"0 - data :{task_id}-{start}-{end} readed from db"
                                                          }))
                    prepared_data = target_adapter.prepare_data(integration=integration, source_data=source_data)
                    target_adapter.write_target_data(integration=integration, prepared_data=prepared_data)
                    end_time = time()
                    publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                          kwargs={
                                                              'data': operation_integration,
                                                              'message': f"0 - data :{task_id}-{start}-{end} process finished task. time:{end_time - start_time}"
                                                          }))
                    end += limit
                    start += limit
            return data_count
        except Exception as ex:
            publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                  kwargs={'data': operation_integration,
                                                          'message': f"Integration getting error. time:{end_time - start_time}",
                                                          'exception': ex}
                                                  ))
            raise
