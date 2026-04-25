"""Minimal pdip pub/sub example — observer pattern using ``TaskMessage``.

Run from the repo root:

    python examples/pubsub_observer/main.py

What this example shows
-----------------------

The smallest possible "subscribe + publish" round trip that
demonstrates pdip's pub/sub *contract* — a callback dict keyed by
event name, and a ``TaskMessage`` carrying ``event`` + ``args`` +
``kwargs`` as the on-the-wire shape every production publisher
emits. Two observers (``order_created_observer`` and
``payment_settled_observer``) register against two different event
names; the script then publishes one of each event and prints what
the observers saw.

Production pdip code wires this contract through
``pdip.integrator.pubsub.MessageBroker``, which adds:

  - a ``multiprocessing.Manager`` for cross-process publish/message
    channels,
  - a ``MessageBrokerWorker`` process that drains the publish channel,
  - an ``EventListener`` process that drains the message channel
    and invokes the registered callbacks.

The demo deliberately reaches one level lower — a tiny
``_SubscribersRegistry`` that holds the same callback dict shape
``MessageBroker.subscribers`` exposes, plus a ``dispatch`` helper
equivalent to the listener's callback loop. That keeps the example
free of multiprocessing setup, so it boots in milliseconds and
runs identically across every supported Python and OS combination
(3.10–3.14 × Linux / macOS / Windows). For the full multi-process
round trip, read the unit tests at
``tests/unittests/integrator/pubsub/test_message_broker.py``;
lifting the dispatch helper here into a real ``broker.initialize()
+ broker.start() + Publisher.publish()`` flow is mechanical.

This file is exercised by
``tests/unittests/examples/pubsub_observer/test_pubsub_observer_example.py``
so CI catches any framework change that regresses the demo.
"""

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

from pdip.integrator.pubsub.domain.message import TaskMessage  # noqa: E402


class _SubscribersRegistry:
    """Demo-only stand-in for ``MessageBroker.subscribers``.

    Holds the same callback-dict shape the real broker exposes
    (``{event_name: [callback, ...]}``) and adds a ``dispatch``
    helper equivalent to ``EventListener``'s callback loop. The
    real ``MessageBroker`` adds the multi-process publish / message
    channels around that core; the example skips them so it does
    not need to spawn processes.
    """

    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event, callback):
        if not callable(callback):
            raise ValueError("callback must be callable")
        if not event:
            raise ValueError("event cannot be empty")
        self.subscribers.setdefault(event, []).append(callback)

    def dispatch(self, message: TaskMessage):
        for callback in self.subscribers.get(message.event, []):
            callback(*(message.args or ()), **(message.kwargs or {}))


def make_observer(label, sink):
    """Return a callback that records the event payload to ``sink``."""

    def _observer(*args, **kwargs):
        sink.append({"observer": label, "args": args, "kwargs": kwargs})

    return _observer


def run():
    """Subscribe two observers, publish one of each event, return the sink."""

    sink = []
    registry = _SubscribersRegistry()

    registry.subscribe("OrderCreated", make_observer("order_created", sink))
    registry.subscribe("PaymentSettled", make_observer("payment_settled", sink))

    # An OrderCreated event with a primitive payload; the observer
    # records it.
    registry.dispatch(
        TaskMessage(
            event="OrderCreated",
            args=(42,),
            kwargs={"customer": "ada@example.com"},
        ),
    )

    # A PaymentSettled event with a dict payload — different shape,
    # different observer.
    registry.dispatch(
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
