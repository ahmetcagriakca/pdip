# Development setup

This page walks through getting a local pdip checkout ready for
development. See [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) for
broader contribution guidance and
[`../governance/`](../governance/README.md) for the architectural
context.

## Prerequisites

- **Python 3.10+** (both the CI matrix floor and the package's
  `python_requires` declaration; see
  [ADR-0028](../governance/adr/0028-raise-python-floor-to-3-10.md),
  which supersedes the floor half of
  [ADR-0020](../governance/adr/0020-raise-python-floor-to-3-9.md)).
- `git`.
- A C toolchain if you plan to install the `[integrator]` extra from
  source: `oracledb`, `pyodbc`, `psycopg2`, and `mysql-connector` can
  require system libraries on some platforms.

## Clone and install

```bash
git clone https://github.com/ahmetcagriakca/pdip.git
cd pdip

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install runtime dependencies the CI uses
pip install -r requirements.txt

# Optional: editable install so `import pdip` resolves to this checkout
pip install -e .
```

If you only need a subset, install the matching extras instead:

```bash
pip install -e ".[api]"
pip install -e ".[integrator]"
pip install -e ".[api,integrator,cryptography]"
```

## Install pre-commit hooks

pdip uses [pre-commit](https://pre-commit.com/) to run the
ADR-0026 / ADR-0027 §5 quality rules and the same blocking flake8
selection as CI **before** a commit leaves your machine. This
catches the common violations (missing assertion, tautology,
pragma-without-reason, star import, long sleep) in ~300 ms instead
of waiting for CI.

```bash
# ``pre-commit`` is already listed in requirements.txt, so it is
# installed by the step above. Register the git hook once:
pre-commit install

# Optionally run every hook against every file right now (normally
# pre-commit only runs on staged files at commit time):
pre-commit run --all-files
```

Uninstall later with `pre-commit uninstall` if you ever need the
raw `git commit` behaviour back.

## Run the tests

```bash
# All unit tests (same as CI)
python run_tests.py

# With coverage — ``.coveragerc`` at the repo root owns the
# source + omit + fail_under settings, so no flags needed.
coverage run run_tests.py
coverage report --fail-under=100
coverage html                                        # writes htmlcov/
```

More granular test invocations (per module, with `--locals`, etc.) are
in [`../../readme.test.md`](../../readme.test.md).

## Linting

CI runs `flake8` with two passes — see
[`.github/workflows/package-build-and-tests.yml`](../../.github/workflows/package-build-and-tests.yml).
The pre-commit hook (registered above) runs the blocking pass
locally before each commit; the warning pass is advisory and
runs only on CI.

```bash
pip install flake8

# Blocking pass: hard-fails CI on any hit. Matches the pre-commit
# hook in .pre-commit-config.yaml.
flake8 . --count --select=E9,F63,F7,F82,E711,E712,E722 --show-source --statistics

# Advisory pass: CI runs with --exit-zero so warnings never block.
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Run the machine-checked quality rules

The six ADR-0026 / ADR-0027 §5 rules live in a single `unittest`
module and are run automatically by the `pre-commit` hook above,
by CI, and can be invoked directly:

```bash
python -m unittest tests.unittests.quality_guard.test_conventions
```

A hit from this suite blocks the commit / CI run; see
[ADR-0026](../governance/adr/0026-test-quality-rules.md) and
[ADR-0027](../governance/adr/0027-tdd-with-diff-coverage.md) for
the rules and the rationale.

## Branching

Follow the branching rule in [`CONTRIBUTING.md`](../../CONTRIBUTING.md):
develop on the feature branch you have been assigned, commit with
descriptive messages, and push only to that branch.

Architectural changes require a new ADR. See the
[governance README](../governance/README.md) for the process and
[`docs/governance/adr/template.md`](../governance/adr/template.md) for
the template.

## Troubleshooting

- **`oracledb` thin-mode isn't enough.** The `[integrator]` extra
  installs `python-oracledb` (per
  [ADR-0021](../governance/adr/0021-cx-oracle-to-python-oracledb.md)),
  which runs in pure-Python thin mode by default — no Instant Client
  required. If you need thick mode for an older Oracle server, install
  the Oracle Instant Client for your platform and export its path
  (`LD_LIBRARY_PATH` on Linux, `DYLD_LIBRARY_PATH` on macOS, `PATH` on
  Windows).
- **`pyodbc` fails to install.** Install an ODBC development package
  (`unixodbc-dev` on Debian/Ubuntu, `unixodbc` via Homebrew on macOS).
- **Tests cannot find a database.** Integration tests under
  `tests/integrationtests/` expect the connection strings defined in
  `tests/environments/`. Copy the template that matches your setup and
  export `ENVIRONMENT=<name>` before running.
