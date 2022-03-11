import queue
import threading

from pdip.logging.loggers.console import ConsoleLogger
from .channel_queue import ChannelQueue
from ..domain import TaskMessage


class MessageBrokerWorker(threading.Thread):
    def __init__(self,
                 logger: ConsoleLogger,
                 publish_channel: ChannelQueue,
                 message_channel: ChannelQueue,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger
        self.message_channel = message_channel
        self.publish_channel = publish_channel
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def run(self):
        while True:
            try:
                work: TaskMessage = self.publish_channel.get()
                if work is None:
                    return
                self.message_channel.put(work)
                if work.is_finished:
                    break
                self.publish_channel.done()
            except queue.Empty:
                return
            except Exception as e:
                self.logger.error('error')
                return
            finally:
                pass
