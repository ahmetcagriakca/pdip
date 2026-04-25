# ADR-0031: Auto-open a tracking issue on two consecutive nightly integration failures

- **Status:** Proposed
- **Date:** 2026-04-25
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, automation, governance
- **Supersedes:** [ADR-0029](./0029-integration-tests-in-ci.md) §6 in
  part — the "no automatic issue" rule is replaced for the
  two-consecutive-failure case; the rest of §6 (manual review for a
  single failure, release-cut blocker for ≥ 2) stays.

## Context

ADR-0029 §6 set the failure policy when the nightly integration
workflow first landed:

> A nightly failure opens no automatic issue. Maintainers review
> the run via the Actions tab on the day after.
> A `workflow_dispatch` failure is expected to be investigated by
> the maintainer who triggered it.
> Consecutive nightly failures (two or more days) should be flagged
> as a blocker in the next release cut per ADR-0024 §3.1.

That policy was conservative on purpose — the workflow had no track
record, the maintainer pool is small, and noisy auto-issues for a
flaky single-night failure (e.g. a Docker Hub mirror hiccup) would
have produced more friction than signal. ADR-0029's `## Follow-ups`
list flagged the auto-issue idea as a *conditional* future change:

> If failures pile up, introduce a lightweight "open an issue on
> two consecutive red nights" step …

The situation today:

