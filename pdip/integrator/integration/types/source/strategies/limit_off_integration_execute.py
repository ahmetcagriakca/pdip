from time import time

from func_timeout import func_set_timeout
from injector import inject

from ..base import IntegrationExecuteStrategy
from ....connection.factories import ConnectionAdapterFactory
from ....domain.enums.events import EVENT_LOG
from ....operation.domain.operation import OperationIntegrationBase
from ....pubsub.base import ChannelQueue
from ....pubsub.domain import TaskMessage
from ....pubsub.publisher import Publisher
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
            channel: ChannelQueue
    ) -> int:
        publisher = Publisher(channel=channel)
        start_time = time()
        try:
            publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                  kwargs={
                                                      'data': operation_integration,
                                                      'message': f"0 - process got a new task"
                                                  }))
            source_adapter = self.connection_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.SourceConnections.ConnectionType)
            source_data = source_adapter.get_source_data(
                integration=operation_integration.Integration)
            data_count = len(source_data)

            publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                  kwargs={
                                                      'data': operation_integration,
                                                      'message': f"0 - {data_count} readed from db"
                                                  }))
            target_adapter = self.connection_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.TargetConnections.ConnectionType)
            prepared_data = target_adapter.prepare_data(integration=operation_integration.Integration,
                                                        source_data=source_data)
            target_adapter.write_target_data(
                integration=operation_integration.Integration, prepared_data=prepared_data)
            end_time = time()
            publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                  kwargs={
                                                      'data': operation_integration,
                                                      'message': f"0 - {data_count} process finished task. time:{end_time - start_time}"
                                                  }))
            return data_count
        except Exception as ex:
            end_time = time()
            publisher.publish(message=TaskMessage(event=EVENT_LOG,
                                                  kwargs={'data': operation_integration,
                                                          'message': f"Integration getting error. time:{end_time - start_time}",
                                                          'exception': ex}
                                                  ))
            raise
