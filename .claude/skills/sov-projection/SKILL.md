---
name: sov-projection
description: Domain know-how for the Soveraeign projection domain - the services/projection chartered boundary (Asset Projection Service). Load when a task mentions "sov-projection", "projection domain", "Asset Projection Service", "retrieval", "search lane", "text lane", "graph lane", "vector lane", "fusion", "context package", "parity", "Polygres", or names the artifacts CHARTER.md, PARITY.md, README.md, contracts/service.json, or conformance/ seed fixtures under services/projection. Covers charter gap closure, parity-ledger upkeep, seed-fixture authoring, doc coherence, and read-path precondition mapping while implementation waits on fixtures and the core.py split. Not for the Asset Service itself, kernel contracts, the conformance oracle, byom, console, or governance work - those have sibling sov-* skills.
---

# sov-projection

## Purpose

Advance the Asset Projection Service boundary - charter, parity ledger, seed
fixtures, and doc coherence - and, once its fixtures are executable and the
Asset Service `core.py` split lands, build its lanes. The domain owns the
retrieval surface over asset records: text search, graph traversal, vector
search, fused ranking, and token-budgeted context packages. Everything it
holds is a projection under the `SPEC.md` Projection rule: rebuildable, every
value resolving to an authoritative record with declared omissions. Its
capability target is parity with Polygres (`services/projection/PARITY.md`),
reached through Soveraeign's rules, never around them.

## Owns / Must not

Owns: `services/projection/` - one bounded lifecycle, its contract drafts,
parity ledger, and seed fixtures. Owned domain records (per CHARTER.md and
contracts/service.json): projection-collection, text-configuration,
vector-registration, graph-configuration, index-declaration, projection-build,
retrieval-receipt, context-package, fidelity-observation, projection-receipt.
Declared operations: declare-collection, configure-text, configure-graph,
register-vectors, build-projection, search-text, traverse-graph, find-path,
search-dense, search-sparse, search-hybrid, package-context, observe-fidelity,
propose-from-projection. Declared ports: asset-record-stream, model-binding,
external-index, http-binding, federation.

Must not: write runtime code before executable positive and defeating
fixtures (`no_runtime_code_before_logical_spec_and_defeating_fixtures`) or
before the Asset Service `core.py` split gives the read stream a stable owner;
open the Asset Service database directly (the crossing is a declared read-only
stream); write Asset Service, Proofing Service, or Console Service state;
generate embeddings inside the service (they arrive by `invoke_model` on a
declared Model Binding or by declared external provenance, never inside this
service); serve an approximate index as exact; skip a
staleness omission; let a projected value, score, or package change an
authority check; add NetworkX, Neo4j, HNSW, Postgres, or any external index
without an observed need and a decision record; report an external index,
HTTP binding, or cross-node query as anything but `UNCONFIGURED`; modify
`lineage/evidence/`; create `EXTERNAL_WORLD` effects; run `git commit` or
`git push`.

## Key files

- `services/projection/CHARTER.md` - role, Phase-I requirement mapping, owned
  records, the six lanes, collection lifecycle, sibling and kernel
  integration, 14-step proving narrative, defeating cases, deferred scope.
- `services/projection/PARITY.md` - the owner-directed capability target
  against Polygres: every capability, its operation here, its lane (Phase I,
  needs embeddings, port, declined), and its precondition. A row reaches parity when its
  operation is BUILT with a positive and defeating fixture, then WITNESSED.
- `services/projection/README.md` - the two implementation gates; boundary
  ratification changes the standing word, not the build.
- `services/projection/contracts/service.json` - manifest, standing PROPOSED.
- `services/projection/conformance/` - seed fixtures PROJ-001..008
  (hit-resolves-to-source through context-package-budgeted); a future
  participant must satisfy each `then` and refuse each `defeating`.
- `decisions/0030-asset-projection-service-boundary.md` - boundary decision
  with defaults taken; `decisions/0032-unblock-ticket-kind.md` for filing a
  stall.
- `reports/2026-08-23-polygres-parity-pressure-map.md` - the reasoning behind
  the parity target.
- Governing set: `AGENTS.md`, `STATUS.yaml`, `CLASSIFICATION.md`, `SPEC.md`,
  `PRD.md`, `CONTRACT.md`, `ENGINEERING.md`.

## Standing and constraints

