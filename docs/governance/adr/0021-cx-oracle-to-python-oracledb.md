# ADR-0021: Migrate the Oracle adapter from `cx_Oracle` to `python-oracledb`

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** dependencies, oracle, integrator

## Context

pdip's Oracle source/target adapter (under
`pdip/integrator/connection/sql/oracle/`) depends on
`cx_Oracle==8.3.0`, declared in the `integrator` extra of
[`setup.py`](../../../setup.py).

`cx_Oracle` is the historical Python driver. Oracle's successor
project is **[`python-oracledb`](https://pypi.org/project/oracledb/)**,
and `cx_Oracle` is frozen — no new features, limited bug fixes, and no
active work toward Python 3.13 / 3.14 wheels.

Relevant differences:

- `python-oracledb` has a **"thin" mode** that removes the hard
  requirement on the Oracle Instant Client for most use cases. Our
  CI and contributors no longer need to install native Oracle
  libraries to boot the package.
- It publishes wheels for modern Python versions where `cx_Oracle`
  does not.
- API compatibility is designed to be drop-in for
  `cx_Oracle`. Most pdip usage is the DB-API 2.0 subset, which is
  unchanged.

[ADR-0019](./0019-python-314-adoption.md) flagged this as a blocker
for Python 3.14 readiness; [ADR-0020](./0020-raise-python-floor-to-3-9.md)
raised the Python floor to 3.9 and brought `python-oracledb`'s
supported window into range.

## Decision

We migrate the Oracle adapter from `cx_Oracle` to `python-oracledb`.
The work is staged:

### Stage 1 — replace the pinned dependency

- `setup.py` `integrator` extra: `cx_Oracle==8.3.0` → `oracledb>=2.0,<3`
  (floor on the first release line with stable thin-mode support).
- `requirements.txt` is unaffected (the driver never belonged in core
  requirements).

### Stage 2 — code change

Update the Oracle adapter import path:

- `import cx_Oracle` → `import oracledb`.
- Default to **thin mode** (`oracledb.init_oracle_client` is not
  called) so contributors do not need the Oracle Instant Client
  locally.
- Users who need **thick mode** (for features the thin driver does
  not cover — LOB streaming, external auth, etc.) enable it
  explicitly via a new connection option; we document the path but
  do not take it by default.
- Connection-string parsing should be identical; DB-API calls
  (`connect`, `cursor`, `execute`, `fetchmany`) are API-compatible.

### Stage 3 — tests

- The existing Oracle integration tests
  (`tests/integrationtests/integrator/connection/sql/oracle/`) keep
  their contract but now require no native library.
- A new unit test mocks `oracledb` to assert we use thin mode by
  default.

### Stage 4 — release note

- **Breaking for downstream**: an app that imports `cx_Oracle` from
  pdip's namespace (there is none today) would break. An app that
  installs `pdip[integrator]` and expected `cx_Oracle` to come with
  it loses that dependency; they can install `cx_Oracle` themselves
  if they truly need it.
- Record the migration in `CHANGELOG.md` under **Changed** with a
  migration note for third-party adapters.

## Consequences

### Positive

- pdip installs cleanly on Python 3.13 / 3.14 on every OS the
  matrix covers.
- Contributors no longer need the Oracle Instant Client to run the
  package, which fixes the single largest contributor-experience
  rough edge.
- We stay on a maintained driver.

### Negative

- Any thick-mode-only features (rare) have to be opted into by
  callers. We surface this in the migration note.
- A small amount of adapter code changes. Tests protect it.

### Neutral

- `python-oracledb` has the same vendor and is actively developed
  by Oracle; there is no governance risk in taking it.

## Alternatives considered

### Option A — Keep `cx_Oracle`

- **Pro:** Zero change today.
- **Con:** Cannot install on 3.13 / 3.14 without native build tools;
  upstream is effectively frozen; every new Python release becomes
  a crisis.
- **Why rejected:** Sunset driver.

### Option B — Dual-driver support (both drivers optional)

- **Pro:** Maximum compatibility.
- **Con:** Two adapter code paths, two test suites, two bug reports
  when they disagree.
- **Why rejected:** Not worth the adapter-layer complexity.

### Option C — Drop Oracle entirely

- **Pro:** Smallest surface.
- **Con:** Oracle is a real customer workload.
- **Why rejected:** We want to keep the backend, just switch the
  driver.

## Follow-ups

- Implementation PR: Stages 1–3 together.
- Track whether `python-oracledb` ships wheels for any future
  Python we plan to add to the matrix.

## References

- [`pdip/integrator/connection/sql/oracle/`](../../../pdip/integrator/connection/sql/oracle)
- [`setup.py`](../../../setup.py) — `integrator` extra
- `python-oracledb` docs: <https://python-oracledb.readthedocs.io/>
- [ADR-0019](./0019-python-314-adoption.md) — flagged this as a
  blocker.
