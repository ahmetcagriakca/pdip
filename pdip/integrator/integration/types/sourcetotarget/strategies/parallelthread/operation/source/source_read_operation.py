import traceback
from queue import Queue

from injector import inject
from pdip.dependency import IScoped

from pdip.integrator.connection.domain.task import DataQueueTask
from pdip.integrator.connection.factories import ConnectionSourceAdapterFactory
from pdip.integrator.domain.enums.events import EVENT_LOG
from pdip.integrator.operation.domain import OperationIntegrationBase
from pdip.integrator.pubsub.base import ChannelQueue
from pdip.integrator.pubsub.domain import TaskMessage
from pdip.integrator.pubsub.publisher import Publisher


class SourceReadOperation(IScoped):
    @inject
    def __init__(
            self,
            connection_source_adapter_factory: ConnectionSourceAdapterFactory,
    ):
        self.connection_source_adapter_factory = connection_source_adapter_factory

    def start(
            self,
            thread_id,
            channel: ChannelQueue,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ):
        publisher = Publisher(channel=channel)
        publisher.publish(
            message=TaskMessage(
                event=EVENT_LOG,
                kwargs={
                    'data': operation_integration,
                    'message': f"Source data operation started on process. thread_id: {thread_id}"
                }
            )
        )
        try:

            source_adapter = self.connection_source_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.SourceConnections.ConnectionType
            )

            data_count = source_adapter.get_source_data_count(integration=operation_integration.Integration)
            if data_count > 0:
                transmitted_data_count = 0
                limit = operation_integration.Limit
                end = limit
                start = 0
                id = 0
                while True:
                    if end != limit and end - data_count >= limit:
                        break
                    id = id + 1
                    data_queue_task = DataQueueTask(
                        Id=id,
                        Data=None,
                        IsDataFrame=False,
                        Start=start,
                        End=end,
                        Limit=limit,
                        IsFinished=False
                    )
                    data_queue.put(data_queue_task)
                    transmitted_data_count = transmitted_data_count + 1
                    if transmitted_data_count >= operation_integration.ProcessCount:
                        result = data_result_queue.get()
                        if result:
                            transmitted_data_count = transmitted_data_count - 1
                        else:
                            break
                    end += limit
                    start += limit
            for i in range(operation_integration.ProcessCount):
                data_queue_finish_task = DataQueueTask(IsFinished=True)
                data_queue.put(data_queue_finish_task)

            publisher.publish(
                message=TaskMessage(
                    event=EVENT_LOG,
                    kwargs={
                        'data': operation_integration,
                        'message': f"Source data operation finished successfully. thread_id: {thread_id}"
                    }
                )
            )
        except Exception as ex:
            exception_traceback = traceback.format_exc()
            for i in range(operation_integration.ProcessCount):
                data_queue_error_task = DataQueueTask(
                    IsFinished=True,
                    Traceback=exception_traceback,
                    Exception=ex
                )
                data_queue.put(data_queue_error_task)

            publisher.publish(
                message=TaskMessage(
                    event=EVENT_LOG,
                    kwargs={
                        'data': operation_integration,
                        'message': f"Source data operation finished with error. thread_id: {thread_id}.",
                        'exception': ex

                    }
                )
            )
            raise
