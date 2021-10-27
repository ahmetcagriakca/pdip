import multiprocessing
import traceback
from multiprocessing.context import Process
from multiprocessing.managers import SyncManager
from queue import Queue
from time import time
from typing import List

from .models import ProcessInfo
from .models import ProcessTask
from ..dependency.container import DependencyContainer
from ..logging.loggers.console import ConsoleLogger


class ProcessManager:
    def __init__(self, fire_and_forget: bool = False):
        self.fire_and_forget = fire_and_forget
        self._manager: SyncManager = None
        self._process_queue: Queue = None
        self._process_result_queue: Queue = None
        self._processes: List[ProcessInfo] = None
        self._process_tasks: List[ProcessTask] = None
        self.logger = ConsoleLogger()

    def __del__(self):
        if not self.fire_and_forget:
            self.__finish_all_processes()
            if self._manager is not None:
                self._manager.shutdown()
            del self.logger

    def get_manager(self):
        if self._manager is None:
            self._manager = multiprocessing.Manager()
        return self._manager

    def create_queue(self) -> Queue:

        return self.get_manager().Queue()

    def start_processes(self, target_method, kwargs, process_count=1):
        self.__configure_process()
        # Initiate the worker processes
        for i in range(process_count):
            # Set process name
            sub_process_id = i + 1
            # Create the process, and connect it to the worker function
            process = self.__start_process(
                sub_process_id=sub_process_id,
                process_queue=self._process_queue,
                process_result_queue=self._process_result_queue,
                target_method=target_method,
                kwargs=kwargs)
            # Add new process to the list of processes
            process_data = ProcessInfo(
                Process=process, SubProcessId=sub_process_id)
            self._processes.append(process_data)
            process_task = ProcessTask(
                SubProcessId=sub_process_id, IsFinished=False)
            self._process_queue.put(process_task)
            self._process_tasks.append(process_task)
            # Start the process

    def get_results(self) -> List[ProcessTask]:
        self.__check_processes()
        return self._process_tasks

    def __configure_process(self):
        self._manager = self.get_manager()
        # Define a list (queue) for tasks and computation results
        self._process_queue = self._manager.Queue()
        self._process_result_queue = self._manager.Queue()
        number_of_cores = multiprocessing.cpu_count()
        # print(f"{number_of_cores} cores available")
        self._processes: List[ProcessInfo] = []
        self._process_tasks: List[ProcessTask] = []

    def __start_process(self,
                        sub_process_id: int,
                        process_queue: Queue,
                        process_result_queue: Queue,
                        target_method: any,
                        kwargs: any) -> Process:
        # Create the process, and connect it to the worker function
        if hasattr(DependencyContainer, 'Instance') and DependencyContainer.Instance is not None:
            root_directory = DependencyContainer.Instance.root_directory
            initialize_container = True
        else:
            root_directory = None
            initialize_container = False
        new_process = Process(
            target=self.start_process_operation,
            args=(
                sub_process_id, root_directory, initialize_container, process_queue, process_result_queue,
                target_method, kwargs))

        new_process.start()
        return new_process

    @staticmethod
    def start_process_operation(sub_process_id: int, root_directory: str, initialize_container: bool,
                                process_queue: Queue,
                                process_result_queue: Queue, target_method,
                                kwargs):
        if initialize_container:
            DependencyContainer.initialize_service(
                root_directory=root_directory, initialize_flask=False)
        ProcessManager().__start_process_operation(sub_process_id=sub_process_id,
                                                   process_queue=process_queue,
                                                   process_result_queue=process_result_queue,
                                                   target_method=target_method,
                                                   kwargs=kwargs)

    def __start_process_operation(self,
                                  sub_process_id: int,
                                  process_queue: Queue,
                                  process_result_queue: Queue,
                                  target_method,
                                  kwargs):
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

    def __check_processes(self):
        # Read calculation results
        while True:
            # Read result
            process_task: ProcessTask = self._process_result_queue.get()
            # Have a look at the results
            if process_task.IsFinished:
                # Process has finished
                if process_task.State == 4:
                    self.__finish_all_processes()
                    for task in self._process_tasks:
                        if task.SubProcessId == process_task.SubProcessId:
                            task.Result = process_task.Result
                            task.State = process_task.State
                            task.Message = process_task.Message
                            task.IsFinished = process_task.IsFinished
                            task.Exception = process_task.Exception
                            task.Traceback = process_task.Traceback
                            task.Data = process_task.Data
                    break
                for process_data in self._processes:
                    if process_data.SubProcessId == process_task.SubProcessId:
                        process_data.IsFinished = True
                for task in self._process_tasks:
                    if task.SubProcessId == process_task.SubProcessId:
                        task.Result = process_task.Result
                        task.State = process_task.State
                        task.Message = process_task.Message
                        task.IsFinished = process_task.IsFinished
                        task.Exception = process_task.Exception
                        task.Traceback = process_task.Traceback
                        task.Data = process_task.Data
                self.__check_unfinished_processes()
                if self.__check_all_processes_finish():
                    break

    def __finish_all_processes(self):
        if self._processes is not None:
            for process in self._processes:
                if process.Process.is_alive():
                    process_task = ProcessTask(
                        SubProcessId=process.SubProcessId, IsFinished=False)
                    self._process_queue.put(process_task)
                    print(
                        f"Process will terminate. SubProcessId:{process.SubProcessId}")
                    process.IsFinished = True
                    process.Process.terminate()

    def __check_unfinished_processes(self):

        for process_data in self._processes:
            if not process_data.IsFinished and not process_data.Process.is_alive():
                print(
                    f"Unfinished process found. SubProcessId:{process_data.SubProcessId}")
                process_data.IsFinished = True

    def __check_all_processes_finish(self):
        check_finish = True
        unfinished_process_list = []
        for process_data in self._processes:
            if not process_data.IsFinished:
                check_finish = False
                unfinished_process_list.append(str(process_data.SubProcessId))
        process_join = ",".join(unfinished_process_list)
        print(
            f"All processes are expected to end . SubProcessId:{process_join}")
        return check_finish
