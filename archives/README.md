# Archives

Superseded governing documents, kept byte-identical.

## The rule

**Nothing in this directory is edited.** Not a typo, not a broken link, not a
stale number. A file here is a record of what a document said when work was
attributed against it, and correcting it destroys the only thing it is for.

**Nothing here is current policy.** Every file is superseded by a document at
the repository root. Read the successor to learn what is true; read the archive
to learn what was committed to.

If an archived file needs to change, the answer is that a different file needs
to change.

## Why they are kept rather than left to git history

`contracts/phases.json` pins some of these by `sha256` digest. A phase must end
against the definition it opened with, or a campaign can close by narrowing its
own definition until the evidence on hand satisfies it — and no later reader
could tell the difference. The pin reads the working tree, not the history, so
the bytes have to exist at a resolvable path.

`scripts/sovcustody/phase.py` refuses on two codes here:
`MISSING_DEFINITION` when a pinned document is absent, and
`UNPINNED_DEFINITION` when its digest no longer matches. Moving or editing a
file in this directory fires one of them.

## What is here

| File | Superseded by | Pinned by | Archived |
| --- | --- | --- | --- |
| `PRD-PHASE-I.md` | `PRD.md` | `contracts/phases.json`, `phase:i` | 2026-08-28 |
| `ROADMAP-F0-F6.md` | `ROADMAP.md` | `contracts/phases.json`, `phase:i` | 2026-08-28 |

**`PRD-PHASE-I.md`** — revision 1 of the product requirements,
`Product Requirements — Founding and Phase I`, written 2026-08-22. It scoped the
product to one campaign and stated nine requirements, `PROD-I-1` through
`PROD-I-9`, with a five-clause exit. Those nine are not retired: they continue
as the `Phase I · Local Sovereign Foundation` qualification profile in `PRD.md`,
with their predicates in `SPEC.md` and their fixtures in `conformance/`.

**`ROADMAP-F0-F6.md`** — the evidence-gated construction ladder, `F0` through
`F6`. Superseded by the `P0`–`P9` product phases, which exit on a demonstrated
product result rather than on component completion. It also holds the original
keying of the name crosswalk, which `ROADMAP.md` carries forward re-keyed.

Both were archived on 2026-08-28 at Bdo's direction, after `phase:i` closed
`CLOSED_INCOMPLETE` on 2026-08-27 and the product definition was rewritten to
cover the whole product rather than one campaign.

## Adding to this directory

A document is archived, not deleted, when something still addresses it — a
digest pin, a decision record, an attribution, or a receipt. If nothing
addresses it, git history is enough and the file should go.

Move it with `git mv` so the bytes are provably unchanged, repoint every
reference, and confirm the pin still holds:

```text
python -m unittest scripts.tests.test_custody_boards
python scripts/verify.py
```

Then add a row above saying what supersedes it and what pins it.

## Standing

This directory holds no standing and grants nothing.
`contracts/publication-surface.json` classifies it `JOURNAL`: kept deliberately,
and never routed to as documentation.
