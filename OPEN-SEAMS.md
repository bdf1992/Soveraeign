# Open Seams

Phase I is closed `CLOSED_INCOMPLETE`. This file records only the unresolved seams that survive that closure and the existing evidence that retired stale seams. It grants no successor-phase standing.

A carried seam is not a promise to solve it. It is an explicit statement that the closed record does not justify claiming it resolved. No implementation may silently choose a side.

## Carried

### S1 · Corpus revision alignment — CARRIED

The accepted relation between current governing text and the legacy evidence-corpus revision has not been closed. Any future opening must not import a corpus-revision assumption as settled.

### S6 · Correction measurement — CARRIED

Correction rate/count semantics still lack a closed denominator, interval, and interpretation. No gate may treat the metric as governing until that relation is fixed.

### S7 · Definition and Gauge operator bindings — CARRIED

Definition/Gauge operator behavior has not been fully re-derived through typed bindings rather than named participants. The semantics may not be claimed machine-complete.

### S8 · Evidence portability — CARRIED

Some cited raw evidence is not portable as independent source material. Dependent claims must remain explicitly unverifiable where the source cannot be independently recovered.

### S10 · Product boundary — CARRIED

Phase I did not settle the boundary between the validated internal runtime and dependent-user product exposure. No later opening may inherit a settled product-boundary claim from Phase I.

### S12 · Ratification mechanism — CARRIED

The owner ratification mechanism remains unresolved between the proposed CODEOWNERS path and the Human Binding path the owner actually uses. Direction exists; the mechanism is not settled.

### S13 · Retraction in the Soveraeign bar — CARRIED

Retraction's exact place in the all-`FULL` Soveraeign bar remains unresolved. The qualification bar may not be described as complete on this point.

### S14 · Two owners of the asset projections — CARRIED

The accepted asset/projection boundary decision leaves the overlapping projection-ownership claim unresolved. `decisions/0030-asset-projection-service-boundary.md` explicitly preserves this seam.

### S15 · Judgement request and unblock request — CARRIED

Unblock-request normalization did not eliminate the separate judgement projection or prove that the two surfaces derive from one source. `decisions/0032-unblock-ticket-kind.md` preserves that distinction.

### S16 · Decision-number allocation across branches — CARRIED

Reservation machinery now exists, but the closed record does not contain accepted seam-closing evidence that settles collision and allocation semantics. Existing settled numbers remain settled.

### S17 · A kernel refusal code the evaluator cannot emit — CARRIED

Refusal-code normalization exists, but the closed record does not establish accepted evidence that the evaluator-emission seam itself was retired. Earned refusal codes and enums remain unchanged.

### S18 · Two layers named gateway — CARRIED

The node service and transport binding still share the name gateway without a settled naming boundary. Their distinct responsibilities remain; the naming question is owner-held.

### S19 · Who publishes: an operator or a seat — CARRIED

Publication attribution remains split between operator identity and seat identity without a governed bridge. Fixtures that supply the seat directly do not close that seam.

### S22 · Two records named collection — CARRIED

Asset collection and projection collection remain distinct machine concepts. Qualified machine names remain valid; the shared human-facing noun has no owner naming settlement.

### S23 · The gateway slice landed without its standing — CARRIED

Historical gateway implementation evidence exists while `STATUS.yaml` records `gateway_service_status: CHARTERED_BOUNDARY_NOT_IMPLEMENTED`. The slice may not be carried forward as current standing.

### S24 · Durability and custody — CARRIED

The closed record does not settle the durability/custody relation across the service and runtime boundary. Existing custody evidence remains evidence, not a broader durability claim.

### S25 · The gate counts checks and never says which — CARRIED

Gate summaries count checks without identifying every atomic credited check. The result may not be claimed independently inspectable beyond the evidence actually named.

### S29 · A conforming witness record cannot satisfy the gate that requires one — CARRIED

`contracts/participant-observation.schema.json` sets `additionalProperties: false` and declares neither `verdict` nor `contributed_to_build`. `scripts/sovkernel/authority.py` `_observation_verdict` reads both at the top level and refuses `OBSERVATION_MISSING` without them. The two are mutually exclusive: a record that conforms to the schema cannot pass the gate, and a record that passes the gate does not conform. Measured 2026-09-08, no observation record under `reports/observations/` satisfies both. A landing that requires an independent observation is therefore refused whatever the witness found. No implementation may resolve this by writing the forbidden fields into a record and calling it conforming, and no reader may take the gate's refusal as evidence that no observation exists.

### S30 · The freeze that would protect witness evidence is refused by the grant that reserves the merge — CARRIED

`contracts/repository-candidate-lifecycle.json` declares `RECONCILE` with `evidence_effect: INVALIDATE_SUBJECT_EVIDENCE`, so reconciling a `MUTABLE` carrier onto a moved trunk voids any witness evidence taken against it. `FREEZE` is the declared remedy, and by the acceptance policy it needs no owner act: it is `RECORD_LOCAL`, matches no `hold_reason`, and writes only under the gitignored `.local/candidates/`. But `scripts/sov_land.py freeze` grades the candidate's declared paths against `contracts/standing-grants.json`, so a candidate touching any owner-held path is refused `AUTHORITY_REFUSED` at the freeze, not only at the landing. Such a change cannot protect its own witness evidence: every trunk move silently spends another attestation, and no carrier state is persisted anywhere in `scripts/`, `contracts/` or `.local/` that would record what was invalidated. Measured 2026-09-08 on a candidate whose evidence was spent five times this way. No implementation may resolve this by declaring only the admissible subset of a candidate's paths in order to pass the freeze, which would freeze a subject that is not the change.

