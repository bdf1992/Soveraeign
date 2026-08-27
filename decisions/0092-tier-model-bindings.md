# 0092 · Tier model bindings and the executable three-tier loop

Status: `PROPOSED`

## Decision

Bind each SDLC tier to a declared model binding in
`contracts/tier-bindings.json`, and make the Control -> Orchestration -> Work
loop executable through `scripts/sov_loop.py`. Control, Orchestration, and the
observation stance run on `gpt-oss-20b`; Work runs on `qwen3-5-4b`; the observer
must differ from the binding that produced the output it judges.

A tier receives exactly one addressed artifact and emits exactly one. The
observer receives the Work tier's report by address and digest, and answers in
a declared form that either names findings or says `NO FINDINGS`. Silence does
not clear a report.

The pair was measured on the owner's hardware, not chosen from parameter
counts. `scripts/sov_bench.py` grades a candidate on how many of five planted
defects it names in a plausible-looking worker report, and each pair is tested
for whether both models stay resident at once. Every tier step and the observation emit a receipt, and every model
invocation records the eleven provenance fields `PRD.md` PROD-I-9 requires.

Seven separation rules are enforced mechanically, each with a named refusal
code: tier depth, grant narrowing, no self-settlement, no self-witness, effect
ceiling, declared binding, and complete provenance.

## Evidence

- `SDLC.md` Three tiers (grants narrow downward, reports never self-settle) and
  Two dyads (no operator holds both hands)
