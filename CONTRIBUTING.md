# Contributing to PDI

The following is a set of guidelines for contributing to PDI.

Note that PDI is an evolving project, so expect things to change over time as the team learns, listens and refines how
we work with the community.

#### Table Of Contents

- [What should I know before I get started?](#what-should-i-know-before-i-get-started)
    * [Code of Conduct](#code-of-conduct)
    * [Governance and Architecture Decisions](#governance-and-architecture-decisions)

- [How Can I Contribute?](#how-can-i-contribute)
    * [Reporting Bugs](#reporting-bugs)
    * [Suggesting Enhancements](#suggesting-enhancements)
    * [Set Up Your Machine](#set-up-your-machine)

## What should I know before I get started?

### Code of Conduct

This project adheres to the Contributor Covenant [code of conduct](../CODE_OF_CONDUCT.md). By participating, you are
expected to uphold this code. Please report unacceptable behavior
to [ahmetcagriakca@gmail.com](mailto:ahmetcagriakca@gmail.com).

### Governance and Architecture Decisions

The *why* behind PDI's architecture lives in [`docs/governance/`](docs/governance/README.md).
Before proposing architecturally significant changes, read the relevant
[Architecture Decision Records](docs/governance/adr/README.md) and the
[contribution policies](docs/governance/policies/README.md). Some rules worth calling out up front:

- All content committed to this repository — code, documentation, commit messages, issue
  and PR titles and descriptions, and review comments — is written in English. See
  [ADR-0016](docs/governance/adr/0016-english-only-content.md) for the rationale.
- Architectural changes require a new or updated ADR; follow the process in the
  [governance README](docs/governance/README.md).
- Tests follow the quality rules in
  [ADR-0026](docs/governance/adr/0026-test-quality-rules.md). Every
  test asserts a concrete behaviour; six of the rules are
  machine-enforced by `tests/unittests/quality_guard/` and will fail
  CI when violated.
- **New production code is written test-first**
  ([ADR-0027](docs/governance/adr/0027-tdd-with-diff-coverage.md)).
  Diff-coverage enforces this mechanically: every PR must leave
  its newly added or modified `pdip/` lines at 100 % line coverage,
  measured against the merge-base with `main`. CI fails otherwise.

### Deprecating a public symbol

The 1.0 contract defined by
[ADR-0034](docs/governance/adr/0034-one-zero-readiness-criteria.md)
guarantees that a public symbol cannot be removed without a
prior-minor `DeprecationWarning`. The check is automated by
[ADR-0036](docs/governance/adr/0036-deprecation-warning-prior-release-check.md)'s
two `quality_guard` rules, so the workflow is:

1. **Emit the warning from the symbol body.** A typical site
   looks like:

   ```python
   import warnings


   def old_thing():
       warnings.warn(
           "old_thing is deprecated since 1.3, use new_thing "
           "instead; removable in 2.0",
           DeprecationWarning,
           stacklevel=2,
       )
       ...
   ```

2. **Register the symbol in
   [`docs/public-api-deprecations.json`](docs/public-api-deprecations.json).**
   Add a key whose qualified name matches the symbol's
   enclosing scope (e.g. `pdip.legacy.OldThing` for a class,
   `pdip.legacy.OldThing.do_x` for a method) and the value
   object documented in ADR-0036 §1:

   ```json
   {
     "pdip.legacy.old_thing": {
       "deprecated_in": "1.3.0",
       "removable_in": "2.0.0",
       "replacement": "pdip.modern.new_thing",
       "reason": "Renamed for the verb-noun convention adopted in 1.3."
     }
   }
   ```

3. **Ship the minor.** Both `quality_guard` rules now stay
   green: `RuleADR0036DeprecationWarningHasManifestEntry`
   passes because the warning's enclosing key is in the
   manifest, and `RuleADR0036RemovalRespectsDeprecationCycle`
   passes because the symbol is still part of the live
   surface (no diff against the
   [signature snapshot](docs/public-api-signatures.json)).

4. **Remove the source + the manifest entry together** in the
   major release where `removable_in` lands. Both rules go quiet
   in lockstep — the warning AST-walk no longer finds the call,
   and the snapshot diff shows the REMOVED key paired with a
   manifest entry whose `removable_in` is `<= pdip.__version__`.

## How Can I Contribute?

### Reporting Bugs

This section guides you through submitting a bug report for PDI. Following these guidelines helps maintainers and the
community understand your report :pencil:, reproduce the behavior, and find related reports :mag_right:.

Before creating bug reports, please check [this list](#before-submitting-a-bug-report)
as you might find out that you don't need to create one. When you are creating a bug report,
please [include as many details as possible](#how-do-i-submit-a-good-bug-report). Fill
out [the required template](ISSUE_TEMPLATE/bug_report.md), the information it asks for helps us resolve issues faster.

#### Before Submitting A Bug Report

**Perform a [cursory search](https://github.com/ahmetcagriakca/pdip/labels/bug)**
to see if the problem has already been reported. If it does exist, add a
:thumbsup: to the issue to indicate this is also an issue for you, and add a comment to the existing issue if there is
extra information you can contribute.

#### How Do I Submit A Bug Report?

Bugs are tracked as [GitHub issues](https://guides.github.com/features/issues/).

Simply create an issue on
the [PDI issue tracker](https://github.com/ahmetcagriakca/pdip/issues/new?template=bug_report.md)
and fill out the provided issue template.

The information we are interested in includes:

- details about your environment - which build, which operating system
- details about reproducing the issue - what steps to take, what happens, how often it happens
- other relevant information - log files, screenshots, etc

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for PDI, including completely new features and
minor improvements to existing functionality. Following these guidelines helps maintainers and the community understand
your suggestion and find related suggestions.

Before creating enhancement suggestions, please check [this list](#before-submitting-an-enhancement-suggestion)
as you might find out that you don't need to create one. When you are creating an enhancement suggestion,
please [include as many details as possible](#how-do-i-submit-a-good-enhancement-suggestion). Fill
in [the template](ISSUE_TEMPLATE/problem-to-raise.md), including the steps that you imagine you would take if the
feature you're requesting existed.

#### Before Submitting An Enhancement Suggestion

**Perform a [cursory search](https://github.com/ahmetcagriakca/pdip/labels/enhancement)**
to see if the enhancement has already been suggested. If it has, add a
:thumbsup: to indicate your interest in it, or comment if there is additional information you would like to add.

### Set Up Your Machine

See [`docs/contributing/setup.md`](docs/contributing/setup.md) for a
full walk-through: prerequisites, clone + install, running the tests,
linting, branching, and troubleshooting.
