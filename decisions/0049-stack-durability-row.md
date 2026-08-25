# 0049 · The stack is missing a durability concern

Status: `PROPOSED · OWNER-DIRECTED EDIT · O2 STILL GATES RATIFICATION`

Bdo, 2026-08-23, on learning that no channel the stack offers can recover a
lost node: *"Then it's not an AI-native tech stack and needs editing."* This
decision makes that claim precise, applies the edit to the proposed baseline,
and records what it does **not** fix.

## The claim, stated exactly

Checked against `AI-NATIVE.md`, the Soveraeign bar's check 8 reads:

> **Local sovereignty** — loss of Claude, GitHub, a graph database, or another
> integration cannot silently remove custody of authoritative memory,
> authority, or operational continuity.

The stack passes the **letter** of check 8 and fails its **principle**. The
letter is scoped to *integrations*: lose Claude, lose GitHub, the node keeps
custody. The principle is that custody of authoritative memory survives the
things that go away — and the stack has no answer for the most ordinary thing
that goes away, which is the machine.

The scoping is consistent throughout the baseline, which is what makes it a
structural omission rather than an oversight in one sentence:

| Where durability is mentioned | Scoped to |
| --- | --- |
| `ENGINEERING.md` selection rule: "survives loss of optional providers" | providers |
| `ENGINEERING.md` growth trigger: "Durable work must outlive a process" | a process |
| `ENGINEERING.md` stack row: "transactional SQLite" | a transaction, within one medium |
| `SPEC.md` fault model: process restart, partial write, power loss | one machine, still running |
| `AI-NATIVE.md` check 8 | integrations |

Every durability concept in the system is scoped to a process, a transaction,
or an external provider. **Nothing is scoped to the medium.** `SPEC.md` says
so directly: "Media durability beyond detectable corruption is an
infrastructure concern and is not claimed by the logical specification."
That sentence is correct for a *logical* specification — and it means the
technical baseline is exactly where the claim must be made instead. The
baseline does not make it.

## Why this is an edit rather than an implementation gap

Three Soveraeign checks are currently unmet, and they are not the same kind of
unmet:

| Check | State | Kind |
| --- | --- | --- |
| 7 · Two-binding proof | one binding exists (Python API and CLI) | **an unimplemented row** — "Local surface" is in the table |
| 9 · Model substitutability | no adapter executes (O12, PROD-I-9) | **an unimplemented row** — "Model execution" is in the table |
| 8 · Local sovereignty, in principle | node loss is total loss | **a missing row** — no durability concern is in the table at all |

Checks 7 and 9 are honest debts: the baseline names the concern, and the work
is queued behind open decisions. Check 8 is different in kind. A row that does
not exist cannot be implemented, scheduled, or witnessed, and no amount of
identity, recovery, or kernel work reaches it — a recovery secret redeems
against a journal that must still exist (`decisions/0048` ID-11b,
`OPEN-SEAMS.md` S11).

That is the sense in which the stack is not yet AI-native by its own standard:
not that it scores badly on a listed axis, but that the axis carrying its own
survival was never listed.

## The edit

Add one concern row to the minimal reference stack and one growth trigger.
Both are deliberately the smallest thing the selection rule admits, and both
lean on primitives that already exist rather than introducing technology.

The Record Service already chains every entry to the digest of the one before
it, and already offers `reconstruct-journal`. A portable export is therefore
**self-verifying by construction**: a copy either replays into the same chain
or it visibly does not. Nothing new is required to make a copy trustworthy —
only to declare that one is owed.

Applied to `ENGINEERING.md`:

- stack row — **Durability and custody** | *Portable self-verifying journal
  export; restore by replay with chain verification* | *Boundary: an export is
  custody of the node's own record, not an integration with an external
  system. Where the copy is kept is the operator's act and the operator's
  risk.*
- growth trigger — **The record must survive its medium** → *journal export
  plus restore-by-replay, verified against the digest chain*.

## What the edit does not fix

- ~~It does not implement export or restore.~~ **Implemented** in
  `services/record/.../custody.py` with sixteen positive and defeating cases.
  Building it surfaced one property worth recording here: an export is
  self-verifying against an edited field, a reordered pair, or an entry cut
  from the middle, and **not** against truncation, because a shortened journal
  is a valid journal. Detecting a truncation requires a head digest held
  outside the export — the same shape as ID-11, where the root cannot recover
  itself from inside the node. A record cannot certify its own completeness
  from the inside.
- **It does not decide off-node custody.** Whether copying an export to
  another disk, another machine, or a remote service is an `EXTERNAL_WORLD`
  effect under O7 is genuinely open — the copy mutates no external system, but
  it does put node bytes somewhere the node does not govern. Queued.
- **It does not answer ID-11c.** Succession is judgement, not durability.
- **It does not close O2.** The baseline remains proposed. This edit changes
  what O2 would ratify, which is the point of making it before ratification
  rather than after.
- **It does not amend `AI-NATIVE.md`.** Check 8's wording is a freeze
  candidate and its scope is Bdo's naming judgement. The proposed widening is
  held below.

## Proposed amendment to `AI-NATIVE.md` (held, not applied)

Check 8, from:

> **Local sovereignty** — loss of Claude, GitHub, a graph database, or another
> integration cannot silently remove custody of authoritative memory,
> authority, or operational continuity.

to:

> **Local sovereignty** — loss of Claude, GitHub, a graph database, another
> integration, **or the storage medium itself** cannot silently remove custody
> of authoritative memory, authority, or operational continuity. Custody that
> depends on one medium surviving is custody on loan.

If Bdo accepts this widening, every prior `soveraeign_checks.local_sovereignty`
assessment recorded before it becomes `UNATTESTABLE` rather than `PASS`, since
they were scored against the narrower question. That is the honest consequence
of widening a bar and is stated here rather than discovered later.

## Judgement queue for Bdo

1. Accept, amend, or strike the durability row and growth trigger.
2. Accept or strike the `AI-NATIVE.md` check 8 widening — and if accepted,
   whether prior assessments re-score as `UNATTESTABLE`.
3. Is an off-node copy an `EXTERNAL_WORLD` effect under O7?
4. O2 remains open; this edit changes what ratifying it would mean.
