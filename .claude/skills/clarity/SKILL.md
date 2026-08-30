---
name: clarity
description: Audit and rewrite persisted project prose into plain, specific human language while preserving the claims and machine-defined distinctions the repository depends on. Use for "clarity", "deslop", "plain language", "rewrite root docs", "terminology cleanup", or "clarity coverage".
---

# clarity

## Purpose

Audit persisted human-facing project text and record the result.

`clarity` requires `unslop/v1`. `unslop` is the default output modifier; this
skill adds claim recovery, source checking, repository-wide terminology control,
and digest-backed coverage. A clarity review is incomplete if the text has not
also passed the unslop modifier.

Preserve the project's actual claim, not inherited wording merely because it
already exists. A clarity pass may rewrite a whole section, reorder explanation,
or delete terminology that earlier drafts accumulated. It must not invent
product meaning or quietly change a contract.

For phase-boundary cleanup, treat the corpus as a rebase from zero. Every current
human-facing artifact must be reconsidered. "No edit needed" is a valid result
only after the artifact has been actively reviewed.

## Process

1. Read the artifact and the governing sources behind its claims.
2. Identify the concrete claims the artifact must communicate.
3. Apply `unslop/v1` to the human-facing prose.
4. Discard inherited wording when it gets in the way.
5. Rewrite in plain language.
6. Restore specialized terms only when they preserve a real distinction.
7. Use one term for one concept.
8. Keep machine identifiers exact.
9. Prefer named actors, mechanisms, states, and observable results over metaphor.
10. Split sentences that carry more than one important claim.
11. Remove repetition unless it helps a reader find the owning rule.
12. Check the rewrite against the sources that govern its meaning.
13. Ask:
    - What still sounds AI-written?
    - What only makes sense to someone who already knows this repository?
14. Fix both.
15. Record the completed review with `python scripts/sov_clarity.py record <path>`.

A reviewed artifact counts as covered even when no edit was needed.

## Patterns to remove

The base pattern pass belongs to `unslop/v1`. Clarity applies those rules and
then asks whether project-specific language itself is carrying unnecessary
complexity.

### Abstract technical metaphor

Treat words such as "substrate", "surface", "primitive", "vector", "locus",
"scaffolding", "paradigm", and similar abstractions as smoke detectors, not a
blind blacklist.

Keep a specialized term only when all three are true:

1. it preserves a distinction the project needs;
2. replacing it with a common word would lose that distinction; and
3. the distinction is defined or enforced somewhere concrete.

If those conditions do not hold, use ordinary language.

### Canonical terms

Do not invent a new synonym for an existing project concept. If the canonical
term is `grant`, use `grant`.

Do not casually rename:

- machine identifiers;
- contract fields;
- enum values;
- operation names;
- refusal codes;
- schema terms with defined semantics.

Historical and archived artifacts keep their historical language. Current reader
documents use current language.

When a root definition changes, update dependent reader text rather than keeping
a second, drifting explanation.

## Scope

`contracts/clarity.json` declares the review population. Its scope is anchored to
`contracts/publication-surface.json` so the denominator cannot be made convenient
by naming only the files already cleaned.

Current prose on `HUB` and `HOST` publication surfaces is considered for clarity.
Derived output, journals, scratch material, local state, and other non-current
surfaces are outside the prose campaign. Machine-defined text is not rewritten
merely to increase coverage.

An artifact may be `EXEMPT` only through an explicit rule with a reason. Exemption
is visible in `scope` and `status`; it is not counted as reviewed. Historical
decision records are the first explicit exemption because rewriting the language
of the act would alter provenance. Current projections of those decisions remain
eligible.

Use `python scripts/sov_clarity.py scope` to prove that every scanned current
prose artifact has a publication classification and is either eligible or
explicitly exempt.

## Basis

Exact `basis_by_path` entries take precedence. Pattern rules provide default
governing sources for repeated surfaces such as services, bindings, host
instructions, and operational documentation.

A receipt records the digests of its basis. If one of those sources changes, the
artifact becomes `BASIS_STALE` even when its own bytes did not move.

Do not add a basis merely to make the graph dense. Use the smallest set that
actually governs the artifact's claims.

## Coverage

`.clarity/coverage.json` records completed reviews by content digest.

Use:

```sh
python scripts/sov_clarity.py scope
python scripts/sov_clarity.py status
python scripts/sov_clarity.py next
python scripts/sov_clarity.py record README.md --changed
python scripts/sov_clarity.py check
python scripts/sov_clarity.py gate
```

Coverage and freshness are different:

- coverage = reviewed eligible artifacts / eligible artifacts;
- freshness = currently valid reviews / reviewed artifacts;
- current coverage = currently valid reviews / eligible artifacts.

States are:

- `CURRENT` — the artifact and recorded basis still match the reviewed bytes;
- `TEXT_STALE` — the artifact changed after review;
- `BASIS_STALE` — a governing source changed after review;
- `UNCHECKED` — the artifact is eligible but has not been reviewed;
- `EXEMPT` — the artifact is deliberately outside review for a recorded reason.

`check` refuses malformed scope, malformed receipts, and stale reviews. It does
not refuse merely because eligible files remain unchecked. This lets a campaign
advance progressively.

`gate` is the terminal form. It requires every eligible artifact to be `CURRENT`
and every non-reviewed candidate to be explicitly `EXEMPT`. A phase-boundary
clarity campaign is not complete until `gate` passes.

## Report

Report:

- scope size and exemptions;
- files reviewed;
- files changed;
- terms removed or normalized when that matters;
- terms deliberately kept because they preserve a real distinction;
- clarity coverage;
- clarity freshness;
- current coverage;
- next target.
