"""Unit tests for ``ChannelQueue`` and the publisher contract.

The real broker composes ``multiprocessing.Manager`` queues and forked
workers; those are left to integration tests. Here we cover the
thin wrapper types that sit on top of a queue and are the ones most
likely to move between Python minor versions.
"""

import queue
from unittest import TestCase

from pdip.integrator.pubsub.base import ChannelQueue
from pdip.integrator.pubsub.domain import TaskMessage
from pdip.integrator.pubsub.publisher import Publisher


class ChannelQueueRoundTripsMessages(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())

    def test_put_then_get_yields_the_same_object(self):
        message = TaskMessage(event="EV", args=(1, 2), kwargs={"k": "v"})
        self.channel.put(message)
        self.assertIs(self.channel.get(), message)

    def test_fifo_order_is_preserved(self):
        first = TaskMessage(event="first")
        second = TaskMessage(event="second")
        self.channel.put(first)
        self.channel.put(second)
        self.assertIs(self.channel.get(), first)
        self.assertIs(self.channel.get(), second)

    def test_done_marks_task_done_on_underlying_queue(self):
        message = TaskMessage(event="done")
        self.channel.put(message)
        self.channel.get()
        # ``task_done`` raises if called more often than ``put``; the
        # single call below must succeed.
        self.channel.done()


class PublisherSendsMessagesThroughChannel(TestCase):
    def setUp(self):
        self.channel = ChannelQueue(queue.Queue())
        self.publisher = Publisher(self.channel)

    def test_publish_places_message_on_channel(self):
        message = TaskMessage(event="EV_STARTED", kwargs={"id": 42})
        self.publisher.publish(message)
        self.assertEqual(self.channel.get(), message)


class TaskMessageIsConstructibleWithDefaults(TestCase):
    def test_default_values_are_none(self):
        message = TaskMessage()
        self.assertIsNone(message.event)
        self.assertIsNone(message.is_finished)
        self.assertIsNone(message.args)
        self.assertIsNone(message.kwargs)

    def test_equality_is_by_value(self):
        a = TaskMessage(event="e", args=(1,), kwargs={"x": 1})
        b = TaskMessage(event="e", args=(1,), kwargs={"x": 1})
        self.assertEqual(a, b)

    def test_inequality_distinguishes_events(self):
        self.assertNotEqual(TaskMessage(event="a"), TaskMessage(event="b"))
