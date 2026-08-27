# Registry Service Ground

Status: `BUILT · SELF-REPORTED, NOT WITNESSED`

This document applies `decisions/0067-service-srd-spec-ground.md` to the
Registry: a short list of claims this service commits to always being true
for its caller — the node's own participants, not a human end user. Not
forced to sixteen. Each claim names what would defeat it and, where one
applies, the root `GROUND-<nnn>` claim it specializes. Accepting this
document is not a claim that the Registry currently keeps every entry below
— `GROUND.md`'s own distinction between accepted meaning and current truth
applies here too, and `SVC-REGISTRY-*` standing in `SRD.md` says which claims
have code behind them today.

## `SVC-GROUND-REGISTRY-1` — a resolution never outruns its sources

> `resolve` answers only when every declared source's bytes still match the
> digest the index was built from; a drifted source refuses the whole index,
> not only the entry it touched.

Specializes `GROUND-005` (a consequential act binds to exact state).

What would defeat it: a `resolve` call returns `COMMITTED` while
`_source_drift` in `src/soveraeign_registry_service/core.py` would report a
mismatch for an address the answer depended on.

Standing: kept today — this is the one operation `contracts/service.json`
marks `BUILT`.

## `SVC-GROUND-REGISTRY-2` — the Registry answers where, never what

> A resolution names the document that owns a subject and that document's
> address and digest. It never restates the subject's own definition,
> standing, or content.

Specializes `GROUND-011` (standing does not collapse) — a copy of a
definition inside the index would let the index's copy silently diverge from
the document that actually owns it, collapsing two distinct standings into
one convenient-looking one.

What would defeat it: an index entry stores a definition, a policy body, or a
standing value the index computed itself rather than a pointer to the
document that computed it (`CHARTER.md`, What it is not).

Standing: kept for `resolve` today, by construction — `index.py` never
carries anything beyond `capability_id`, `standing` copied verbatim from the
manifest, addresses, and digests. Untested for the `PROPOSED` write
operations, which do not exist yet to violate it.

## `SVC-GROUND-REGISTRY-3` — resolving something grants nothing

> A resolution, a read, or an entry's existence in the index never confers
> authority, standing, or permission to act on the thing it names.

Specializes `GROUND-003` (authority is granted, never acquired).

What would defeat it: any receipt from this service carries a
`standing_effect` other than `NONE`, or any code path infers an authority
grant from an entry's presence in the index.

Standing: kept today — every `resolve` receipt hard-codes
`standing_effect: NONE` in `src/soveraeign_registry_service/core.py`.

## `SVC-GROUND-REGISTRY-4` — an owner is never its own witness

> `declare-owner` and `supersede-owner` refuse when the declared witness and
> the declared owner are the same participant.

Specializes `GROUND-010` (a report is not an observation).

What would defeat it: an owner record is recorded with `owner.actor_id ==
witness.actor_id` and the operation still commits.

Standing: `OPEN`. `declare-owner` is `PROPOSED`; the constraint is declared
in `contracts/service.json` (`WITNESS_NOT_INDEPENDENT`) and in
`CHARTER.md`'s constraint list, and checked by
`python scripts/sov_owners.py check` against the authored
`contracts/domain-owners.json` table, but no Registry code path enforces it
yet — the table is policy input the Registry reads, not something it writes.

## `SVC-GROUND-REGISTRY-5` — retiring an owner counters; it never erases

> Retiring an owner record adds a counter-record under `retract` semantics.
> The original record stays addressable.

Specializes `GROUND-009` (correction never erases occurrence).

What would defeat it: `retire-owner` deletes or overwrites the retired
record instead of adding a `COUNTERED` receipt that preserves it.

Standing: `OPEN`. `retire-owner` is `PROPOSED`.

## `SVC-GROUND-REGISTRY-6` — human and model callers see the same answer

> `resolve` returns the same resolution semantics whether the request arrives
> through the human binding or the model binding, formed from the same Node
> Interface operation record.

Specializes `GROUND-002` (one governed world).

What would defeat it: the human and model bindings for `resolve` diverge in
which fields a receipt carries, or in what counts as `NAME_UNKNOWN` versus
`INDEX_STALE`.

Standing: kept as `BUILT` parity evidence per `CHARTER.md`, Built resolve
slice — explicitly self-reported, not independently observed. Does not
extend to `declare-owner`, `supersede-owner`, or `retire-owner`, which
`contracts/capability-offices.json` restricts to `HUMAN` actor kinds only —
those three operations do not promise `GROUND-002` parity even once built.

## What was deliberately kept out

- A claim that the Registry currently resolves *who is accountable* for a
  domain end to end. `read-owner` and `declare-owner` are `PROPOSED`; see
  `JOURNEYS.md` for the open custody questions this leaves unanswered.
- A claim about the eight hand-maintained tables converging. Nothing checks
  them against each other or against the index today (`CHARTER.md`, Role in
  Soveraeign); a ground claim asserting convergence would be aspirational,
  not kept.
