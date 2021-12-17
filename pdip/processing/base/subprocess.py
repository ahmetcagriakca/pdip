import traceback
from queue import Queue
from time import time

from pdip.dependency.container import DependencyContainer
from pdip.logging.loggers.console import ConsoleLogger
from pdip.processing.models import ProcessTask
from pdip.utils.utils import Utils


class Subprocess:
    def __init__(
            self,
            initialize_container: bool = None,
            root_directory: str = None
    ):
        if initialize_container:
            DependencyContainer.initialize_service(
                root_directory=root_directory, initialize_flask=False)
            self.logger = DependencyContainer.Instance.get(ConsoleLogger)
        else:
            self.logger = ConsoleLogger()

    def __del__(self) -> None:
        del self.logger

    def start(
            self,
            sub_process_id: int,
            process_queue: Queue,
            process_result_queue: Queue,
            target_method,
            kwargs
    ):
        self.logger.info(f"{sub_process_id} process started")
        try:
            while True:
                process_task: ProcessTask = process_queue.get()
                process_task.SubProcessId = sub_process_id
                process_task.State = 2
                if process_task.IsFinished:
                    self.logger.info(f"{sub_process_id} process finished")
                    # Indicate finished
                    break
                else:
                    # TODO: return result with task

                    start = time()
                    # calling target method
                    kwargs["sub_process_id"] = sub_process_id
                    result = target_method(**kwargs)
                    end = time()
                    self.logger.info(
                        f"{sub_process_id} process finished. time:{end - start}")
                    process_task.IsFinished = True
                    process_task.State = 3
                    process_task.Result = result
                    process_result_queue.put(process_task)
                    return
        except Exception as ex:
            self.logger.error(
                f"{sub_process_id} process getting error:{ex}")
            process_task = ProcessTask(SubProcessId=sub_process_id, State=4, Exception=ex,
                                       Traceback=traceback.format_exc(), IsFinished=True)
            process_result_queue.put(process_task)