- The integration workflow has now run against four real backends
  (Postgres 16, MySQL 8.4, Oracle XE 21c, SQL Server 2022 — see
  PRs #98, #100, #105). The MSSQL and Oracle jobs each took two
  iterations to land; the historical patch rate on this workflow is
  not zero, and a future driver bump could land a regression that
  the daily-Actions-tab check misses on the day it arrives.
- The maintainer pool is still small. A nightly failure that
  surfaces only via an Actions-tab notification depends on at least
  one maintainer remembering to look the next morning.
- We now have a code-scanning alert path (PR #104 added explicit
  workflow `permissions:`), and the GitHub MCP integration in this
  repository's tooling demonstrates that issue create / update is a
  routine, low-risk operation.

The cost of leaving the gap is bounded but real: a failing nightly
that goes unnoticed for several days delays the time-to-detect for
any downstream regression and erodes the value ADR-0029 set out to
deliver.

## Decision

We adopt a **two-consecutive-failure trigger** for an automatically
opened tracking issue:

### 1. Trigger condition

A new workflow opens (or appends to) a single tracking issue when
**both** of the following hold:

1. The most recent completed run of the
   `Integration tests (nightly)` workflow on the default branch
   ended with `conclusion: failure` for *at least one* job in the
   matrix (not just `cancelled` / `timed_out`).
2. The run immediately before it on the default branch ended the
   same way.

`workflow_dispatch` runs are excluded from the count — they are
maintainer-initiated and ADR-0029 §6 already places investigation
on the triggering maintainer.

### 2. Issue shape

A single open issue tracks the outage; a second consecutive failure
does **not** open a second issue. The workflow searches for an open
issue labelled `nightly-red` and updates it (adds a comment with the
new run URL and the names of the failing jobs) instead of creating a
duplicate.

When all backends pass on a subsequent nightly run, the workflow
adds a "resolved" comment and closes the issue automatically. The
next two-consecutive-failure window opens a fresh issue.

The issue body documents the affected backends, the run URLs, and a
link back to this ADR for context. The `nightly-red` label is
created on first use; no maintainer setup is required.

### 3. Permissions

The new workflow declares `permissions: { issues: write,
contents: read }` at the workflow level — the minimum needed to
create / comment on / close issues, with no write access to code
or releases. This sits below the per-job permissions floor pdip
adopted in PR #104 for `package-build-and-tests.yml`.

### 4. Implementation outline

A new file `.github/workflows/nightly-failure-tracker.yml`:

- Triggers on `workflow_run` for the
  `Integration tests (nightly)` workflow, completed event only,
  filtered to `branches: [main]`.
- One job that:
  1. Reads the *previous* workflow run on the same workflow + branch
     via `gh api repos/{owner}/{repo}/actions/workflows/<id>/runs`.
  2. Computes the trigger condition from §1.
  3. If true, calls `gh issue list --label nightly-red` to find an
     open tracker issue; if absent, calls `gh issue create`; if
     present, calls `gh issue comment`.
  4. If the *current* run is green and an open `nightly-red` issue
     exists, calls `gh issue close` after a confirming comment.

The workflow uses only `gh` calls available with the default
`GITHUB_TOKEN` — no PAT, no third-party action.

## Consequences

### Positive

- Time-to-detect for nightly regressions shrinks from "next time a
  maintainer remembers to look" to "the morning of the second
  failed nightly". For a regression introduced on day N, the issue
  fires day N+2 instead of an indefinite manual-review window.
- The single-issue-per-outage shape keeps the issue tracker quiet —
  a sustained outage produces one issue with comments, not a daily
  flood.
- The auto-close ties the lifecycle of the tracker to the workflow
  result, so a stale "nightly broken" issue cannot persist past the
  fix.
- Squeezes the gap that motivated ADR-0029's `## Follow-ups` bullet
  without taking ADR-0029 §6's other guarantees off the table
  (single-night failure stays manual; release-cut blocker stays).

### Negative

- **One more workflow file to maintain.** The tracker is small
  (~80 lines of YAML + a couple of `gh` commands) but it is real
  code that can rot if the GitHub Actions API changes.
- **Issue noise during a flaky window.** If the workflow itself is
  flaky (e.g. Docker Hub rate-limiting that resolves on retry), the
  tracker may open and close issues across consecutive nights. The
  trigger requires *two* failures to dampen this, and the
  single-issue shape limits the comment-spam blast radius.
- **`issues: write` permission scope.** Larger than the
  `contents: read` baseline most workflows in this repo run with.
  Bounded by sitting on its own workflow (no code-touching steps)
  and explicit declaration; CodeQL's
  `actions/missing-workflow-permissions` rule that PR #104 fixed
  stays satisfied.

### Neutral

- ADR-0024 §3.1's "two-or-more consecutive failures block the next
  release cut" provision is unchanged. The automated issue is a
  *signal* for that policy, not a replacement.
- Maintainer day-after review remains the right channel for a
  *single* nightly failure; this ADR explicitly does not auto-open
  an issue then.

## Alternatives considered

### Option A — Keep ADR-0029 §6 verbatim ("no automatic issue, ever")

- **Pro:** Zero new workflow code, no permission expansion.
- **Con:** Leaves the time-to-detect gap. The longer the workflow
  runs without auto-tracking, the more likely a regression slips
  past two consecutive nights without anyone noticing.
- **Why rejected:** The original §6 wording explicitly anticipated
  this revision via the `## Follow-ups` "if failures pile up"
  bullet. We are not changing the spirit of §6, just acting on the
  follow-up trigger condition it pre-described.

### Option B — Open an issue on the *first* failure

- **Pro:** Minimal latency; first failure surfaces immediately.
- **Con:** Noisy. A single Docker Hub blip, runner image
  regression, or upstream image GC creates a fresh issue every time.
  Maintainers learn to ignore the channel, defeating the purpose.
- **Why rejected:** ADR-0029 §6 already names the single-failure
  case as "review via the Actions tab" specifically to avoid this
  noise level. The two-failure threshold preserves that intent.

### Option C — Slack / email webhook instead of an issue

- **Pro:** Doesn't expand workflow `permissions:`; relies on
  external delivery.
- **Con:** pdip is a public open-source project without a shared
  Slack workspace or maintainer mailing list. The right surface for
  contributors to discover *and* discuss a regression is the issue
  tracker, where the conversation can also be referenced from a
  follow-up release-cut decision (ADR-0024 §3.1).
- **Why rejected:** Wrong channel for an open-source workflow.

### Option D — Schedule-only check (cron at 06:00 UTC)

- **Pro:** Simpler trigger; no `workflow_run` dependency.
- **Con:** Wastes a runner if no nightly happened (the cron in
  ADR-0029 §2 fires at 04:00 UTC, but failures or `workflow_dispatch`
  blow that schedule). The `workflow_run` trigger reacts to the
  *actual* workflow result, regardless of when it ran.
- **Why rejected:** Less accurate for the same maintenance cost.

## Follow-ups

- **Implementation PR** — adds
  `.github/workflows/nightly-failure-tracker.yml` and a smoke test
  (a manual `workflow_dispatch` against a known-failed run id). The
  PR moves this ADR's status to `Accepted — Implemented YYYY-MM-DD
  (PR #N)`, matching the ADR-0021 / ADR-0022 implementation-stamp
  convention.
- **ADR-0029 cross-reference** — once this lands, ADR-0029 §6 gains
  a one-line note pointing at this ADR for the
  two-consecutive-failure path.
- **Tuning window** — revisit after the first three months of
  nightly runs. If false-positive issue opens fire more than once
  per month, raise the threshold to three consecutive failures or
  add a same-day-fix exception (don't open if a maintainer-merged
  PR landed between the two failures).

## References

- ADR-0029 §6 / §Follow-ups: `docs/governance/adr/0029-integration-tests-in-ci.md`
- ADR-0024 §3.1: `docs/governance/adr/0024-release-process.md`
- PR #104 — workflow permissions baseline pdip adopted earlier in 2026-04
- GitHub Actions `workflow_run` event: <https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run>
- GitHub `gh issue` CLI: <https://cli.github.com/manual/gh_issue>
