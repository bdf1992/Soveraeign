# Asset Service Charter

Status: `BUILT_SELF_TESTED_NOT_WITNESSED`

## Role in Soveraeign

The **Asset Service** is a bounded service within Soveraeign responsible
for the custody, description, transformation, relationship, discovery, and
governed use of enterprise assets.

It may also be deployed as a local service and serve as one concrete reference
binding of the broader Soveraeign stack. “Microservice” describes a deployment
and failure boundary; it does not grant the service separate authority or make
its internal database the product's source of truth.

## Current boundary

The Asset Service is one bounded service inside a local Soveraeign Node. It owns asset custody, versioned asset records, derivation and relationship history, declared transformations, and the receipts for those operations. It uses the shared kernel and authority model; deployment as a local service does not make it a separate authority or a node of its own.

## Current reference binding

The current reference participant uses:

- one asset service inside one sovereign local Soveraeign node;
- one local content-addressed asset store;
- one canonical record and receipt ledger;
- one shared transition API for human and model bindings;
- one or more disposable search and graph projections;
- local workers acting through leased, scoped operations;
- adapter ports for Claude, GitHub, and media tools; federation remains unconfigured.

It is not:

- a federation;
- a second sovereign node;
- the whole Soveraeign product;
- a frozen technology choice;
- or an authority island with rules different from the common kernel.

## Not current standing

The service is not a federation, a second sovereign node, the whole product, or a separate authority island. `FederationPort` is an unconfigured seam and must refuse as `UNCONFIGURED` when no admitted binding exists.

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
| Federation | inactive governed-crossing port | unconfigured; no federation standing |

Graph-originated edits must return as proposals through the canonical transition
path before they can affect effective state.

## Built evidence

The code in this directory is a reference participant. Its current self-tests establish `BUILT` evidence only. They do not establish independent observation, owner acceptance, or F3 qualification. `KNOWN-GAPS.md` records the remaining differences from the service contracts.

The reference participant keeps local custody and ledger state, uses scoped worker leases, preserves receipts and retraction history, and refuses unavailable integrations as `UNATTESTABLE` or `UNCONFIGURED` rather than reporting simulated success.
