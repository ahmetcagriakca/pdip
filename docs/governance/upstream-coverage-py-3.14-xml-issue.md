# Draft — upstream coverage.py issue: `coverage xml` fails on Python 3.14 runners

Not filed yet. This page holds the draft so a maintainer can copy it
into a new issue at <https://github.com/nedbat/coveragepy/issues/new>
when they have time, along with whatever fresh reproducer run the
current CI matrix gives.

## Context for why we hold this draft here

The pdip CI matrix scopes `coverage xml` (and by extension the
`diff-cover` gate) to a single canonical cell — Python 3.11 on
ubuntu-latest — because `coverage xml` fails on **all three** 3.14
cells (ubuntu, macos, windows). The other cells run
`coverage run run_tests.py` + `coverage report` fine.

This isn't fixed by upgrading coverage.py: versions 7.6.12
(ships with CPython bundles), 7.10.7 (last release with 3.9 +
3.14 classifiers), and 7.13.5 (latest, requires ≥3.10) all
reproduce the failure. The workaround lives in
`.github/workflows/package-build-and-tests.yml` and is documented
in [ADR-0023 §5](./adr/0023-coverage-floor-policy.md) and
[ADR-0028 Decision](./adr/0028-raise-python-floor-to-3-10.md).

Filing upstream closes the loop: either `coverage.py` lands a fix
and we can un-scope `coverage xml` back to every cell, or the
response clarifies that the failure is in a downstream dependency
(for instance a C-extension build) and we can file it there instead.

## Draft issue title

> `coverage xml` / `coverage html` fail on Python 3.14 matrix cells across 7.6.x, 7.10.x, and 7.13.x

## Draft issue body

> **Environment**
>
> - coverage.py versions tried: `7.6.12`, `7.10.7`, `7.13.5` — all fail identically.
> - Python: 3.14 (as provided by `actions/setup-python@v5` with `allow-prereleases: true` on `ubuntu-latest`, `macos-latest`, `windows-latest`).
> - Project: <https://github.com/ahmetcagriakca/pdip> — unit suite (≈665 tests, 100 % line coverage on `pdip/`).
>
> **Behaviour**
>
> The following flow succeeds on Python 3.10–3.13 on the same runners and with the same `.coveragerc`:
>
> ```
> coverage run run_tests.py       # OK
> coverage report --fail-under=0  # OK
> coverage xml                    # FAILS on Python 3.14 only
> ```
>
> `coverage run` produces a `.coverage` file and `coverage report` formats it without issue. The failure is specifically in the XML report generator (and, the same symptom, `coverage html`). Up the matrix on 3.10–3.13 on all three OSes, and down on 3.14 on all three OSes — deterministic.
>
> Because admin-only API access is needed to pull the raw workflow log, we have not captured the specific traceback. The failure is fast (< 2 s from the `coverage xml` invocation to a non-zero exit) and the job surfaces no stderr in the check-run output field.
>
> **What we've tried**
>
> 1. Upgrading from 7.6.12 → 7.13.5 — no change, both fail on 3.14. (Also verified that 7.13.5 requires `>=3.10`, so we raised our floor.)
> 2. Switching to 7.10.7 (last release still classifying 3.9) — no change on 3.14.
> 3. Scoping `coverage xml` to Python 3.11 only — the workaround, avoids the symptom, doesn't explain it.
>
> **Reproducer**
>
> Smallest reproducer we can distil from pdip is the test suite itself (100 % coverage, mixed SQLAlchemy / Flask / injector / multiprocessing). We can attempt a trimmed standalone reproducer if the above is enough to confirm it's on the coverage side. Pointer:
>
> - Workflow: [`package-build-and-tests.yml`](https://github.com/ahmetcagriakca/pdip/blob/main/.github/workflows/package-build-and-tests.yml) — the canonical-cell scoping is the `if: matrix.python == '3.11' && matrix.os == 'ubuntu-latest'` gate on the XML step.
> - Configuration: [`.coveragerc`](https://github.com/ahmetcagriakca/pdip/blob/main/.coveragerc).
>
> **Ask**
>
> What's the best way to capture the XML-report-side traceback on a public runner without admin API access? Would the XML reporter emit to stderr reliably if we added `--debug=trace` around the failing call? Happy to run whatever probe would help — the reproducer is free.
>
> **Why we care**
>
> Per-cell `coverage xml` upload is useful for artefact diffing when a regression only shows on one Python version. Scoping to the canonical cell works but hides Python-version-specific coverage drift. A proper fix (or a clear statement that this is expected pending a 3.14 final release) lets us un-scope.

## When to file

- After 3.14 reaches final / stable upstream — to rule out "pre-release runner".
- After we produce a minimal standalone reproducer, or confirm the above is enough.
- At any time, if a collaborator on coverage.py or the maintainers explicitly ask about it.

## How to file

```bash
gh issue create \
    --repo nedbat/coveragepy \
    --title "coverage xml / coverage html fail on Python 3.14 matrix cells across 7.6.x, 7.10.x, and 7.13.x" \
    --body-file docs/governance/upstream-coverage-py-3.14-xml-issue.md  # trim header first
```

…or paste the body via the web UI. Link the resulting issue number
back into ADR-0028's Follow-ups table so the canonical-cell
workaround has a clear deprecation trigger.
