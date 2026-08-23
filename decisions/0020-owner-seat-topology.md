# 0020 · Owner as a typed, topologically located seat

Status: `PROPOSED · DRAFTED AT OWNER DIRECTION · RATIFICATION PENDING`

Numbering note: decisions 0018 and 0019 are already occupied twice across
concurrent branches (`verification-engagement-kind` and
`kernel-transition-contract` on `main`; `federation-harness` and
`shared-kernel-reference` unmerged). This decision uses 0020 and records the
collision as a seam rather than resolving it.

This decision was drafted by Claude at Bdo's direction (2026-08-23
conversation). The definition is Bdo's; the compilation is a proposal; nothing
here is applied to `AGENTS.md`, `STATUS.yaml`, or `SPEC.md` — the amendment
text is held below for Bdo to apply or strike.

## Decision

Redefine **Owner** from a fixed person to a **seat**: a durable position in
the delegation topology, typed by what it settles and located by whom it
owns.

```text
owner(X) = the seat that issued X's live grant and settles X's receipts
```

- A **seat** is not a person, model, process, or credential. Humans and
  models are users of the system; occupying a seat is an attributable,
  revocable claim, not an identity attribute.
- Ownership is **typed**: each edge declares what the owning seat settles.
  A control seat owns orchestration and cares about coordination; an
  orchestration seat owns work and cares about the work; a work seat is in
  charge of its own execution and owns nothing.
- Ownership is **topological**: one edge up, never global. When Bdo
  interfaces with a controller, Bdo owns that controller. Bdo does not
  thereby own its workers; the orchestrator does. Ownership is not
  transitive — what crosses tiers is a grant chain, and every grant narrows.
- Reports route to the owning seat. Anyone may observe independently; only
  the owning seat settles; no seat settles its own output (C7, generalized
  from workers to every tier).

**The root seat.** A purely relational Owner makes "only the owner ratifies"
circular, so exactly one seat owns no one and is owned by no one: the root.
It holds product-intent, naming, judgement, and phase-gate authority — not
because its occupant is human, but because `decisions/0001` seated them
there. Bdo occupies the root seat. Its proper name is a naming act reserved
for Bdo (`NAMING.md`); this decision uses the descriptive term `root` only.

**The tree guard.** In Phase I the ownership graph is a tree rooted at the
root seat: every seat except the root has exactly one owner, and every
ownership chain terminates at the root in bounded steps. A cycle — any seat
that transitively owns itself — is the self-settlement failure with extra
steps and is refused at validation, not discovered at runtime. Matrix
ownership (two owners for one seat) is deliberately excluded until a
conformance case forces it.

**Identity is the missing primitive, recorded rather than faked.** A human
may claim any seat their identity would allow, and no identity verification
exists yet. Phase I therefore does not verify claims; it makes every claim
an attributable event with an actor, basis, and timestamp, so that when
identity arrives (O3), every past occupancy is auditable rather than
folklore. The wild west is admitted and journaled.

**Adoption records for ownerless history.** Runs that executed before this
topology have no owning seat on record. The honest retroactive form is not a
backdated grant — that would fabricate authority — but an **adoption
record**: a named seat states that it adopts a past run, what evidence it
adopted, what it now settles about that run, and what was never granted.
`reports/2026-08-23-seat-adoption.md` carries the first adoptions.

## Machine form

`contracts/seat-registry.schema.json` (PROPOSED) types the registry: seats,
their type, owner edge, what they settle, and current occupancy claim. The
registry is a rebuildable projection — occupancy changes are events in the
operational record; the registry file is the current view and never a second
System of Record. `contracts/fixtures/seat-registry.fixtures.json` carries
positive and defeating validation cases plus rooted-tree cases;
`scripts/tests/test_seat_registry.py` executes them.

## Composition with the stance dyads

The seat topology and the stance vocabulary (`SDLC.md`, and the colour-grade
proposal in discussion) compose into one rule:

```text
an operator's legal moves are the left hands of its own seat
plus the delegable right hands over the seats it owns
```

A worker's `RIGHT-BLUE` settlement belongs to its orchestrator-owner. A
controller's `RIGHT-GREEN` belongs to whoever is seated above it. The right
hand of a `VERIFICATION`-typed edge is delegable under grant; the right hand
of a `JUDGEMENT`-typed edge belongs to the root while the root is the owner.

## Proposed amendment text (held, not applied)

`AGENTS.md`, Authority, first sentence — from:

> Bdo holds product-intent, naming, judgement, and phase-gate authority.

to:

> The root seat holds product-intent, naming, judgement, and phase-gate
> authority; Bdo occupies the root seat (`decisions/0020`). Every other
> owner is the seat one edge up: the seat that issued the live grant and
> settles the receipts.

`AGENTS.md`, Evidence and standing — from "only Bdo can ratify judgement
claims" to "only the root seat can ratify judgement claims".

`STATUS.yaml`, authority block — each entry gains the seat form:

```yaml
authority:
  product_intent:
    seat: root
    occupied_by: Bdo
    type: human_judgement
```

`SPEC.md`, QualificationRecord — "Only the owner may change
`owner_acceptance`" reads "only the root seat"; no field change.

## What this decision does not do

- It does not reassign any authority. Bdo occupies the root seat; every
  current "Bdo holds X" sentence stays true under the new reading.
- It does not build identity verification; O3 remains open and owns the
  bootstrap question ("what seats the root seat" is O3 restated).
- It does not decide the root seat's proper name.
- It does not migrate `AGENTS.md`, `STATUS.yaml`, or `SPEC.md`; the text
  above is a proposal for Bdo's hand only.

## Judgement queue for Bdo

1. Ratify, amend, or strike the seat definition of Owner.
2. Name the root seat.
3. Tree confirmed, or is matrix ownership wanted sooner?
4. Should the seat registry live as a repository file, a Record Service
   projection, or both (file as the checked-in view)?
5. Adopt, re-execute, or strike the retroactive adoptions in
   `reports/2026-08-23-seat-adoption.md`.
6. The decision-number collisions at 0018/0019 across branches need one
   renumbering pass when the branches merge.
