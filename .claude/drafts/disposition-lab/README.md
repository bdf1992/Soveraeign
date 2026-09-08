# Disposition Lab v0.1

Status: `EXPERIMENTAL · NON-CANONICAL · ISSUE #200`

Disposition Lab tests whether Soveraeign can measure behavioral tendencies across different subject kinds without turning personality frameworks into truth or anthropomorphizing non-human subjects.

## Research question

Can the same semantic construct be instantiated as different probes for humans, agents/models, code, or mechanisms while preserving enough measurement meaning for useful comparison?

The experiment separates:

`subject -> probe -> observation -> construct evidence -> disposition estimate -> profile -> projection`

The evidence ledger is primary. Profiles and framework reports are rebuildable projections.

## What v0.1 is allowed to claim

- recorded observations can be replayed deterministically into the same profile;
- repeated observations can expose center and variation rather than collapse behavior to one answer;
- a projection can transparently state its mapping, calibration standing, and information loss;
- the runtime can refuse comparisons that have not earned measurement-equivalence standing.

## What v0.1 is not allowed to claim

- that the seed constructs are the latent structure of personality;
- that a human construct automatically means the same thing for code, agents, or models;
- that an MBTI-like, CVI-like, Big-Five-like, HEXACO-like, or other projection is an official result of the named instrument;
- that a profile establishes diagnosis, identity, authority, permission, suitability, or standing.

## Quality model

The research program treats validity as use-specific. Reliability alone cannot validate an interpretation. Cross-subject comparison additionally depends on evidence of measurement equivalence.

Minimum gates:

1. deterministic replay;
2. append-only observation history;
3. explicit subject/configuration revision;
4. applicability and missing-data handling;
5. repeatability/variation reporting;
6. projection provenance and loss declaration;
7. comparison/equivalence refusal;
8. calibration evidence before adaptive optimization or strong crosswalk claims.

## Persistence

`scripts/sov_disposition.py` stores local experimental state under `.local/disposition/` by default:

- `subjects.ndjson` — append-only subject declarations;
- `observations.ndjson` — append-only observations;
- `profiles/<subject>.json` — deterministic derived profile snapshot;
- `reports/<subject>.<projection>.json` — deterministic derived report.

The NDJSON files are a research working store, **not** a new authoritative Soveraeign System of Record. They are local participant evidence and can later be promoted through a declared Record Service crossing. Profile/report files are disposable projections and can always be rebuilt from the observation ledger plus the pinned construct/projection definitions.

## Seed constructs

The seed bank is intentionally small and provisional:

- exploration;
- evidence threshold;
- reversibility preference;
- invariant fidelity;
- abstraction preference;
- initiative;
- coordination;
- scope horizon.

Each value is normalized to `[-1, 1]`; the poles are declared in `constructs.json`. A score is the arithmetic mean of admitted observation values in v0.1. Spread is population standard deviation. This simple scorer is intentionally transparent and is not an IRT model.

## Comparison gate

A cohort or subject-kind comparison is only admissible when an equivalence record explicitly names the construct, source adapter, target adapter, evidence, and standing. v0.1 ships no such equivalence records, therefore cross-kind comparative percentiles must refuse by default.

## Research anchors

- AERA, APA, NCME — *Standards for Educational and Psychological Testing*: validity evidence, reliability/precision, fairness, interpretation and use.
- Putnick & Bornstein (2016) — measurement invariance as a prerequisite for meaningful cross-group/time comparisons.
- Fleeson & Jayawickreme / Whole Trait Theory — descriptive traits as density distributions of states, preserving both stable individual differences and within-subject variability.
- Waller & Reise (1989); Forbey & Ben-Porath (2007) — computerized adaptive personality assessment and item-response approaches can reduce test burden when the bank is calibrated.
- International Personality Item Pool (IPIP) — public-domain personality items/scales useful as research/calibration seeds.
- Recent LLM psychometrics — personality-like model measurements must bind prompt/configuration and test reliability/construct validity empirically.

## Next research gates

Before adding a large probe bank or adaptive selection:

1. run synthetic replay/property tests against the storage/scoring kernel;
2. run same-subject retest experiments under controlled contexts;
3. test alternate probe phrasings/manifests for response-process sensitivity;
4. measure convergent/discriminant relationships against public-domain human instruments where applicable;
5. test adapter-specific differential behavior before any cross-subject comparison;
6. only then calibrate information functions for adaptive probe selection.
