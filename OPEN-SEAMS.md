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