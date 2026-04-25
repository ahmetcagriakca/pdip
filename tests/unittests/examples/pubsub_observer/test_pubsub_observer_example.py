"""Coverage gate for ``examples/pubsub_observer``.

Mirrors ``tests/unittests/examples/etl/test_etl_example.py`` and
``tests/unittests/examples/crud_api/test_crud_api_example.py`` — the
runnable example is loaded and exercised against its public
``run()`` entry point so a future change to ``TaskMessage`` or the
demo's subscribe/dispatch contract that breaks the example surfaces
in CI rather than when a contributor tries to follow the README.
"""

from unittest import TestCase

from examples.pubsub_observer.main import run


class TestPubsubObserverExample(TestCase):
    def test_run_returns_one_record_per_published_event(self):
        sink = run()

        self.assertEqual(len(sink), 2)

    def test_each_observer_only_sees_its_own_event(self):
        sink = run()

        observers_in_order = [entry["observer"] for entry in sink]
        self.assertEqual(observers_in_order, ["order_created", "payment_settled"])

    def test_order_created_observer_receives_args_and_kwargs(self):
        sink = run()

        order_event = sink[0]
        self.assertEqual(order_event["args"], (42,))
        self.assertEqual(order_event["kwargs"], {"customer": "ada@example.com"})

    def test_payment_settled_observer_receives_kwargs_only(self):
        sink = run()

        payment_event = sink[1]
        self.assertEqual(payment_event["args"], ())
        self.assertEqual(
            payment_event["kwargs"],
            {"order_id": 42, "amount_cents": 1999},
        )
