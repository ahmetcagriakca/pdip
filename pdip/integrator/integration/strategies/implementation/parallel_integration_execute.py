import multiprocessing
import traceback
from queue import Queue
from time import time

import pandas as pd
from func_timeout import FunctionTimedOut, func_set_timeout
from injector import inject
from pandas import DataFrame, notnull

from ..base import IntegrationExecuteStrategy
from ...domain.base import IntegrationBase
from ....connection.domain.task import DataQueueTask
from ....connection.factories import ConnectionAdapterFactory
from ....models.enums.events import EVENT_LOG
from ....operation.domain import OperationIntegrationBase
from ....pubsub import EventChannel
from .....data.decorators import transactionhandler
from .....dependency import IScoped
from .....dependency.container import DependencyContainer
from .....logging.loggers.database import SqlLogger
from .....processing import ProcessManager
from .....processing.factories import ProcessManagerFactory


class ParallelIntegrationExecute(IntegrationExecuteStrategy, IScoped):
    @inject
    def __init__(
            self,
            logger: SqlLogger,
            process_manager_factory: ProcessManagerFactory,
            connection_adapter_factory: ConnectionAdapterFactory
    ):
        self.process_manager_factory = process_manager_factory
        self.logger = logger
        self.connection_adapter_factory = connection_adapter_factory

    def execute(
            self,
            operation_integration: OperationIntegrationBase,
            event_channel: EventChannel
    ) -> int:
        try:
            try:
                manager = multiprocessing.Manager()
                source_data_process_manager = self.process_manager_factory.get()
                execute_data_process_manager = self.process_manager_factory.get()
                data_queue = manager.Queue()
                data_result_queue = manager.Queue()

                event_channel.publish(
                    event=EVENT_LOG,
                    data=operation_integration,
                    log=f"Source data process will start")
                self.start_source_data_subprocess(source_data_process_manager=source_data_process_manager,
                                                  operation_integration=operation_integration,
                                                  data_queue=data_queue,
                                                  data_result_queue=data_result_queue)

                event_channel.publish(
                    event=EVENT_LOG,
                    data=operation_integration,
                    log=f"Source data process started")

                event_channel.publish(
                    event=EVENT_LOG,
                    data=operation_integration,
                    log=f"Execute data process will start")
                total_row_count = self.start_execute_data_subprocess(
                    execute_data_process_manager=execute_data_process_manager,
                    operation_integration=operation_integration,
                    data_queue=data_queue,
                    data_result_queue=data_result_queue)

                event_channel.publish(
                    event=EVENT_LOG,
                    data=operation_integration,
                    log=f"Execute data process finished")
            finally:
                manager.shutdown()
                del source_data_process_manager
                del execute_data_process_manager

            return total_row_count
        except Exception as ex:
            event_channel.publish(
                event=EVENT_LOG,
                data=operation_integration,
                log=f"Integration getting error.",
                exception=ex)
            raise

    def start_source_data_subprocess(
            self,
            source_data_process_manager: ProcessManager,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ):

        source_data_kwargs = {
            "operation_integration": operation_integration,
            "data_queue": data_queue,
            "data_result_queue": data_result_queue,
        }

        source_data_process_manager.start_processes(
            process_count=1,
            target_method=self.start_source_data_process,
            kwargs=source_data_kwargs)

    def start_execute_data_subprocess(
            self,
            execute_data_process_manager: ProcessManager,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ) -> int:
        total_row_count = 0
        execute_data_kwargs = {
            "operation_integration": operation_integration,
            "data_queue": data_queue,
            "data_result_queue": data_result_queue,
        }
        execute_data_process_manager.start_processes(
            process_count=operation_integration.ProcessCount,
            target_method=self.start_execute_data_process,
            kwargs=execute_data_kwargs)
        execute_data_process_results = execute_data_process_manager.get_results()
        for result in execute_data_process_results:
            if result.Exception is not None:
                raise result.Exception
            if result.Result is not None:
                total_row_count = total_row_count + result.Result
        return total_row_count

    @staticmethod
    def start_source_data_process(
            sub_process_id,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ):

        return DependencyContainer.Instance.get(ParallelIntegrationExecute).start_source_data_operation(
            sub_process_id=sub_process_id,
            operation_integration=operation_integration,
            data_queue=data_queue,
            data_result_queue=data_result_queue,
        )

    @transactionhandler
    def start_source_data_operation(
            self,
            sub_process_id,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ):
        self.logger.info(f"Source data operation started on process. SubProcessId: {sub_process_id}")
        try:

            source_adapter = self.connection_adapter_factory.get_adapter(
                connection_type=operation_integration.Integration.SourceConnections.ConnectionType)

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
                    data_queue_task = DataQueueTask(Id=id, Data=None, IsDataFrame=False,
                                                    Start=start,
                                                    End=end, Limit=limit, IsFinished=False)
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

            self.logger.info(f"Source data operation finished successfully. SubProcessId: {sub_process_id}")
        except Exception as ex:
            exception_traceback = traceback.format_exc()
            for i in range(operation_integration.ProcessCount):
                data_queue_error_task = DataQueueTask(IsFinished=True, Traceback=exception_traceback, Exception=ex)
                data_queue.put(data_queue_error_task)
            self.logger.info(
                f"Source data operation finished with error. SubProcessId: {sub_process_id}. Error:{ex} traceback:{exception_traceback}")
            raise

    @staticmethod
    def start_execute_data_process(
            sub_process_id,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ) -> int:
        return DependencyContainer.Instance.get(ParallelIntegrationExecute).start_execute_data_operation(
            sub_process_id=sub_process_id,
            operation_integration=operation_integration,
            data_queue=data_queue,
            data_result_queue=data_result_queue,
        )

    def start_execute_data_operation(
            self,
            sub_process_id: int,
            operation_integration: OperationIntegrationBase,
            data_queue: Queue,
            data_result_queue: Queue
    ) -> int:

        total_row_count = 0
        try:
            while True:
                data_task: DataQueueTask = data_queue.get()
                if data_task.IsFinished:
                    if data_task.Exception is not None:
                        exc = Exception(data_task.Traceback + '\n' + str(data_task.Exception))
                        raise exc
                    self.logger.info(f"{sub_process_id} process tasks finished")
                    return total_row_count
                else:
                    start = time()
                    data = data_task.Data
                    if data_task.IsDataFrame and data is not None:
                        source_data_json = data_task.Data
                        data: DataFrame = DataFrame(source_data_json)
                    data_count = 0
                    if data is None:
                        self.logger.info(
                            f"{sub_process_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process got a new task without data", )
                        data_count = self.start_execute_integration_with_paging(
                            integration=operation_integration.Integration,
                            start=data_task.Start,
                            end=data_task.End)
                    elif data is not None and len(data) > 0:
                        if data_task.IsDataFrame and data_task.DataTypes is not None:
                            source_data = data.astype(dtype=data_task.DataTypes)
                        else:
                            source_data = data
                        if data_task.IsDataFrame:
                            source_data = source_data.where(notnull(data), None)
                            source_data = source_data.replace({pd.NaT: None})

                        self.logger.info(
                            f"{sub_process_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process got a new task")
                        data_count = self.start_execute_integration_with_source_data(
                            integration=operation_integration.Integration,
                            source_data=source_data)
                    else:
                        self.logger.info(
                            f"{sub_process_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process got an empty task")

                    total_row_count = total_row_count + data_count
                    end = time()
                    self.logger.info(
                        f"{sub_process_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process finished task. time:{end - start}")
                    data_task.IsProcessed = True
                    data_result_queue.put(True)
                data_queue.task_done()
        except FunctionTimedOut as fto:
            data_result_queue.put(False)
            end = time()
            self.logger.info(
                f"{sub_process_id}-{data_task.Message}:{data_task.Id}-{data_task.Start}-{data_task.End} process getting error. time:{end - start} - Error {fto.getMsg()}")
            raise Exception(f'Execution Operation timed out after {fto.timedOutAfter} seconds.')
        except Exception as ex:
            data_result_queue.put(False)
            raise

    @func_set_timeout(1800)
    def start_execute_integration_with_source_data(self,
                                                   integration: IntegrationBase,
                                                   source_data: any
                                                   ):
        target_adapter = self.connection_adapter_factory.get_adapter(
            connection_type=integration.TargetConnections.ConnectionType)
        prepared_data = target_adapter.prepare_data(integration=integration, source_data=source_data)
        target_adapter.write_target_data(integration=integration, prepared_data=prepared_data)
        return len(source_data)

    @func_set_timeout(1800)
    def start_execute_integration_with_paging(self,
                                              integration: IntegrationBase,
                                              start,
                                              end
                                              ):
        source_adapter = self.connection_adapter_factory.get_adapter(
            connection_type=integration.SourceConnections.ConnectionType)
        source_data = source_adapter.get_source_data_with_paging(
            integration=integration, start=start, end=end)
        target_adapter = self.connection_adapter_factory.get_adapter(
            connection_type=integration.TargetConnections.ConnectionType)
        prepared_data = target_adapter.prepare_data(integration=integration, source_data=source_data)
        target_adapter.write_target_data(integration=integration, prepared_data=prepared_data)
        return len(source_data)
