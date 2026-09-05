# 0104 · Settlement is one verb at three scales, and the run-level act belongs to the kernel

Status: `RULED AT CONTROL RESOLUTION · OWNER ACCEPTANCE OVER EVIDENCE`

The thin commissioning circuit (`reports/2026-09-05-thin-circuit-1.md`) judged `settle_run`
through the kernel and then appended the receipt by hand, because no participant performs
the transition. Wave 1 (`reports/2026-09-05-wave-1.md`) deferred the lane that would build one,
because three homes were possible and they are not equivalent. Bdo asked that the question be
answered from the record rather than from his own judgement, and then read the same record as
saying settlement is cumulative as well as momentary. This record holds what the governing
documents already settle, cites each line, and names what would defeat the reading.

## What the record says

**Settlement is a kernel act.** `SYSTEM.md`, Main parts: the runtime kernel "applies admission,
transition, observation, settlement, receipt, and retraction rules." `SPEC.md`, Transition
contract, row `settle_run`: current input state and a satisfactory observation in; a
`COMMITTED`, `FAILED` or `UNRESOLVED` receipt out; refuses `STALE_STATE` or
`OBSERVATION_MISSING`. `SPEC.md`, Run: "Executor completion is a report, not settlement."
`scripts/sovkernel/transitions.py` already judges the transition on exactly those terms and
`contracts/kernel-transitions.json` compiles it.

**The tiers say who asks for it.** `SDLC.md`, tier table, and `contracts/tier-bindings.json`:
Control may "settle receipts"; Orchestration may "settle worker-task outcomes" and may not
"settle its own operation"; Work may not settle. `scripts/sovloop/run.py` already records
`settlement.settled_by` as the Control binding and `scripts/sovloop/rules.py` refuses
`SELF_SETTLEMENT_REFUSED` when producer and settler coincide.

**Two homes are refused by their own charters.** `services/observation/CHARTER.md`, line 100:
"It does not settle. A satisfactory observation lets the kernel settle; it is not the
settlement." `services/record/CHARTER.md`, line 43: "It does not decide legality." The Record
holds the receipt; it does not produce the verdict.

**Settlement is also cumulative, and the record keeps the scales apart.**
`contracts/concern-admission.json` names SETTLEMENT as a role distinct from CLOSURE and LANDING,
"recompute what the landed result did to the concern: advance it, satisfy it, supersede it, or
leave it open", reached through the RECONCILE step after every landing.
`contracts/ticket-settlement.json` gives the relations: `advances` is not terminal ("the issue
remains open with the next unsatisfied state visible"); `satisfies` and `supersedes` are; merge
and green CI are never terminal. `contracts/custody.schema.json`, terminal: a DELIVERY custody
"ends SETTLED when their target predicates were evidenced and settled." `CLASSIFICATION.md`
names Root as "the irreducible local settlement locus for one Node."

## Ruling

1. **A run settles as an act, performed through the kernel.** The participant that did not
   produce the report requests `settle_run`; the kernel judges it against current state and an
   independent observation; on `PERMITTED` the receipt is appended to the Record with the settler
   as actor. The act refuses when the settler is the reporter or the observer. Its home is the
   kernel primitives under `scripts/sovkernel/`, beside the judge it uses, not either service.
2. **The act reconciles the concern it served.** After the receipt, the same act records the
   concern-level relation, `advances`, `satisfies` or `supersedes`, as a Record entry on the
   concern subject. That is the RECONCILE step made a transition instead of a hand edit.
3. **The cumulative view is a projection.** "Settling", a concern with settled runs under it and
   an unsatisfied remainder, is the `advances` relation on that concern and an open custody whose
   members are below target; "settled" is `satisfies` on the concern and `SETTLED` on the
   custody. Neither is a stored status. The board derives them, as it derives every column.
   No new vocabulary word is minted; if one is wanted, that is a `CLASSIFICATION.md` change and
   the governance domain's.
4. **A RecordProjection at session entry (P15-Q1.1) waits on session admission.** `SPEC.md`
   P15-Q1.1 asks for an "assigned Record projection", and a projection is "for one subject". A
   session has no subject in the Record until it is admitted as a node, which is the initiative
   `custody:session-as-node` already holds ("registration alone makes a session addressable
   plumbing, not a node with standing"). The entry projection is that custody's downstream, not a
   feature of the brief.

## Defect found on the way

`custody:session-as-node` closes on `python scripts/sov_node.py admit --session current`, and
`sov_node.py` has no `admit` subcommand. The thin-circuit report recorded the same shape for two
Phase I custodies. The check must name a command that exists, or say the transition is absent.
Custody upkeep, not a decision; recorded here so it is not lost.

## Defaults taken

- The settle act appends its receipt through the Record Service command line, never by import,
  so the kernel and the Record stay separate processes with the entry shape as their boundary.
- The reconcile record is an EVENT on the concern subject, not an edit to
  `contracts/custodies/*.json`. Reading it back into the board is the next bounded operation.
- Lane C is handed to a worker on these terms (`concern:phase-1-5/wave-1/settle-act`).

## What would defeat this ruling

- A governing document placing the runtime kernel inside a service.
- A ruling that a receipt appended by a control-tier participant is not Record.
- A run whose concern must be reconciled before the run settles, which would invert step 2.
- `advances` or `SETTLED` turning out to be stored somewhere as a status rather than derived.

## Judgement queue for Bdo

Nothing. Acceptance over the landed lane, when it lands, is the only owner act, and it is not a
question.
