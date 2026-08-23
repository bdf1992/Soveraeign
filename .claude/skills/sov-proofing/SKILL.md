---
name: sov-proofing
description: Working knowledge for the Soveraeign proofing domain — the services/proofing chartered boundary. Load when a task mentions "sov-proofing", "proofing domain", "Proofing Service", "proofing session", "review round", "version-pinned annotation", "proofing charter", "proofing receipt", or names the artifacts CHARTER.md, proofing-session.schema.json, annotation.schema.json, or contracts/service.json under services/proofing. Covers charter refinement, proofing contract drafting, and defeating-fixture authoring while O11 keeps implementation queued. Not for the Asset Service, kernel contracts, or conformance oracle work.
---

# sov-proofing

## Purpose

Advance the Proofing Service boundary of the Soveraeign repository — charter,
contracts, and defeating fixtures — without crossing the protected boundary
that forbids runtime code before a ratified logical spec and executable
defeating fixtures. The domain governs review-and-approval lifecycles for
exact asset versions; it references the Asset Service and never becomes a
second source of asset truth.

## Owns / Must not

Owns: `services/proofing/` — one bounded lifecycle, its contract drafts, and
future tests. Owned domain records (per CHARTER.md and contracts/service.json):
proofing-session, review-round, participant-assignment, version-pinned
annotation, comparison-recording, decision-proposal, authorized-decision,
proofing-receipt.

Must not: implement runtime code before O11 ratification plus logical spec and
defeating fixtures (`no_runtime_code_before_logical_spec_and_defeating_fixtures`);
touch Asset Service state or write another service's directory; modify
`lineage/evidence/` (immutable); create `EXTERNAL_WORLD` effects (none in
Phase I); write directly to asset storage or review an implicit "latest"
version; let a model ratify judgement or an executor report count as
observation; run `git commit` or `git push`.

## Key files

- `services/proofing/CHARTER.md` — role, owned records, lifecycle, Asset
  Service integration, proving narrative, defeating cases, deferred scope.
- `services/proofing/README.md` — implementation gates; no placeholder code.
- `services/proofing/contracts/service.json` — owns/references/operations/
  ports/forbids declaration.
- `services/proofing/contracts/proofing-session.schema.json` — session shape.
- `services/proofing/contracts/annotation.schema.json` — version-pinned
  annotation shape.
- `decisions/0010-proofing-service-boundary.md` — boundary decision, PROPOSED.
- Governing set: `AGENTS.md`, `STATUS.yaml`, `CLASSIFICATION.md`, `SPEC.md`,
  `PRD.md`, `CONTRACT.md`.

## Standing and blockers

- `proofing_service_status: CHARTERED_NOT_IMPLEMENTED` (STATUS.yaml).
- O11 — "Is Proofing Service the accepted second service boundary after Asset
  Service?" — blocks `proofing_implementation`. All implementation requests are
  refused and queued as judgement items for Bdo.
- O2 — engineering baseline ratification — blocks `production_implementation`.
- O10 — SPEC.md ratification — blocks `f1_closure`.
- Judgement-typed questions queue for Bdo; they never block bounded doc,
  contract, or fixture work and are never silently decided by an agent.

## Named operations (available now)

1. Charter gap closure: reconcile `CHARTER.md` with `CLASSIFICATION.md`'s
   service map and decision 0010, preserving the defeating cases.
2. Contract field refinement: align `proofing-session.schema.json` and
   `annotation.schema.json` with SPEC.md object shapes (standing, receipts,
   actor attribution) as proposals.
3. Missing contract drafting: draft schemas for owned records not yet covered
   (review-round, comparison-recording, decision-proposal, proofing-receipt).
4. Defeating fixture authoring: turn CHARTER.md defeating cases into concrete
   declarative fixtures (payloads that a future participant must refuse),
   without runtime code.
5. Doc coherence: align `README.md`, `service.json`, and `CHARTER.md`
   vocabulary and cross-references with `CLASSIFICATION.md`.
6. Asset-binding precondition mapping: record exactly what the Asset Service
   version-address contract must stabilize before proofing can bind (README
   gate 3), as a proposal.
7. Judgement-queue drafting: write the precise O11 ratification question set
   for Bdo with the evidence paths a decision needs.

## Verification

- `python scripts/verify.py` — required, from repo root, three-second budget.
- `python scripts/lint.py` — hygiene, module size, secret shapes.
- `python -m json.tool services/proofing/contracts/service.json` (and the two
  `.schema.json` files) — JSON syntax check per contract file.
- No `services/proofing/tests/` exists yet by design; do not create test
  scaffolding that implies implementation before O11.

## Vocabulary (exact; no synonyms)

- Repository artifact standing: `OPEN -> BUILT -> WITNESSED -> RATIFIED`.
- Record standing: `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`.
- Event outcome: `ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED |
  UNRESOLVED`.
- Attestation outcome: `REPRODUCED | DISSENTED | UNATTESTABLE`.
- Effect class: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD`.
- Session lifecycle (proposed policy): `OPEN -> IN_REVIEW -> DECISION_PENDING
  -> CLOSED`.
- Annotation `version_relation`: `CURRENT | STALE | CARRIED | RESOLVED`.
- Roles: Operator, Actor, Worker (report is not observation), Witness,
  Binding, Adapter, Projection (never authoritative by convenience).
- Information roles: Proposal, Recording, Receipt, Observation, Retraction.

## Report format

Report: files changed (repo-relative paths); checks observed (exact commands
with exit codes); standing proposals (own work supports at most `BUILT`; a
build report cannot witness itself); judgement items queued for Bdo; next
bounded operation.
