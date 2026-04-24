# Development setup

This page walks through getting a local pdip checkout ready for
development. See [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) for
broader contribution guidance and
[`../governance/`](../governance/README.md) for the architectural
context.

## Prerequisites

- **Python 3.9+** (CI runs 3.9, 3.10, 3.11; the package declares
  `python_requires >= 3.8`).
- `git`.
- A C toolchain if you plan to install the `[integrator]` extra from
  source: `cx_Oracle`, `pyodbc`, `psycopg2`, and `mysql-connector` can
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

## Run the tests

```bash
# All unit and integration tests (same as CI)
python run_tests.py

# With coverage
coverage run --source=pdip run_tests.py
coverage report -m --omit="*/tests/*,*/site-packages/*"
coverage html --omit="*/tests/*,*/site-packages/*"   # writes htmlcov/
```

More granular test invocations (per module, with `--locals`, etc.) are
in [`../../readme.test.md`](../../readme.test.md).

## Linting

CI runs `flake8` with two passes — see
[`.github/workflows/package-build-and-tests.yml`](../../.github/workflows/package-build-and-tests.yml):

```bash
pip install flake8

# Fail on syntax errors / undefined names (CI hard-fails on this)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Warnings pass (CI runs with --exit-zero)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

## Branching

Follow the branching rule in [`CONTRIBUTING.md`](../../CONTRIBUTING.md):
develop on the feature branch you have been assigned, commit with
descriptive messages, and push only to that branch.

Architectural changes require a new ADR. See the
[governance README](../governance/README.md) for the process and
[`docs/governance/adr/template.md`](../governance/adr/template.md) for
the template.

## Troubleshooting

- **`cx_Oracle` fails to install.** Install the Oracle Instant Client
  for your platform and export its path (`LD_LIBRARY_PATH` on Linux,
  `DYLD_LIBRARY_PATH` on macOS, `PATH` on Windows).
- **`pyodbc` fails to install.** Install an ODBC development package
  (`unixodbc-dev` on Debian/Ubuntu, `unixodbc` via Homebrew on macOS).
- **Tests cannot find a database.** Integration tests under
  `tests/integrationtests/` expect the connection strings defined in
  `tests/environments/`. Copy the template that matches your setup and
  export `ENVIRONMENT=<name>` before running.
