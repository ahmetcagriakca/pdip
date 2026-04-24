import queue


class ChannelQueue:
    def __init__(self, channel_queue: queue):
        self.channel_queue: queue = channel_queue

    def put(self, message):
        self.channel_queue.put(message)

    def get(self):
        return self.channel_queue.get()

    def get_nowait(self):
        """Return a message without blocking; raise ``queue.Empty`` if
        the channel has no pending messages. Mirrors
        ``queue.Queue.get_nowait`` so callers can drain a channel in
        tests or observability paths without blocking the caller."""
        return self.channel_queue.get_nowait()

    def done(self):
        return self.channel_queue.task_done()
