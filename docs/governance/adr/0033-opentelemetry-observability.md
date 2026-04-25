# ADR-0033: OpenTelemetry observability via `pdip[observability]`

- **Status:** Accepted
- **Date:** 2026-04-25
- **Deciders:** pdip maintainers
- **Tags:** observability, telemetry, integrator, packaging

## Context

pdip jobs run in production as multi-process ETL pipelines and as
Flask-Restx services. When something goes wrong — a stuck integration,
a queue backing up, a slow query — operators today have only two
sources of evidence:

- The stdlib `logging` output that flows through the wrappers in
  `pdip/logging/loggers/console/`, `pdip/logging/loggers/file/`,
  `pdip/logging/loggers/sql/`. These are unstructured strings.
- Whatever the host application chooses to instrument.

There is no out-of-the-box way to answer "where did this 30-second
integration spend its time?", "how many rows did this batch move?",
or "did the connector retry?". OpenTelemetry has converged as the
cross-language standard for traces, metrics, and logs; emitting OTel
signals from the framework would let any OTLP-speaking backend
(Jaeger, Tempo, Honeycomb, Datadog, etc.) pick the data up without
per-backend integration code.

We deliberately do not want to take a hard dependency on
`opentelemetry-api` for users who do not need it — ADR-0014's extras
model exists for exactly this kind of optional capability.

## Decision

### 1. New optional extra: `pdip[observability]`

We add an `observability` extra to `setup.py` alongside `api`,
`integrator`, `cryptography`. It pulls:

- `opentelemetry-api` (interfaces only).
- `opentelemetry-sdk` (default in-process implementation).

We do **not** pin a specific exporter (OTLP/HTTP, OTLP/gRPC,
console). The host application chooses the exporter and configures
it through the standard `OTEL_*` environment variables documented by
upstream. pdip emits signals into whatever provider is registered;
if no provider is registered the OTel API ships a no-op default and
emission costs are negligible.

### 2. Lazy, no-op-by-default integration

Framework code never imports `opentelemetry` at module top-level. A
single internal helper module — `pdip/observability/` (new) — wraps
`opentelemetry.trace.get_tracer` / `metrics.get_meter` behind:

- `get_tracer(name)` — returns the OTel tracer if the extra is
  installed, otherwise returns a no-op tracer object whose
  `start_as_current_span` is a context manager that does nothing.
- `get_meter(name)` — symmetric.

This keeps the import-time cost of `pdip` unchanged for users who do
not install the extra and avoids `ImportError` at framework startup.
The pattern matches how ADR-0014 talks about gating extras.

### 3. Span hierarchy (traces)

The traced surface is the integrator and the CQRS dispatcher; we
explicitly do **not** auto-instrument SQLAlchemy, pandas, or the
Flask layer — those have first-party OTel instrumentations that the
host can opt into independently.

Span names use the `pdip.<area>.<operation>` convention:

| Span name | Where | Attributes (mandatory) |
|---|---|---|
| `pdip.integrator.job` | `pdip/integrator/base/integrator.py` :: `Integrator.run` | `pdip.integration.id`, `pdip.integration.name` |
| `pdip.integrator.step` | per integration step | `pdip.step.index`, `pdip.step.strategy` (`single`/`thread`/`process`/`async`) |
| `pdip.integrator.source.read` | `ConnectionSourceAdapter` call sites | `pdip.connection.type`, `pdip.connection.driver`, `pdip.batch.size` |
| `pdip.integrator.target.write` | `ConnectionTargetAdapter` call sites | `pdip.connection.type`, `pdip.connection.driver`, `pdip.batch.size`, `pdip.rows.written` |
| `pdip.cqrs.command` | `pdip/cqrs/dispatcher.py` :: `Dispatcher.dispatch` (command branch) | `pdip.cqrs.handler` |
| `pdip.cqrs.query` | same, query branch | `pdip.cqrs.handler` |
| `pdip.pubsub.publish` | `pdip/integrator/pubsub/base/message_broker.py` :: publish path | `pdip.pubsub.channel` |
| `pdip.pubsub.handle` | `EventListener` dispatch | `pdip.pubsub.channel`, `pdip.pubsub.handler` |

Cross-process span propagation: `pdip/processing/base/subprocess.py`
serialises the active span context into the task payload (W3C
`traceparent` header) and the worker rehydrates it on startup before
running the task. This is the only place we touch OTel context
manually; everywhere else uses `start_as_current_span`.

The async strategy added by [ADR-0032](./0032-hybrid-async-strategy.md)
reuses these span names with `pdip.step.strategy = "async"`; no new
spans are introduced for async execution.

### 4. Metric conventions

Metrics use the `pdip.*` namespace and follow OTel semantic
conventions for type:

| Metric name | Type | Unit | Attributes |
|---|---|---|---|
| `pdip.integrator.rows.read` | counter | rows | `pdip.connection.type`, `pdip.integration.name` |
| `pdip.integrator.rows.written` | counter | rows | `pdip.connection.type`, `pdip.integration.name` |
| `pdip.integrator.batch.duration` | histogram | s | `pdip.connection.type`, `pdip.step.strategy` |
| `pdip.integrator.errors` | counter | errors | `pdip.connection.type`, `error.type` |
| `pdip.cqrs.dispatch.duration` | histogram | s | `pdip.cqrs.handler`, `pdip.cqrs.kind` (`command`/`query`) |
| `pdip.pubsub.queue.depth` | up-down counter | messages | `pdip.pubsub.channel` |

Histograms use the OTel default explicit bucket boundaries; we do
not override them unless production data later shows a problem.

### 5. Logging bridge