## Closed by existing evidence

These seams are not carried into the gap. Their closing evidence already exists; this file does not mint a new ruling.

- **S2 · Reproduction versus applicability — CLOSED.** `decisions/0046-decision-queue-drain.md` O4 separates immutable historical Attestation from rebuildable CurrentEffectiveness.
- **S3 · Authority in the Gauge — CLOSED.** `decisions/0046-decision-queue-drain.md` O5 keeps authority separate from evidence strength and gives Gauge no authority of its own.
- **S4 · Unattestable effectiveness — CLOSED.** `decisions/0046-decision-queue-drain.md` O6 preserves ratified history while keeping an unattestable claim out of `EFFECTIVE`.
- **S5 · Cold-start semantics — CLOSED AS A SEMANTIC SEAM.** `decisions/0021-semantic-cold-start-task.md`, under the owner ruling in `decisions/0046-decision-queue-drain.md` O8, closes the semantic task shape. Cold-start competence remains a measured qualification gap because time-to-useful, adjustments, and correction effectiveness were not measured.
- **S9 · External effects — CLOSED 2026-08-30.** Root acceptance A4 and PR #182 establish explicit scope, live grant, attributable receipt, and defeating above-ceiling behavior.
- **S11 · Red-lane inputs — CLOSED 2026-08-23.** Independent verification may read builder tests as part of the artifact but never treats them as the oracle.
- **S20 · Two ladders named requirement — CLOSED 2026-08-24.** `decisions/0052` reserves bare `Requirement` for the product ladder and names the skill-side concept `CompetenceRequirement`.
- **S21 · The contract names a terminal no harness role can reach — CLOSED.** `decisions/0064-standing-authorization-and-the-landing-loop.md` separates bounded presentation from authorized landing; `decisions/0065-standing-grant-ratified.md` records the Phase-I standing grant and operational landing loop. That Phase-I grant does not survive phase closure.
- **S28 · Accepted document wording — CLOSED 2026-08-30.** The accepted wording repair is already recorded in the closed seam history.

`contracts/SUCCESSOR-PREP.md` is the gap synthesis of the surviving residue. `STATUS.yaml` remains the machine source for current phase state.

### S31 · No producer puts work in front of a session — CARRIED

`contracts/phase-1-5-phase-ii-horizon.md` draws the commissioning circuit as Definition,
Request, Agenda, Queue/Custody/Lease, and onward. A session can declare its own sources and
queues: `python scripts/sov_session.py register --source S --queue Q` populates both, and
`console` then projects them, so the projection is not inert. What does not exist is anything
that puts work there which the session did not name itself. No Request object and no Agenda
object exist. `scripts/sov_ticket.py` reads a ticket export produced by the GitHub registrar
under `adapters/github/`, and nothing carries those tickets to a session. So a participant
still learns what to do only from whoever launched it, which is the oral history `P15-X1`
forbids, at the front of the circuit whose exit clause forbids it. Measured 2026-09-08 by
carrying one concern around the circuit by hand; corrected 2026-09-09 after an independent
reading showed the first wording, "nothing anywhere writes into either", was false and
disproved in one command. No implementation may resolve this by treating a human prompt, or
a session's own registration, as a Request.

### S32 · The kernel evidence contracts are met by fixtures and by nothing that settles — CARRIED

One standard, applied to both contracts: an instance is any object that validates against
the contract.

`contracts/finding.schema.json` has one conforming instance,
`conformance/fixtures/commissioning/evidence-contract-cases.json` case
`finding-work-positive`, which validates with no defects and is checked inside
`scripts/verify.py`. `.claude/workflows/sov-loop.js` shapes another at runtime and gates it
at `frozenFinding()`, requiring the schema token, a non-placeholder projection id,
`frozen_at`, and both effects `NONE`.

`contracts/receipt.schema.json` has two conforming instances:
`contracts/fixtures/receipt.fixtures.json` and
`bindings/mcp/observations/journey-02-receipt.json`, which
`bindings/mcp/observe_journey_02.py` really emits under an issued grant.

So both contracts are exercised, by a fixture, a harness workflow and a binding. What
neither is exercised by is a service settling its own work. Console, Registry, Host,
Gateway, Observation and Asset all end a transition with a `receipt(...)` call carrying
emitted addresses, grants and effect class — a real terminal record, and a different
object. `receipt_digest` appears in no file under `services/`, so no service receipt
validates against the kernel contract, and nothing reconciles the two shapes.

`conformance/commissioning.py` grades `P15-Q2.4` by reading
`projections_frozen_before_sharing` as a boolean out of an `observed` mapping, so the
freeze is asserted to the oracle and performed by nothing.

Distinct from S29, which is a contradiction between a schema and a gate. Measured
2026-09-08.

Two earlier wordings are struck, both disproved by independent readings. The first
claimed no operation had ever emitted a receipt, that exactly one object satisfied the
schema, and that `finding_schema` appeared in exactly two files. The second denied any
Finding instance was checked in while naming the fixture that is one, and counted the
receipt fixture as an instance in the same seam — two incompatible standards for the same
evidence class — and then claimed no service emits a receipt into the Record, which
Console's `append.py` disproves. No implementation may resolve this by writing another
conforming fixture and calling the contract exercised.

