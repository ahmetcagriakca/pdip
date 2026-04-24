"""Unit tests for ``pdip.integrator.pubsub.base.event_listener.EventListener``.

``EventListener`` is a ``threading.Thread`` subclass, but its ``run``
loop is pure — given a channel and a subscriber map it dispatches or
warns per message. These tests invoke ``run`` directly on the main
thread against a mock ``ChannelQueue`` so no worker thread is started.
"""

# Stub pandas + func_timeout — the module tree touches optional
# integrator extras.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

import queue  # noqa: E402
from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.pubsub.base.event_listener import EventListener  # noqa: E402
from pdip.integrator.pubsub.domain import TaskMessage  # noqa: E402


def _build_listener(messages, subscribers=None):
    """Build an ``EventListener`` with a channel mock that yields the
    given ``messages`` one-by-one from ``.get()``."""
    channel = MagicMock()
    channel.get.side_effect = messages
    logger = MagicMock(name="ConsoleLogger")
    listener = EventListener(
        channel=channel,
        subscribers=subscribers if subscribers is not None else {},
        logger=logger,
    )
    return listener, channel, logger


class EventListenerStopEvent(TestCase):
    def test_stop_sets_stop_event(self):
        listener, _, _ = _build_listener([])

        listener.stop()

        self.assertTrue(listener.stopped())

    def test_stopped_false_by_default(self):
        listener, _, _ = _build_listener([])

        self.assertFalse(listener.stopped())


class EventListenerRunDispatchesMessages(TestCase):
    def test_run_invokes_subscriber_callback_with_kwargs(self):
        callback = MagicMock()
        message = TaskMessage(
            event="CREATED",
            is_finished=True,
            kwargs={"id": 7},
        )
        listener, _, _ = _build_listener(
            [message],
            subscribers={"CREATED": [callback]},
        )

        listener.run()

        callback.assert_called_once_with(id=7)

    def test_run_invokes_all_callbacks_for_event(self):
        cb1, cb2 = MagicMock(), MagicMock()
        message = TaskMessage(
            event="EV",
            is_finished=True,
            kwargs={"payload": "hi"},
        )
        listener, _, _ = _build_listener(
            [message],
            subscribers={"EV": [cb1, cb2]},
        )

        listener.run()

        cb1.assert_called_once_with(payload="hi")
        cb2.assert_called_once_with(payload="hi")

    def test_run_warns_when_event_has_no_subscribers(self):
        message = TaskMessage(
            event="UNKNOWN", is_finished=True, kwargs={}
        )
        listener, _, logger = _build_listener(
            [message], subscribers={"OTHER": [MagicMock()]}
        )

        listener.run()

        logger.warning.assert_called_once()
        self.assertIn("UNKNOWN", logger.warning.call_args.args[0])

    def test_run_returns_immediately_when_channel_yields_none(self):
        callback = MagicMock()
        listener, _, _ = _build_listener(
            [None], subscribers={"EV": [callback]}
        )

        listener.run()

        callback.assert_not_called()

    def test_run_breaks_loop_when_task_is_finished(self):
        cb = MagicMock()
        finished = TaskMessage(
            event="EV", is_finished=True, kwargs={}
        )
        # If the loop did not break we would exhaust the second element;
        # a second get() call would blow up due to StopIteration.
        listener, channel, _ = _build_listener(
            [finished], subscribers={"EV": [cb]}
        )

        listener.run()

        cb.assert_called_once()
        self.assertEqual(channel.get.call_count, 1)

    def test_run_continues_and_marks_done_for_unfinished_message(self):
        cb = MagicMock()
        first = TaskMessage(event="EV", is_finished=False, kwargs={"n": 1})
        last = TaskMessage(event="EV", is_finished=True, kwargs={"n": 2})
        listener, channel, _ = _build_listener(
            [first, last], subscribers={"EV": [cb]}
        )

        listener.run()

        # First message is not finished → done() called before loop
        # fetches the next. Second message is finished → loop breaks
        # before calling done() again.
        self.assertEqual(channel.done.call_count, 1)
        self.assertEqual(cb.call_count, 2)

    def test_run_returns_when_channel_raises_queue_empty(self):
        channel = MagicMock()
        channel.get.side_effect = queue.Empty()
        logger = MagicMock()
        listener = EventListener(
            channel=channel, subscribers={}, logger=logger
        )

        listener.run()

        logger.exception.assert_not_called()

    def test_run_logs_and_returns_on_unexpected_exception(self):
        channel = MagicMock()
        boom = RuntimeError("kaboom")
        channel.get.side_effect = boom
        logger = MagicMock()
        listener = EventListener(
            channel=channel, subscribers={}, logger=logger
        )

        listener.run()

        logger.exception.assert_called_once()
        self.assertIs(logger.exception.call_args.args[0], boom)
