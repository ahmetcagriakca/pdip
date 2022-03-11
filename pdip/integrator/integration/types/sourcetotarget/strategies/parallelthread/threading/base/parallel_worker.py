import threading
import traceback
from time import time

from ..domain import ThreadTask
from ........domain.enums.events import EVENT_LOG
from ........pubsub.base import ChannelQueue
from ........pubsub.domain import TaskMessage
from ........pubsub.publisher import Publisher


class ParallelWorker(threading.Thread):
    def __init__(
            self,
            thread_id: int,
            operation_integration,
            channel: ChannelQueue,
            process_channel: ChannelQueue,
            process_result_channel: ChannelQueue,
            target_method,
            target_kwargs,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.operation_integration = operation_integration
        self.publisher = Publisher(channel=channel)
        self.target_kwargs = target_kwargs
        self.target_method = target_method
        self.process_result_channel = process_result_channel
        self.process_channel = process_channel
        self.thread_id = thread_id
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):

        self.publisher.publish(
            message=TaskMessage(
                event=EVENT_LOG,
                kwargs={
                    'data': self.operation_integration,
                    'message': f"{self.thread_id} process started"
                }
            )
        )
        try:
            while True:
                process_task: ThreadTask = self.process_channel.get()
                process_task.Id = self.thread_id
                process_task.State = 2
                if process_task.IsFinished:
                    self.publisher.publish(
                        message=TaskMessage(
                            event=EVENT_LOG,
                            kwargs={
                                'data': self.operation_integration,
                                'message': f"{self.thread_id} process finished"
                            }
                        )
                    )
                    break
                else:
                    start = time()
                    # calling target method
                    self.target_kwargs["thread_id"] = self.thread_id
                    result = self.target_method(**self.target_kwargs)
                    end = time()

                    self.publisher.publish(
                        message=TaskMessage(
                            event=EVENT_LOG,
                            kwargs={
                                'data': self.operation_integration,
                                'message': f"{self.thread_id} process finished. time:{end - start}"
                            }
                        )
                    )
                    process_task.IsFinished = True
                    process_task.State = 3
                    process_task.Result = result
                    self.process_result_channel.put(process_task)
                    return
        except Exception as ex:

            self.publisher.publish(
                message=TaskMessage(
                    event=EVENT_LOG,
                    kwargs={
                        'data': self.operation_integration,
                        'message': f"{self.thread_id} process getting error.",
                        'exception': ex
                    }
                )
            )
            process_task = ThreadTask(
                Id=self.thread_id,
                State=4,
                Exception=ex,
                Traceback=traceback.format_exc(),
                IsFinished=True
            )
            self.process_result_channel.put(process_task)
