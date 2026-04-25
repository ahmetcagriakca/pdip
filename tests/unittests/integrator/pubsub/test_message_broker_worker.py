"""Unit tests for
``pdip.integrator.pubsub.base.message_broker_worker.MessageBrokerWorker``.

The worker pulls tasks from a publish channel and forwards them onto
a message channel. It runs on a thread in production, but the loop
body is pure and is exercised here by calling ``run`` directly with
mocked channels.
"""

# Stub optional integrator extras before importing the subject.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.pubsub.base.message_broker_worker import MessageBrokerWorker  # noqa: E402
from pdip.integrator.pubsub.domain import TaskMessage  # noqa: E402


def _build_worker(publish_messages):
    publish = MagicMock()
    publish.get.side_effect = publish_messages
    message = MagicMock()
    logger = MagicMock(name="ConsoleLogger")
    worker = MessageBrokerWorker(
        logger=logger,
        publish_channel=publish,
        message_channel=message,
    )
    return worker, publish, message, logger


class MessageBrokerWorkerStopEvent(TestCase):
    def test_stop_sets_stop_event(self):
        worker, _, _, _ = _build_worker([])

        worker.stop()

        self.assertTrue(worker.stopped())

    def test_stopped_false_by_default(self):
        worker, _, _, _ = _build_worker([])

        self.assertFalse(worker.stopped())


class MessageBrokerWorkerForwardsMessages(TestCase):
    def test_run_forwards_message_from_publish_to_message_channel(self):
        task = TaskMessage(event="EV", is_finished=True, kwargs={"k": "v"})
        worker, _, message_channel, _ = _build_worker([task])

        worker.run()

        message_channel.put.assert_called_once_with(task)

    def test_run_returns_when_publish_channel_yields_none(self):
        worker, _, message_channel, _ = _build_worker([None])

        worker.run()

        message_channel.put.assert_not_called()

    def test_run_breaks_loop_when_task_is_finished(self):
        finished = TaskMessage(event="EV", is_finished=True)
        worker, publish_channel, _, _ = _build_worker([finished])

        worker.run()

        # Only one iteration — get() called once, done() never called
        # because the loop breaks before the done() statement.
        self.assertEqual(publish_channel.get.call_count, 1)
        publish_channel.done.assert_not_called()

    def test_run_marks_publish_done_for_unfinished_message_and_continues(self):
        first = TaskMessage(event="A", is_finished=False)
        last = TaskMessage(event="B", is_finished=True)
        worker, publish_channel, message_channel, _ = _build_worker(
            [first, last]
        )

        worker.run()

        # Both tasks forwarded, done() called once (for the unfinished
        # message only).
        self.assertEqual(message_channel.put.call_count, 2)
        publish_channel.done.assert_called_once_with()

    def test_run_returns_when_publish_channel_raises_queue_empty(self):
        worker, _, message_channel, logger = _build_worker([queue.Empty()])
        # Rebuild the mock with the exception as the side_effect itself.
        worker.publish_channel.get.side_effect = queue.Empty()

        worker.run()

        message_channel.put.assert_not_called()
        logger.error.assert_not_called()

    def test_run_logs_error_and_returns_on_unexpected_exception(self):
        worker, publish_channel, message_channel, logger = _build_worker([])
        publish_channel.get.side_effect = RuntimeError("boom")

        worker.run()

        logger.error.assert_called_once()
        message_channel.put.assert_not_called()
