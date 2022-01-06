import queue
import threading

from pdip.logging.loggers.console import ConsoleLogger
from .channel_queue import ChannelQueue
from ..domain import TaskMessage


class EventListener(threading.Thread):
    def __init__(self,
                 channel: ChannelQueue,
                 subscribers: {},
                 logger: ConsoleLogger,
                 *args, **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.subscribers = subscribers
        self.channel = channel
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            try:
                task: TaskMessage = self.channel.get()
                if task is None:
                    return
                if task.event in self.subscribers.keys():
                    for callback in self.subscribers[task.event]:
                        callback(**task.kwargs)
                else:
                    self.logger.warning("Event {0} has no subscribers".format(task.event))
                if task.is_finished:
                    break
                self.channel.done()
            except queue.Empty:
                return
            except Exception as ex:
                self.logger.exception(ex, f'Event listener getting error.')
                return
            finally:
                pass
