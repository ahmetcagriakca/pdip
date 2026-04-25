# pdip pub/sub example — minimal observer pattern

The smallest possible "subscribe + publish" round trip on
`pdip.integrator.pubsub.MessageBroker`. Two observers register
against two different event names, the script publishes one of
each, and the observers record what they saw.

## Run it

From the repo root after `pip install -e ".[integrator]"`:

```bash
python examples/pubsub_observer/main.py
```

Expected output:

```
Observed 2 event(s):
  order_created    args=(42,)  kwargs={'customer': 'ada@example.com'}
  payment_settled  args=()  kwargs={'order_id': 42, 'amount_cents': 1999}
```

## What it shows (and what it deliberately doesn't)

The example exercises pdip's **subscribe / dispatch contract** —
`broker.subscribe(event, callback)` to register, `broker.subscribers[event]`
as the in-memory routing table, and a `TaskMessage` carrying
`event` + `args` + `kwargs` as the on-the-wire shape every
production publisher emits.

It does **not** boot the multi-process pipeline that production
pdip uses. The real path is:

1. `broker.initialize()` creates a `multiprocessing.Manager` and
   the publish + message channels.
2. `broker.start()` launches a `MessageBrokerWorker` process and
   an `EventListener` process.
3. A `Publisher(broker.publish_channel).publish(message)` puts
   the `TaskMessage` on the publish channel.
4. The worker process forwards it to the message channel.
5. The listener process drains the message channel and invokes
   the callbacks registered in `broker.subscribers`.

Skipping that machinery in the demo makes the example boot in
milliseconds, run identically on Linux / macOS / Windows, and
work on every supported Python version (3.10–3.14) without
worrying about the spawn-vs-fork shift in 3.14. The
[unit tests for `MessageBroker`](../../tests/unittests/integrator/pubsub/test_message_broker.py)
cover the multi-process round trip; once a contributor needs to
demo or extend that path, lifting the dispatch from
`examples/pubsub_observer/main.py::dispatch` into a real
`broker.initialize() / broker.start() / publisher.publish()` flow
is mechanical.

## Why these two events

`OrderCreated` and `PaymentSettled` are the canonical pdip-style
event names — short, past-tense, business-domain language. The
two observers carry different label / payload shapes so the
example demonstrates that subscriptions are independent: the
`OrderCreated` observer never fires on `PaymentSettled` and
vice versa.
