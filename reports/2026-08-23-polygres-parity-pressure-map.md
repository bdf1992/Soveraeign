# Parity pressure map: Polygres against the asset and record plans, 2026-08-23

Status: `DRAFT MAP · NOT WITNESSED · NOTHING RATIFIED`

Bdo asked for a feature-parity pressure map between Polygres
(<https://polygres.com/>, docs at <https://docs.evokoa.com/polygres>) and
Soveraeign's assetization and database plans. This file is a report, not
policy (`AGENTS.md`, Design System of Record). It changes no standing and
decides nothing; every pressure grade below is this report's own rubric.

Follow-up the same day: Bdo directed a dedicated Asset Projection Service with
parity as its target. The boundary is chartered at `services/projection/`
(`CHARTER.md`, `PARITY.md`, seed fixtures) under `decisions/0021`, open
decision O21. This report stays as the reasoning behind that charter.

## The two things in one sentence each

Polygres turns a Postgres database into one retrieval call for agents: graph
traversal, dense and sparse vectors, full-text and fuzzy text, and a fused,
re-ranked result, with no sidecar and no embedding generation of its own.

Soveraeign is an authority and record kernel: content-addressed sources, typed
grants, receipts on every crossing, retraction as counter-record, and a rule
that every search index, graph store, or model context package is a rebuildable
projection that must resolve each value to an authoritative record and declare
its omissions (`SPEC.md`, Projection rule, lines 373-378).

So the map is not peer-to-peer. Almost everything Polygres is lives in our
vocabulary as a **projection**. The pressure question is therefore: which of
Polygres's projection capabilities do our own requirements already demand, which
are chartered, which are deliberately deferred, and which do not belong.

## Pressure rubric (this report only)

- **required** — a PRD or contract clause already demands it;
- **chartered** — a charter or adapter note names it, nothing built;
- **deferred** — `ENGINEERING.md` lines 45-48 lists it as "not yet selected"
  and line 185 gives the trigger: "a projection fails a measured local query";
- **none** — out of Phase I scope, or contrary to a governing rule.

## What is built today on our side

- Search: `search_projection` is one denormalised text column queried with
  `LIKE '%q%'`, ordered by `asset_id`, no ranking
  (`services/asset/src/soveraeign_asset_service/core.py` 293-326).
- Graph: `graph_projection` holds edges copied from ratified proposals carrying
  a `relationship` key; `neighbors()` is one hop, one `SELECT`
  (`core.py` 308-332).
- Rebuild deletes both tables and re-derives them from records, emitting a
  `projection.rebuild` receipt (`core.py` 290-321). A forged projection row
  does not survive rebuild (`tests/test_projection_authority.py` 75-111).
- No FTS5, no recursive CTE, no vectors, no embeddings, no event journal.

## Forward pressure: Polygres capability to Soveraeign locus

| Polygres capability | Our locus | Today | Pressure | Gate |
| --- | --- | --- | --- | --- |
| Full-text (`tsvector`) and fuzzy (`pg_trgm`) text search | search projection | `LIKE` substring scan | **chartered** — `services/asset/CHARTER.md` line 74 already claims "SQLite FTS projection" | `core.py` split (`ENGINEERING.md` 171-173); FTS5 is in the stdlib `sqlite3`, so no dependency decision |
| Graph `related` / `expand` / `neighborhood` / `path` / `connection`, `max_depth` 1..20, direction, relationship-type filter | graph projection; `adapters/README.md` Graph row: "rebuildable projection and traversal results" | one hop | **chartered** — `CHARTER.md` line 75 "lineage traversal" | `core.py` split; a recursive CTE is stdlib. NetworkX or Neo4j would each need a decision record |
| Graph derived from the schema itself (foreign keys) | lineage edges: asset -> version -> source, run -> input/output version | these edges exist as rows but are not projected | **chartered** — same line 75 | none beyond the split; edges must still resolve to records |
| Dense vector search (HNSW, quantised, in memory) | "model context packages are rebuildable projections" (`SPEC.md` 373-378); vector store "not yet selected" (`ENGINEERING.md` 46) | absent | **deferred** | observed local query failure + decision record; embeddings also need `invoke_model`, which is O12 |
| Sparse retrieval | same bucket as dense | absent | **deferred** | same |
| Fusion and re-ranking (weighted RRF, `score_kind`, lane evidence, `introduced_by_graph`) | the *explanation* half maps to "resolves to authoritative source records and declares omissions" | no ranking, no omissions on a hit | **required** for the provenance of any projected hit (PROD-I-3: "origin and projection visible"); **deferred** for the ranking itself | provenance: none; ranking: as dense |
| Scalar filters (`must` / `should` / `must_not`, ranges, `is_null`) | a `WHERE` clause over the projection | absent | **none** in Phase I; trivial when a fixture asks | none |
| Recommend / discover / explore / grouped search | no locus | absent | **none** — PRD non-goal "optimizing performance before semantic conformance" | none |
| Recall check (HNSW vs exact top-K) | projection fidelity proof; C7 reports vs observations | rebuild-proof test exists for authority, not for fidelity | **required** in principle: a projection must declare omissions; a lossy index is a declared omission | none; add a fixture when a lossy index exists |
| Readiness states (graph `Ready`, index `Ready`) | `projection.rebuild` receipt + `source_receipt` per row; Console `projection-view.schema.json` requires `rebuild_operation_id` and a deterministic `content_digest` | receipt only; no freshness signal on a read | **chartered** (Console) | O18 |
| Runtime row writes through the API | the transition contract; "projection-originated edits return as proposals" | proposals exist | **none** — ours is stricter by design | none |
| Roles Owner / Admin / Developer / Viewer; three credentials, each unlocking one surface | `AuthorityGrant` with type, budget, validity, revocation | grants carry actor, capability, scope only (`KNOWN-GAPS.md`, Authority envelope) | **required** already (PROD-I-5); Polygres's fixed roles are weaker than our spec and stronger than our code | none |
| Sync from external Postgres (Supabase, Neon) without exposing the copy | `read_source` + `Recording` (`SPEC.md` 84-104); GitHub source adapter | `read_source` absent; `.claude/drafts/recording-slice-ticket.md` proposes it | **required** (PROD-I-2 Remember) | `core.py` split; the draft ticket is unregistered |
| Python SDK, HTTP API, CLI, "Agent Skills" | bindings; two-binding proof (`PRD.md` 120-126) | CLI with four subcommands | **required** (two model bindings + one human binding); HTTP itself waits for a conformance case (`AGENTS.md`, Technical baseline) | O12 for model bindings; O18 for the human binding |
| Token-ready ranked context for an agent | `ModelBinding.input_projection_id` + data boundary | absent | **required** that every invocation records an addressed input projection (PROD-I-9); ranking not required | O12 |
| Managed hosting; connect any Postgres by connection string | `SPEC.md` lines 24-27: Phase I runs with no network service; optional integrations are adapters or refuse `UNCONFIGURED` with a receipt | n/a | **none** as a dependency; admissible only as an adapter, never authoritative | decision record + O7 for anything external |
| GQL / Cypher | none | absent | **none** | none |
| Millisecond retrieval | PRD non-goal | n/a | **none** | none |

## Reverse pressure: what we demand that Polygres does not show

These are not gaps in Polygres's product; they are the reasons it cannot be
our record, only ever a projection of it.

- A receipt on every crossing, including refusals (C8; `receipt.schema.json`,
  15 required fields).
- Retraction as a counter-record that preserves the act (C9).
- Content-addressed inputs and outputs on every event
  (`event-envelope.schema.json`, `inputs`/`outputs` as `{address, digest}`).
- Declared omissions on every projected value (`SPEC.md` 373-378).
- Typed grants with budget and validity, not four fixed roles (`SPEC.md`
  114-126).
- Independent observation separate from executor self-report (C7). Polygres's
  recall check is the nearest thing, and it is a self-check.
- Local sovereignty: losing the integration cannot remove custody
  (`AI-NATIVE.md` 130-132).
- Model identity, data boundary, usage, and cost on every invocation
  (PROD-I-9). Polygres does not generate embeddings, so it does not record
  who did.

## One overstatement in our own documents

`services/asset/CHARTER.md` line 74 says the search mechanism is an
"SQLite FTS projection". The build is a `LIKE` scan. `KNOWN-GAPS.md` does not
list this. It is the only place the repository currently claims more than it
has in this area; it should be added to the gap table before any parity claim
is made against it.

## Where Polygres could sit if Bdo ever wanted it

Behind the `graph-projection` port named in
`services/asset/contracts/service.json`, as a declared adapter that consumes
canonical relationship and version records and returns traversal and search
results. It would: refuse `UNCONFIGURED` with a receipt when absent; never
hold a `relationships` row or a grant; carry a decision record naming the
boundary, the observed need, and failure behaviour; and stay outside Phase I
because it is a network service. Nothing about it is incompatible; it is
simply a projection target, and not the first one we need.

## Yours to decide (queued, not decided)

1. Whether vector or embedding retrieval belongs to any phase. No open
   decision asks this; `ENGINEERING.md` only defers it. If it belongs, it
   needs a number in `STATUS.yaml`.
2. O12 — without a ratified binding contract there is no `invoke_model`, so
   no embeddings and no addressed input projection.
3. O2 — the SQLite baseline is still proposed; FTS5 and recursive CTEs ride on
   it.
4. O18 — projection readiness and freshness on a read belong to Console.
5. Whether an external Postgres-backed projection (Polygres or otherwise) is
   ever an admissible adapter target. Not raised anywhere today.

## What I would do

- Two minutes: add the FTS row to `services/asset/KNOWN-GAPS.md` so the
  charter and the build agree.
- Then, in order and each with a positive and a defeating fixture: finish the
  `core.py` split (`#6`/`#27`, already the reachable job per
  `scripts/sov_next.py`); FTS5 search with per-hit `source_receipt` and
  declared omissions; recursive-CTE traversal with `max_depth` and direction;
  lineage edges projected from `versions`, `sources`, and `runs`. All
  stdlib, no decision record needed, about a day each.
- Leave dense and sparse retrieval where `ENGINEERING.md` leaves them until a
  measured local query fails or Bdo rules on item 1.

## Sources read

Polygres landing page; docs pages `getting-started/key-concepts`,
`reference/pgcontext-api`, `reference/graph-retrieval-api`. Not read:
`reference/limits`, `roles-and-permissions`, `runtime-row-writes`, pricing.
Claims attributed to Polygres are its own marketing and documentation text as
of today and were not executed or observed.
