# ADR-0036: Automating the warning-bearing-prior-release check for public-API removals

- **Status:** Accepted
- **Date:** 2026-04-25
- **Deciders:** pdip maintainers
- **Tags:** testing, ci, quality, governance, api, release
- **Extends:** [ADR-0034](./0034-one-zero-readiness-criteria.md)
  (1.0 readiness — §3 deprecation policy currently enforced in
  review),
  [ADR-0035](./0035-public-api-signature-snapshot-guard.md)
  (signature-snapshot guard — Follow-ups list this automation as
  the only remaining open item)

## Context

[ADR-0034](./0034-one-zero-readiness-criteria.md) §3 says a public
symbol may only be removed in a major release **after one full minor
release shipped a `DeprecationWarning` from that symbol**. ADR-0034
§5's three guard layers — drift, coverage,
[signature](./0035-public-api-signature-snapshot-guard.md) — catch
*that* a removal happened. They do **not** check *whether* a
`DeprecationWarning` was raised in any prior minor release.

That last check today is review-only:

- A reviewer of a removal-bearing PR is expected to inspect the
  prior minor's source (or tag) and confirm a
  `DeprecationWarning` was emitted from the removed symbol.
- This is fragile: reviewers are time-pressed, the prior minor's
  source isn't in the PR diff, and a misread closes a contract
  break that the rest of the §5 stack was designed to catch
  mechanically.

The candidates for automating it are:

- **PyPI sdist of the previous minor** — fetch the released
  artefact at CI time, walk the source for
  `warnings.warn(..., DeprecationWarning)` (or
  `@deprecated` decorator) calls inside the symbol that the
  current PR is about to remove, fail CI when the warning is
  absent. *Pro:* Authoritative — the actual artefact users
  installed. *Con:* Network dependency in every PR build,
  sandbox cost (the older source must be parseable but not
  importable into the current process), and the AST walk
  needs to track callable bodies across the prior version's
  module structure.
- **Git tag introspection** — checkout the previous minor's tag
  in CI, AST-walk. Same pros/cons trade-offs as the PyPI sdist
  alternative (no network; multi-checkout/sparse-checkout
  fragility; tooling differences across the matrix).
- **Checked-in deprecation manifest** — a JSON file
  (`docs/public-api-deprecations.json`) listing every
  currently-deprecated symbol with the minor it was deprecated
  in and the earliest minor it may be removed in. Contributors
  who land a `DeprecationWarning` add an entry; CI cross-checks
  on every removal that the symbol appears in the manifest with
  a `removable_in` value `<=` the current package version.
  *Pro:* Self-contained; reviewable in PR diff alongside the
  source change; works on every CI cell identically; reuses the
  ADR-0035 lockstep pattern; no network or multi-checkout cost.
  *Con:* Requires a contributor to remember to update the
  manifest when emitting the warning (the CI guard above can
  enforce this — see §3).

The signature guard (ADR-0035) already taught us that a
checked-in artefact paired with a guard rule scales well for
this team and this CI matrix.

## Decision

### 1. Baseline source: checked-in deprecation manifest

We add `docs/public-api-deprecations.json` whose entries are:

```json
{
  "pdip.legacy.OldThing": {
    "deprecated_in": "1.3.0",
    "removable_in": "2.0.0",
    "replacement": "pdip.modern.NewThing",
    "reason": "Renamed; OldThing.do_x has been split into two methods."
  }
}
```

`deprecated_in` is the minor that first emitted the
`DeprecationWarning`. `removable_in` is the earliest version where
the symbol may legitimately be removed (per ADR-0034 §3, the next
major after `deprecated_in`). `replacement` and `reason` are
human-readable hints that surface in failure messages and in
release notes.

The file is checked in. Every PR that adds a deprecation OR
removes a previously-deprecated symbol updates this file in the
same diff.

### 2. New quality_guard rules

Two rules land in
`tests/unittests/quality_guard/test_conventions.py`:

- **`RuleADR0036DeprecationWarningHasManifestEntry`** — AST-walks
  the `pdip/` tree looking for
  `warnings.warn(..., DeprecationWarning)` calls (or any decorator
  whose name matches `deprecated*` from `warnings` /
  `typing_extensions`). For each call, the enclosing
  module/symbol qualified name must appear as a key in the
  manifest. Contributors who emit a warning without registering it
  fail CI.
- **`RuleADR0036RemovalRespectsDeprecationCycle`** — when the
  ADR-0035 signature snapshot diff (computed inline — same source
  of truth) contains a REMOVED entry, the removed symbol's key
  must appear in the manifest with `removable_in` `<=` the
  current `pdip.__version__` (read from `setup.py`'s
  `version` constant, same way the release process does it).
  Removals of un-deprecated symbols — or of symbols whose
  `removable_in` is still in the future — fail CI.

The two rules together close the loop: emitting a warning forces
manifest registration; landing a removal forces a matching
manifest entry whose deadline has arrived. Reviewers stop being
the load-bearing layer for ADR-0034 §3.

### 3. Manifest hygiene

The manifest is sorted by key (same convention as
`docs/public-api-signatures.json`). On every release the
release-PR template (per ADR-0024 / ADR-0034 §4 follow-up) gets a
checklist line: "audit manifest entries whose `removable_in`
matches the new major and either remove the symbol + its manifest
entry, or extend `removable_in`."

A removed manifest entry whose source-side `DeprecationWarning`
was *also* removed in the same PR satisfies both rules (the
warning AST-walk no longer finds the call; the removal-cycle
check passes because the symbol disappears from the snapshot
diff in lockstep).

