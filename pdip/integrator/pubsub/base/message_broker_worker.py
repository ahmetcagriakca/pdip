import queue
import threading

from .channel_queue import ChannelQueue
from ..domain import TaskMessage


class MessageBrokerWorker(threading.Thread):
    def __init__(self,
                 publish_channel: ChannelQueue,
                 message_channel: ChannelQueue,
                 other_arg,
                 *args, **kwargs):
        self.message_channel = message_channel
        self.publish_channel = publish_channel
        self.other_arg = other_arg
        super().__init__(*args, **kwargs)

    def run(self):
        while True:
            try:
                work: TaskMessage = self.publish_channel.get()
                self.message_channel.put(work)
                if work.is_finished:
                    break
            except queue.Empty:
                return
            finally:
                self.publish_channel.done()