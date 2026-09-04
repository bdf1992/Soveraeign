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
9. Ask two questions and fix what they surface. Could anyone have written this,
   for anyone? And what fact would go false if this passage disappeared? A
   passage that survives neither goes.

Steps 1 to 8 can be done by pattern. Step 9 cannot, and it is the one that
decides whether the prose reads as a person. Running a search for the tells
below and finding none is not step 9; it is a way of skipping it.

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

Shape tells, which survive a clean vocabulary:

- sentences that all land in the same 10 to 15 word band;
- a run of clipped fragments used for emphasis: "Short. Punchy. Exhausting.";
- the comparator, "this isn't X, it's Y", and its quieter form "not the models,
  the rules around them";
- one punctuation mark carrying every aside, most often the em dash, while
  parentheses and semicolons sit unused. Swapping the dash for parentheses
  trades one tell for another; the fix is usually a second sentence;
- a hedge attached to every sentence rather than once to the limitation it
  qualifies;
- paragraphs of matching length and identical internal shape;
- a conclusion that chews what the opening already said.

Formatting tells, which are the same defects done with typography:

- a bold lead-in on every paragraph. It looks like emphasis and works like an
  index, and two in a row is a list pretending to be prose;
- a heading over three sentences, or a heading in Title Case;
- a "Summary" or "Conclusion" section, which is the flourish given a header;
- a table or bulleted list whose content was never parallel. Structure when the
  content is already structured, and write paragraphs otherwise;
- markdown debris: tracking parameters, stray anchors, a link label that is a
  bare URL.

Protect the plain constructions these replace. `is`, `has` and `does` are not
upgrades waiting to happen, and a sentence that already says the thing needs no
frame in front of it.

These are signals, not blind replacement rules. A technical term stays when it
names a distinction the project actually uses.

## What to keep

This modifier only subtracts, so applied hard enough it removes a voice along
with the slop. Before cutting, note what is deliberate in the writing at hand:
the words this project uses exactly, the rhythm of a person who habitually writes
short, an aside that carries a judgement, a joke that survives the edit. Those
are not tells. A pass that leaves every author sounding the same has failed, and
a flat, careful, evenly-paced neutral is its own recognisable voice.

Where a corpus of the author's own writing exists, read some of it first and
write down what recurs, so the pass has something to protect and not only a list
of things to remove.

## Checking it

Nothing here is falsifiable on its own, which is how a pass gets claimed without
being run. Two scripts in the owner's local kit report what a machine can see and
are the check to reach for rather than reimplement: `bdos/cores/level-with-me/
scripts/passive/read_back.py` finds preamble openings, stacked bold openers,
restating closers, and sentences past forty words; `bdos/cores/kill-your-darlings/
scripts/passive/cut_report.py` lists passages no fact depends on and pairs of
sentences that say the same thing. `bdos/cores/level-with-me/references/
phrasebook.md` gives the substitution rather than the prohibition.

Their findings are candidates to argue with. Neither can run step 9.

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
