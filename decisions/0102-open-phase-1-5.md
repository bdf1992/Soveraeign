# 0102 · Open Phase 1.5

Status: `OWNER-DIRECTED · ROOT ACT PERFORMED · NOT SELF-RATIFYING`

Bdo, occupying the root seat, directed on 2026-09-03 that Phase 1.5 be open, in his own
words in the session that prepared this branch. Opening a phase is a root act
(`contracts/phase-1-5-phase-ii-horizon.md`, "What would justify opening Phase 1.5";
`AGENTS.md`, Design System of Record). This record performs the act exactly as the
prepared records describe it and settles nothing else.

## Decision

`phase:1-5`, Phase 1.5 - Operational Commissioning, working name Participant Delivery
Substrate, is open from 2026-09-03.

1. **The definition is pinned.** `contracts/phases.json` pins three byte copies made at
   opening: `archives/PRD-PHASE-1-5-OPENING.txt` (the qualification profile P15-Q1 to
   P15-Q4 and the commissioning terminal), `archives/SPEC-PHASE-1-5-OPENING.txt` (the twelve
   P15 predicates and the 44 normative predicates), and `archives/PHASE-1-5-HORIZON-OPENING.md`
   (the human-readable horizon). `PRD.md` and `SPEC.md` keep moving; the exit does not.
2. **Six exit clauses, quoted not paraphrased.** P15-X1 fresh participation, P15-X2 evidenced
   and fairly judged work, P15-X3 discovery, continuity, and reuse, P15-X4 definition
   recurrence and institution-neutral composition, P15-X5 the commissioning terminal, and
   P15-X6 root operational acceptance. X1 to X5 open `NOT_EARNED`; X6 opens `NOT_REACHED`
   because it cannot begin before the others carry evidence.
3. **Live custody from the first day.** `contracts/custodies/phase-1-5.json` holds one
   `EXIT` custody per clause, held by `seat:session-control` and judged by `seat:root`, each
   with a closure check a reader can run and a defeating condition. The Phase I lesson was
   that exit predicates were never on the critical path of work; an exit carried by nobody
   is the failure this collection refuses.
4. **A progress floor that refuses regression.** `contracts/phase-progress.json` carries the
   active profile: every exit custody's opening stage, `VERTICAL_SLICE` where a witnessed
   member already exists (the Observation Service thin slice under P15-X2) and `ROOT_POINT`
   elsewhere. `python scripts/sov_active_phase_progress.py` refuses a custody that falls
   below its floor.
5. **`STATUS.yaml` projects the phase.** `phase: phase:1-5`, `next_gate:
   P15_COMMISSIONING_TERMINAL`. `phase:i` names `phase:1-5` as `succeeded_by`, which carries
   no obligation forward by itself; Phase I's unmet clauses keep their own closed-unmet
   custody successors.

## What the opening does not do

- It grants no standing to any prepared material. The horizon document, the profile, and
  the P15 instrument were context; they are now the definition, which is a different thing
  from being satisfied.
- It settles no clause and earns nothing. `sov_opening_readiness.py` read `READY_TO_OPEN` at
  commit `900326e`; that was evidence for the act, not the act.
- It admits no institution. The Controller, Orchestrator, Worker, and Witness roles stay a
  commissioning instance, not the ontology (`archives/PHASE-1-5-HORIZON-OPENING.md`, "What
  Phase 1.5 must not become").
- It changes no authority. Every consequential transition still uses a typed, scoped, live
  grant; the carried seams S1 to S25 in `contracts/SUCCESSOR-PREP.md` stay carried and
  block the claims they name.

## Defaults taken

Reversible choices; Bdo may overturn any without defeating the act.

- **Six clauses rather than twelve.** The clauses follow the profile's four criteria plus
  the terminal's two sentences, and each carries the predicates of its criterion. A reader
  who wants twelve predicate-level clauses can split them; the custody board stays coherent
  at six.
- **`seat:session-control` holds every exit custody**, matching the Phase I collection.
  Work leases under them belong to principals; the seat is the carrier across sessions.
- **The next-gate token is `P15_COMMISSIONING_TERMINAL`.** No reader validates the token's
  value; `sov_opening_readiness.py` stops at `ACTIVE_PHASE` before reading it.
- **Byte copies under `archives/` rather than live pins.** `archives/README.md` already
  explains why pins must resolve against a path that does not move.
- **Closure checks are the readers that exist today.** Each names the command that reads
  the clause's state now; none of them turns green by itself, and `judgement_seat` is root
  for all six. The commissioning circuit will need a reader of its own, which is P15-X5's
  first piece of work.

## What would defeat this ruling

- A pinned archive that differs from the `PRD.md` or `SPEC.md` bytes at commit `900326e`.
- An unmet clause with no live custody, or a custody whose closure names a command that
  does not run.
- A reader that treats `phase:1-5` as ratified, or that reads a prepared predicate as
  satisfied because the phase is open.

## Judgement queue for Bdo

None. The act was his direction, performed as the records prescribe. Acceptance of the
branch that carries it is the ordinary gate.
