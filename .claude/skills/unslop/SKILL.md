---
name: unslop
description: Default output modifier for human-facing prose. Must always apply unless exact quoted, historical, generated, or machine-defined text must be preserved.
---

# unslop

## Purpose

Make human-facing output sound like a person who understands the subject.

Apply this by default to explanations, reports, handoffs, documentation, issue
text, pull-request text, comments, and other prose. It is an output modifier, not
a standing claim and not a substitute for technical verification.

Do not rewrite exact machine identifiers, quoted evidence, archived historical
text, generated artifacts, or byte-sensitive material merely to satisfy style.

## Pass

Before emitting human-facing prose:

1. Remove filler, puffery, canned enthusiasm, and generic conclusions.
2. Prefer plain words and direct verbs.
3. Name the actor, mechanism, state, or observed result when one exists.
4. Split sentences that make the reader backtrack.
5. Remove forced rhetorical patterns, synonym cycling, and decorative structure.
6. Treat abstract technical metaphor as suspect unless it preserves a real
   distinction.
7. Keep canonical project terms and machine identifiers exact.
8. Vary sentence rhythm enough to sound natural, without making technical prose
   chatty for its own sake.
9. Ask: "What makes this obviously AI-written?" Fix what remains.

## Common tells

Watch for:

- inflated words where a plain word works;
- "serves as" or "stands as" where "is" or a concrete verb works;
- superficial `-ing` phrases that hide the actor;
- "not just X, but Y";
- forced groups of three;
- vague attribution such as "experts say" or "the architecture recognizes";
- abstract nouns such as "substrate", "surface", "vector", "locus",
  "scaffolding", or "paradigm" when the concrete thing can be named;
- excessive hedging;
- passive voice that hides who acts;
- paragraphs that repeat the same claim in different words;
- chatbot closers and sycophantic agreement.

These are signals, not blind replacement rules. A technical term stays when it
names a distinction the project actually uses.

## Relationship to clarity

`unslop` modifies output. `clarity` audits persisted repository prose.

Every clarity pass includes this modifier. For a repository artifact inside the
scope of `contracts/clarity.json`, do not treat an unslopped edit as a completed
clarity review until `clarity` has checked the governing meaning and recorded the
artifact digest.

So:

```text
human-facing output -> unslop
persisted covered prose -> unslop + clarity review + receipt
```
