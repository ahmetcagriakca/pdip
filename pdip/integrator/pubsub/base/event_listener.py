import queue
import threading

from pdip.logging.loggers.console import ConsoleLogger
from .channel_queue import ChannelQueue
from ..domain import TaskMessage


class EventListener(threading.Thread):
    def __init__(self,
                 channel: ChannelQueue,
                 subscribers: {},
                 logger:ConsoleLogger,
                 *args, **kwargs
                 ):
        self.logger = logger
        self.subscribers = subscribers
        self.channel = channel
        super().__init__(*args, **kwargs)

    def run(self):
        while True:
            try:
                task: TaskMessage = self.channel.get()
                if task.event in self.subscribers.keys():
                    for callback in self.subscribers[task.event]:
                        callback(**task.kwargs)
                else:
                    self.logger.warning("Event {0} has no subscribers".format(task.event))
                if task.is_finished:
                    break
            except queue.Empty:
                return
            finally:
                self.channel.done()
