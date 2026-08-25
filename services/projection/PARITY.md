# Asset Projection Service — Parity Ledger

Status: `PROPOSED TARGET · OWNER-DIRECTED · NOTHING BUILT`

Bdo set the target on 2026-08-23: feature parity with Polygres
(<https://polygres.com/>, docs <https://docs.evokoa.com/polygres>). This ledger
maps each Polygres capability to the operation that realises it here, the
parity lane it sits in, and what gates it. `CHARTER.md` owns the boundary;
this file only tracks the target. Polygres's capabilities are quoted from its
own pages as of 2026-08-23 and were not executed or observed.

Lanes:

- **Phase I** — buildable from the standard library once fixtures exist and
  the `core.py` split (`ENGINEERING.md` lines 171-173) is done;
- **after O12** — needs a ratified Model Binding so `invoke_model` can
  produce embeddings with provenance;
- **port** — declared interface, refuses `UNCONFIGURED`, needs an observed
  need plus a decision record before any implementation;
- **declined** — contrary to a governing rule or a Phase-I non-goal; parity
  is met by a stricter equivalent or deliberately not pursued.

## Capability map

| Polygres capability | Operation here | Lane | Gate |
| --- | --- | --- | --- |
| Full-text search (`tsvector`) | `search-text` over FTS5 unicode tokenizer | Phase I | fixtures; `core.py` split |
| Fuzzy matching (`pg_trgm`) | `search-text` with FTS5 trigram tokenizer | Phase I | same |
| Graph `related` (immediate neighbours) | `traverse-graph` with `max_depth` 1 | Phase I | same |
| Graph `expand` (flat ranked traversal) | `traverse-graph` ranked by depth and `graph_score` | Phase I | same |
| Graph `neighborhood` (depth and table grouping) | `traverse-graph` with `groups` by depth and record kind | Phase I | same |
| Graph `path` (shortest route) | `find-path` | Phase I | same |
| Graph `connection` (chain 2–10 entities) | `find-path` with an ordered entity list | Phase I | same |
| `max_depth` 1..20, `direction` `out` / `in` / `any`, `relationship_types` | parameters of `traverse-graph` and `find-path` | Phase I | same |
| Graph derived from the schema (foreign keys) | `configure-graph` projecting relationship records plus lineage edges (asset → version → source, run → input/output version) | Phase I | same |
| Scalar filters `must` / `should` / `must_not`, ranges, `is_null` | `filter` parameter on every lane | Phase I | same |
| Readiness (`Ready` per mode) | collection lifecycle `DECLARED → READY → STALE` with build receipt | Phase I | same |
| Pagination (`limit`, `cursor`) | `limit` and `cursor` on every retrieval | Phase I | same |
| Dense vector search (`/search`) | `search-dense`, exact cosine scan, `index_kind: NONE` | after O12 | O12; fixtures |
| "Polygres does not generate embeddings" | same: embeddings by `invoke_model` on a declared binding or declared external provenance | after O12 | O12 |
| Sparse retrieval | `search-sparse`, exact scan | after O12 | O12; fixtures |
| Raw search (score explicit point ids) | `search-dense` with `candidates` restricted to given keys | after O12 | O12 |
| Candidate search (within given point ids) | same parameter | after O12 | O12 |
| Hybrid rank fusion (`/hybrid/rank-fusion`) | `search-hybrid` mode `RANK_FUSION`, weighted RRF `k = 60` | after O12 for the dense lane; text + graph fusion is Phase I | fixtures |
| Hybrid joint (`/hybrid/joint`, unified rescoring, lane evidence, `introduced_by_graph`) | `search-hybrid` mode `JOINT`; receipt carries score breakdown, lane evidence, `introduced_by_graph` | same | fixtures |
| Text-first / graph-first / vector-first hybrid | `search-hybrid` with a declared `seed_lane` | same | fixtures |
| Recall check (HNSW vs exact) | `observe-fidelity`: an independent observer compares an approximate lane to the exact lane over one build | port (needs an approximate index to compare) | external index decision |
| HNSW index, quantised, in memory | `index_kind` external port | port | observed local query failure + decision record (`ENGINEERING.md` line 185) |
| Recommendation (positive / negative examples) | `recommend` | port | decision record; PRD non-goal until conformance |
| Discovery (contextual expansion) | `discover` | port | same |
| Exploration | `explore` | port | same |
| Grouped search (by filter key) | `group-search` | port | same |
| Query plans (`/query/execute`) | `execute-plan`: a declared operation plan over lanes | port | same; maps onto `operation-plan.schema.json` when admitted |
| Token-ready ranked context | `package-context` with `token_budget`, addresses, digests, omissions, `content_digest`; is the `input_projection_id` for a Model Binding | after O12 for model use; package itself Phase I | O12 |
| Python SDK | Python API binding | Phase I | two-binding proof |
| CLI | CLI binding | Phase I | same |
| HTTP API | `http-binding` port | port | a conformance case that requires HTTP (`AGENTS.md`, Technical baseline) |
| Agent Skills | harness skill `sov-projection` (host plumbing, not a product surface) | Phase I | `.claude/README.md` |
| Runtime row writes | declined as written; a projection edit returns as a Proposal through the Asset Service transition contract | declined | — |
| Roles Owner / Admin / Developer / Viewer; one credential per surface | declined as fixed roles; typed, scoped, budgeted, revocable grants (`SPEC.md` `AuthorityGrant`) | declined | PROD-I-5 |
| Sync from external Postgres (Supabase, Neon) | `asset:event-and-receipt-stream` crossing is the only source; external sources enter through Asset Service `capture_source` / `read_source` | declined as a projection input; required as an Asset Service capability | `read_source` (unbuilt) |
| Managed hosting; connect any Postgres by connection string | declined in Phase I (`SPEC.md` lines 24-27, local operation); a Postgres-backed projection target is a port | port | decision record; O7 |
| GQL / Cypher | declined | declined | no requirement names it |
| Millisecond retrieval | not a parity criterion | declined | PRD non-goal |

## Beyond parity

These are required here and are not part of Polygres's offer. They are the
conditions under which parity counts.

- a receipt on every retrieval, build, registration, and refusal (C8);
- every hit resolves to a `source_address` and `source_digest` (Projection
  rule);
- declared omissions on every result and every context package;
- staleness declared on the receipt, never silent;
- exact versus approximate never confused (`index_kind`);
- embedding provenance: the binding, model, version, data boundary, usage,
  and cost that produced each vector (PROD-I-9);
- counter-records survive rebuild in the source and take effect in the
  projection (C9);
- independent fidelity observation, not the index's self-report (C7);
- local sovereignty: losing any external index or provider leaves the
  stdlib lanes and the record intact (`AI-NATIVE.md` lines 130-132).

## Reading this ledger

A row reaches parity when its operation is `BUILT` with a positive and a
defeating fixture, then `WITNESSED` by a different agent. This file records
the target; standing lives in `STATUS.yaml` and the service manifest.
