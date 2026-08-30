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

## Coverage

`contracts/clarity.json` declares what counts and declares `unslop/v1` as the
required base modifier. `.clarity/coverage.json` records completed reviews by
content digest.

Use:

```sh
python scripts/sov_clarity.py status
python scripts/sov_clarity.py next
python scripts/sov_clarity.py record README.md --changed
python scripts/sov_clarity.py check
```

Coverage and freshness are different:

- coverage = reviewed eligible artifacts / eligible artifacts;
- freshness = currently valid reviews / reviewed artifacts;
- current coverage = currently valid reviews / eligible artifacts.

A review becomes `TEXT_STALE` when the artifact changes. It becomes
`BASIS_STALE` when a recorded governing source changes. `UNCHECKED` means the
skill has not reviewed the artifact. `CURRENT` means the current bytes match the
review receipt.

`check` refuses malformed or stale receipts. It does not refuse merely because
coverage is incomplete. That lets the cleanup advance progressively without
allowing a file that claims review to drift silently.

## Report

Report:

- files reviewed;
- files changed;
- terms removed or normalized when that matters;
- terms deliberately kept because they preserve a real distinction;
- clarity coverage;
- clarity freshness;
- next target.
