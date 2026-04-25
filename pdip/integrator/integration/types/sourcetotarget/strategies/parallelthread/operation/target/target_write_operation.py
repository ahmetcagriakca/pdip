from queue import Queue
from time import time

import pandas as pd
from func_timeout import FunctionTimedOut, func_set_timeout
from injector import inject
from pandas import DataFrame, notnull

from pdip.dependency import IScoped
from pdip.integrator.connection.domain.task import DataQueueTask
from pdip.integrator.connection.factories import ConnectionSourceAdapterFactory, ConnectionTargetAdapterFactory
from pdip.integrator.domain.enums.events import EVENT_LOG
from pdip.integrator.integration.domain.base import IntegrationBase
from pdip.integrator.integration.types.sourcetotarget.strategies.base.span_helpers import (
    attr_name,
    resolve_driver,
)
from pdip.integrator.operation.domain import OperationIntegrationBase
from pdip.integrator.pubsub.base import ChannelQueue
from pdip.integrator.pubsub.domain import TaskMessage
from pdip.integrator.pubsub.publisher import Publisher
from pdip.observability import get_tracer


class TargetWriteOperation(IScoped):
    @inject
    def __init__(
            self,
            connection_source_adapter_factory: ConnectionSourceAdapterFactory,
            connection_target_adapter_factory: ConnectionTargetAdapterFactory
    ):
        self.connection_source_adapter_factory = connection_source_adapter_factory
        self.connection_target_adapter_factory = connection_target_adapter_factory

    def start(
            self,
            thread_id: int,
            channel: ChannelQueue,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ) -> int:
        publisher = Publisher(channel=channel)
        total_row_count = 0
        try:
            while True:
                data_task: DataQueueTask = data_queue.get()
                if data_task.IsFinished:
                    if data_task.Exception is not None:
                        exc = Exception(data_task.Traceback + '\n' + str(data_task.Exception))
                        raise exc
                    publisher.publish(
                        message=TaskMessage(
                            event=EVENT_LOG,
                            kwargs={
                                'data': operation_integration,
                                'message': f"{thread_id} process tasks finished"
                            }
                        )
                    )
                    return total_row_count
                else:
                    start = time()
                    data = data_task.Data
                    if data_task.IsDataFrame and data is not None:
                        source_data_json = data_task.Data
                        data: DataFrame = DataFrame(source_data_json)
                    data_count = 0
                    if data is None:
                        publisher.publish(
                            message=TaskMessage(
                                event=EVENT_LOG,
                                kwargs={
                                    'data': operation_integration,
                                    'message': f"{thread_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process got a new task without data"
                                }
                            )
                        )
                        data_count = self.start_execute_integration_with_paging(
                            integration=operation_integration.Integration,
                            start=data_task.Start,
                            end=data_task.End
                        )
                    elif data is not None and len(data) > 0:
                        if data_task.IsDataFrame and data_task.DataTypes is not None:
                            source_data = data.astype(dtype=data_task.DataTypes)
                        else:
                            source_data = data
                        if data_task.IsDataFrame:
                            source_data = source_data.where(notnull(data), None)
                            source_data = source_data.replace({pd.NaT: None})

                        publisher.publish(
                            message=TaskMessage(
                                event=EVENT_LOG,
                                kwargs={
                                    'data': operation_integration,
                                    'message': f"{thread_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process got a new task"
                                }
                            )
                        )
                        data_count = self.start_execute_integration_with_source_data(
                            integration=operation_integration.Integration,
                            source_data=source_data
                        )
                    else:
                        publisher.publish(
                            message=TaskMessage(
                                event=EVENT_LOG,
                                kwargs={
                                    'data': operation_integration,
                                    'message': f"{thread_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process got an empty task"
                                }
                            )
                        )
                    total_row_count = total_row_count + data_count
                    end = time()
                    publisher.publish(
                        message=TaskMessage(
                            event=EVENT_LOG,
                            kwargs={
                                'data': operation_integration,
                                'message': f"{thread_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process finished task. time:{end - start}"
                            }
                        )
                    )
                    data_task.IsProcessed = True
                    thread_result = True if data_count > 0 else False
                    data_result_queue.put(thread_result)
                data_queue.task_done()
        except FunctionTimedOut as fto:
            data_result_queue.put(False)
            end = time()
            publisher.publish(
                message=TaskMessage(
                    event=EVENT_LOG,
                    kwargs={
                        'data': operation_integration,
                        'message': f"{thread_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process getting error. time:{end - start} - Error {fto.getMsg()}"
                    }
                )
            )
            raise Exception(f'Execution Operation timed out after {fto.timedOutAfter} seconds.')
        except Exception as ex:
            data_result_queue.put(False)
            raise

    def start_execute_integration_with_source_data(self,
                                                   integration: IntegrationBase,
                                                   source_data: any
                                                   ):
        target_adapter = self.connection_target_adapter_factory.get_adapter(
            connection_type=integration.TargetConnections.ConnectionType
        )
        self.write_target_data(
            target_adapter=target_adapter,
            integration=integration,
            source_data=source_data
        )
        return len(source_data)

    def start_execute_integration_with_paging(self,
                                              integration: IntegrationBase,
                                              start,
                                              end
                                              ):
        source_connection_type = integration.SourceConnections.ConnectionType
        source_adapter = self.connection_source_adapter_factory.get_adapter(
            connection_type=source_connection_type
        )
        tracer = get_tracer("pdip.integrator")
        with tracer.start_as_current_span(
                "pdip.integrator.source.read"
        ) as read_span:
            read_span.set_attribute(
                "pdip.connection.type", attr_name(source_connection_type)
            )
            read_span.set_attribute(
                "pdip.connection.driver",
                resolve_driver(integration.SourceConnections),
            )
            read_span.set_attribute("pdip.batch.size", end - start)
            source_data = source_adapter.get_source_data_with_paging(
                integration=integration,
                start=start,
                end=end
            )
        target_adapter = self.connection_target_adapter_factory.get_adapter(
            connection_type=integration.TargetConnections.ConnectionType
        )

        self.write_target_data(
            target_adapter=target_adapter,
            integration=integration,
            source_data=source_data
        )
        return len(source_data)

    @func_set_timeout(1800)
    def write_target_data(
            self,
            target_adapter,
            integration,
            source_data
    ):
        target_connection_type = integration.TargetConnections.ConnectionType
        tracer = get_tracer("pdip.integrator")
        with tracer.start_as_current_span(
                "pdip.integrator.target.write"
        ) as write_span:
            write_span.set_attribute(
                "pdip.connection.type", attr_name(target_connection_type)
            )
            write_span.set_attribute(
                "pdip.connection.driver",
                resolve_driver(integration.TargetConnections),
            )
            write_span.set_attribute(
                "pdip.batch.size",
                len(source_data) if source_data is not None else 0,
            )
            write_span.set_attribute(
                "pdip.rows.written",
                len(source_data) if source_data is not None else 0,
            )
            target_adapter.write_data(integration=integration,
                                      source_data=source_data)
