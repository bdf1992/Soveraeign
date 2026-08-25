# Asset Projection Service Charter

Status: `PROPOSED SERVICE BOUNDARY · NOT IMPLEMENTED`

## Role

The Asset Projection Service is a sibling of the Asset Service, the Proofing
Service, and the Console Service inside a local Soveraeign Node. It owns the
retrieval surface over asset records: text search, graph traversal, vector
search, fused ranking, and token-budgeted context packages that a human or
model operator asks for and receives with provenance. Its target capability
set is parity with Polygres (`PARITY.md`), reached through Soveraeign's own
rules rather than around them.

Everything it holds is a projection under the `SPEC.md` Projection rule: a
rebuildable read model whose every value resolves to an authoritative record
and declares its omissions. It reads the Asset Service's records and receipts
through a declared read-only crossing. It never owns an asset, a version, a
payload, a relationship record, a grant, or a standing, and it never becomes a
private authority system. A projection-originated edit returns as a Proposal
through the transition contract.

Bdo directed this boundary on 2026-08-23: the Asset Service needs an asset
projection service, and that service's feature set should reach parity with
what Polygres offers. This charter carries that intent at proposal standing.

## Relationship to Phase-I requirements

- `PRD.md` PROD-I-3 (Cross): a fact deposited by one operator is retrieved by
  the other "with origin and projection visible". Retrieval with provenance is
  this service's whole job.
- `PRD.md` PROD-I-2 (Remember): a retrieval hit reconstructs its source,
  version, and reader; it does not replace them.
- `PRD.md` PROD-I-9 (Bring your own model): every model invocation records an
  addressed `input_projection`. The context package is that projection. The
  service does not generate embeddings; a declared Model Binding does, through
  `invoke_model`, and the vector registration names it.
- `PRD.md` PROD-I-4 (Gate and retract): a countered record drops out of the
  next build; the original and the counter-record stay visible in the source.
- `SPEC.md` Projection rule and `CONTRACT.md` C15: indexes, graphs, caches,
  and model context packages are rebuildable; events and receipts remain.
- `CONTRACT.md` C7: an index's own recall report is an executor report. A
  fidelity observation by an independent observer decides whether the index
  is faithful.
- `PRD.md` non-goal "optimizing performance before semantic conformance":
  parity is defined by capability and provenance, not latency.

## Owned domain records

- projection collection — a declared retrieval scope: the source record kinds
  it projects, its key column, its text, vector, graph, and filter fields, and
  its lifecycle;
- text configuration — tokenizer and fuzzy-match declaration for a collection;
- vector registration — a named vector space on a collection: dimension,
  distance, the Model Binding or declared external provenance that produced
  the embeddings, and the index declaration;
- graph configuration — the record kinds, relationship types, lineage edges,
  and directions that traversal may follow;
- index declaration — `index_kind` for a lane: `NONE` (exact scan), `FTS`,
  `TRIGRAM`, or a declared external index port; exact and approximate are
  never confused;
- projection build — one rebuild operation: the input addresses and
  `input_state_digest` consumed, the lanes built, the resulting
  `content_digest`, and its receipt;
- retrieval receipt — one query: parameters, lanes used, every hit with
  `source_address`, `source_digest`, rank, score breakdown, and
  `introduced_by_graph`, the build it read, and declared omissions;
- context package — a token-budgeted, ordered set of hits with addresses,
  digests, omissions, and `content_digest`, addressable as a Model Binding's
  `input_projection_id`;
- fidelity observation — an independent comparison of an approximate lane
  against its exact lane over the same build;
- projection receipt and history.

Proposed lifecycle (service policy awaiting owner ratification; it does not
replace the shared `RECORDED`, `ADMITTED`, `RATIFIED`, and `EFFECTIVE`
standings):

```text
projection collection:  DECLARED → READY → STALE → READY
```

`READY` means a build exists whose `input_state_digest` matches the current
source stream. `STALE` means the source stream has advanced past the last
build; reads still answer, and every retrieval receipt names the build it
read and carries the staleness as a declared omission.

## Retrieval lanes

| Lane | Mechanism | Phase-I standing |
| --- | --- | --- |
| Text | SQLite FTS5 with unicode and trigram tokenizers (stdlib `sqlite3` 3.34+) | buildable now; no dependency decision |
| Graph | recursive CTE over projected relationship and lineage edges: `related`, `expand`, `neighborhood`, `path`, `connection`; `max_depth` 1..20, `direction` `OUT` / `IN` / `ANY`, relationship-type filter | buildable now; no dependency decision |
| Dense vector | exact cosine scan over registered vectors; embeddings arrive by `invoke_model` or declared external provenance | exact scan buildable after O12; approximate index is a port |
| Sparse vector | exact sparse dot product over registered sparse vectors | same as dense |
| Filter | `must` / `should` / `must_not` groups of scalar match, range, and `is_null` over declared filter fields; applies to every lane | buildable now |
| Fusion | weighted reciprocal rank fusion, `k = 60` by default, declared per query; joint rescoring across lanes | buildable after two lanes exist |

