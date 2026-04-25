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

from unittest.mock import patch  # noqa: E402

from pdip.integrator.pubsub.base import message_broker as message_broker_module  # noqa: E402
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


class MessageBrokerLifecycle(TestCase):
    """Tests for ``initialize`` / ``start`` / ``join`` / ``close`` /
    ``get_publish_channel`` / ``__exit__``.

    The production broker spawns a ``multiprocessing.Manager`` server
    and two long-running threads (``MessageBrokerWorker``,
    ``EventListener``). Unit tests do not touch the real subprocess
    path: the manager factory is replaced with a ``MagicMock`` and the
    worker / listener constructors are patched so the broker talks to
    mocks it cannot distinguish from the real classes.

    The real multiprocessing-manager start-up and the real worker /
    listener threads are covered by the basic_app integration suite;
    see the skipped-paths note on the PR.
    """

    def setUp(self):
        self.logger = MagicMock(name="logger")
        self.broker = MessageBroker(logger=self.logger)

    def test_initialize_wires_manager_queues_channels_and_worker(self):
        fake_manager = MagicMock(name="manager")
        fake_manager.Queue.side_effect = [
            MagicMock(name="publish-queue"),
            MagicMock(name="message-queue"),
        ]
        with patch.object(
            message_broker_module, "_MP_CONTEXT"
        ) as mp_context, patch.object(
            message_broker_module, "MessageBrokerWorker"
        ) as Worker:
            mp_context.Manager.return_value = fake_manager

            self.broker.initialize()

            # Manager is acquired from the pinned spawn context.
            mp_context.Manager.assert_called_once_with()
            self.assertIs(self.broker.manager, fake_manager)
            # Two queues are requested from it: publish + message.
            self.assertEqual(fake_manager.Queue.call_count, 2)
            self.assertIsNotNone(self.broker.publish_channel)
            self.assertIsNotNone(self.broker.message_channel)
            # Worker is built with both channels and the logger.
            Worker.assert_called_once()
            kwargs = Worker.call_args.kwargs
            self.assertIs(kwargs["logger"], self.logger)
            self.assertIs(
                kwargs["publish_channel"], self.broker.publish_channel
            )
            self.assertIs(
                kwargs["message_channel"], self.broker.message_channel
            )

    def test_start_runs_worker_then_constructs_and_starts_listener(self):
        self.broker.worker = MagicMock(name="worker")
        self.broker.message_channel = MagicMock(name="message-channel")
        self.broker.subscribers = {"EVT": [MagicMock()]}
        with patch.object(
            message_broker_module, "EventListener"
        ) as Listener:
            listener_instance = MagicMock(name="listener")
            Listener.return_value = listener_instance

            self.broker.start()

            self.broker.worker.start.assert_called_once_with()
            Listener.assert_called_once_with(
                channel=self.broker.message_channel,
                subscribers=self.broker.subscribers,
                logger=self.logger,
            )
            listener_instance.start.assert_called_once_with()
            self.assertIs(self.broker.listener, listener_instance)

    def test_join_forwards_max_join_time_to_worker_and_listener(self):
        self.broker.worker = MagicMock(name="worker")
        self.broker.listener = MagicMock(name="listener")
        self.broker.max_join_time = 5

        self.broker.join()

        self.broker.worker.join.assert_called_once_with(5)
        self.broker.listener.join.assert_called_once_with(5)

    def test_get_publish_channel_returns_the_initialised_publish_channel(self):
        sentinel = MagicMock(name="publish-channel")
        self.broker.publish_channel = sentinel

        self.assertIs(self.broker.get_publish_channel(), sentinel)

    def test_close_stops_running_worker_listener_and_shuts_manager_down(self):
        worker = MagicMock(name="worker")
        worker.is_alive.return_value = True
        worker.stopped.return_value = False
        listener = MagicMock(name="listener")
        listener.is_alive.return_value = True
        listener.stopped.return_value = False
        manager = MagicMock(name="manager")
        self.broker.worker = worker
        self.broker.listener = listener
        self.broker.manager = manager

        self.broker.close()

        worker.stop.assert_called_once_with()
        listener.stop.assert_called_once_with()
        manager.shutdown.assert_called_once_with()

    def test_close_skips_stop_calls_when_threads_are_not_alive(self):
        worker = MagicMock(name="worker")
        worker.is_alive.return_value = False
        listener = MagicMock(name="listener")
        listener.is_alive.return_value = False
        self.broker.worker = worker
        self.broker.listener = listener
        self.broker.manager = None  # nothing to shut down

        self.broker.close()

        worker.stop.assert_not_called()
        listener.stop.assert_not_called()

    def test_close_skips_stop_calls_when_threads_are_already_stopped(self):
        worker = MagicMock(name="worker")
        worker.is_alive.return_value = True
        worker.stopped.return_value = True
        listener = MagicMock(name="listener")
        listener.is_alive.return_value = True
        listener.stopped.return_value = True
        self.broker.worker = worker
        self.broker.listener = listener
        self.broker.manager = None

        self.broker.close()

        worker.stop.assert_not_called()
        listener.stop.assert_not_called()

    def test_exit_delegates_to_close(self):
        with patch.object(self.broker, "close") as close:
            self.broker.__exit__(None, None, None)

            close.assert_called_once_with()
