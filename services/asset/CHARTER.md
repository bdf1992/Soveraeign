# Asset Service Charter

Status: `PROPOSED VERTICAL-SLICE BOUNDARY`

## Role in Soveraeign

The **Asset Service** is a bounded service within Soveraeign responsible
for the custody, description, transformation, relationship, discovery, and
governed use of enterprise assets.

It may also be deployed as a local service and serve as one concrete reference
binding of the broader Soveraeign stack. “Microservice” describes a deployment
and failure boundary; it does not grant the service separate authority or make
its internal database the product's source of truth.

## Source-grounded boundary

- `ANCHOR.md` A1 defines the product as the working system rather than any one
  instrument within it.
- `PRD-PRODUCT(1).md` explicitly treats these instruments as subsystems and requires Phase-I
  runtime, configuration, interfaces, and minimum infrastructure assumptions.
- `PRODUCT(1).md` §5 defines the destination as a distributed federation of
  sovereign local-first nodes joined by governed crossings.
- `PRD-PRODUCT(1).md` Phase II says federation begins with a real second node,
  not a platform launch.
- `FREEZE-LEDGER(1).md` defers operational messaging and routing until node two
  exists.
- `HANDOFF-SPEC.md` requires the logical specification to remain stack-neutral.

Therefore the Asset Service may prove one real stack slice now while keeping the service,
database, graph, transport, and deployment mechanisms replaceable.

## Initial deployment identity

For the first vertical slice, the Asset Service is:

- one asset service inside one sovereign local Soveraeign node;
- one local content-addressed asset store;
- one canonical record and receipt ledger;
- one shared transition API for human and model bindings;
- one or more disposable search and graph projections;
- local workers acting through leased, scoped operations;
- adapter ports for Claude, GitHub, media tools, and future federation.

It is not yet:

- a federation;
- a second sovereign node;
- the whole Soveraeign product;
- a frozen technology choice;
- or an authority island with rules different from the common kernel.

## When it could become a node

The asset service may later qualify as a sovereign node only if it:

1. owns a durable local record rather than only a cache or projection;
2. can operate safely when external integrations are absent;
3. declares its own authority, resource, trust, and fault envelopes;
4. exports and admits state only through governed crossings;
5. preserves source, standing, receipt, and retraction semantics across those
   crossings;
6. and actually interoperates with a distinct second node.

Until then, `FederationPort` is an interface seam whose operations refuse as
`UNCONFIGURED`, leaving a receipt. It is not a simulated federation.

## Authoritative versus derived stores

| Concern | Initial mechanism | Standing |
| --- | --- | --- |
| Asset bytes | local content-addressed files | authoritative payload custody |
| Assets, versions, operations, authority, receipts | SQLite ledger | canonical reference binding |
| Search | SQLite FTS projection | derived and rebuildable |
| Relationships and lineage traversal | SQLite edge projection; optional NetworkX | derived and rebuildable |
| External graph database | optional `GraphProjection` adapter | never authoritative |
| Claude analysis | proposal-producing adapter | evidence/candidate, never authority |
| GitHub import | exact repository/commit/path source adapter | external source provenance |
| Federation | inactive governed-crossing port | deferred until node two |

Graph-originated edits must return as proposals through the canonical transition
path before they can affect effective state.

## First proving operation

From a clean local checkout:

1. ingest an original asset and preserve its exact bytes;
2. request a declared derivative for a named enterprise use;
3. allow a scoped worker to claim and execute the operation through a fenced
   lease;
4. independently observe the output rather than trusting the worker report;
5. allow a model adapter to propose metadata and relationships;
6. ratify only through typed authority;
7. rebuild search and graph projections from canonical receipts;
8. expose the same effective asset state to human and model bindings;
9. retract one effective relationship or use without erasing the history;
10. reproduce the same effective projections after a clean rebuild.

This operation is evaluated under `AI-NATIVE.md`. The presence of Claude, an
API, workers, or a graph database does not itself earn the verdict.

The code in this directory is an experimental reference participant. Its current
self-tests establish `BUILT` evidence only. `KNOWN-GAPS.md` records where it
does not yet satisfy `SPEC.md`; it must not be represented as F3-qualified.

## One-hour implementation constraint

The first pass optimizes for semantic reach rather than production breadth:

- standard-library local custody and ledger;
- one real end-to-end asset operation;
- deterministic adapters when live integrations are unavailable;
- explicit `UNATTESTABLE` or `UNCONFIGURED` outcomes instead of simulated
  success;
- positive and defeating fixtures;
- no cloud dependency, external mutation, federation claim, or stack freeze.
