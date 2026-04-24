# Dependency security audit — 2026-04-24

This report captures the state of pdip's declared dependencies at the
time it was written and flags versions that warrant a Dependabot or
manual review. It is a *snapshot*; any action taken against it should
re-check against the current vulnerability databases at the time of the
upgrade.

## Scope

- Runtime dependencies declared in [`setup.py`](../../setup.py) and
  pinned in [`requirements.txt`](../../requirements.txt) as of commit
  `f9e3db3`.
- GitHub's Dependabot reported **13 open vulnerabilities** on the
  default branch at audit time (1 high, 9 moderate, 3 low). This
  report does not copy the Dependabot dashboard; consult
  <https://github.com/ahmetcagriakca/pdip/security/dependabot> for the
  authoritative list.

## Declared versions (snapshot)

From `setup.py` extras and `requirements.txt`:

| Package | Pin | Extra | Notes |
|---|---|---|---|
| `injector` | `0.22.0` | `preferred` / runtime | Small DI library, stable API. Bumped from 0.21.0 alongside this report. |
| `SQLAlchemy` | `2.0.35` | `preferred` / runtime | 2.0.x line; check for 2.0.x patch releases. |
| `PyYAML` | `6.0.1` | `preferred` / runtime | — |
| ~~`dataclasses`~~ | ~~`0.6`~~ | — | Removed as part of this audit; Python 3.6 backport is a no-op on `python_requires >= 3.8`. |
| `dataclasses-json` | `0.6.7` | `integrator` | — |
| `pandas` | `2.2.2` | `integrator` | — |
| `pyodbc` | `5.1.0` | `integrator` | — |
| `psycopg2-binary` | `2.9.9` | `integrator` | — |
| `mysql-connector-python` | `8.4.0` | `integrator` | — |
| `cx_Oracle` | `8.3.0` | `integrator` | Superseded by `python-oracledb`; see action items. |
| `kafka-python` | `2.0.2` | `integrator` | `kafka-python` has been stagnant; consider `kafka-python-ng` or `confluent-kafka`. |
| `func-timeout` | `4.3.5` | `integrator` | — |
| `Flask` | `3.0.3` | `api` | Current 3.x. |
| `Flask-Cors` | `5.0.0` | `api` | — |
| ~~`Flask-Ext`~~ | ~~`0.1`~~ | — | Removed as part of this audit; no imports found in `pdip/` or `tests/`. |
| `Flask-Injector` | `0.15.0` | `api` | Pinned to an older minor; check compatibility with current `injector`. |
| `flask-restx` | `1.3.0` | `api` | — |
| `Werkzeug` | `3.0.3` | `api` | Known advisories historically around this minor; re-check. |
| `markupsafe` | `2.1.5` | `api` | — |
| `cryptography` | `43.0.0` | `cryptography` | Active CVE surface; always keep current. |
| ~~`Fernet`~~ | ~~`1.0.1`~~ | — | Removed as part of this audit; pdip uses `cryptography.fernet.Fernet` from the `cryptography` package. |
| `coverage` | `7.5.1` | dev only | — |

## Observations

1. **Stale / ambiguous packages**
   - `Flask-Ext==0.1` is effectively abandoned. If pdip still uses it,
     the import should be replaced by Flask's modern extension
     machinery.
   - `Fernet==1.0.1` is a third-party wrapper; `cryptography`'s own
     `cryptography.fernet.Fernet` makes it redundant.
   - `dataclasses==0.6` is a backport for Python < 3.7. pdip requires
     Python 3.8+, so this pin does nothing on any supported runtime.
2. **Packages with newer maintained forks**
   - `cx_Oracle` is replaced by `python-oracledb` for new development.
     Keeping `cx_Oracle` is fine for compatibility but future work
     should target `python-oracledb`.
   - `kafka-python` has been largely idle; `kafka-python-ng` is a
     community fork with patch activity. Decide per
     [ADR-0012](adr/0012-connection-source-target-adapters.md) whether
     to switch the Kafka adapter.
