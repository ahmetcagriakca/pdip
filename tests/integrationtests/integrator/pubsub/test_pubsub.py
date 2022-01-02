import threading
from unittest import TestCase

from pdip.integrator.pubsub.base.message_broker import MessageBroker
from pdip.integrator.pubsub.domain.message import TaskMessage
from pdip.integrator.pubsub.publisher.publisher import Publisher
from pdip.integrator.pubsub.base.event_listener import Subscriber
from pdip.logging.loggers.console import ConsoleLogger


class TestPubSub(TestCase):
    def setUp(self):
        pass
        # try:
        #     self.pdi = Pdi()
        # except:
        #     self.tearDown()
        #     raise

    def tearDown(self):
        if hasattr(self, 'pdi') and self.pdi is not None:
            self.pdi.cleanup()
            del self.pdi
        return super().tearDown()

    @staticmethod
    def subscriber_thread(channel):
        Subscriber(channel=channel).on_message()

    def test_integration(self):
        try:
            message_broker = MessageBroker()
            message_broker.start()
            subscriber_thread = threading.Thread(target=self.subscriber_thread,
                                                 args=(message_broker.message_channel,))
            subscriber_thread.start()

            publisher = Publisher(channel=message_broker.publish_channel)
            publisher.publish(message=TaskMessage(data="test", message='test'))
            publisher.publish(message=TaskMessage(data="test", message='test', is_finished=True))
            message_broker.worker.join()
        except Exception as ex:
            ConsoleLogger().exception(ex)
