# ADR-0016: Documentation, code, and commit messages are English-only

- **Status:** Accepted
- **Date:** 2026-04-24
- **Deciders:** pdip maintainers
- **Tags:** documentation, contribution

## Context

pdip is an open-source framework with contributors and users across
multiple language backgrounds. Conversations with maintainers may happen
in any language, but the artefacts that live in the repository — code,
documentation, commit messages, issue and PR descriptions, review
comments — need a single lingua franca to be searchable, reviewable, and
useful to the broadest audience.

Without an explicit rule, artefacts drift into whichever language the
original author was most comfortable with. That makes code review
harder for contributors who do not share the language, fragments search
results, and raises the cost of maintenance over time.

## Decision

All content committed to the repository is written in **English**. This
covers:

- Source code: identifiers, comments, docstrings, log messages, error
  messages, exception text.
- Repository documentation: everything under `docs/`, the `README`,
  `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, and any other
  root-level Markdown.
- Governance artefacts: ADRs, policies, templates, and the MADR prose
  itself.
- Git artefacts: commit messages, branch names, tag messages.
- GitHub artefacts: issue titles and bodies, PR titles and bodies,
  inline review comments, and PR labels.

Non-English content is acceptable in places that never land in the
repository — private chat, live discussion, design sketches that will be
rewritten in English before merge.

Translations are out of scope for this ADR. If demand appears later,
translated documentation would live under a separate path (for example
`docs/i18n/<lang>/`) and would not replace the English source of truth.

## Consequences

### Positive

- One language to grep, one language to review. Maintainers do not
  need to translate to understand a diff.
- Aligns with the existing English-only tone of `README.md`,
  `CONTRIBUTING.md`, and the rest of the repository.
- Lowers the barrier to entry for new contributors from any region
  who can read technical English.

### Negative

- Contributors whose strongest language is not English may find
  drafting PR descriptions, ADRs, or code comments slower. The project
  accepts imperfect English over no contribution and reviewers help
  polish wording during review.
- Error messages and user-facing strings are not localised. A consumer
  application that needs localisation layers it on top.

### Neutral

- Reviewers are expected to point out non-English content during review
  and ask for it to be rewritten before merge. This is a gentle rule,
  not a hostile gatekeep.

## Alternatives considered

### Option A — No language rule

- **Pro:** Lowest friction for the contributor at the moment of
  writing.
- **Con:** Drift. Mixed-language repositories are harder to search,
  review, and maintain.
- **Why rejected:** Long-term cost outweighs short-term convenience.

### Option B — Bilingual (English + another language) with both in-repo

- **Pro:** Serves a specific non-English audience directly.
- **Con:** Doubles the maintenance surface; the two versions inevitably
  drift.
- **Why rejected:** Translations can be added later under a dedicated
  path if there is demand; the *source of truth* stays single.

### Option C — Code and commits in English, free-form in issues/PRs

- **Pro:** Matches a common open-source pattern.
- **Con:** Review conversations become the weakest link: a PR whose
  discussion is in another language is opaque to contributors who
  otherwise could help.
- **Why rejected:** The GitHub surface is as much part of the project
  as the code.

## Follow-ups

- Add a short note to `CONTRIBUTING.md` pointing at this ADR.
- Add an "English-only" bullet to `docs/governance/policies/README.md`.

## References

- Prior art: `README.md`, `CONTRIBUTING.md`, and existing source code,
  all of which are already English-only.
