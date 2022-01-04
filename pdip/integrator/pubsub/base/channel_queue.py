import queue


class ChannelQueue:
    def __init__(self, channel_queue: queue):
        self.channel_queue: queue = channel_queue

    def put(self, message):
        self.channel_queue.put(message)

    def get(self):
        return self.channel_queue.get()

    def done(self):
        return self.channel_queue.task_done()
