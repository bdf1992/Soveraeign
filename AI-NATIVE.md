# AI-Native Standard

Status: `OWNER-DIRECTED · FREEZE CANDIDATE`

## Definition

An enterprise surface is **AI-native** when a model can reach and perform a
substantive domain operation through the system's declared interfaces while
remaining inside the same authoritative state, constraints, and history as a
human operator—and the resulting operation is attributable, inspectable, and
correctable.

AI use is not sufficient. A chat box, generated suggestion, computer-use script,
or hidden automation may be useful without making the underlying surface
AI-native.

The unit of evaluation is a **surface performing a named operation**, not a
company, product, repository, or model in the abstract.

## Minimum AI-native threshold

Score each axis `NONE`, `PARTIAL`, or `FULL`. Every score above `NONE` must
identify observable evidence; otherwise the assessment is invalid.

### Reachability — the gate

Can a fresh model instance discover the relevant state, available operations,
required inputs, and returned result through a declared machine-usable path?

- `NONE` — no declared path; the model depends on human translation or visual
  impersonation.
- `PARTIAL` — a structured path exists, but material parts of the operation
  remain hidden, manual, or surface-specific.
- `FULL` — all state, operations, constraints, and results needed for the named
  operation are available through a stable declared interface.

An unreachable surface cannot be AI-native regardless of every other score.

### Commitment

Can the system distinguish a model's output from accepted enterprise state?

- `NONE` — generated output and accepted state are indistinguishable.
- `PARTIAL` — proposals are marked and require an explicit acceptance step.
- `FULL` — recording, admission, typed ratification, attestation, and current
  effectiveness remain distinguishable.

### Provenance

Can a model-used or model-produced value resolve to where it came from?

- `NONE` — origin cannot be recovered.
- `PARTIAL` — the value identifies source records or versions.
- `FULL` — source, version, reader, derivation, configuration, and
  exact-or-lossy status are reconstructable.

### Retraction

Can an AI-caused effective change be countered without erasing what happened?

- `NONE` — no governed counteraction exists.
- `PARTIAL` — record-local state can be countered while preserving history.
- `FULL` — counteraction is effect-class aware: record state, consumed
  resources, and external-world effects are distinguished; compensation or
  refusal boundaries are explicit.

### Substantive-operation check (`earn_it`)

Would removing the AI path remove a material domain capability, rather than a
convenient explanation, suggestion, or alternate control surface?

This is a human judgement with an attributable reviewer:

- `SUBSTANTIVE` — model operation is integral to the evaluated surface;
- `BOLTED_ON` — AI is an accessory beside the actual operating surface;
- `OPEN` — the judgement has not landed.

`OPEN` is not a favorable result. `BOLTED_ON` produces `DECORATION` even when
the technical interface is excellent.

## Derived verdict

A valid, complete surface assessment receives the minimum `AI_NATIVE` verdict
only when:

```text
reachability >= PARTIAL
AND at least one of {commitment, provenance, retraction} >= PARTIAL
AND earn_it = SUBSTANTIVE
```

Assessment state is separate from verdict:

- missing evidence or contradictory scores → `INVALID`;
- `earn_it = OPEN` → `OPEN`;
- evidence and human judgement present → `COMPLETE`.

For a complete assessment:

- unreachable with another structural axis present → `TRUTH_CAPABLE`;
- reachable but bolted on → `DECORATION`;
- reachable and substantive but below the supporting-axis threshold →
  `TRUTH_CAPABLE` when a structural axis is present, otherwise `DECORATION`.

The verdict is derived from the recorded scores. It is never selected directly.

## Soveraeign target bar

The minimum verdict is useful for evaluating the market. It is not sufficient
for Soveraeign's own operational surfaces.

A surface is `SOVERAEIGN_QUALIFIED` only when the named operation passes the
minimum verdict, scores `FULL` on reachability, commitment, provenance, and the
effect envelope admitted for the current phase, and also proves:

1. **Same-world parity** — human and model interfaces resolve to the same
   authoritative transitions, constraints, standings, and receipts.
2. **Typed authority** — permissions are scoped, revocable, attributable, and
   checked at the operation; verification authority cannot ratify judgement.
3. **Independent observation** — an executor's report is not the success oracle.
4. **Receipt completeness** — admission, refusal, operation, failure,
   observation, and counteraction leave the required durable records.
5. **Effect honesty** — record retraction never masquerades as resource refund
   or external-world rollback.
6. **Cold-start competence** — a fresh instance can become safely useful from
   the artifact alone, with time and intervention measured.
7. **Two-binding proof** — a human binding and a model binding pass the same
   positive and defeating fixtures against the same kernel contract.
8. **Local sovereignty** — loss of Claude, GitHub, a graph database, or another
   integration cannot silently remove custody of authoritative memory,
   authority, or operational continuity.
9. **Model substitutability** — two materially different models, including one
   owner-supplied local or remote model, can use the same named operation and
   kernel contracts; model/provider identity, crossed data, usage, and cost
   remain visible, and unavailable models refuse without silent fallback.

The Soveraeign bar does not replace the minimum verdict. It is a stricter
qualification layered above it.

## Required test record

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
  model_substitutability: PASS | FAIL | UNATTESTABLE
qualification: SOVERAEIGN_QUALIFIED | NOT_QUALIFIED
evidence: [<addresses>]
defeating_cases: [<fixture identifiers>]
```

`UNATTESTABLE` is not a pass and must remain visible.

## Asset Service proving operation

The first proving operation for the asset system is:

> From a fresh local environment, locate an original asset, create a declared
> derivative for a named use, relate it to the source and campaign, obtain the
> required authority, independently verify the output, expose the same result to
> a human and a model, and retract the effective use without erasing provenance
> or claiming the generated file never existed.

The positive narrative must complete with reconstructable receipts. Defeating
fixtures must include unauthorized success, missing derivation provenance,
executor-only success, stale source use, direct graph mutation, and retraction
that erases history.

## Evidence and policy boundary

The minimum verdict and `TRUTH_CAPABLE` outcome preserve the ratified source
threshold and existing Gauge language in
`lineage/evidence/core/SUBSTRATE.md` T2. Same-world operation, authority,
observation, receipts, effect honesty, cold-start competence, personal-local
operation, and model substitutability are the stricter Soveraeign qualification
derived from the broader founding contract and owner direction.
Exact score meanings, explicit assessment states, the all-`FULL` Soveraeign
bar, two-binding proof, and integration-loss sovereignty are new freeze-candidate
policy. They must not be misrepresented as part of the earlier minimum
arithmetic until separately ratified.
