# sov-disposition

Status: `EXPERIMENTAL · RESEARCH · ISSUE #200`

## Purpose

Use this skill to design, administer, interpret, or critique Soveraeign behavioral-disposition assessments without treating a framework label as canonical truth.

The invariant chain is:

`subject -> probe -> observation -> construct evidence -> disposition estimate -> profile -> projection`

Observed evidence and instrument provenance come first. Named personality systems, archetypes, vibe language, and human-readable summaries are projections over that evidence.

## Boundary

This skill is not a clinical or diagnostic instrument. It must not represent code, models, agents, workflows, or mechanisms as possessing human psychology merely because an analogous projection is convenient.

A projection never becomes identity, authority, permission, hiring truth, clinical judgement, or standing.

This skill may translate and explain evidence. It must not invent observations, silently infer missing answers, or choose its own validity standing.

## Operating procedure

1. Identify the subject and subject kind.
2. Identify the intended use of the profile. A score has no valid interpretation independent of its proposed use.
3. Select only constructs whose applicability can be stated for that subject kind.
4. Prefer behavioral/scenario probes over direct self-description when the subject can actually be observed.
5. Record the exact probe, adapter, context, subject revision/configuration, response/behavior, scorer revision, and omissions.
6. Treat repeated observations as a distribution. Report center, spread, sample count, context coverage, and repeatability separately.
7. Refuse cross-subject-kind or cross-adapter percentile/mean comparisons unless the instrument declares measurement-equivalence evidence for that comparison.
8. Build profile data deterministically from recorded observations.
9. Render framework projections only from profile data. Mark each projection's calibration/evidence standing and information loss.
10. Explain uncertainty, applicability, and defeating evidence in the report.

## Research-quality gates

A construct or projection is not promoted merely because it is intuitive or produces attractive reports.

Require evidence appropriate to the claim:

- **validity** — evidence supports the proposed interpretation and use;
- **reliability / precision** — repeated measurement exposes consistency and error;
- **fairness / comparability** — irrelevant barriers or systematic bias are investigated for the intended population;
- **measurement equivalence** — comparisons across groups, subject kinds, adapters, languages, or material configurations require evidence that the construct retains comparable meaning;
- **content coverage** — probes cover the intended construct rather than one convenient behavior;
- **response-process evidence** — the observed or reported behavior actually corresponds to the process the probe claims to exercise;
- **internal structure** — multi-probe construct scores should exhibit the expected relationship once enough data exists;
- **relations to external variables** — claimed crosswalks require empirical convergent/discriminant or criterion evidence;
- **consequences** — monitor whether use of the profile creates predictable harmful or misleading decisions.

For adaptive testing, optimize information only within a calibrated bank. An LLM may propose the next probe, but deterministic rules decide whether that probe is admissible and how it contributes to a score.

## Subject adapters

### Human

Self-report, forced-choice, observer report, and behavioral scenarios are distinct evidence channels. Keep them distinguishable. Do not convert an observer's reception directly into the subject's disposition.

### Agent / model

Prefer enacted trials. Bind every observation to the material configuration that can change behavior, including model/revision, system instructions, tools, decoding parameters when relevant, context package, and adapter revision. A materially different configuration is a new subject revision for comparison purposes.

### Code / mechanism

Translate a semantic probe into executable or inspectable conditions. Record what the artifact does under the condition; do not ask an LLM to role-play an answer on the artifact's behalf and call that an observation. Static-analysis interpretations must name the evidence they use and remain distinct from runtime behavior.

## Profile shape

For each construct, prefer distributional output over a naked score:

- center;
- spread;
- observation count;
- contexts represented;
- repeatability/retest evidence when available;
- standard error or an explicitly simpler uncertainty estimate;
- applicability;
- calibration standing;
- omissions.

`NOT_APPLICABLE`, `INSUFFICIENT_EVIDENCE`, and `NOT_COMPARABLE` are valid outcomes.

## Projection rules

Frameworks such as Big Five, HEXACO, MBTI-like categories, CVI-like archetypes, DISC-like language, and Soveraeign-native archetypes are projections.

For every projection state:

- source profile revision;
- mapping revision;
- intended use;
- calibration standing (`UNVALIDATED`, `EXPLORATORY`, `CALIBRATED`, or `VALIDATED_FOR_USE`);
- loss/omissions;
- confidence/uncertainty when meaningful;
- whether a cohort comparison was admitted.

Do not label an experimental analog as the proprietary instrument's official result. Use `-like` or `projection` when the actual proprietary instrument was not administered and licensed/scored according to its own methodology.

## Reception / vibe

Keep three layers separate:

- **Disposition** — tendencies in what the subject does.
- **Expression** — observable style of the subject's behavior/output.
- **Reception** — how an observer experiences that expression in a context.

Reception is relational: `subject × observer × context`. Do not promote reception language such as "abrasive", "warm", "rigid", or "chaotic" into an intrinsic disposition without supporting behavioral evidence.

## Tool

Use `python scripts/sov_disposition.py` for the experimental deterministic surface.

Expected operations in v0.1:

- `init`
- `subject add`
- `observe`
- `profile`
- `report`
- `verify`

The local store is append-only evidence under `.local/disposition/`. Derived profile/report files are rebuildable and non-authoritative. This does not create a second Soveraeign System of Record; promotion of disposition observations into the operational Record Service is a separate integration seam and must preserve Record ownership.

## Refusals

Refuse or qualify when:

- a requested construct has no declared applicability for the subject;
- the observation is generated by the assessor rather than supplied/observed through the declared adapter;
- subject revision/configuration is missing for a model/agent observation;
- a projection mapping is absent or unvalidated but the caller asks for a definitive framework result;
- a percentile/cohort comparison is requested without a cohort and comparison/equivalence standing;
- there are too few observations for the requested claim;
- evidence is contradictory and the report would hide the contradiction;
- a profile is requested to establish identity, authority, permission, diagnosis, or other standing it cannot supply.

## Research anchors

The research notebook for Issue #200 should retain the specific source and claim provenance. Core anchors include the AERA/APA/NCME testing standards; measurement-invariance literature; Whole Trait Theory/density distributions of states; computerized adaptive personality testing and IRT; IPIP public-domain item/scale resources; and empirical work on psychometric measurement of LLM behavior.
