# Policies

Policies are **living rules** that apply to day-to-day contribution. They
are distinct from [ADRs](../adr/), which are point-in-time decisions.

The rules below are derived from the ADRs. When a rule and an ADR
disagree, the ADR is the source of truth and the policy must be updated.

## Contribution

- All architectural changes require an ADR. See the
  [governance README](../README.md) for what counts as architectural.
- Everything committed to the repository is written in English: code,
  comments, docs, commit messages, and GitHub titles / descriptions /
  review comments ([ADR-0016](../adr/0016-english-only-content.md)).
- Pull requests that introduce a new service inherit from `ISingleton`
  or `IScoped` as required by [ADR-0002](../adr/0002-custom-di-scopes.md);
  do not hand-bind services to the injector.
- Handlers placed next to their `ICommand` / `IQuery` follow the
  convention in [ADR-0003](../adr/0003-cqrs-dispatcher.md). Do not add a
  central handler registry.

## Data

- All domain tables inherit from `Entity`
  ([ADR-0010](../adr/0010-audit-columns-on-base-entity.md)).
- Deletion goes through the repository and sets `GcRecId`
  ([ADR-0009](../adr/0009-soft-delete-gcrecid.md)). Physical `DELETE`
  belongs only in dedicated purge jobs.
- Every query runs in tenant scope unless explicitly widened
  ([ADR-0011](../adr/0011-multi-tenancy-via-tenant-id.md)).

## Integration

- New source or target backends are added as adapters behind the
  interfaces in [ADR-0012](../adr/0012-connection-source-target-adapters.md).
  Do not add backend-specific branches to the executor.
- Objects that cross the process boundary must be picklable
  ([ADR-0007](../adr/0007-multiprocessing-for-etl.md)).
- Lifecycle observability goes through the pub/sub broker events
  ([ADR-0006](../adr/0006-pubsub-message-broker.md)); do not add direct
  callbacks on the executor.

## Configuration

- Runtime configuration is YAML plus environment overrides
  ([ADR-0005](../adr/0005-yaml-configuration-with-env-overrides.md)).
  Do not hard-code environment-specific values.
- Secrets live in environment variables, not in YAML files in source
  control.

## Packaging

- New heavyweight or native dependencies go behind an `extras_require`
  feature set ([ADR-0014](../adr/0014-optional-extras-packaging.md)).
  Imports that depend on an extra must be guarded so that the core
  package remains importable without it.
- Do not accept a dependency upgrade whose release notes drop a Python
  version inside our supported window — the supported matrix is owned
  by pdip, not by a dependency
  ([ADR-0017](../adr/0017-python-support-policy.md)). Either pin the
  last supporting version, or raise `python_requires` deliberately in
  a dedicated ADR.
- The current supported floor is **Python 3.9**
  ([ADR-0020](../adr/0020-raise-python-floor-to-3-9.md)). Raising it
  further requires another ADR and a **minor** version bump.

## Testing

- Coverage floor is enforced by `.coveragerc`'s `fail_under`
  ([ADR-0023](../adr/0023-coverage-floor-policy.md)). New tests should
  hold or improve coverage; the floor is ratcheted up by separate
  maintenance PRs, not edited on feature PRs.
- Integration adapters under
  `pdip/integrator/connection/{sql,bigdata,webservice,file}/` are
  excluded from the unit-coverage score because they need external
  services to run.
- **Test quality rules** are fixed in
  [ADR-0026](../adr/0026-test-quality-rules.md). Every test asserts a
  concrete behaviour; no tautologies; AAA structure; mocks at
  boundaries only; `unittest` only; no star imports; deterministic.
  Six of the rules are machine-enforced by
  `tests/unittests/quality_guard/test_conventions.py` — CI fails
  when they are violated. Reviewers enforce the rest with the ADR
  as the reference.
- **TDD is the default workflow** for new production code
  ([ADR-0027](../adr/0027-tdd-with-diff-coverage.md)). Write the
  failing test first, watch it fail for the right reason, then
  write the smallest change that makes it pass. Reviewers check
  the commit graph for that ordering.
- **Diff-coverage gates every PR at 100 %.** New or modified
  `pdip/` lines must be covered by the same PR's test changes, or
  CI fails — independent of the overall `fail_under` floor.
- `# pragma: no cover` requires an inline reason comment on the
  same line (the `quality_guard` meta-test enforces this).

## Review expectations

Reviewers verify, in order:

1. The change does not violate an existing ADR. If it does, either the
   ADR is updated / superseded in the same PR, or the change is
   rejected.
2. The change follows the policies above.
3. Code quality, tests, and documentation.
