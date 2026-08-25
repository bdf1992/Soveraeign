# O2 ratification packet · ENGINEERING.md Phase-I baseline

Status: `PROPOSED · OWNER RATIFICATION PENDING`

This packet assembles, for Bdo, what the `ENGINEERING.md` baseline proposes, the self-test evidence
reported today, and the consequences of ratifying or declining open decision O2. It is a Worker
proposal, not Bdo's judgement, and witnesses nothing it cites (`AGENTS.md` Authority).

## Owned scope

Owned: the O2 question verbatim, the proposal it refers to, the current authoritative state in
`STATUS.yaml`, one dated self-test run, and the implications each answer directly entails from the
sources listed under Source and authority. Not owned: the answer to O2; any edit to `STATUS.yaml`,
`ENGINEERING.md`, or `decisions/0012`; any replacement stack for a decline; any judgement on O1 or
O3 to O12; and any claim of `WITNESSED` or `RATIFIED` standing for itself or for the baseline.

## The question

`STATUS.yaml` line 66, verbatim; it carries `blocks: production_implementation` (line 67):

> Does Bdo ratify ENGINEERING.md's Python, SQLite, filesystem CAS, JSON Schema, and unittest baseline for Phase I?

## What is proposed

`ENGINEERING.md` (Status: `OWNER-DIRECTED FRAMEWORK · TECHNICAL BASELINE PROPOSED`) proposes:

- Selection rule: a technology belongs in the baseline only when it is required to prove a current
  operation locally, keeps authority and history inspectable, survives loss of optional providers,
  and can be replaced behind an existing contract (`ENGINEERING.md` Selection rule).
- Minimal reference stack: Python 3.11+; Python standard library first; append-preserving events and
  receipts in transactional SQLite; filesystem content-addressed store using SHA-256; JSON Schema
  Draft 2020-12; Markdown and small YAML fixtures; Python API and CLI; `unittest` and dependency-free
  repository scripts; rebuildable local projections; declared Model Binding plus Model Adapter; each
  row names a Boundary, for Tests and lint "under three seconds" (`ENGINEERING.md` stack table).
- Deliberately not selected: HTTP or frontend framework, background queue, container runtime,
  orchestrator, distributed database, event broker, vector store, graph database, identity
  provider, cloud, or model SDK (`ENGINEERING.md` Minimal reference stack, closing paragraph).
- Acceptance: the framework is `BUILT` when the root instruction surfaces agree, the
  dependency-free lint and verification loop enforce their invariants in under three seconds, and
  existing conformance and participant tests still run; it is `RATIFIED` only when Bdo accepts the
  exact Phase-I technology choices and composition rules (`ENGINEERING.md` Acceptance).
- Named debt: the current Asset Service `core.py` exceeds the 300-line module budget; no behavior
  is to be added before it is split (`ENGINEERING.md` Context and module budget).

`decisions/0012-engineering-baseline.md` (Status: `OWNER-DIRECTED · EXACT BASELINE PROPOSED`)
records the same proposal and states under Consequences: "Exact technical choices remain proposed
until Bdo ratifies the baseline." `AGENTS.md` Technical baseline restates the choices as operating
rules and defers the primitive set and boundary rationale to `ENGINEERING.md`.

## Current authoritative state

- `engineering_framework_status: BUILT_SELF_TESTED_NOT_WITNESSED_BASELINE_PROPOSED`
  (`STATUS.yaml` line 16).
- `proposed_repository_claims` include `minimal_phase_i_reference_stack`,
  `composable_kernel_primitive_baseline`, and `dependency_free_day_zero_verification`
  (`STATUS.yaml` lines 57-59); they are proposed, not settled.
- `protected_boundaries` include `no_runtime_code_before_logical_spec_and_defeating_fixtures`
  and `no_external_effects_in_phase_i` (`STATUS.yaml` lines 102 and 104).
- O10, "Does Bdo ratify SPEC.md as the Phase-I logical specification?", is open and blocks
  `f1_closure` (`STATUS.yaml` lines 89-91).
