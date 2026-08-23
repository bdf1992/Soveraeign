# 0033 · Tier model bindings and the executable three-tier loop

Status: `PROPOSED`

## Decision

Bind each SDLC tier to a declared model binding in
`contracts/tier-bindings.json`, and make the Control -> Orchestration -> Work
loop executable through `scripts/sov_loop.py`. Control and Orchestration run on
`gpt-oss-20b`; Work runs on `qwen3-4b`; the observation stance runs on
`gpt-oss-20b` and must differ from the binding that produced the output it
judges. Every tier step and the observation emit a receipt, and every model
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
- Live run 2026-08-23: 4 invocations, 4 receipts, 4446 input and 5486 output
  tokens, 94.6s wall, `LOCAL_ONLY` throughout, settlement `COMMITTED`

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

## Consequences

- `python scripts/sov_loop.py table | selfcheck | audit | run` exists.
- `conformance/fixtures/loop/tier-cases.json` carries 1 positive and 8
  defeating cases; every declared refusal code has a case that proves it.
- `scripts/tests/test_sov_loop.py` adds 15 tests; `verify.py` discovers them
  without edit, so this lands without touching the verification harness.
- Which model each tier runs on is now a recorded choice rather than a host
  accident, and changing it is a contract edit with a visible diff.

## Defaults taken

- Assigned the larger local model to Control, Orchestration, and observation,
  and the smaller to Work, on the reasoning that judgement and decomposition
  carry more consequence than execution. Reversible: it is one field per tier.
- Modelled observation as a stance rather than a fourth tier, because
  `SDLC.md` fixes depth at three.
- Modelled grant narrowing as authority scope rather than verb subsetting: a
  worker executes, which its orchestrator does not, so a literal subset rule
  would refuse every legitimate run.
- Left the SPEC-versus-kernel-contract refusal-code drift alone. At `cf587d5`
  `sov_kernel.py selfcheck` passes; the drift is in another session's
  uncommitted redesign of `contracts/kernel-transitions.json` and belongs to
  whoever finishes it.
