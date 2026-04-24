# ADR-0022: Replace `kafka-python` with `confluent-kafka` for the Kafka adapter

- **Status:** Accepted — **Implemented 2026-04-24** (PR replacing
  `kafka_connector.py` + `setup.py` extra + unit tests).
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** dependencies, kafka, integrator

## Context

pdip's Kafka source/target adapter (under
`pdip/integrator/connection/bigdata/kafka/`) depends on
`kafka-python==2.0.2`, declared in the `integrator` extra of
[`setup.py`](../../../setup.py).

`kafka-python` has been **effectively unmaintained since 2020.** It
has no releases on PyPI for years, no merged fixes for current broker
features, and no support for Python 3.13 / 3.14 wheels. The project
still exists but is not moving.

Two candidate successors exist:

- **[`confluent-kafka`](https://pypi.org/project/confluent-kafka/)** —
  thin Python wrapper around `librdkafka`, maintained by Confluent,
  widely deployed in production, ships wheels for 3.9–3.14 on every
  supported OS. Used by most large Python Kafka deployments today.
- **[`kafka-python-ng`](https://pypi.org/project/kafka-python-ng/)** —
  a community fork that aims to keep the pure-Python original alive.
  Active patch stream, API-compatible with `kafka-python`, but
  smaller community and thinner production deployments.

The choice is between "closest to current code, smaller risk" and
"best-supported, larger upfront change".

[ADR-0019](./0019-python-314-adoption.md) flagged this as a blocker
for Python 3.14 readiness.

## Decision

We migrate the Kafka adapter to **`confluent-kafka`**.

### Stage 1 — replace the pinned dependency

- `setup.py` `integrator` extra:
  `kafka-python==2.0.2` → `confluent-kafka>=2.4,<3`.

### Stage 2 — code change

- Replace the `KafkaProducer` / `KafkaConsumer` imports with
  `confluent_kafka.Producer` / `confluent_kafka.Consumer`.
- Translate configuration keys (`bootstrap_servers` → `bootstrap.servers`,
  etc.) at the adapter boundary so callers' configuration shape is
  preserved.
- Keep the pdip-level adapter interface unchanged. Consumers of the
  Kafka connection type do not see a new surface.

### Stage 3 — tests

- The existing Kafka integration tests continue to exercise produce /
  consume round-trips.
- Add a unit test that asserts configuration keys are translated
  correctly at the adapter boundary.

### Stage 4 — release note

- **Breaking for downstream**: any app that reached into pdip's
  adapter internals and referenced `kafka` directly (there is none
  in the public API today) would break. The pdip-facing connection
  model in ADR-0012 is unchanged.
- Record the migration in `CHANGELOG.md` under **Changed**.

## Consequences

### Positive

- Runs on every Python version in the current and planned matrix
  (3.9 – 3.14).
- Uses the librdkafka client that Confluent and the broader Kafka
  ecosystem have hardened in production.
- Unblocks the final known dependency barrier for Python 3.14
  readiness.

### Negative

- `confluent-kafka` is a C extension. Installation on platforms
  without prebuilt wheels (rare) needs `librdkafka` development
  headers. This is the same constraint as our existing C
  dependencies (`psycopg2-binary`, `pyodbc`); we accept it.
- A small amount of adapter code changes. Tests protect it.

### Neutral

- The alternative `kafka-python-ng` is viable. We pick
  `confluent-kafka` because its production footprint is larger and
  its release cadence is reliable; but if a future contributor
  shows the C dependency is a real problem for their deployment, we
  revisit.

## Alternatives considered

### Option A — Keep `kafka-python 2.0.2`

- **Pro:** Zero change.
- **Con:** Unmaintained; no 3.13 / 3.14 wheels; broker-side feature
  gap widens over time.
- **Why rejected:** Dead driver.

### Option B — Switch to `kafka-python-ng`

- **Pro:** API-compatible with current code; no C dependency.
- **Con:** Smaller community; the project's longevity is less
  certain than `confluent-kafka`'s.
- **Why rejected:** Confluent-backed maintenance is a stronger
  long-term bet for a framework dependency.

### Option C — Drop Kafka entirely

- **Pro:** Smallest surface.
- **Con:** Kafka is a listed backend in our connection model
  (ADR-0012).
- **Why rejected:** We want to keep the backend, just refresh the
  driver.

## Follow-ups

- Implementation PR: Stages 1–3 together.
- Evaluate whether the C extension is acceptable for every
  contributor's development setup; surface an installation note in
  the README if wheel coverage ever regresses.

## References

- [`pdip/integrator/connection/bigdata/kafka/`](../../../pdip/integrator/connection/bigdata/kafka)
- [`setup.py`](../../../setup.py) — `integrator` extra
- `confluent-kafka-python` docs: <https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html>
- [ADR-0019](./0019-python-314-adoption.md) — flagged this as a
  blocker.
