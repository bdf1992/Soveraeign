---
name: sov-contracts
description: Load for work on the Soveraeign contracts domain — the shared kernel and crossing JSON Schema contracts. Triggers include "sov-contracts", "contracts domain", "kernel schema", "crossing contract", or any of the six artifact names event-envelope.schema.json, receipt.schema.json, operation-plan.schema.json, model-binding.schema.json, participant-observation.schema.json, service-manifest.schema.json, plus contracts/README.md. Covers schema-spec gap audits, conformance fixture authoring, vocabulary audits, and doc coherence — not service lifecycles (sov-asset, sov-proofing), conformance oracle internals, or bindings/adapters.
---

# sov-contracts

## Purpose

The contracts domain keeps the six shared JSON Schema Draft 2020-12 contracts
in `contracts/` aligned with the logical objects in `SPEC.md` and the
vocabulary in `CLASSIFICATION.md`. These schemas constrain records crossing
service and participant boundaries; they do not prescribe storage, classes,
transport, or deployment.

## Owns / Must not

Owns: `contracts/*.schema.json` (event-envelope, receipt, operation-plan,
model-binding, participant-observation, service-manifest) and
`contracts/README.md`.

Must not: contain service-specific lifecycle logic; admit provider SDK types
into kernel contracts; create a second semantic contract in YAML; change a
schema without a positive and a defeating conformance case; touch
`lineage/evidence/` (immutable); import participant implementation code.

## Key files

- `contracts/README.md` — contract table and stack-neutral status
- `contracts/event-envelope.schema.json`
- `contracts/receipt.schema.json`
- `contracts/operation-plan.schema.json`
- `contracts/model-binding.schema.json`
- `contracts/participant-observation.schema.json`
- `contracts/service-manifest.schema.json`
- `SPEC.md` — logical object field blocks the schemas compile
- `CLASSIFICATION.md` — canonical vocabulary for every enum
- `scripts/verify_bootstrap.py` — asserts the six files exist and parse as JSON
- `AGENTS.md`, `STATUS.yaml` — operating contract and current standing

## Standing and blockers

`specification_status: PROPOSED_LOGICAL_SPEC_OWNER_FREEZE_PENDING`;
`classification_status: PROPOSED_OWNER_RATIFICATION_PENDING`. Gating open
decisions (STATUS.yaml):

- **O10** (Bdo ratifies SPEC.md) blocks `f1_closure` — schema changes ahead of
  the spec freeze must be marked proposals with positive and defeating cases.
- **O9** (Bdo ratifies CLASSIFICATION.md) blocks `terminology_freeze` — enum
  vocabulary stays proposed; mismatches queue as judgement items, not renames.
- **O12** blocks `byom_contract_freeze` — `model-binding.schema.json` fields,
  data-boundary modes, and the two-model fixture cannot be frozen.
- **O4** blocks `attestation_schema` — do not author an attestation contract;
  queue the question for Bdo.
- **O2** blocks `production_implementation` — the JSON Schema baseline itself
  is proposed, not ratified.

## Named operations

1. **Schema-spec gap audit** — compare each schema's required fields and enums
   against the matching SPEC.md logical object block and record divergences as
   proposals (RECORD_LOCAL).
2. **Conformance fixture authoring** — add one positive and one defeating
   validation fixture for a named schema before any schema edit.
3. **Vocabulary audit** — verify every enum value in the six schemas against
   CLASSIFICATION.md/SPEC.md exactly; queue mismatches (e.g. the
   service-manifest `standing` enum's `PROPOSED` versus the `OPEN` lifecycle
   term) for Bdo rather than renaming.
4. **README coherence** — keep the `contracts/README.md` table aligned with
   the actual schema files and their SPEC.md purposes.
5. **Draft 2020-12 hygiene** — verify `$schema`, `$id`, `additionalProperties`,
   and `required` conventions are consistent across all six files.
6. **Proposal drafting for missing kernel contracts** — draft a clearly marked
   proposal for a SPEC.md object lacking a schema (e.g. retraction,
   authority-grant) only where no open decision blocks it; attestation is
   O4-blocked and queues instead.

## Verification

- `python scripts/verify.py` — required gate, from repo root, three-second
  budget; runs lint, bootstrap, oracle controls, oracle tests, asset tests.
- `python scripts/lint.py` — text hygiene, module size, secret shapes.
- `python scripts/verify_bootstrap.py` — contract file presence and JSON parse.
- `python conformance/run.py` — executable oracle controls.
- `python -m unittest discover -s conformance/tests -v` — oracle unit tests.

## Vocabulary

Use these exactly; never invent synonyms:

- Effect classes: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD`
  (the last is refused in Phase I).
- Record standing: `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`.
- Artifact standing lifecycle: `OPEN -> BUILT -> WITNESSED -> RATIFIED`.
- Event phase: `ATTEMPTED | REPORTED | OBSERVED | SETTLED | COUNTERED`.
- Outcome: `ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED`.
- Attestation outcome: `REPRODUCED | DISSENTED | UNATTESTABLE`.
- Actor kind: `HUMAN | MODEL | WORKER | SYSTEM`.
- Authority type: `VERIFICATION | JUDGEMENT` — verification authority cannot
  ratify a judgement claim.
- Data boundary: `LOCAL_ONLY | REDACTED_REMOTE | REMOTE_ALLOWED`.
- Roles: a Worker's report is not an Observation; a Witness is independent; a
  Projection is rebuildable and never authoritative by convenience; a Receipt
  records every attempted crossing, including refusals.

## Report format

Files changed; checks observed (exact commands with exit codes); standing
proposals (`OPEN -> BUILT` at most from self-tests — a build report cannot
witness itself); judgement items queued for Bdo; assumptions introduced; next
bounded operation.
