# ADR-0006: Use a pub/sub message broker for integration lifecycle events

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** integrator, eventing

## Context

When the integrator runs an operation it executes a sequence of
integration steps that can run in the same process, in a thread pool, or
in worker subprocesses (see [ADR-0007](./0007-multiprocessing-for-etl.md)).
Observers of the run — loggers, progress trackers, external schedulers,
audit sinks — need to react to lifecycle events (initialised, started,
finished) without the executor knowing who is listening.

We need an eventing mechanism that:

- Works across process boundaries because workers are separate OS
  processes.
- Decouples the executor from the observers so adding a new observer
  does not require touching the executor.
- Is not a new infrastructure dependency: we cannot require Kafka or
  Redis just to observe a local ETL run.

## Decision

We implement a pub/sub message broker in
`pdip/integrator/pubsub/base/message_broker.py`. The broker:

- Uses `multiprocessing.Manager` queues so producers in worker processes
  can hand events to a consumer in the parent process.
- Exposes `subscribe(event, callback)` and `unsubscribe(event, callback)`
  to observers.
- Runs a `MessageBrokerWorker` process that drains the publish queue and
  an `EventListener` process that invokes subscribed callbacks.

The integration pipeline publishes a small, closed set of events
declared in `pdip/integrator/domain/enums/events.py`:

- `EVENT_EXECUTION_INTEGRATION_INITIALIZED`
- `EVENT_EXECUTION_INTEGRATION_STARTED`
- `EVENT_EXECUTION_INTEGRATION_FINISHED`

Event payloads are `TaskMessage` records (event name + keyword args).

## Consequences

### Positive

- The executor emits events without knowing who, if anyone, is
  listening. Observers attach themselves from outside the pipeline.
- Cross-process eventing works with stdlib primitives only. No new
  deployment dependency.
- The event catalogue is small and explicit, which keeps the contract
  reviewable.

### Negative

- Multiprocessing queues are not durable. If a subscriber crashes, events
  delivered during the crash are lost. For observability that is
  acceptable; for audit trails, subscribers must persist events
  themselves.
- Callbacks are invoked in a dedicated listener process. They must be
  picklable (no lambdas, no local closures) and should be cheap.
- Introducing a new event requires adding a constant to the enum and
  publishing it from the executor; we prefer this explicitness over
  free-form event strings.

### Neutral

- The broker is intentionally not exposed as an `ISingleton`. It is
  started and stopped per integration run because its lifecycle is
  tied to the run, not to the process.

## Alternatives considered

### Option A — Direct callbacks on the executor

- **Pro:** Zero infrastructure.
- **Con:** Executor would need a list of observers and would carry the
  coupling. Cross-process callbacks would not work without an IPC
  layer anyway.
- **Why rejected:** Does not survive the jump to worker subprocesses.

### Option B — An external broker (Kafka, Redis, NATS)

- **Pro:** Durable, scalable, well-known operational tooling.
- **Con:** Forces every pdip user to stand up an additional service
  just to run a local job.
- **Why rejected:** Disproportionate dependency for the framework's
  core observability. Users who need durability can subscribe and
  forward to their own broker.

### Option C — Python `logging` with structured handlers

- **Pro:** Already in the standard library.
- **Con:** Logging is one-way and designed for text; it does not match
  a typed event contract.
- **Why rejected:** Wrong tool for event-driven subscribers.

## Follow-ups

- If the catalogue grows, consider grouping events by domain (execution,
  connection, adapter) and adding per-group subscription helpers.

## References

- Code: `pdip/integrator/pubsub/base/message_broker.py`,
  `pdip/integrator/pubsub/publisher/publisher.py`,
  `pdip/integrator/pubsub/base/event_listener.py`,
  `pdip/integrator/domain/enums/events.py`
