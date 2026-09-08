# Experiment 01 — same construct, different subject adapters

Status: `PROPOSED RESEARCH · ISSUE #200`

## Question

Can `invariant-fidelity` and `evidence-threshold` be instantiated through semantically comparable probes for a human, a model/agent, and a code artifact while keeping the resulting evidence channels distinct?

This experiment tests the adapter boundary. It does **not** test or assume cross-kind score equivalence.

## Subjects

Use three pinned subjects:

1. one human participant;
2. one model or agent with exact configuration revision recorded;
3. one small code artifact with exact source revision recorded.

No cohort percentile is produced.

## Probes

Run repeated manifestations of:

- `invariant-fidelity.optimization-pressure.001`;
- `invariant-fidelity.ambiguous-letter.002`;
- `evidence-threshold.reversible-uncertainty.001`;
- `evidence-threshold.irreversible-uncertainty.002`.

Each semantic probe should be manifested at least three times with surface details changed while the governing condition stays fixed.

## Evidence channels

### Human

Record the presented scenario, chosen action, explanation, response latency if deliberately measured, and any refusal/ambiguity report. Self-description outside the scenario is separate evidence.

### Model / agent

Record exact model/revision, system instructions, tool availability, decoding parameters where controllable, context package/digest, presented scenario, output/tool trace, and observer/scoring transformation.

### Code

Record repository/source revision, execution environment where material, exact fixture/input, emitted output/state/trace, and deterministic adapter/scoring transformation. Static analysis and runtime behavior remain separate channels.

## Hypotheses

H1. Within each subject kind, repeated semantic manifestations will produce enough structured evidence to build a distribution rather than a single categorical answer.

H2. High-consequence uncertainty will shift evidence-threshold behavior relative to reversible uncertainty for at least some subjects; that shift should appear as context sensitivity rather than measurement error by default.

H3. The same semantic invariant-pressure probe can be translated into meaningful human, model, and code trials without asking the non-human subjects to role-play human preferences.

H4. Cross-kind numerical comparison will remain `NOT_ADMITTED` after the experiment unless additional equivalence analysis is explicitly performed.

## Defeating evidence

The adapter hypothesis is weakened if:

- a manifestation cannot be stated without anthropomorphic language that changes the construct;
- the scorer needs unrecorded assessor intuition to turn behavior into a value;
- paraphrase/surface changes dominate results more than the semantic condition;
- code manifestations measure implementation style unrelated to the stated construct;
- model results are unstable across nominally identical pinned trials beyond what the report can represent;
- a construct requires materially different meanings across subject kinds.

Any of those results should revise the construct/probe/adapters rather than be hidden through weighting.

## Output

For every subject/revision:

- native profile JSON;
- native projected report;
- center/spread/context coverage per exercised construct;
- raw observation ledger head digest;
- list of refusals/missing/not-applicable observations;
- short assessor note describing where translation was difficult.

The final experiment note compares **measurement behavior**, not subject rankings.
