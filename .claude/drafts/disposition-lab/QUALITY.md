# Disposition Lab quality program

Status: `EXPERIMENTAL · ISSUE #200`

The purpose of this program is to discover whether the assessment model deserves stronger claims. Passing software tests is necessary but not psychometric validation.

## Gate 0 — implementation integrity

Required before collecting research data:

- deterministic replay from unchanged ledgers;
- append-chain verification detects changed/reordered/cut-middle records;
- derived profiles and reports can be deleted and rebuilt;
- non-finite/out-of-range values refuse;
- unknown constructs refuse;
- model/agent observations bind a material subject configuration;
- unvalidated external-framework projections require explicit opt-in;
- cross-kind comparison refuses by default.

## Gate 1 — probe mechanics

Goal: establish that a probe exercises the process its construct definition names.

For each probe:

- state the semantic situation independent of subject kind;
- state the observable choices/behaviors and directional scoring rationale;
- produce at least one defeating example where a superficially similar behavior must not count;
- run paraphrase/manifestation variants;
- test whether irrelevant wording changes the score distribution;
- record missing/refusal/not-applicable separately from midpoint behavior.

Failure result: revise or retire the probe. Do not tune scoring merely to recover the expected answer.

## Gate 2 — within-subject repeatability and variability

Goal: distinguish persistent tendency from context-sensitive state.

For a pinned subject revision:

- repeat semantically equivalent probes across occasions;
- vary one declared context dimension at a time;
- estimate center, spread, retest consistency, and context sensitivity;
- compare self-report, observer, and enacted channels for human subjects without merging them;
- for models, repeat across random seeds/decoding where applicable while preserving the same material configuration family.

Expected result: the profile may be stable in aggregate while individual enactments vary. High variation is evidence, not automatically noise.

## Gate 3 — construct structure

Goal: test whether the seed constructs are distinguishable and coherent.

After sufficient observations:

- inspect inter-construct correlations;
- test whether probes intended for the same construct cohere better than unrelated probes;
- test alternative factor structures rather than forcing the eight-axis seed model;
- look for redundant axes, missing common factors, and method effects;
- preserve evidence when constructs are renamed/split/retired so old profiles remain reproducible under their pinned bank revision.

Failure result: change the ontology. The seed bank has no protected status.

## Gate 4 — external validity / crosswalks

Goal: determine what established instruments or external outcomes the native constructs actually relate to.

For human subjects, prefer public-domain or properly licensed instruments and compare against their documented scoring rules. IPIP is a preferred public-domain source for early research.

For every proposed projection/crosswalk:

- preregister the mapping hypothesis when practical;
- measure convergent and discriminant relationships;
- hold out validation data from mapping development;
- report uncertainty and effect sizes;
- reject mappings that only work because of shared wording or assessor interpretation.

Framework labels remain `UNVALIDATED` until this gate earns stronger standing.

## Gate 5 — measurement equivalence

Goal: determine whether a construct preserves enough meaning to support comparisons across adapters or subject kinds.

Treat each crossing separately, for example:

- human self-report <-> human enacted behavior;
- model adapter A <-> model adapter B;
- model family A <-> model family B;
- human <-> agent;
- agent <-> code;
- code static-analysis <-> code runtime trial.

Require explicit equivalence evidence before comparing means, percentiles, or cohort rank. Partial equivalence may admit only narrower comparisons. A failed equivalence test is a useful result and should remain visible.

## Gate 6 — adaptive assessment

Only after a calibrated probe bank exists:

- estimate item/probe information;
- select probes based on expected information gain under deterministic admissibility rules;
- compare adaptive profiles against fixed-form profiles on held-out subjects;
- measure item savings against precision loss;
- test stop rules and extreme-profile behavior;
- prohibit an LLM from assigning information/calibration parameters without empirical estimation.

## Gate 7 — consequential-use review

Before using profiles for decisions about people or durable authority:

- define the exact intended use;
- gather validity evidence for that use rather than relying on general validity language;
- investigate fairness and differential functioning for the intended population;
- provide correction/retest paths;
- prevent the profile from becoming identity or authority by convenience;
- require explicit governance before any high-impact use.

Disposition Lab v0.1 is not admitted for such use.

## Standing ladder

A construct, probe, adapter, or projection can independently carry:

`UNVALIDATED -> EXPLORATORY -> CALIBRATED -> VALIDATED_FOR_USE`

The right-hand state always names the use/population/context it was validated for. Validation never becomes universal by omission.

## Initial acceptance target

v0.1 is successful when Gate 0 passes and a small Gate-1/Gate-2 experiment demonstrates:

1. one semantic construct instantiated through at least two different subject adapters;
2. deterministic profile reconstruction from both;
3. visible within-subject variability;
4. explicit refusal to compare the two subject kinds until equivalence evidence exists;
5. a rebuildable native report plus at least one explicitly unvalidated framework-like report.
