# ADR-0025: Dependabot auto-merge policy

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** dependencies, ci, automation

## Context

Dependabot has been the primary source of dependency pressure in
this repository. The ADR chain from 0017 onward produced a backlog
of Dependabot PRs we triaged manually. Some are trivially safe
(a patch bump of `coverage` to pick up a bug fix); some need
careful review (a major bump of `Flask-Cors` or a driver swap).

Handling them all by hand is wasteful. Handling them all by
auto-merge is dangerous. We want a policy that treats the two
cases differently.

[ADR-0017](./0017-python-support-policy.md) already established
that **a dependency upgrade that narrows the supported Python
matrix is not auto-mergeable.** This ADR extends that with a rule
set for everything else.

## Decision

### 1. What auto-merges

A Dependabot PR auto-merges when **all** of the following are true:

1. It is a **patch-level bump** (third component of semver) of a
   library that is already pinned in `requirements.txt` or
   `setup.py`.
2. Every job on the CI matrix is green (including 3.9–3.14 ×
   Linux / macOS / Windows, coverage floor, CodeQL, Analyze).
3. The PR's changed files are **only** dependency manifests
   (`requirements.txt`, `setup.py`). No source or test edits.
4. The bump does **not** drop a Python version in pdip's
   supported window (ADR-0017 / ADR-0020).

Qualifying patch bumps are merged with the `merge` method and the
default merge commit message.

### 2. What waits for human review

A Dependabot PR is reviewed by a maintainer before merge when:

- The bump is **minor** or **major** (second or first component of
  semver). Even if CI is green, the release notes get a human read
  before it lands — breakage often hides in behaviour, not tests.
- The changed files extend beyond the two dependency manifests.
- The PR's CI has any red matrix cell.
- The bump touches a driver listed in the **integrator** extra
  (`oracledb`, `confluent-kafka`, `psycopg2-binary`,
  `mysql-connector-python`, `pyodbc`). These sit behind unit test
  stubs (ADR-0021, ADR-0022) but the real behaviour only shows up
  in integration tests, which CI does not run.

### 3. What is declined

A Dependabot PR is **closed without merging** when:

- The bump requires raising `python_requires` and no companion
  ADR raises the floor (ADR-0017). The PR is closed with a link
  to ADR-0017 so the policy is visible to the bot (and to
  anyone who opens the PR later).

### 4. Grouping

`dependabot.yml` groups patch-level bumps across the `pip`
ecosystem into one PR per week. Grouped PRs still auto-merge
when every package in the group satisfies rule 1. If any one
package would flag rule 1, the whole group waits for review.

### 5. Implementation

- `.github/dependabot.yml` enables grouped PRs.
- `.github/workflows/dependabot-auto-merge.yml` (to be added in a
  follow-up PR) uses the `dependabot/fetch-metadata` action to
  read the semver jump, and `gh pr merge --auto --merge` for
  qualifying PRs.
- Until the auto-merge workflow is wired up, maintainers apply
  this policy manually on each Dependabot PR. The decision table
  in this ADR is the script they follow.

### 6. Breaking-change sentinels

These keywords in a Dependabot PR title or release-notes block
always bump the PR out of auto-merge, regardless of semver:

- `drop support for Python`
- `remove` (followed by a public-API symbol)
- `breaking change`
- `CVE` (so a security bump gets explicit attention even if it's
  a patch)

## Consequences

### Positive

- Routine maintenance lands in minutes, not days. Security patch
  bumps (e.g. the recent `cryptography` 43 → 46 grouped with
  Flask / Werkzeug) don't sit around waiting for a human to look.
- Risky bumps still get a human. A driver swap has to pass the
  integrator-extras rule *and* be read.
- Policy is codified in one place; a new maintainer does not have
  to reason about each PR from first principles.

### Negative

- Auto-merge means a bad Dependabot PR that passes CI lands
  without human eyes. The existing unit-test suite (ADR-0018)
  plus the coverage floor (ADR-0023) are our only backstop. We
  accept this for patch-level bumps of already-pinned packages.
- The "breaking-change sentinel" list is a best-effort filter. A
  PR with careful release notes that avoid those phrases slips
  through.

### Neutral

- The policy does not govern **security advisories** reported by
  Dependabot Security Updates (not the version PRs). Those are
  triaged on the security dashboard; they get their own ADR when
  a concrete case calls for one.

## Alternatives considered

### Option A — Auto-merge every green Dependabot PR

- **Pro:** Simplest rule.
- **Con:** A minor or major bump with subtle behaviour changes
  lands unexamined. A few hours of human attention prevents a
  full release cycle of regressions.
- **Why rejected:** Too permissive.

### Option B — Human review for every Dependabot PR

- **Pro:** Nothing unreviewed reaches main.
- **Con:** Patch-level bumps are effectively always safe when CI
  is green. Requiring human review burns attention with no real
  risk reduction.
- **Why rejected:** Opportunity cost is real; attention is a
  budget, not a freebie.

### Option C — Only auto-merge dev-only dependencies

- **Pro:** Runtime deps always get a human.
- **Con:** The most common patch bumps (Flask, Werkzeug,
  cryptography) are runtime deps; excluding them means no
  auto-merge in practice.
- **Why rejected:** Most of the value is in runtime patch
  bumps.

## Follow-ups

- Add `.github/dependabot.yml` with group and schedule.
- Add `.github/workflows/dependabot-auto-merge.yml` that
  implements the rules above.
- Revisit this ADR once the auto-merge workflow has one release
  cycle of data — in particular, whether the
  integrator-extras exclusion is too broad.

## References

- [ADR-0017](./0017-python-support-policy.md) — Python support
  matrix is owned by `python_requires`.
- [ADR-0018](./0018-testing-strategy.md) — Testing pyramid and CI
  gating.
- [ADR-0023](./0023-coverage-floor-policy.md) — Coverage floor.
- [Dependabot fetch-metadata action](https://github.com/dependabot/fetch-metadata).
