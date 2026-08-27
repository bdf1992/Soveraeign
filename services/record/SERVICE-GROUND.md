# Record Service Ground

Status: `BUILT` (self-report, drafting session, 2026-08-27 — not
`WITNESSED`, not `RATIFIED`)

Service-scoped projection of `GROUND.md`, per `decisions/0067`. Named
`SERVICE-GROUND.md`, not `GROUND.md` — the root document owns that name and
holds the sixteen claims that say what product Soveraeign is. These are
narrower: what this service commits to always being true for whatever
crosses into it, each with what would defeat it, each citing the root
`GROUND-<nnn>` claim it specializes where one applies.

### A journal row, once committed, is never mutated or deleted

> No method updates or deletes a journal row. The only `DELETE` this service
> performs is against a projection, which is rebuildable by definition.

Specializes `GROUND-009` (correction never erases occurrence).

*What would defeat it.* Any code path that issues `UPDATE` or `DELETE`
against a journal-entry row, or a projection rebuild that silently changes a
journal row instead of only reading it.

### Retraction preserves the countered entry

> `counter-entry` appends a counter-record and leaves the original entry
> exactly where it was, readable, with its payload intact. It never claims
> that consumed resources or an external effect came back.

Specializes `GROUND-009`.

*What would defeat it.* A retraction that removes, hides, or edits the
original entry; a counter-record whose text or receipt claims a rollback of
anything outside this journal.

### Every entry binds to the exact digest of the entry before it

> Each row names the exact hashing profile used to produce it and the digest
> of its predecessor. `reconstruct` stops verifying at the first link that
> does not hold rather than accepting a partially valid chain.

Specializes `GROUND-005` (a consequential act binds to exact state).

*What would defeat it.* A rewritten payload, actor, kind, or subject that
still verifies; a row hashed under one profile that is accepted as verifying
under another; `reconstruct-journal` returning success past a broken link.

### A projection cannot become the record

> `subject_projection` is derived: dropped and rebuilt from the journal
> alone, identical every time. `append_from_projection` exists only to
> refuse.

No root `GROUND-<nnn>` claim names this directly; the closest is `GROUND-011`
(standing does not collapse), and treating a derived projection as
authoritative is, by inference rather than a stated citation, the same shape
of collapse that claim refuses at the standing-lifecycle level.

*What would defeat it.* `append_from_projection` committing instead of
refusing; two rebuilds of the same unchanged journal producing different
projection content.

### This journal is verifiable without trusting this service's own code

> `scripts/witness_record.py` recomputes every digest from the stated chain
> rule and reaches the service only through its CLI subprocess boundary,
> never by importing `core.py`.

Specializes `GROUND-010` (a report is not an observation).

*What would defeat it.* A claim about this journal's integrity that requires
importing the participant's own module to check, or that requires oral
explanation beyond what `CHARTER.md` and the CLI already state.

### Every crossing into this journal leaves a durable attributable record

> An append, a receipt, a counter-entry, or a refusal — `DESIGN_RECORD_REFUSED`
> included — is itself an attributable outcome a caller can point to.

Specializes `GROUND-007` (every crossing leaves a record).

*What would defeat it.* A crossing into this service — commit or refusal —
that leaves nothing an outside party can later address or attribute.
