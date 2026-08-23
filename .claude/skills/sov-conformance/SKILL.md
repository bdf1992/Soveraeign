---
name: sov-conformance
description: Domain know-how for the Soveraeign conformance domain - the independent oracle and qualification suite in conformance/. Load when a task names "sov-conformance", "conformance domain", "oracle", "oracle-controls.json", "scenarios.json", "founding-scenarios", "test_oracle.py", "conformance/run.py", "fixture gap", "defeating fixture", "positive and defeating pair", "participant observations", "fresh witness", "PROD-I-7", or "F2 conformance corpus". Not for building participant implementations (asset, proofing, byom domains) or for editing scripts/verify.py (verification domain).
---

## Purpose

The conformance domain owns Soveraeign's independent qualification machinery:
a strategy-neutral oracle that derives defects from observation records, control
fixtures that prove the oracle distinguishes good from defeating narratives, and
the participant observation contract a second implementation can bind to. It
exists so that no participant is ever qualified by its own self-report.

## Owns / Must not

Owns (AGENTS.md directory boundaries: `/conformance` owns independent scenarios,
oracle controls, witness inputs): the oracle runner and its nine requirement
checks (PROD-I-1..9); embedded positive/defeating oracle controls; participant
scenario narratives; founding scenario seeds; the oracle's own unit tests; and
the fresh-witness qualification contract (PROD-I-7, FOUND-007).

Must not:

- Import participant implementation code (nothing from services/, bindings/,
  adapters/, workers/) - the oracle evaluates externally visible records only.
- Weaken an oracle check merely to make a participant pass (AGENTS.md,
  Implementation order).
- Trust an implementation self-report; the runner derives defects from
  `observed` records, never from a participant verdict field.

## Key files

- conformance/run.py - oracle runner; CHECKS map for PROD-I-1..9; PASS / FAIL /
  INVALID verdicts; coverage gate for positive and defeating polarity.
- conformance/oracle-controls.json - one positive and one defeating embedded
  observation per requirement (CONF-I<n>-POS / CONF-I<n>-DEF).
- conformance/scenarios.json - one strategy-neutral participant narrative per
  requirement (RUN-I<n>-*), polarity "participant".
- conformance/founding-scenarios/001-source-reading-recording.yaml through
  008-model-portability.yaml - FOUND-001..008 seeds (006 two-binding parity,
  007 fresh witness).
- conformance/tests/test_oracle.py - unittest self-tests for the oracle.
- conformance/README.md - the participant observation contract and result
  meanings.
- Governing: PRD.md (PROD-I-7, "Two-binding proof", "Phase-I exit"), SPEC.md
  ("Requirement predicates", "Conformance boundary"), ROADMAP.md (F2).

## Standing and blockers

- STATUS.yaml conformance_status:
  `EXECUTABLE_ORACLE_CONTROLS_PARTICIPANT_BINDING_OPEN` - the oracle runs and
  distinguishes its embedded controls, but no participant has bound; passing the
  controls does not witness any implementation.
- F2 exit (ROADMAP.md): every normative predicate has at least one positive and
  one defeating fixture, and the suite can be bound to more than one
  implementation. Participant binding is the open half.
- O10 (blocks f1_closure): SPEC.md is not yet ratified, so the predicates the
  fixtures trace to are proposals - author fixtures as proposals, do not freeze.
- O8 (blocks operational_qualification_measurement): what observation completes
  semantic cold-start beyond schema validity - gates any strengthening of
  check_i7 / FOUND-007 measurement semantics; queue for Bdo.
- O12 (blocks byom_contract_freeze): the exact BYOM binding fields - check_i9's
  required-field list embodies the proposed fields; changing it tracks O12.

## Named operations

- Fixture gap audit: diff SPEC.md requirement predicates against
  oracle-controls.json and report which predicates lack a positive or defeating
  control (RECORD_LOCAL, read-mostly).
- Control pair authoring: add one positive and one defeating observation pair
  for one uncovered predicate, with matching expected_oracle values.
- F2 case-family extension: add one boundary, stale-state, authority,
  concurrency, reconstruction, dissent, or retraction case per ROADMAP F2.
- Oracle self-test hardening: add a test_oracle.py case proving the oracle
  rejects a manipulated observation or smuggled participant verdict.
- Participant-binding interface sharpening: tighten the observations-JSON
  contract in conformance/README.md so a second implementation can bind without
  the oracle importing its code.
- Scenario coherence pass: reconcile scenarios.json and founding-scenarios
  wording with CLASSIFICATION.md and SPEC.md vocabulary without weakening any
  check.
- Fresh-witness drill preparation: tighten FOUND-007 and check_i7 observables
  within current spec text; queue O8 measurement questions for Bdo.

## Verification

- `python scripts/verify.py` - required gate, from repo root, three-second
  budget (runs the oracle controls and the oracle unit tests).
- `python scripts/lint.py` - repository text, syntax, size, secret shapes.
- `python conformance/run.py` - embedded controls; add `--json` for machine
  output.
- `python -m unittest discover -s conformance/tests -v` - oracle self-tests,
  from repo root.
- Participant binding form (once observations exist):
  `python conformance/run.py --cases conformance/scenarios.json --observations
  <path>` - exit 1 on any non-PASS.

## Vocabulary

- Witness: an independent verifier depositing evidence; a Worker's report is
  not observation. Observation: independent evidence of what occurred.
  Receipt: the record returned by an attempted crossing or operation.
- Record standing: `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`; repository
  artifact lifecycle: `OPEN -> BUILT -> WITNESSED -> RATIFIED` (distinct scales,
  never merged).
- Event outcomes: `ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED |
  UNRESOLVED`.
- Effect classes: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD`
  (none of the third in Phase I).
- Oracle verdicts: `PASS` / `FAIL` / `INVALID`; case polarity: `positive` /
  `defeating` / `participant`.
- Attestation outcome `REPRODUCED`; refusal reasons `DISSENTED`,
  `UNATTESTABLE`; qualification objects `QualificationRecord`,
  `time_to_safe_competence`.

## Report format

- files_changed: repo-relative paths with one-line reasons.
- checks_observed: exact commands, exit codes, bounded excerpts.
- standing_proposals: at most OPEN -> BUILT; never WITNESSED or RATIFIED from a
  builder.
- judgement_items: questions queued for Bdo (O8, O10, O12 touchpoints).
- next_bounded_operation: single next step, or none.