- `AGENTS.md` Authority ("a model receives no authority merely by operating
  successfully"), Evidence and standing ("a build report cannot witness itself")
- `PRD.md` PROD-I-9 provenance fields; `SPEC.md` `invoke_model` refusals
- `CLAUDE.md`: "Launched agents inherit the session model today; no tier is
  pinned" - the open item this closes
- `adapters/ollama/bindings/gpt-oss-20b.json`, `qwen3-4b.json`
- Observer probe, worst of three samples per candidate, RTX 5080 16 GB:
  `gpt-oss:20b` 4/5 at 67 tok/s and 12.8 GB; `lfm2.5:8b` 4/5 at 165 tok/s and
  6.43 GB; `qwen3.5:9b` 3/5; `qwen3.5:4b` 3/5; `qwen3:4b` 3/5
- Co-residency: `lfm2.5:8b + qwen3.5:4b` both resident at 12.04 GB with 2.19 GB
  headroom. `lfm2.5:8b + qwen3.5:9b` refused, 9b evicts lfm2.5.
  `lfm2.5:8b + qwen3:4b` refused, qwen3:4b takes 12.74 GB of KV cache.
- Live run before: 94.6s wall, `gpt-oss:20b` reloading twice
- Live run after: 32.6s wall, both models resident throughout, same objective,
  4 invocations, 4 receipts, `LOCAL_ONLY`, settlement `COMMITTED`

## Constraints

- The model call is injected. No test reaches a network; the live binding is
  exercised in tests only through its refusals.
- No silent fallback: an unreachable model refuses `MODEL_UNAVAILABLE` rather
  than retrying against another.
- `EXTERNAL_WORLD` stays refused; the loop's ceiling is
  `RESOURCE_CONSUMPTION`.
- `scripts/sovloop/ollama.py` is the loop's narrow binding.
  `adapters/ollama/invoke.py` owns the general adapter path; when it lands,
  this module should delegate rather than duplicate.

## Known gap this decision does not close

The separation rules are structural, not semantic. In the live run the Work
tier reported simulated execution ("all actions are simulated, no live system
access required") and the observer accepted it as "perfectly acceptable in this
no-real-system scenario". Every mechanical rule passed: the bindings differed,
the scope narrowed, the provenance was complete, and the run settled
`COMMITTED`.

So the loop currently proves that a different model looked at the output. It
does not prove the observer challenged anything, and it cannot distinguish a
report of work done from a report of work imagined. That is the `RED` stance
`SDLC.md` describes and this decision does not implement. Until it exists, a
`COMMITTED` settlement from this loop is `BUILT` evidence about the machinery,
not evidence about the work.

## What the measurement overturned

Parameter count predicted neither score nor cost here.

- `lfm2.5:8b` matched `gpt-oss:20b`'s worst-case probe score on half the VRAM
  and 2.5x the throughput, so the larger model earned nothing in this role.
- `qwen3.5:9b` is newer and larger than `lfm2.5:8b` and scored lower, 3/5
  against 4/5.
- `qwen3:4b` is a 2.5 GB model that took 12.74 GB of VRAM once its context
  cache was allocated, which is why the original pairing reloaded on every
  tier change.

## The reversal, and why it matters more than the choice

The first version of this decision put `lfm2-5-8b` in the judging tiers on a
probe score of 4/5 against `gpt-oss-20b`'s 4/5, at half the VRAM and 2.5x the
throughput. That measurement was taken with a bench prompt, not through the
interface the model would actually run in.

Re-graded through the loop's own observation interface - an addressed artifact,
a declared output form, and the loop's own parser - the ordering inverted:

| Binding | Bench prompt | Loop interface |
| --- | --- | --- |
| `gpt-oss:20b` | 4/5 | 5/5 in every sample |
| `qwen3.5:4b` | 3/5 | 3/5 worst, 3.7 mean |
| `lfm2.5:8b` | 4/5 | 2/5 worst, 2.3 mean |

`lfm2.5:8b` scored well on the loose prompt because marker matching caught its
prose. Asked for disciplined findings about a named artifact, it collapsed. The
general lesson is the one worth keeping: a model graded outside the interface
it will run in has not been graded, and the interface moved the score further
than the model choice did.

This costs co-residency. `gpt-oss:20b` at 12.8 GB plus `qwen3.5:4b` at 5.61 GB
exceeds the 16 GB card, so the loop reloads twice per run: 32.6s resident
against 93.2s with reloads. An observer that names two of five planted defects
is not performing the function the tier exists for, so the time is spent.

## Residuals this run exposed

Both defects the previous version recorded are now closed and their fixes are
covered by cases.

- Thinking blocks are separated from the answer in `sovloop/ollama.py`. The
  reasoning is kept as evidence with its own digest and character count; it is
  not what the next tier reads. A model returning only reasoning refuses rather
  than recording an empty answer.
- The observer receives an addressed artifact instead of a transcript. In the
  live run on the new interface it named two genuinely unsupported claims in
  the worker's own output - a placeholder ticket id, and an audit-log entry the
  report claimed while also admitting it could not be written - and the run
  settled `UNRESOLVED`.

What remains open:

- Marker-based grading is coarse: it can miss a correct objection phrased
  unusually, so each score is a floor.
- The probe grades the observation stance only. Nothing yet grades Control,
  Orchestration, or Work on what those tiers are for, so their bindings rest on
  a weaker basis than the observer's does.
- `UNPARSABLE` and `FINDINGS` both settle `UNRESOLVED`. They are distinguished
  on the record but not yet acted on differently.

## Consequences

- `python scripts/sov_loop.py table | selfcheck | audit | run` exists.
- `conformance/fixtures/loop/tier-cases.json` carries 1 positive and 8
  defeating cases; every declared refusal code has a case that proves it.
- `scripts/tests/test_sov_loop.py` adds 15 tests; `verify.py` discovers them
  without edit, so this lands without touching the verification harness.
- Which model each tier runs on is now a recorded choice rather than a host
  accident, and changing it is a contract edit with a visible diff.

## Defaults taken

- Assigned the better-scoring model to Control, Orchestration, and observation
  and the other to Work, on the reasoning that judgement carries more
  consequence than execution. Reversible: it is one field per tier.
- Chose observer quality over co-residency, reversing the earlier default. Bdo
  asked for the resident pair when the evidence said the resident pair judged
  as well; it does not. Restoring the fast pair is one field per tier and the
  cost is stated above.
- Treated an unreadable observation as `UNRESOLVED` rather than as a pass.
- Kept `gpt-oss-20b` and `qwen3-4b` as declared bindings rather than deleting
  them; they are the recorded comparison the choice rests on.
- Modelled observation as a stance rather than a fourth tier, because
  `SDLC.md` fixes depth at three.
- Modelled grant narrowing as authority scope rather than verb subsetting: a
  worker executes, which its orchestrator does not, so a literal subset rule
  would refuse every legitimate run.
- Left the SPEC-versus-kernel-contract refusal-code drift alone. At `cf587d5`
  `sov_kernel.py selfcheck` passes; the drift is in another session's
  uncommitted redesign of `contracts/kernel-transitions.json` and belongs to
  whoever finishes it.
