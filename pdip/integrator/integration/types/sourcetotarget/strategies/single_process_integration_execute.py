from time import time

from func_timeout import func_set_timeout
from injector import inject

from ..base import IntegrationSourceToTargetExecuteStrategy
from .....connection.base import ConnectionSourceAdapter, ConnectionTargetAdapter
from .....connection.factories import ConnectionSourceAdapterFactory, ConnectionTargetAdapterFactory
from .....domain.enums.events import EVENT_LOG
from .....operation.domain.operation import OperationIntegrationBase
from .....pubsub.base import ChannelQueue
from .....pubsub.domain import TaskMessage
from .....pubsub.publisher import Publisher
from ......dependency import IScoped


class SingleProcessIntegrationExecute(IntegrationSourceToTargetExecuteStrategy, IScoped):
    @inject
    def __init__(self,
                 connection_source_adapter_factory: ConnectionSourceAdapterFactory,
                 connection_target_adapter_factory: ConnectionTargetAdapterFactory
                 ):
        self.connection_source_adapter_factory = connection_source_adapter_factory
        self.connection_target_adapter_factory = connection_target_adapter_factory

    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            channel: ChannelQueue
    ) -> int:
        publisher = Publisher(channel=channel)
        try:
            source_adapter = self.connection_source_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.SourceConnections.ConnectionType)
            target_adapter = self.connection_target_adapter_factory.get_adapter(
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
                    id = id + 1
                    task_id = id
                    self.start_execute_integration_with_paging(operation_integration=operation_integration,
                                                               source_adapter=source_adapter,
                                                               target_adapter=target_adapter, task_id=task_id,
                                                               start=start, end=end, channel=channel)
                    end += limit
                    start += limit
            return data_count
        except Exception as ex:
            publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                  kwargs={'data': operation_integration,
                                                          'message': f"Integration getting error. ",
                                                          'exception': ex}
                                                  ))
            raise

    @func_set_timeout(1800)
    def start_execute_integration_with_paging(self,
                                              operation_integration: OperationIntegrationBase,
                                              source_adapter: ConnectionSourceAdapter,
                                              target_adapter: ConnectionTargetAdapter,
                                              task_id: int,
                                              start: int,
                                              end: int,
                                              channel: ChannelQueue
                                              ):

        publisher = Publisher(channel=channel)
        start_time = time()
        publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                              kwargs={
                                                  'data': operation_integration,
                                                  'message': f"0 - data :{task_id}-{start}-{end} process got a new task"
                                              }))
        source_data = source_adapter.get_source_data_with_paging(
            integration=operation_integration.Integration, start=start, end=end)
        publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                              kwargs={
                                                  'data': operation_integration,
                                                  'message': f"0 - data :{task_id}-{start}-{end} readed from db"
                                              }))
        prepared_data = target_adapter.prepare_data(integration=operation_integration.Integration,
                                                    source_data=source_data)
        target_adapter.write_target_data(integration=operation_integration.Integration, prepared_data=prepared_data)
        end_time = time()
        publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                              kwargs={
                                                  'data': operation_integration,
                                                  'message': f"0 - data :{task_id}-{start}-{end} process finished task. time:{end_time - start_time}"
                                              }))
        return len(source_data)