### 4. Failure messages cite the policy

The two rules' `assertEqual` messages quote ADR-0034 §3 verbatim
in the failure body and link to the manifest path so the
contributor knows exactly which file to edit. The same "fail on
any drift, no soft warnings" stance ADR-0027 §3 and ADR-0035 §3
take applies here.

### 5. Documentation

- ADR-0034 §5 grows a fourth bullet ("Deprecation cycle guard
  (shipped via ADR-0036)") once this ADR moves to Accepted and
  the rules ship.
- `CONTRIBUTING.md` gains a one-paragraph "Deprecating a public
  symbol" section pointing at the manifest path and walking
  through the three-step process: emit the warning, register the
  manifest entry, ship the minor; later, in the major, remove the
  source + the manifest entry together.

### 6. Format stability

The manifest's flat-JSON shape (`<package>.<symbol>` keys with the
documented value object) is part of the contract this ADR
establishes. Changing the format — for example, splitting into
per-package nested files when the manifest grows past ~50
entries — requires its own ADR.

## Consequences

### Positive

- Reviewers stop being the load-bearing check for ADR-0034 §3 —
  CI now refuses an undocumented deprecation, and refuses a
  removal that did not go through a deprecation cycle.
- The manifest is self-contained: no network, no second checkout,
  no per-platform fragility. Same operational profile as
  ADR-0035's snapshot.
- The manifest serves as living release-notes input: the
  release-PR template can list every entry whose `removable_in`
  is the new major and the maintainer eyeballs the list once.

### Negative

- One more file in the lockstep set (`__all__` +
  `docs/public-api.md` + `EXPECTED_PUBLIC_SURFACE` +
  `public-api-signatures.json` + now `public-api-deprecations.json`).
  The failure messages all point at the right artefact so the
  cost stays bounded.
- The AST-walk for `DeprecationWarning` calls has to track common
  patterns (positional `DeprecationWarning`, keyword
  `category=DeprecationWarning`, decorator forms). The first cut
  covers the two `warnings.warn` shapes; decorator support lands
  the first time we use it.
- The rule reads `pdip.__version__` — same place the release
  process does, so they cannot drift.

### Neutral

- The manifest grows linearly with the count of currently-active
  deprecations. It shrinks when removals land in a major, so the
  steady-state size mirrors how aggressive deprecation policy is.
- The `replacement` and `reason` fields are advisory — the rule
  enforces presence of the **key**; reviewers ensure the
  human-readable fields are useful.

## Alternatives considered

### Option A — PyPI sdist baseline

- **Pro:** Authoritative — reflects what users actually
  installed.
- **Con:** Network dependency, sandbox cost, brittle on PyPI
  outages; AST walk has to navigate the prior version's module
  structure (which may have moved between versions). Slow CI.
- **Why rejected:** Same cost-vs-benefit reasoning as ADR-0035
  Option A. The checked-in artefact is the snapshot of intent at
  the moment we ship; that is the contract we want to enforce.

### Option B — Git tag introspection

- **Pro:** No network.
- **Con:** Multi-checkout dance, fragile across squash-merged
  history, doesn't degrade gracefully on shallow clones.
- **Why rejected:** Same as ADR-0035 Option B.

### Option C — Just keep the review check

- **Pro:** No new files, no new rules.
- **Con:** ADR-0034 §3 is the contract that backs the SemVer
  promise users rely on at 1.0+. Leaving it review-only puts the
  whole stack on a single human eye per PR.
- **Why rejected:** The §5 stack exists exactly because review is
  not a reliable place for a contract that ratchets a major
  version's compatibility promise.

## Follow-ups

- ✅ Manifest at
  [`docs/public-api-deprecations.json`](../../public-api-deprecations.json)
  shipped as an empty object (`{}`) — no current deprecations in
  the public surface. *(Landed.)*
- ✅
  `RuleADR0036DeprecationWarningHasManifestEntry` and
  `RuleADR0036RemovalRespectsDeprecationCycle` shipped in
  `tests/unittests/quality_guard/test_conventions.py`. *(Landed.)*
- ✅ ADR-0034 §5 grew the fourth (deprecation-cycle) bullet
  pointing here. *(Landed.)*
- ✅ `pdip.__version__` exposed as a public symbol so the
  removal-cycle rule can read the live version without parsing
  `setup.py`. *(Landed.)*
- ✅ `CONTRIBUTING.md` gained the "Deprecating a public symbol"
  section walking through the three-step process. *(Landed.)*
- The first real deprecation will exercise the manifest format —
  if it surfaces ergonomic gaps (e.g. wanting nested per-package
  files for large manifests) those land as a follow-up ADR per
  ADR-0036 §6.

## References

- [ADR-0034](./0034-one-zero-readiness-criteria.md) §3, §5 (this
  ADR closes the last open guard layer).
- [ADR-0035](./0035-public-api-signature-snapshot-guard.md)
  (companion guard whose snapshot diff feeds the
  removal-cycle check).
- [ADR-0026](./0026-test-quality-rules.md) — quality_guard host
  for the new rules.
- [ADR-0027](./0027-tdd-with-diff-coverage.md) §3 — same
  "fail on any drift, no soft warnings" stance.
- External:
  [PEP 387 (Backwards Compatibility Policy)](https://peps.python.org/pep-0387/),
  [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html),
  [`warnings.warn`](https://docs.python.org/3/library/warnings.html#warnings.warn).
