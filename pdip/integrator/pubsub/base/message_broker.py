import multiprocessing

from .channel_queue import ChannelQueue
from .event_listener import EventListener
from .message_broker_worker import MessageBrokerWorker


class MessageBroker:
    def __init__(self, logger):
        self.logger = logger
        self.manager = multiprocessing.Manager()
        self.publish_queue = self.manager.Queue()
        self.publish_channel = ChannelQueue(channel_queue=self.publish_queue)
        self.message_queue = self.manager.Queue()
        self.message_channel = ChannelQueue(channel_queue=self.message_queue)
        self.worker: MessageBrokerWorker = MessageBrokerWorker(publish_channel=self.publish_channel,
                                                               message_channel=self.message_channel,
                                                               other_arg=None)
        self.listener: EventListener = None
        self.subscribers = {}
        self.max_join_time = 60

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        if self.worker.is_alive() and not self.worker.stopped():
            self.worker.stop()
        if self.listener.is_alive() and not self.listener.stopped():
            self.listener.stop()
        self.manager.shutdown()

    def get_publish_channel(self):
        return self.publish_channel

    def start(self):
        self.worker.start()
        self.listener = EventListener(channel=self.message_channel, subscribers=self.subscribers, logger=self.logger)
        self.listener.start()

    def join(self):
        self.worker.join(self.max_join_time)
        self.listener.join(self.max_join_time)

    def subscribe(self, event, callback):
        if not callable(callback):
            raise ValueError("callback must be callable")
        if event is None or event == "":
            raise ValueError("Event cant be empty")

        if event not in self.subscribers.keys():
            self.subscribers[event] = [callback]
        else:
            self.subscribers[event].append(callback)

    def unsubscribe(self, event, callback):
        if event is not None or event != "" \
                and event in self.subscribers.keys():
            self.subscribers[event] = list(
                filter(
                    lambda x: x is not callback,
                    self.subscribers[event]
                )
            )
        else:
            self.logger.warning("Cant unsubscribe function '{0}' from event '{1}' ".format(event, callback))
