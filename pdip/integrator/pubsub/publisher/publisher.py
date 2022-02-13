from ..base import ChannelQueue
from ..domain import TaskMessage


class Publisher:
    def __init__(self, channel: ChannelQueue):
        self.channel = channel

    def publish(self, message: TaskMessage):
        self.channel.put(message)
