import multiprocessing
from multiprocessing.managers import SyncManager

from .channel_queue import ChannelQueue
from .event_listener import EventListener
from .message_broker_worker import MessageBrokerWorker


class MessageBroker:
    def __init__(self, logger):
        self.logger = logger
        self.manager: SyncManager = None
        self.publish_queue = None
        self.message_queue = None
        self.publish_channel: ChannelQueue = None
        self.message_channel: ChannelQueue = None
        self.worker: MessageBrokerWorker = None
        self.listener: EventListener = None
        self.subscribers = {}
        self.max_join_time = 120

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __del__(self):
        self.close()

    def close(self):
        if self.worker is not None and self.worker.is_alive() and not self.worker.stopped():
            self.worker.stop()
        if self.listener is not None and self.listener.is_alive() and not self.listener.stopped():
            self.listener.stop()
        if self.manager is not None:
            self.manager.shutdown()

    def initialize(self):
        self.manager = multiprocessing.Manager()
        self.publish_queue = self.manager.Queue()
        self.message_queue = self.manager.Queue()
        self.publish_channel = ChannelQueue(channel_queue=self.publish_queue)
        self.message_channel = ChannelQueue(channel_queue=self.message_queue)
        self.worker: MessageBrokerWorker = MessageBrokerWorker(
            logger=self.logger,
            publish_channel=self.publish_channel,
            message_channel=self.message_channel,
        )

    def start(self):
        self.worker.start()
        self.listener = EventListener(
            channel=self.message_channel,
            subscribers=self.subscribers,
            logger=self.logger
        )
        self.listener.start()

    def join(self):
        self.worker.join(self.max_join_time)
        self.listener.join(self.max_join_time)

    def get_publish_channel(self):
        return self.publish_channel

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
