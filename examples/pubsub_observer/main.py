"""Minimal pdip pub/sub example — observer pattern over ``MessageBroker``.

Run from the repo root:

    python examples/pubsub_observer/main.py

What this example shows
-----------------------

The smallest possible "subscribe + publish" round trip on
``pdip.integrator.pubsub.MessageBroker``. Two observers
(``order_created_observer`` and ``payment_settled_observer``)
register against two different event names; the script then
publishes one of each event and prints what the observers saw.

Production pdip code wires the broker through its multi-process
``Manager`` + ``MessageBrokerWorker`` + ``EventListener``
pipeline (see ``pdip/integrator/pubsub/base/message_broker.py``).
This example **does not** boot the worker / listener processes —
it exercises only the ``subscribers`` dict + the in-process
dispatch helper below, so the demo runs in milliseconds and works
identically on every supported Python version. The README points
at the integration test under
``tests/integrationtests/`` (none yet — see
ADR-0029 §Follow-ups) for the full multi-process round trip.

This file is exercised by
``tests/unittests/examples/pubsub_observer/test_pubsub_observer_example.py``
so CI catches any framework change that regresses the demo.
"""

import logging
import os
import sys

# When invoked as ``python examples/pubsub_observer/main.py`` Python
# adds only the script's own directory to ``sys.path``. Prepend the
# repo root so ``from pdip…`` resolves the same way it does under
# ``unittest`` / pytest.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from pdip.integrator.pubsub.base.message_broker import MessageBroker  # noqa: E402
from pdip.integrator.pubsub.domain.message import TaskMessage  # noqa: E402


def make_observer(label, sink):
    """Return a callback that records the event payload to ``sink``."""

    def _observer(*args, **kwargs):
        sink.append({"observer": label, "args": args, "kwargs": kwargs})

    return _observer


def dispatch(broker, message: TaskMessage):
    """In-process equivalent of ``EventListener``'s callback loop.

    Production pdip drops a ``TaskMessage`` on the broker's publish
    channel and a worker process pushes it through to the listener,
    which then iterates ``broker.subscribers[event]`` and calls each
    callback with the message's ``args`` / ``kwargs``. We do the
    same thing inline here so the demo does not need to spawn
    processes.
    """

    callbacks = broker.subscribers.get(message.event, [])
    for callback in callbacks:
        callback(*(message.args or ()), **(message.kwargs or {}))


def run():
    """Subscribe two observers, publish one of each event, return the sink."""

    sink = []

    # The broker logs to a standard library logger; any logger works
    # for this demo because we never reach the warn/error code paths
    # that would actually emit.
    broker = MessageBroker(logger=logging.getLogger("pdip.examples.pubsub"))

    broker.subscribe("OrderCreated", make_observer("order_created", sink))
    broker.subscribe("PaymentSettled", make_observer("payment_settled", sink))

    # An OrderCreated event with a primitive payload; the observer
    # records it.
    dispatch(
        broker,
        TaskMessage(
            event="OrderCreated",
            args=(42,),
            kwargs={"customer": "ada@example.com"},
        ),
    )

    # A PaymentSettled event with a dict payload — different shape,
    # different observer.
    dispatch(
        broker,
        TaskMessage(
            event="PaymentSettled",
            args=(),
            kwargs={"order_id": 42, "amount_cents": 1999},
        ),
    )

    return sink


def main():
    sink = run()
    print(f"Observed {len(sink)} event(s):")
    for entry in sink:
        print(f"  {entry['observer']:<16}  args={entry['args']}  kwargs={entry['kwargs']}")


if __name__ == "__main__":
    main()
