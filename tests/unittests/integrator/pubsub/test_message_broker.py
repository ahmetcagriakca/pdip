"""Unit tests for ``MessageBroker.subscribe`` / ``unsubscribe``.

The broker owns a ``multiprocessing.Manager`` + worker + listener in
production. Those are not exercised here — they belong to integration
tests. These tests exercise the in-process subscriber bookkeeping,
which a pre-existing operator-precedence bug in ``unsubscribe`` was
silently corrupting.
"""

# Stub pandas + func_timeout — the broker module imports through the
# integrator package tree which touches optional-extras adapters.
from tests.unittests.integrator import _stub_pandas  # noqa: F401, E402

from unittest import TestCase  # noqa: E402
from unittest.mock import MagicMock  # noqa: E402

from pdip.integrator.pubsub.base.message_broker import MessageBroker  # noqa: E402


class MessageBrokerSubscriberBookkeeping(TestCase):
    def setUp(self):
        self.broker = MessageBroker(logger=MagicMock(name="logger"))

    def test_subscribe_stores_callback_under_event(self):
        cb = MagicMock()
        self.broker.subscribe("EVT", cb)
        self.assertEqual(self.broker.subscribers["EVT"], [cb])

    def test_subscribe_appends_additional_callbacks(self):
        cb1, cb2 = MagicMock(), MagicMock()
        self.broker.subscribe("EVT", cb1)
        self.broker.subscribe("EVT", cb2)
        self.assertEqual(self.broker.subscribers["EVT"], [cb1, cb2])

    def test_subscribe_rejects_non_callable(self):
        with self.assertRaises(ValueError):
            self.broker.subscribe("EVT", "not a callable")

    def test_subscribe_rejects_empty_event(self):
        with self.assertRaises(ValueError):
            self.broker.subscribe("", MagicMock())
        with self.assertRaises(ValueError):
            self.broker.subscribe(None, MagicMock())

    def test_unsubscribe_removes_the_callback_from_its_event(self):
        cb1, cb2 = MagicMock(), MagicMock()
        self.broker.subscribe("EVT", cb1)
        self.broker.subscribe("EVT", cb2)

        self.broker.unsubscribe("EVT", cb1)

        self.assertEqual(self.broker.subscribers["EVT"], [cb2])

    def test_unsubscribe_leaves_other_events_alone(self):
        cb = MagicMock()
        self.broker.subscribe("EVT-A", cb)
        self.broker.subscribe("EVT-B", cb)

        self.broker.unsubscribe("EVT-A", cb)

        self.assertEqual(self.broker.subscribers["EVT-A"], [])
        self.assertEqual(self.broker.subscribers["EVT-B"], [cb])

    def test_unsubscribe_warns_when_event_was_never_subscribed(self):
        # Previously this path was dead: the operator-precedence bug
        # forced the happy branch even for events not in
        # ``self.subscribers``. A clean run must now log a warning
        # and must not mutate ``subscribers``.
        self.broker.unsubscribe("UNKNOWN", MagicMock())

        self.broker.logger.warning.assert_called_once()
        self.assertNotIn("UNKNOWN", self.broker.subscribers)

    def test_unsubscribe_warns_when_event_is_empty(self):
        self.broker.unsubscribe("", MagicMock())
        self.broker.logger.warning.assert_called_once()

    def test_unsubscribe_warns_when_event_is_none(self):
        self.broker.unsubscribe(None, MagicMock())
        self.broker.logger.warning.assert_called_once()