- `projection_service_status: OWNER_ACCEPTED_BOUNDARY_NOT_IMPLEMENTED` (STATUS.yaml).
- The boundary and the name are accepted
  (`decisions/0033-close-the-founding-docket.md`). Parity target and lane scope
  remain defaults taken in `decisions/0030-asset-projection-service-boundary.md`:
  counter them with a fixture, which is cheaper than asking.
- The ruling is defeated by a retrieval result this service can produce that the
  Asset Service cannot reconstruct from authoritative records - that would make
  the projection a second authority. It is the thing to test first.
- The dense and sparse lanes need embeddings with declared provenance, which
  arrive through `invoke_model`. The text, graph, filter, and fusion lanes do
  not depend on that.
- The engineering baseline and `SPEC.md` are accepted (0024, O2 and O10).
- Precursor, not a gate you can vote on: the Asset Service `core.py` split
  (`ENGINEERING.md`, Context and module budget) must land before this service
  reads its stream. If it will not land, that is an unblock request for the
  asset domain, filed with `python scripts/sov_unblock.py draft`.
- Blocked edge is not blocked frontier (`AGENTS.md`): a gate stops one
  transition, not the domain.

## Named operations (available now)

1. Fixture executable-ization: turn seed fixtures PROJ-001..008 into
   executable declarative cases a future participant binds to, without
   runtime code - the precondition the protected boundary names.
2. Parity-ledger upkeep: keep `PARITY.md` rows honest against the working
   tree; a row's lane or gate changes only with the evidence path named.
3. Charter gap closure: reconcile CHARTER.md with `CLASSIFICATION.md`, the
   SPEC.md Projection rule, and decision 0021.
4. Read-path precondition mapping: record exactly what the Asset Service
   stream must stabilize (record kinds, receipt fields, digests) before a
   collection can build without direct database access, as a proposal.
5. Contract drafting: JSON Schema record contracts under
   `services/projection/contracts/` for the owned records, as proposals.
6. Doc coherence: README, manifest, CHARTER, PARITY vocabulary and
   cross-references.
7. After the core.py split and executable fixtures - lane implementation in
   PARITY.md order: text (FTS5 unicode + trigram), graph (recursive CTE,
   `max_depth` 1..20, direction, type filter), filters, fusion over built
   lanes, context packages. Stdlib only; each lane lands with its positive
   and defeating fixture and per-hit source resolution.

## Verification

- `python scripts/verify.py` - required, from repo root, three-second budget.
- `python scripts/lint.py` - hygiene, module size, secret shapes.
- `python -m json.tool services/projection/contracts/service.json` and any
  added schema or fixture JSON.
- Once tests exist: `python -m unittest discover -s tests -v` from
  `services/projection/`; tests establish at most BUILT.

## Vocabulary (exact; no synonyms)

- Repository artifact standing: `OPEN -> BUILT -> WITNESSED -> RATIFIED`.
- Record standing: `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`.
- Effect class: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD`.
- Proposed collection lifecycle (CHARTER.md; service policy awaiting owner
  ratification): `DECLARED -> READY -> STALE -> READY`. `READY` means a build
  exists whose `input_state_digest` matches the current source stream; a
  stale read still answers and declares the staleness as an omission.
- Lanes: text, graph, dense vector, sparse vector, filter, fusion.
- `index_kind`: `NONE` (exact scan) | `FTS` | `TRIGRAM` | declared external
  port. Exact and approximate are never confused.
- Retrieval receipt fields of consequence: `source_address`, `source_digest`,
  rank, score breakdown, `introduced_by_graph`, build id,
  `input_state_digest`, omissions, `authoritative: false`.
- Refusals in the charter: `MODEL_UNAVAILABLE` (unavailable binding, never a
  silent substitute), `INCOMPLETE_PROPOSAL` (vectors with no provenance),
  `UNCONFIGURED` (external index, HTTP, federation), `REFUSED` with the depth
  contract (traversal beyond `max_depth` 20).
- Roles: Worker (report is not observation), Witness, Binding, Adapter,
  Projection (never authoritative by convenience).

## Report format

Report: files changed (repo-relative paths); checks observed (exact commands
with exit codes); standing proposals (own work supports at most `BUILT`; a
build report cannot witness itself); defaults taken; judgement items queued
for Bdo naming the transition each gates; next bounded operation.
