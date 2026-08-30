# AI-native standard

Status: `OWNER-DIRECTED · FREEZE CANDIDATE`

## Definition

A named operation is **AI-native** when a model can discover and perform it through a
declared machine-usable interface while using the same authoritative state, constraints,
and history as a human operator. The result must remain attributable, inspectable, and
correctable.

AI use by itself does not qualify. A chat box, generated suggestion, computer-use script,
or hidden automation can be useful while the underlying operation remains human-only.

The unit of evaluation is one named operation on one operating surface. Do not grade an
entire company, product, repository, or model at once.

## Minimum threshold

Score each axis `NONE`, `PARTIAL`, or `FULL`. Any score above `NONE` needs observable
evidence. A score without evidence makes the assessment invalid.

### Reachability

This is the gate.

Can a fresh model discover the relevant state, available operation, required inputs,
constraints, and result through a declared machine-usable path?

- `NONE`: no declared path exists. The model depends on human translation or visual
  impersonation.
- `PARTIAL`: a structured path exists, but material parts of the operation remain hidden,
  manual, or specific to one interface.
- `FULL`: the model can reach all state, operations, constraints, and results needed for
  the named operation through a stable declared interface.

An unreachable operation cannot be AI-native.

### Commitment

Can the system tell generated output apart from accepted enterprise state?

- `NONE`: generated output and accepted state are indistinguishable.
- `PARTIAL`: proposals are marked and require an explicit acceptance step.
- `FULL`: recording, admission, typed ratification, attestation, and current effectiveness
  remain distinct.

### Provenance

Can a model-used or model-produced value be traced back to its source?

- `NONE`: the origin cannot be recovered.
- `PARTIAL`: the value identifies source records or versions.
- `FULL`: source, version, reader, derivation, configuration, and exact-or-lossy status are
  reconstructable.

### Retraction

Can an AI-caused effective change be countered without erasing history?

- `NONE`: no governed counteraction exists.
- `PARTIAL`: record-local state can be countered while history remains intact.
- `FULL`: counteraction respects effect class. Record state, consumed resources, and
  external-world effects stay distinct, with explicit compensation or refusal rules.

### Substantive-operation check: `earn_it`

Would removing the model path remove real domain capability, or only an explanation,
suggestion, or alternate control?

This is an attributed human judgement:

- `SUBSTANTIVE`: the model operation is part of the actual operating path.
- `BOLTED_ON`: AI sits beside the real operating path.
- `OPEN`: the judgement has not landed.

`OPEN` is not favorable. `BOLTED_ON` produces `DECORATION` even when the technical
interface is otherwise strong.

## Derived verdict

A complete assessment earns the minimum `AI_NATIVE` verdict only when:

```text
reachability >= PARTIAL
AND at least one of {commitment, provenance, retraction} >= PARTIAL
AND earn_it = SUBSTANTIVE
```

Assessment state and verdict are separate:

- missing evidence or contradictory scores -> `INVALID`;
- `earn_it = OPEN` -> `OPEN`;
- sufficient evidence plus the human judgement -> `COMPLETE`.

For a complete assessment:

- unreachable with another structural axis present -> `TRUTH_CAPABLE`;
- unreachable with no structural axis present -> `DECORATION`;
- reachable but bolted on -> `DECORATION`;
- reachable and substantive but below the supporting threshold -> `TRUTH_CAPABLE` when a
  structural axis is present, otherwise `DECORATION`.

The system derives the verdict from the recorded scores. A participant never selects its
own verdict.

## Soveraeign qualification

The minimum verdict is useful for comparing systems. It is not enough for Soveraeign's
own operations.

A named operation is `SOVERAEIGN_QUALIFIED` only when it earns the minimum verdict,
scores `FULL` on reachability, commitment, provenance, and the admitted effect envelope,
and passes every check below.

1. **Same-world parity.** Human and model interfaces resolve to the same authoritative
   transitions, constraints, standing, and receipts.
2. **Typed authority.** Grants are scoped, revocable, attributable, and checked at the
   operation. Verification authority cannot ratify judgement.
3. **Independent observation.** The executor's report is not the success oracle.
4. **Receipt completeness.** Admission, refusal, operation, failure, observation, and
   counteraction leave their required durable records.
5. **Effect honesty.** Record retraction never pretends to refund resources or reverse an
   external-world effect.
6. **Cold-start competence.** A fresh instance can become safely useful from the artifact
   alone, with time and intervention measured.
7. **Two-binding proof.** A human binding and a model binding pass the same positive and
   defeating fixtures against the same kernel contract.
8. **Local sovereignty.** Losing Claude, GitHub, a graph database, or another integration
   cannot silently remove authoritative memory, authority, or local operational
   continuity.
9. **Model substitutability.** Two materially different models, including one supplied by
   the owner, can use the same operation and kernel contracts. Model identity, crossed
   data, usage, and cost remain visible. An unavailable model refuses without silent
   fallback.

## Required assessment record

Every evaluated operation records:

```yaml
surface: <stable surface identifier>
operation: <named domain operation>
artifact_revision: <commit or digest>
model_and_host: <model, runtime, tools, versions>
scores:
  reachability: NONE | PARTIAL | FULL
  commitment: NONE | PARTIAL | FULL
  provenance: NONE | PARTIAL | FULL
  retraction: NONE | PARTIAL | FULL
earn_it:
  value: SUBSTANTIVE | BOLTED_ON | OPEN
  reviewer: <attributed judgement authority>
assessment_state: INVALID | OPEN | COMPLETE
minimum_verdict: <derived>
soveraeign_checks:
  same_world_parity: PASS | FAIL | UNATTESTABLE
  typed_authority: PASS | FAIL | UNATTESTABLE
  independent_observation: PASS | FAIL | UNATTESTABLE
  receipt_completeness: PASS | FAIL | UNATTESTABLE
  effect_honesty: PASS | FAIL | UNATTESTABLE
  cold_start_competence: PASS | FAIL | UNATTESTABLE
  two_binding_proof: PASS | FAIL | UNATTESTABLE
  local_sovereignty: PASS | FAIL | UNATTESTABLE
  model_substitutability: PASS | FAIL | UNATTESTABLE
qualification: SOVERAEIGN_QUALIFIED | NOT_QUALIFIED
evidence: [<addresses>]
defeating_cases: [<fixture identifiers>]
```

`UNATTESTABLE` is not a pass. Qualification is derived, never selected. It requires a
complete `AI_NATIVE` assessment and `PASS` on every Soveraeign check.

## Asset Service proving operation

The first proving operation for the asset system is:

> From a fresh local environment, locate an original asset, create a declared derivative
> for a named use, relate it to the source and campaign, obtain the required authority,
> independently verify the output, expose the same result to a human and a model, and
> retract the effective use without erasing provenance or claiming the generated file
> never existed.

The positive case must finish with reconstructable receipts. Defeating cases include
unauthorized success, missing derivation provenance, executor-only success, stale source
use, direct graph mutation, and retraction that erases history.

## Policy boundary

The minimum verdict and `TRUTH_CAPABLE` preserve the earlier threshold and Gauge language
from the project's source evidence. Same-world operation, typed authority, independent
observation, complete receipts, effect honesty, cold-start use, local ownership, and model
substitutability are the stricter Soveraeign qualification.

Exact score meanings, explicit assessment states, the all-`FULL` target bar, two-binding
proof, and integration-loss sovereignty remain freeze-candidate policy until separately
ratified. Do not present them as older settled policy merely because the checker implements
them.