- `OPEN-SEAMS.md` S1 to S10: no seam names O2, `ENGINEERING.md`, or the baseline, so no recorded
  seam objects to it. Absence of an objection is not evidence for the baseline.

## Self-test evidence, 2026-08-22 (Worker report, not a Witness deposit)

One run of `python scripts/verify.py` from the repository root at HEAD `b5819da`, working tree not
clean (five tracked files modified, five untracked paths), so not the clean root `AGENTS.md`
Implementation order step 5 names. Exit code 0; total 0.662s against `BUDGET_SECONDS = 3.0`; the
five `CHECKS` (`scripts/verify.py` lines 15-23) reported:

- repository hygiene: PASS, with `WARN: KNOWN DEBT`: Asset Service `core.py` has 341 lines (above).
- bootstrap and locked evidence: PASS, with `SKIP: historical evidence archive is not present in
  this checkout`; evidence integrity against `lineage/SOURCES.lock` was therefore not exercised.
- conformance oracle controls: `SUITE PASS cases=20 coverage_gaps=0`; the ten per-case
  `FAIL CONF-I*-DEF` lines, `CONF-I5-GRANT-DEF` among them, are expected defeating-fixture verdicts.
- conformance oracle tests: `Ran 5 tests`, OK. Asset Service reference tests: `Ran 5 tests`, OK.

The harness prints its own limit: "self-tests establish BUILT evidence only; no independent
witness or owner ratification is implied" (`scripts/verify.py` line 44). A Worker's report is not
Observation (`CLASSIFICATION.md` Participation and boundary roles); a test may establish `BUILT`,
never `WITNESSED` or `RATIFIED` (`AGENTS.md` Testing and verification).

## If Bdo ratifies

- O2 closes and its `blocks: production_implementation` lifts (`STATUS.yaml` lines 65-67).
- `ENGINEERING.md` and `decisions/0012` Status lines, and `engineering_framework_status`, become
  due for update, recorded per `AGENTS.md` Implementation order step 6; this packet performs none.
- `no_runtime_code_before_logical_spec_and_defeating_fixtures` still stands (`STATUS.yaml` line
  102) and O10 stays open; ratifying the stack does not ratify `SPEC.md` or close `f1_closure`.
- The `core.py` debt remains named debt; ratification does not discharge it (`ENGINEERING.md`
  Context and module budget). New runtime dependencies still require a named boundary, an observed
  need, failure behavior, and a decision record (`AGENTS.md` Technical baseline).

## If Bdo declines

- O2 stays open and `production_implementation` stays blocked (`STATUS.yaml` lines 65-67).
- `ENGINEERING.md` and `decisions/0012` remain proposed; "Exact technical choices remain proposed
  until Bdo ratifies the baseline" continues to govern (`decisions/0012` Consequences).
- `engineering_framework_status` keeps `BASELINE_PROPOSED` (`STATUS.yaml` line 16).
- A revised baseline would be a policy change recorded in `decisions/` (`AGENTS.md` Repository
  protections); this packet proposes no replacement stack.

## Judgement items for Bdo

1. O2 names five choices; `ENGINEERING.md` Acceptance covers "the exact Phase-I technology choices
   and composition rules" across ten stack rows. Does ratification cover the whole, or the five?
2. Does the evidence-archive SKIP change the weight Bdo gives to today's self-test run?
3. Must the `core.py` debt be split before ratification, or only before new behavior?

## Standing proposal

This packet proposes at most `OPEN -> BUILT` for itself. It awaits critique by sov-witness, a
different agent, before any revision. It is not Bdo's judgement.

## Source and authority

- `ENGINEERING.md`, `decisions/0012-engineering-baseline.md`, `STATUS.yaml`, `AGENTS.md`,
  `scripts/verify.py`, `OPEN-SEAMS.md`; `CLASSIFICATION.md` for vocabulary.
- `RECORD_LOCAL`: this draft; `RESOURCE_CONSUMPTION`: one local `scripts/verify.py` run, no network.
