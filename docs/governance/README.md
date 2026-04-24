# Governance

This directory captures how the **pdip** project is governed at an
architectural and process level. The goal is to make implicit decisions
explicit so that contributors, reviewers, and maintainers share the same
mental model of the system.

The governance model is intentionally lightweight: it consists of a small
set of **Architecture Decision Records (ADRs)**, a handful of **policies**,
and a clear path for proposing change.

## Contents

| Section | Purpose |
|---|---|
| [`adr/`](./adr/) | Immutable log of architecturally significant decisions that shape pdip |
| [`policies/`](./policies/) | Living rules that apply to day-to-day contribution (coding, branching, releasing) |
| [`adr/README.md`](./adr/README.md) | Index of all ADRs and their current status |
| [`adr/template.md`](./adr/template.md) | MADR-style template for new ADRs |

## Methodology

pdip uses the [**MADR (Markdown Any Decision Records)**](https://adr.github.io/madr/)
convention for ADRs. Each record is a short Markdown file that documents:

1. **Context** — the forces at play when the decision was taken.
2. **Decision** — the option that was chosen.
3. **Consequences** — the trade-offs that result, both positive and negative.
4. **Alternatives** — what was considered and rejected, and why.

ADRs are *append-only*. When a decision changes, a new ADR is written and
the old one is marked `Superseded by ADR-XXXX`. This preserves the history
of *why* the system looks the way it does.

## Scope of governance

A change is "architecturally significant" — and therefore warrants an ADR —
when it meets at least one of the following:

- It changes a cross-cutting contract (DI scopes, repository base, CQRS
  dispatch, connection adapter interface, base entity audit columns).
- It introduces or removes a runtime framework or protocol (e.g. Flask,
  SQLAlchemy, a new message broker, asyncio).
- It alters a public behaviour that downstream consumers rely on (the
  `Pdi` entry point, the `@dtoclass` / `@request_class` / `@response_class`
  decorators, extras in `setup.py`).
- It trades off a property that is hard to reverse (security, multi-tenant
  isolation, data retention, process model).

Implementation-level choices (refactors, renames, local performance fixes)
do **not** need an ADR. A clear pull request description is enough.

## Lifecycle of a decision

```
Proposed  ──►  Accepted  ──►  Deprecated
                   │
                   └────────►  Superseded by ADR-XXXX
```

- **Proposed** — opened as a pull request on the next free ADR number.
- **Accepted** — merged. The decision is in force.
- **Deprecated** — the decision is no longer recommended but no replacement
  has been designed yet.
- **Superseded** — a newer ADR has replaced it. The old ADR stays in place
  with a pointer forward.

## How to add or change an ADR

1. Copy [`adr/template.md`](./adr/template.md) to the next number
   (e.g. `adr/0016-my-decision.md`).
2. Fill in Context, Decision, Consequences, and Alternatives.
3. Add the entry to [`adr/README.md`](./adr/README.md).
4. Open a pull request titled `ADR-XXXX: <short decision>`.
5. Reviewers focus on *whether the decision is sound*, not on prose
   quality. Merge when at least one maintainer approves.

When superseding an existing ADR, update the old file's status to
`Superseded by ADR-XXXX` and link both ways.

## Relationship to other documents

- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) — how to contribute code.
- [`../../CODE_OF_CONDUCT.md`](../../CODE_OF_CONDUCT.md) — community norms.
- [`../../SECURITY.md`](../../SECURITY.md) — reporting vulnerabilities.
- ADRs here — *why* the code looks the way it does.
