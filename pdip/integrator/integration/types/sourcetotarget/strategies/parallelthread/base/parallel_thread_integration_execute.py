import multiprocessing
from queue import Queue

from injector import inject

from ..operation.source import SourceReadOperation
from ..operation.target import TargetWriteOperation
from ..threading.base import ParallelSessionBroker
from ...base import IntegrationSourceToTargetExecuteStrategy
from .......connection.factories import ConnectionSourceAdapterFactory, ConnectionTargetAdapterFactory
from .......domain.enums.events import EVENT_LOG
from .......operation.domain import OperationIntegrationBase
from .......pubsub.base import ChannelQueue
from .......pubsub.domain import TaskMessage
from .......pubsub.publisher import Publisher
from ........dependency import IScoped
from ........dependency.container import DependencyContainer


class ParallelThreadIntegrationExecute(IntegrationSourceToTargetExecuteStrategy, IScoped):
    @inject
    def __init__(
            self,
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
            try:
                manager = multiprocessing.Manager()
                source_data_process_manager = ParallelSessionBroker(channel=channel,
                                                                    operation_integration=operation_integration)
                execute_data_process_manager = ParallelSessionBroker(channel=channel,
                                                                     operation_integration=operation_integration)
                data_queue = manager.Queue()
                data_result_queue = manager.Queue()

                self.start_source_data_subprocess(
                    source_data_process_manager=source_data_process_manager,
                    channel=channel,
                    operation_integration=operation_integration,
                    data_queue=data_queue,
                    data_result_queue=data_result_queue
                )

                publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': operation_integration,
                            'message': f"Source data process started"
                        }
                    )
                )

                publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': operation_integration,
                            'message': f"Execute data process will start"
                        }
                    )
                )
                total_row_count = self.start_execute_data_subprocess(
                    execute_data_process_manager=execute_data_process_manager,
                    channel=channel,
                    operation_integration=operation_integration,
                    data_queue=data_queue,
                    data_result_queue=data_result_queue
                )

                publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': operation_integration,
                            'message': f"Execute data process finished"
                        }
                    )
                )
            finally:
                manager.shutdown()
                del source_data_process_manager
                del execute_data_process_manager

            return total_row_count
        except Exception as ex:
            publisher.publish(
                message=TaskMessage(
                    event=EVENT_LOG,
                    kwargs={
                        'data': operation_integration,
                        'message': f"Integration getting error.",
                        'exception': ex
                    }
                )
            )
            raise

    def start_source_data_subprocess(
            self,
            source_data_process_manager: ParallelSessionBroker,
            channel: ChannelQueue,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ):
        source_data_kwargs = {
            "operation_integration": operation_integration,
            "channel": channel,
            "data_queue": data_queue,
            "data_result_queue": data_result_queue,
        }

        source_data_process_manager.start(
            process_count=1,
            target_method=self.start_source_data_process,
            target_kwargs=source_data_kwargs
        )

    def start_execute_data_subprocess(
            self,
            execute_data_process_manager: ParallelSessionBroker,
            channel: ChannelQueue,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ) -> int:
        total_row_count = 0
        execute_data_kwargs = {
            "channel": channel,
            "operation_integration": operation_integration,
            "data_queue": data_queue,
            "data_result_queue": data_result_queue,
        }
        execute_data_process_manager.start(
            process_count=operation_integration.ProcessCount,
            target_method=self.start_execute_data_process,
            target_kwargs=execute_data_kwargs
        )
        execute_data_process_results = execute_data_process_manager.get_results()
        for result in execute_data_process_results:
            if result.Exception is not None:
                raise result.Exception
            if result.Result is not None:
                total_row_count = total_row_count + result.Result
        return total_row_count

    @staticmethod
    def start_source_data_process(
            thread_id,
            channel: ChannelQueue,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ):
        return DependencyContainer.Instance.get(SourceReadOperation).start(
            thread_id=thread_id,
            channel=channel,
            operation_integration=operation_integration,
            data_queue=data_queue,
            data_result_queue=data_result_queue,
        )

    @staticmethod
    def start_execute_data_process(
            thread_id,
            channel: ChannelQueue,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ) -> int:
        return DependencyContainer.Instance.get(TargetWriteOperation).start(
            thread_id=thread_id,
            channel=channel,
            operation_integration=operation_integration,
            data_queue=data_queue,
            data_result_queue=data_result_queue,
        )
