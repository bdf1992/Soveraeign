# 0033 · Tier model bindings and the executable three-tier loop

Status: `PROPOSED`

## Decision

Bind each SDLC tier to a declared model binding in
`contracts/tier-bindings.json`, and make the Control -> Orchestration -> Work
loop executable through `scripts/sov_loop.py`. Control, Orchestration, and the
observation stance run on `lfm2-5-8b`; Work runs on `qwen3-5-4b`; the observer
must differ from the binding that produced the output it judges.

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

## Residuals this run exposed

- The observer's raw `<think>` reasoning is captured verbatim into the
  transcript. `lfm2.5:8b` and `qwen3.5:4b` are both thinking models and nothing
  strips those blocks, so the recorded output is not the observer's answer.
- In the live run the observer said it could not find a report to judge. The
  loop passes accumulated context rather than an addressed report, so the
  observation stance is reading a conversation, not an artifact. That is a
  prompt and interface defect, not a model defect, and it weakens every
  observation the loop currently produces.
- Marker-based grading is coarse: it can miss a correct objection phrased
  unusually, so each score is a floor. No candidate caught all five planted
  defects in every sample.

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
- Chose the pair that co-resides over the pair with the higher ceiling, because
  the owner asked for the fast loop and eviction cost more than the score
  difference bought.
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
