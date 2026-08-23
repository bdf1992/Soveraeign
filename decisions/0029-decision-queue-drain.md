# 0029 · Drain the founding decision queue

Status: `OWNER-DIRECTED · RULINGS TAKEN AS REVERSIBLE DEFAULTS`

Seventeen questions sat in `STATUS.yaml` addressed to the owner. Roughly two of
them needed to be. The rest were reversible choices that any seat could have made
and recorded, and leaving them open stopped work that no rule actually stopped.

This record says what each became. Under `0028` a ruling is a default taken
without asking, not a settlement: every one names the evidence that overturns it,
and `python scripts/sov_accept.py audit` fails on a ruling that names none.

## Presented for acceptance

Two had a finished result already sitting behind them, so they are presented
rather than ruled. The third presents this change itself.

| Was | Packet | Claim |
| --- | --- | --- |
| O2 | `acceptance/A1.json` | The Phase-I engineering baseline, built and self-tested |
| O10 | `acceptance/A2.json` | `SPEC.md` as the Phase-I logical specification, witnessed |
| none | `acceptance/A3.json` | The acceptance gate itself. O13 is ruled below; what A3 presents is the gate, which no O-number ever named. |

## Held, with a declared reason

Three name an effect that genuinely leaves the node or makes the repository
public. They stay held, each blocking exactly one transition and naming what
stays reachable meanwhile.

| Held | Reason | Blocks |
| --- | --- | --- |
| O1 | `PUBLICATION` | `repository.publish_public` |
| O7 | `EXTERNAL_WORLD_EFFECT` | `kernel.commit_external_world_effect` |
| O16b | `EXTERNAL_WORLD_EFFECT` | `coordination.activate_external_effects` |

O1 does not block Phase-I engineering. Work continues under the working name and
no agent claims legal clearance. O7 does not block building record-local doubles
and receipts. O16b does not block the ticket table, its corpus, or any draft; it
blocks writing to the live coordination surface.

## Ruled

Each ruling and its counter are in `STATUS.yaml` under `rulings`. The reasoning:

**O3, bootstrap authority.** Bootstrap trust is explicit, local, and finite: one
`BootstrapGrant` pinning attestor identity, validator version, capability, scope,
validity, and artifact revision, able to attest verification-typed claims only.
The alternative, ambient root permission, is the failure the whole authority
model exists to refuse, so this is the conservative reading rather than a
preference.

**O4, reproduction versus applicability.** Separate objects. An `Attestation` is
immutable evidence about an exact run; `CurrentEffectiveness` is a rebuildable
projection. Collapsing them would let changed applicability rewrite history,
which `CONTRACT.md` already forbids elsewhere.

**O5, Gauge and governance.** Gauge measures and owns nothing. Any other answer
collapses evidence strength into right-to-act, which is a settled source claim.

**O6, unattestable claims.** `UNATTESTABLE` keeps a claim out of `EFFECTIVE`
while preserving its historical `RATIFIED` standing, and the absence stays
visible. No silent degrade from required to optional.

**O8, semantic cold-start.** The observation shape is a named domain task
performed against exact held data with attributable outputs. It is already
executed and checked by `scripts/sov_witness.py semantic` in every verify run, so
ruling it records what is true rather than choosing something new.

**O9, classification vocabulary.** `CLASSIFICATION.md` is canonical for this
phase, subject to versioned change. A vocabulary that cannot be used until it is
ratified is not a vocabulary.

**O11, Proofing boundary.** Second boundary, at chartered standing. The counter
is a conformance case showing it is the asset lifecycle renamed, which is the
real risk and is testable.

**O12, BYOM contract.** The declared binding fields, data-boundary modes, and
two-model fixture stand. A second adapter that the fields cannot describe
overturns it.

**O13, SDLC loop.** Tiers, dyads, concern-registry derivation, and Red-gated
release stand, amended by `0028` so ordinary work needs no pre-approval. The
loop's shape was never the thing blocking work; the pre-approval reading was.

**O16, ticket workflow.** The table is the workflow. Its outward-facing steps
split off as O16b.

**O17, Sov envelope.** The declared envelope stands. Loading Sov still grants no
authority, so adopting the declaration costs nothing that refusing it protects.

**O19, verification-engagement kind.** Stands as declared, with a pinned target
and a refusal of construction identity.

**O20, kernel transition contract.** `contracts/kernel-transitions.json` is the
compiled statement of `SPEC.md`, and participants migrate onto it.
`scripts/sov_kernel.py parity` reports drift, so the counter is executable.

**O2b, baseline scope.** The baseline is a mechanism choice, replaceable behind a
proved contract without a new owner act. This is what makes A1 safe to accept:
accepting it does not freeze the mechanism.

## Decision 0020's own queue

`0020` closed with four questions for Bdo. Three are ruled here; one is presented.

1. *Ratify, amend, or strike the seat definition of Owner.* — Applied, and
   presented inside `acceptance/A3.json`. Rejecting A3 reverts it.
2. *Name the root seat.* — Left unnamed. Naming is owner-held
   (`OWNER_IDENTITY_OR_NAMING`) and nothing needs the name to proceed; the
   descriptive term `seat:root` carries the work.
3. *Tree, or matrix ownership?* — Tree, as `0020` proposed. Counter: a
   conformance case that genuinely needs two owners for one seat.
4. *Where does the registry live?* — A checked-in file at
   `contracts/seat-registry.json`, beside the other declared tables. Counter: the
   file and the operational record disagreeing once the Record Service can
   rebuild it, at which point the file becomes the projection.

## Consequences

- `STATUS.yaml` `open_decisions` is empty and the audit fails if it stops being.
- The O-numbers are kept as ruling ids so the documents that cite them resolve.
- A ruling is not a settlement. Any of them can be overturned by the evidence it
  names, which is a cheaper path than the queue it replaced.

## Source and authority

Bdo's direction, 2026-08-23, to stop generating decisions that do not need an
owner. Ruled by the control seat as reversible defaults under `0028`. None of
these rulings is an owner acceptance, and none claims to be.
