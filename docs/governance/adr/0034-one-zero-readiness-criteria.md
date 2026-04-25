# ADR-0034: 1.0 readiness criteria and deprecation policy

- **Status:** Accepted
- **Date:** 2026-04-25
- **Deciders:** pdip maintainers
- **Tags:** release, packaging, process, governance, api

## Context

pdip has been on `0.x` since its first PyPI release. The `0.x` line lets
us evolve the public surface without committing to backwards-compatible
behaviour, but it has three costs that have grown over time:

- Downstream consumers cannot rely on a stable import path. A minor
  release (`0.7 → 0.8`) is allowed to rename, move, or delete a public
  symbol, so users either pin exact versions or stop upgrading.
- Reviewers have no objective signal for whether a PR breaks the public
  contract. ADR-0027 raises the bar on internal quality (tests, diff
  cover, quality_guard), but says nothing about whether a class is
  *meant* to be public.
- The active development authorised on 2026-04-25 (Async via ADR-0032,
  OpenTelemetry via ADR-0033) introduces new top-level surface
  (`pdip[async]`, `pdip[observability]`). If we add that surface under
  `0.x` rules and *then* cut 1.0, we either freeze immature ergonomics
  or cut 1.0 immediately after a churn cycle. Neither is ideal.

We need a written contract that says (a) what counts as the 1.0 public
surface, (b) what guarantees 1.0+ gives, and (c) how we deprecate
something inside that contract without breaking consumers.

## Decision

### 1. The 1.0 public surface is what is exported, not what exists

A symbol (class, function, dataclass, type alias) is part of the 1.0
public contract if and only if it is reachable through one of the
following entry points:

- `pdip/__init__.py` (top-level re-exports).
- The `__init__.py` of a documented subpackage: `pdip.integrator`,
  `pdip.cqrs`, `pdip.data`, `pdip.dependency`, `pdip.api`,
  `pdip.configuration`, `pdip.processing`, `pdip.logging`,
  `pdip.cryptography`, `pdip.io`, `pdip.json`, `pdip.html`,
  `pdip.delivery`, `pdip.utils`, `pdip.exceptions`.

Anything reached only through a deeper module path
(`pdip.integrator.connection.types.sql.oracle.connectors.foo`) is
**internal**. Internal symbols may move or change shape between any two
1.x releases without a deprecation cycle. The 1.0 audit (Follow-ups
below) decides what each of those `__init__.py` files should re-export.

The headline public classes the audit must classify include at least:

- `pdip/integrator/base/integrator.py` → `Integrator`.
- `pdip/integrator/initializer/integrator/integrator_initializer_factory.py`
  → `IntegratorInitializerFactory`.
- `pdip/integrator/connection/base/connection_source_adapter.py` →
  `ConnectionSourceAdapter`.
- `pdip/integrator/connection/base/connection_target_adapter.py` →
  `ConnectionTargetAdapter`.
- `pdip/cqrs/dispatcher.py` → `Dispatcher`.
- `pdip/data/repository/repository.py` → `Repository`.
- `pdip/data/repository/repository_provider.py` → `RepositoryProvider`.
- `pdip/processing/base/process_manager.py` → `ProcessManager`.
- `pdip/processing/base/subprocess.py` → `Subprocess`.

### 2. Versioning guarantees from 1.0 onwards

We follow [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) on the
public surface defined in §1:

- **Patch (1.x.y → 1.x.y+1):** bug fixes, performance, internal
  refactors. No public signature change.
- **Minor (1.x → 1.x+1):** new public symbols, new keyword arguments
  with defaults, new optional extras. No removal, no signature break.
  Deprecations are allowed and must follow §3.
- **Major (1.x → 2.0):** removal or signature break of a public symbol
  is permitted only here, and only after one full minor with a
  deprecation warning emitted at runtime (§3).

Internal symbols (everything outside §1) are exempt from all three.
The Python floor (ADR-0028) and the supported driver matrix
(ADR-0014, ADR-0021, ADR-0022) are part of the contract: dropping a
Python version or a driver in a minor release is forbidden.

### 3. Deprecation policy

To deprecate a public symbol:

1. Add a `DeprecationWarning` raised on first use, with a one-line
   message that names the replacement and the minor version in which
   removal is allowed (`"X is deprecated since 1.3, use Y instead;
   removable in 2.0"`).
2. Add a `# Deprecated` row to `CHANGELOG.md` under the next minor.
3. Keep the deprecated symbol fully functional for **at least one full
   minor release** (i.e. deprecate in 1.3, earliest removal in 2.0).
4. Document the migration in the release notes for the minor that
   introduced the warning, not the major that removed it.

Removing a symbol that was never warned on is a contract break and is
treated as a release blocker.

### 4. 1.0 readiness gates

A `1.0.0` release is cut only when **all** the following hold on
`main`:

- The public-surface audit (§1) is recorded as a tracked artefact —
  either an `__all__` list per public `__init__.py` or a checked-in
  `docs/public-api.md` table — and reviewed by at least one
  maintainer.
- ADR-0032 (Async) and ADR-0033 (OpenTelemetry) are either Accepted
  with their first-implementation PRs landed *or* explicitly deferred
  past 1.0 with an ADR follow-up note. The 1.0 release does not block
  on full coverage of every connector; it blocks on the *shape* of
  the new extras being decided.
- ADR-0023's coverage floor is at 100 % and ADR-0027's diff-cover gate
  has been green on `main` for the last 10 merges.
- ADR-0029's nightly integration matrix has been green for at least
  seven consecutive nights (or has open tracking issues per ADR-0031
  for any persistent failure).