3. **Dependabot backlog**
   - 13 open alerts on the default branch at audit time. Most appear
     to be transitive; a few are likely direct (`cryptography`,
     `Werkzeug`, possibly `SQLAlchemy` patch releases). Triage should
     happen against the live dashboard.

## Recommended actions

In order of impact / risk:

1. **Clear the Dependabot queue.** Open PRs for each alert, group them
   by package where possible, and run the full test matrix per PR. No
   blanket bump without CI; native drivers (`cx_Oracle`, `pyodbc`,
   `psycopg2-binary`) are particularly prone to ABI drift.
2. **Remove redundant pins.**
   - Drop `dataclasses==0.6` from `install_requires` and the
     `preferred` extras in `setup.py`.
   - If `Fernet` (the PyPI package, not `cryptography.fernet.Fernet`)
     is not imported anywhere, remove it from the `cryptography`
     extra.
   Both are mechanical changes and should land with test confirmation.
3. **Audit `Flask-Ext==0.1` usage.** If there are no references in
   `pdip/`, drop it from the `api` extra. If there are, replace with
   the modern equivalent.
4. **Plan driver modernisation.** Raise ADRs for:
   - Migration from `cx_Oracle` to `python-oracledb`.
   - Replacement or supplementation of `kafka-python` with a
     maintained fork.
   Each would be a behaviour-affecting change and deserves a decision
   record.
5. **Publish a Dependabot policy.** Document which upgrades auto-merge,
   which require review, and who owns the backlog. An ADR is a
   reasonable home for this policy.

## Non-actions (deliberate)

- This report **does not** propose version bumps in a single commit.
  Dependency changes in this package directly affect every downstream
  consumer, and blanket bumps without a green CI run across the full
  3.9 / 3.10 / 3.11 × Linux / macOS / Windows matrix would be
  irresponsible.
- This report does not change `setup.py` or `requirements.txt`.

## Follow-up log

Actions taken after the original audit:

- **2026-04-24** — Safe patch-level bumps landed via PR #44
  (coverage 7.6.10, cryptography 43.0.1, pandas 2.2.3, PyYAML 6.0.2,
  Werkzeug 3.0.6).
- **2026-04-24** — Dependency cleanup and policy work:
  - Removed redundant pins: `dataclasses==0.6` (backport, no-op on
    Python 3.8+), `Fernet==1.0.1` (pdip uses `cryptography.fernet.Fernet`
    and never imported the third-party `Fernet` package), and
    `Flask-Ext==0.1` (no imports anywhere in the codebase).
  - `injector` bumped 0.21.0 → 0.22.0 (PR #28 closed as merged via
    cleanup). 0.22 adds PEP 593 `Annotated` support and drops Python
    3.7; neither affects pdip.
  - `mysql-connector-python` **kept at 8.4.0**. Dependabot PR #37
    proposed 9.1.0, which removes Python 3.8 support; ADR-0017 blocks
    this until the Python floor is raised deliberately. PR #37 closed
    with a link to ADR-0017.
- **Open items**
  - `cx_Oracle` → `python-oracledb` migration still needs an ADR.
  - `kafka-python` maintenance status still needs a decision.
  - CI matrix does not yet include Python 3.8 even though
    `python_requires >= 3.8`; widening the matrix would catch future
    floor regressions (see ADR-0017's follow-ups).

## How to use this report

1. Cross-reference each row with the live Dependabot dashboard.
2. Open a dedicated PR per maintenance theme (e.g. "bump web layer",
   "bump crypto layer") so CI can prove each slice.
3. When a decision is structural (drop a package, migrate to a fork),
   write an ADR and link it from this report.

---

*Prepared on 2026-04-24. Re-run the audit when CI dependencies change
materially, or every six months, whichever is sooner.*
