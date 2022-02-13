from func_timeout import func_set_timeout
from injector import inject

from ...base import IntegrationSourceToTargetExecuteStrategy
from .......connection.factories import ConnectionSourceAdapterFactory, ConnectionTargetAdapterFactory
from .......domain.enums.events import EVENT_LOG
from .......operation.domain.operation import OperationIntegrationBase
from .......pubsub.base import ChannelQueue
from .......pubsub.domain import TaskMessage
from .......pubsub.publisher import Publisher
from ........dependency import IScoped


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
                connection_type=operation_integration.Integration.SourceConnections.ConnectionType
            )
            target_adapter = self.connection_target_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.TargetConnections.ConnectionType
            )
            integration = operation_integration.Integration
            limit = operation_integration.Limit
            iterator = source_adapter.get_iterator(
                integration=integration,
                limit=limit
            )

            task_id = 0
            start = 0
            data_count = 0
            end = limit
            for results in iterator:
                task_id += 1
                data_length = len(results)
                publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': operation_integration,
                            'message': f"0 - data :{task_id}-{start}-{end} readed from db"
                        }
                    )
                )
                self.write_target_data(
                    target_adapter=target_adapter,
                    integration=operation_integration.Integration,
                    source_data=results
                )
                publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': operation_integration,
                            'message': f"0 - data :{task_id}-{start}-{end} process finished task. "
                        }
                    )
                )
                data_count += data_length
                end += limit
                start += limit

            return data_count
        except Exception as ex:
            publisher.publish(
                message=TaskMessage(
                    event=EVENT_LOG,
                    kwargs={
                        'data': operation_integration,
                        'message': f"Integration getting error. ",
                        'exception': ex
                    }
                )
            )
            raise

    @func_set_timeout(1800)
    def write_target_data(
            self,
            target_adapter,
            integration,
            source_data
    ):
        target_adapter.write_data(integration=integration,
                                  source_data=source_data)
