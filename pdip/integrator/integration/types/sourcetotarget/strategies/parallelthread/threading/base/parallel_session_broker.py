import multiprocessing
from multiprocessing.managers import SyncManager
from queue import Queue
from typing import List

from .parallel_worker import ParallelWorker
from ..domain import ThreadInfo
from ..domain import ThreadTask
from ........domain.enums.events import EVENT_LOG
from ........pubsub.base import ChannelQueue
from ........pubsub.domain import TaskMessage
from ........pubsub.publisher import Publisher


class ParallelSessionBroker:
    def __init__(
            self,
            channel: ChannelQueue,
            operation_integration
    ):
        self.operation_integration = operation_integration
        self.publisher = Publisher(channel=channel)
        self._process_queue: Queue = None
        self._process_result_queue: Queue = None
        self.process_result_channel: ChannelQueue = None
        self.process_channel: ChannelQueue = None

        self._threads: List[ThreadInfo] = None
        self._thread_tasks: List[ThreadTask] = None
        self.channel = channel
        self.number_of_cores = multiprocessing.cpu_count()
        self._manager: SyncManager = None

    def __del__(self):
        self.__finish_all_threads()
        if self.manager is not None:
            self.manager.shutdown()

    @property
    def manager(self) -> SyncManager:
        if self._manager is None:
            self._manager = multiprocessing.Manager()
        return self._manager

    def create_queue(self) -> Queue:
        return self.manager.Queue()

    def initialize(self):
        self._process_queue = self.create_queue()
        self._process_result_queue = self.create_queue()
        self.process_channel = ChannelQueue(channel_queue=self._process_queue)
        self.process_result_channel = ChannelQueue(channel_queue=self._process_result_queue)
        self._threads: List[ThreadInfo] = []
        self._thread_tasks: List[ThreadTask] = []


    def start(self, target_method, target_kwargs, process_count=1):
        self.initialize()
        # Initiate the worker processes
        for i in range(process_count):
            thread_id = i + 1
            worker = ParallelWorker(
                thread_id=thread_id,
                operation_integration=self.operation_integration,
                channel=self.channel,
                process_channel=self.process_channel,
                process_result_channel=self.process_result_channel,
                target_method=target_method,
                target_kwargs=target_kwargs,
            )

            # Add new process to the list of processes
            thread_info = ThreadInfo(
                Id=thread_id,
                Thread=worker
            )
            self._threads.append(thread_info)
            process_task = ThreadTask(
                Id=thread_id,
                IsFinished=False
            )
            self.process_channel.put(process_task)
            self._thread_tasks.append(process_task)
            # Start the process
        for t in self._threads:
            t.Thread.start()

    def get_results(self) -> List[ThreadTask]:
        self.__check_threads()
        return self._thread_tasks

    def __check_threads(self):
        # Read calculation results
        while True:
            # Read result
            thread_task: ThreadTask = self.process_result_channel.get()
            # Have a look at the results
            if thread_task.IsFinished:
                # Process has finished
                if thread_task.State == 4:
                    self.__finish_all_threads()
                    for task in self._thread_tasks:
                        if task.Id == thread_task.Id:
                            task.Result = thread_task.Result
                            task.State = thread_task.State
                            task.Message = thread_task.Message
                            task.IsFinished = thread_task.IsFinished
                            task.Exception = thread_task.Exception
                            task.Traceback = thread_task.Traceback
                            task.Data = thread_task.Data
                    break
                for t in self._threads:
                    if t.Id == thread_task.Id:
                        t.IsFinished = True
                for task in self._thread_tasks:
                    if task.Id == thread_task.Id:
                        task.Result = thread_task.Result
                        task.State = thread_task.State
                        task.Message = thread_task.Message
                        task.IsFinished = thread_task.IsFinished
                        task.Exception = thread_task.Exception
                        task.Traceback = thread_task.Traceback
                        task.Data = thread_task.Data
                self.__check_unfinished_threads()
                if self.__check_all_threads_finished():
                    break

    def __finish_all_threads(self):
        if self._threads is not None:
            for t in self._threads:

                if t is not None and t.Thread.is_alive() and not t.Thread.stopped():
                    t.Thread.stop()
                if t.Thread.is_alive():
                    process_task = ThreadTask(
                        Id=t.Id,
                        IsFinished=False
                    )
                    self.process_channel.put(process_task)

                    self.publisher.publish(
                        message=TaskMessage(
                            event=EVENT_LOG,
                            kwargs={
                                'data': self.operation_integration,
                                'message': f"Process will terminate. WorkerId:{t.Id}"
                            }
                        )
                    )
                    t.IsFinished = True
                    t.Thread.stop()

    def __check_unfinished_threads(self):

        for t in self._threads:
            if not t.IsFinished and not t.Thread.is_alive():
                self.publisher.publish(
                    message=TaskMessage(
                        event=EVENT_LOG,
                        kwargs={
                            'data': self.operation_integration,
                            'message': f"Unfinished process found. WorkerId:{t.Id}"
                        }
                    )
                )
                t.IsFinished = True

    def __check_all_threads_finished(self):
        check_finish = True
        unfinished_thread_list = []
        for t in self._threads:
            if not t.IsFinished:
                check_finish = False
                unfinished_thread_list.append(str(t.Id))
        thread_join = ",".join(unfinished_thread_list)

        self.publisher.publish(
            message=TaskMessage(
                event=EVENT_LOG,
                kwargs={
                    'data': self.operation_integration,
                    'message': f"All processes are expected to end . WorkerId:{thread_join}"
                }
            )
        )
        return check_finish