- A `CHANGELOG.md` `[1.0.0]` section exists with a "Breaking changes
  since 0.x" subsection that lists every removal made on the way to
  1.0.

### 5. Enforcement

The contract is enforced in three layers, two already shipped:

- **Drift guard (shipped)** —
  `tests/unittests/public_api/test_public_api_contract.py` walks
  every package in `EXPECTED_PUBLIC_SURFACE`, asserts `__all__` is
  declared, matches the documented set, contains no unresolved or
  duplicated names. A change to any of `docs/public-api.md`, the
  package's `__all__`, or the test mapping that is not mirrored in
  the other two fails CI.
- **Coverage guard (shipped)** — quality_guard rule
  `RuleADR0034NoUndocumentedTopLevelPackage` in
  `tests/unittests/quality_guard/test_conventions.py` walks every
  directory directly under `pdip/` and fails CI when one is neither
  in `EXPECTED_PUBLIC_SURFACE` nor on the rule's
  `_ADR0034_INTERNAL_PACKAGES` allowlist (which itself requires a
  one-line reason comment per ADR-0026 §G.3). A new top-level
  package cannot be added without an explicit public/internal
  decision.
- **Signature guard (deferred to a follow-up ADR)** — comparing the
  public signature against the previous minor needs an external
  baseline (PyPI sdist, git tag artefact, or a checked-in snapshot)
  and is its own design decision; tracked as a §Follow-ups item
  below.

Adjacent process steps:

- `CHANGELOG.md` lint already catches missing release headers under
  ADR-0024; we extend it to require a `# Deprecated` and `# Removed`
  sub-header on majors that contain removals.
- The pre-existing release process (ADR-0024) gains a one-line
  "1.0 readiness check" item in its release-PR template referencing
  §4.

## Consequences

### Positive

- Consumers get a stable import surface; pinning to `pdip>=1,<2` is
  a real promise rather than a polite hope.
- Reviewers have an objective question to ask: *is this symbol in the
  §1 set?* — and a written rule for what they should do if it is.
- The Async and OpenTelemetry work (ADR-0032, ADR-0033) gets a clean
  home: their entry points are added to the public surface during the
  1.0 audit, not folded in retroactively after a churn cycle.

### Negative

- Internal refactors that today touch a deeply nested but historically
  imported class become breaking changes if that class is in §1.
  The audit must surface those before 1.0.
- The deprecation policy adds a release of latency to every public
  rename. This is the trade-off for predictability.
- One more quality_guard rule is one more thing to maintain.

### Neutral

- The 1.0 audit is a documentation exercise, not a code rewrite. Most
  symbols already live where they should; the audit makes the
  contract explicit.
- A symbol can move from "internal" to "public" at any minor; the
  reverse requires §3.

## Alternatives considered

### Option A — Stay on 0.x indefinitely

- **Pro:** Zero process change.
- **Con:** Consumers continue to pin exact versions; the new
  `pdip[async]` and `pdip[observability]` surfaces never get a stable
  contract.
- **Why rejected:** The cost of the 0.x freedom is paid by every
  downstream user, and the active development on async + OTel is
  exactly the moment to set the contract.

### Option B — Cut 1.0 immediately, audit later

- **Pro:** Marketing milestone, clear SemVer signal.
- **Con:** The §1 audit is the contract; without it, "1.0" is a
  number, not a guarantee.
- **Why rejected:** A 1.0 we cannot defend against the next breaking
  rename is worse than a 0.x we can.

### Option C — Per-symbol stability tiers (`@stable`, `@experimental`)

- **Pro:** Lets us ship experimental features without the deprecation
  cost.
- **Con:** Significantly more machinery (decorator, doc tooling,
  reviewer training); ADR-0014's `extras_require` already gives us a
  per-feature stability dial through the extra name.
- **Why rejected:** Premature; revisit if the audit surfaces more than
  ~5 symbols that genuinely need experimental status.

## Follow-ups

- ✅ 1.0 audit PR: walk every subpackage in §1, write or update the
  `__init__.py` `__all__`, record results in `docs/public-api.md`.
  *(Landed.)*
- ✅ quality_guard "coverage" rule for §5
  (`RuleADR0034NoUndocumentedTopLevelPackage`). *(Landed.)*
- Signature-baseline guard: compare each public symbol's signature
  against the previous minor's release artefact and fail CI on a
  break that is not preceded by a `DeprecationWarning`. Needs a
  separate design ADR to pick the baseline source (PyPI sdist /
  git-tag introspection / checked-in snapshot) and the diff
  algorithm.
- Release-PR template update for §4.
- Coordinate with ADR-0032 and ADR-0033 so the new public symbols
  introduced by Async / OTel land *with* their `__all__` entries, not
  retroactively.

## References

- [ADR-0014](./0014-optional-extras-packaging.md) — extras as the
  feature-stability dial.
- [ADR-0023](./0023-coverage-floor-policy.md), [ADR-0027](./0027-tdd-with-diff-coverage.md)
  — coverage / diff-cover gates referenced by §4.
- [ADR-0024](./0024-release-process.md) — release process this ADR
  extends.
- [ADR-0026](./0026-test-quality-rules.md) — quality_guard host for
  §5's rule.
- [ADR-0029](./0029-integration-tests-in-ci.md), [ADR-0031](./0031-adaptive-nightly-failure-issue.md)
  — nightly-green readiness gate.
- [ADR-0032](./0032-hybrid-async-strategy.md), [ADR-0033](./0033-opentelemetry-observability.md)
  — concurrent ADRs whose surfaces enter the 1.0 audit.
- External: [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html).