## Integration with sibling services and the kernel

The Asset Projection Service:

1. reads asset, version, source, relationship, run, and receipt records from
   the Asset Service through a declared read-only crossing
   (`asset:event-and-receipt-stream`); it never writes Asset Service state
   and never opens the Asset Service database directly;
2. builds every lane from that stream in one `build-projection` operation
   that emits `ATTEMPTED`, stores the executor's report, and settles only on
   an independent observation of the resulting `content_digest`;
3. requests embeddings only through `invoke_model` on a declared Model
   Binding within its data boundary; a vector registration that names no
   binding and no declared external provenance refuses `INCOMPLETE_PROPOSAL`;
   an unavailable binding refuses `MODEL_UNAVAILABLE` and never falls back
   silently;
4. serves every retrieval with a receipt whose hits resolve to source
   addresses and digests, whose omissions are declared, and whose build id
   and `input_state_digest` are named;
5. returns a projection-originated edit as a Proposal standing `RECORDED`
   through the Asset Service transition contract;
6. refuses an external index, an external graph database, an HTTP binding,
   and cross-node retrieval as `UNCONFIGURED` with a receipt until a separate
   decision admits each;
7. never rewrites a retrieval receipt, build, or observation; corrections are
   new records or counter-records.

Authority stays where the kernel puts it: holding a grant to read a collection
does not grant a right to change what it projects.

## Human and model participation

Humans and models query the same service through different bindings:

- both declare collections, request builds, and query lanes under scoped
  grants; every operation returns a receipt;
- a model receives a context package as its addressed input projection; a
  human receives the same hits rendered through the Console Service;
- a model's retrieval is recorded with its binding identity; a human's with
  their operator identity; neither changes a score or a source;
- machine verification authority may settle checkable predicates (rebuild
  equality, hit resolution, fidelity comparison) but cannot ratify a Proposal
  that a projection edit raised.

## Initial proving narrative

From a clean local checkout with the Asset Service walking skeleton ingested:

1. declare one collection over asset versions with text, filter, and graph
   fields; observe `DECLARED`;
2. build it; observe the build receipt naming the asset stream's addresses and
   `input_state_digest`, and the collection `READY`;
3. run a text query, a fuzzy text query, and a filtered query; show every hit
   naming a `source_address` and `source_digest` that resolves in the Asset
   Service;
4. traverse from one asset with `max_depth` 3 and `direction` `ANY`; show
   depth, path, edge path, and that every edge resolves to a relationship or
   lineage record;
5. find the path between two assets and a connection across three; show the
   step-by-step records;
6. register a vector space with an unconfigured Model Binding; observe
   `MODEL_UNAVAILABLE` with a receipt and no silent substitute;
7. register the same space with owner-supplied vectors under declared external
   provenance; run an exact dense query; show the provenance on the receipt;
8. run a fused query over text, graph, and dense; show the per-lane score
   breakdown, `introduced_by_graph`, and the RRF parameters on the receipt;
9. package a context of 2,000 tokens from that result; show the addresses,
   digests, omissions, and `content_digest`, and that a second package over
   the same build is byte-identical;
10. ingest a new asset version; observe the collection `STALE` and a retrieval
    receipt that names the old build and declares the staleness;
11. rebuild; observe `READY`, a new `content_digest`, and the old build still
    in history;
12. retract one relationship in the Asset Service; rebuild; show the edge gone
    from traversal and the counter-record visible in the source;
13. attempt, from a hit, to change a projected label; observe one Proposal
    standing `RECORDED` and no projection or asset state change;
14. attempt an external HNSW index, an HTTP binding, and a cross-node query;
    observe `UNCONFIGURED` refusals with receipts.

## Defeating cases

- a hit names no source address or digest, or names one that does not
  resolve to an Asset Service record;
- two builds from an unchanged stream differ in `content_digest`;
- a retrieval answers from a stale build without declaring it;
- a countered relationship still appears in traversal after rebuild, or
  rebuild erases the counter-record's visibility in the source;
- a vector registration carries no binding and no declared provenance, or an
  unavailable binding is replaced silently;
- an approximate index serves as exact, or a fidelity observation is the
  index's own report;
- a projection edit writes Asset Service state directly, or a projected value
  is cited as a grant or precondition;
- a traversal exceeds its declared `max_depth` or follows an undeclared
  relationship type;
- a fused hit cannot show which lanes produced it;
- a context package exceeds its token budget or omits a dropped hit from
  omissions;
- the service opens the Asset Service database directly;
- an external index, binding, or node is reported as success instead of
  `UNCONFIGURED`.

## Deferred

Approximate nearest-neighbour indexes (HNSW or otherwise), quantisation,
recommend, discover, explore, grouped search, query plans, Postgres-backed or
Polygres-backed projection targets, an HTTP binding, and cross-node retrieval
are outside the first proof. Their interfaces may be declared as ports; their
effects remain refused until separately admitted. `PARITY.md` names each one
and its gate.