We do **not** replace the existing logging stack from ADR-0006-era
loggers. Instead, when the extra is installed and a span is active,
log records emitted through `pdip/logging/` are tagged with the
current `trace_id` / `span_id` via OTel's logging instrumentation
(opt-in by the host: `LoggingInstrumentor().instrument()`). Records
emitted with no active span flow through unchanged.

### 6. Configuration

Configuration is by environment variable only (the OTel SDK already
reads `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`,
`OTEL_RESOURCE_ATTRIBUTES`, etc.). pdip itself adds **one** opt-in
toggle: `PDIP_OBSERVABILITY_ENABLED` — when unset or `0`, the lazy
helpers from §2 short-circuit to no-ops even if the extra is
installed. This matters because someone may install
`pdip[observability]` to *develop* against the API without wanting
emission in CI runs.

The toggle defaults to `0` to preserve the "install does not change
behaviour" promise; documentation and the README install table call
out that turning it on is a one-line `export`.

### 7. Stability under ADR-0034

The new public symbol set added by this ADR is:

- `pdip.observability.get_tracer`, `pdip.observability.get_meter`
  (re-exported from `pdip/observability/__init__.py`).
- The span and metric names in §3 and §4 — once shipped, they are
  part of the public contract under [ADR-0034](./0034-one-zero-readiness-criteria.md)
  and follow its deprecation policy. Renaming a span name is a
  minor-with-deprecation operation; removing one is a major.

## Consequences

### Positive

- Operators get traces and metrics for free across every connector
  and the CQRS dispatcher.
- The contract is OTel — no per-backend coupling, no per-vendor
  shim.
- Cross-process trace continuity through `Subprocess` makes
  multi-worker integrations debuggable for the first time.

### Negative

- Every call site that gets a span has a new line of code; the diff
  in the first-implementation PR is wide if shallow.
- The cross-process context propagation in `Subprocess` is the one
  place we write OTel plumbing by hand; it has to round-trip a
  string and survive pickling.
- Span and metric *names* become part of the public contract — a
  rename is a minor-with-deprecation. We have to pick well in the
  first implementation.

### Neutral

- The extra is opt-in; users who do not install it pay one extra
  function call (the no-op tracer) per traced site, which is
  irrelevant at integration scale.
- We do not auto-instrument SQLAlchemy / Flask / etc.; the host
  composes those instrumentations the same way they would in any
  OTel-using app.

## Alternatives considered

### Option A — Hard dependency on `opentelemetry-api`

- **Pro:** No lazy import dance.
- **Con:** Every user of `pdip[api]` or `pdip[cqrs]` pays for OTel
  even if they never emit a span.
- **Why rejected:** Violates ADR-0014's "core stays small" principle.

### Option B — Custom tracing API that *can* be backed by OTel

- **Pro:** Decouples our span vocabulary from upstream.
- **Con:** Reinvents OTel's data model and forces a translation
  layer at every backend.
- **Why rejected:** OTel is the standard; wrapping it adds churn for
  no portability win.

### Option C — Logs only (structured logging, no traces / metrics)

- **Pro:** Smaller surface, no dependency.
- **Con:** Cannot answer "where did the time go?" — that needs
  spans, which need a trace context.
- **Why rejected:** The questions operators ask in §Context are
  trace and metric questions, not log questions.

### Option D — Auto-instrument every connector library

- **Pro:** Zero pdip code change at adapter sites.
- **Con:** Every backend (oracledb, psycopg2, pyodbc, confluent-kafka,
  pandas) has its own auto-instrumentation maturity; we would inherit
  the worst of them and have to gate per-driver.
- **Why rejected:** Hand-rolling spans at the adapter boundary is
  five lines per adapter and gives consistent attributes.

## Follow-ups

- First-implementation PR: add `pdip/observability/` with the lazy
  helpers, the `observability` extra, and instrument
  `pdip/cqrs/dispatcher.py` (smallest surface, immediate value).
  TDD per ADR-0027: tests assert the no-op path is genuinely no-op
  and that the tracer path emits the documented span name.
- Second PR: instrument `Integrator.run` and the
  `ConnectionSourceAdapter` / `ConnectionTargetAdapter` call sites.
- Third PR: cross-process context propagation in `Subprocess`.
- Document the metric / span vocabulary in `docs/observability.md`
  in the first PR; that page is referenced from the README.
- Coordinate with [ADR-0032](./0032-hybrid-async-strategy.md) so the
  async strategy is instrumented under the same span names from day
  one.
- Coordinate with [ADR-0034](./0034-one-zero-readiness-criteria.md)
  so `pdip.observability` enters the public-API audit before 1.0.

## References

- Code seams: `pdip/cqrs/dispatcher.py`,
  `pdip/integrator/base/integrator.py`,
  `pdip/integrator/connection/base/connection_source_adapter.py`,
  `pdip/integrator/connection/base/connection_target_adapter.py`,
  `pdip/integrator/pubsub/base/message_broker.py`,
  `pdip/processing/base/subprocess.py`,
  `pdip/logging/`.
- [ADR-0006](./0006-pubsub-message-broker.md) — pub/sub broker that
  hosts the `pdip.pubsub.*` spans.
- [ADR-0014](./0014-optional-extras-packaging.md) — the extras
  pattern this ADR follows.
- [ADR-0027](./0027-tdd-with-diff-coverage.md) — TDD discipline for
  the implementation PRs.
- [ADR-0032](./0032-hybrid-async-strategy.md), [ADR-0034](./0034-one-zero-readiness-criteria.md)
  — concurrent ADRs that interact with this surface.
- External: [OpenTelemetry specification](https://opentelemetry.io/docs/specs/otel/),
  [OTel semantic conventions](https://opentelemetry.io/docs/specs/semconv/),
  [W3C Trace Context](https://www.w3.org/TR/trace-context/).
