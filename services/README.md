# Services

Services are bounded enterprise capabilities inside a local Soveraeign Node.
They share the kernel's standing, authority, transition, observation, receipt,
and retraction semantics; no service creates a private authority system.

## Current boundaries

| Service | Standing | Owns |
| --- | --- | --- |
| `asset/` | experimental reference participant | asset identity, payload custody, versions, derivation lineage, discovery, and asset-use records |
| `record/` | experimental reference participant | the append-preserving journal, terminal receipts, counter-records, the digest chain, subject projections, and journal export and restore (`decisions/0049`) |
| `identity/` | placement provisional; challenge component built | the challenge lifecycle: mint, deliver, present, expire (`decisions/0048` ID-12..14). Whether identity is a service at all is open at judgement 3 |
| `console/` | built in part, remainder chartered | operator sessions, channels, threads, posts, notifications, judgement requests, authority grants, operator settings, and dashboard and activity projections |
| `gateway/` | proposed boundary; first IN_PROCESS route pattern built and self-tested | the node's door: requests admitted, capabilities resolved, authority checked, routes recorded, receipts returned, transports bound |
| `host/` | built read-health slice; mutating operations declared and unreachable | normalized host readings and the lifecycle of requested scans, restart/power, driver, and utility operations behind a Host Port |
| `registry/` | built read-only resolve slice; broader registry charter remains | versioned name resolution, source-owned registry entries and relations, owner records, rebuildable indexes, and drift findings |
| `observation/` | chartered, not implemented | independent observation: observer registrations, declared predicates, observation requests, independence checks, observations, and attestations. Not the log - the journal is the Record Service's |
| `proofing/` | chartered, not implemented | version-pinned review sessions, annotations, rounds, and decision history |
| `projection/` | chartered, not implemented | projection collections, text, graph, and vector configurations, builds, retrieval receipts, context packages, and fidelity observations over asset records; parity target in `PARITY.md` |

A service's repository implementation and its standing are separate facts. A participant can
exist under `src/` and pass its own tests while its manifest remains `PROPOSED`; tests are
evidence for a standing transition, not the transition itself.

## Construction view: root, vertical, horizontal, surface, node

This is a construction vocabulary, not a new structural scale. `CLASSIFICATION.md` still owns
`System > Federation > Node > Service > Component`.

Two dimensions must not be collapsed:

- **Kernel** is the available grammar of operation, not a geometric or structural level. It
  defines the admissible typology (what kinds may exist), topology (how those kinds may relate),
  legal traversal and transitions, and the invariants that may never collapse. Nodes, services,
  operations, and crossings instantiate that grammar; they do not redefine it by convenience.
- **Root** is the irreducible local settlement locus for one Node. Geometrically, the point. A
  root seat may settle judgement or verification for its Node, but the Root is not the Node and
  does not travel across a federation crossing.
- **Vertical** is one declared operation carried end to end through the Kernel: request,
  resolution, authority, service execution, terminal receipt. A completed vertical closes back
  on durable evidence rather than ending at an executor return. Geometrically, a closed path.
- **Horizontal** is several service-owned verticals composed inside one Node through shared
  resolution, authority, record, and routing semantics. Horizontal growth adds capabilities
  without turning Gateway into a domain service or giving any service private Kernel rules.
- **Surface** is the addressable actor- and crossing-facing boundary of that horizontal
  composition. Console and bindings may realize actor-facing pieces; Gateway may realize a
  governed crossing seam; projections may describe what is exposed. Exposure creates no new
  authority.
- **Node** is the filled locally sovereign operating volume: Root, durable record, services,
  runtime and custody, history, and crossing policy bounded by its Surface.

The structural construction is therefore:

`Root -> Vertical -> Horizontal -> Surface -> Node`

with **Kernel governing every term in the expression rather than preceding them**.

The useful geometric progression is `point -> closed path -> extent -> sphere -> ball`: Root is
the point; verticals close paths; horizontal composition gives extent; Surface is the sphere;
Node is the filled ball. Kernel defines which shapes, relations, and traversals are legal at
every stage.

A federation crossing relates Node surfaces, not roots. Each receiving Node resolves and admits
the crossing under its own Kernel and settles its own side against its own Root. A peer's root
identity or evidence can cross; the peer Root's authority cannot silently become local
authority.

The current Gateway/Asset slice proves one Vertical. `sov://asset/read-asset` is the next boring
same-service repetition. `sov://registry/resolve` is the stronger Horizontal proof because it
adds a second service family without adding Registry-specific logic to Gateway. After those
survive the same route contract, a Node composition root can assemble identity, Root topology,
Record, authority, Registry, Gateway, and service-owned routes without becoming a god-service.

## The declared surface

Every service declares its operations in `contracts/service.json` against
`contracts/service-manifest.schema.json`. Each operation states the record it acts on, the
append-preserving CRUD verb it realizes, its logical endpoint, the preconditions it checks,
what a commit produces, and every refusal it may return
(`decisions/0040-the-declared-service-surface.md`).

A logical endpoint is `sov://<service>/<operation>`. It names what is being asked for and
never how the bytes arrive; `contracts/capability-offices.json` binds transports to it.

```
python scripts/sov_service.py check       # judge every manifest
python scripts/sov_service.py endpoints   # every declared logical endpoint
python scripts/sov_service.py crud        # CRUD coverage per service
```

`CREATE` appends. `READ` derives without writing. `SUPERSEDE` adds a later version and keeps
the earlier one. `COUNTER` adds a counter-record and erases nothing. `REBUILD` recomputes a
projection only. There is no `UPDATE` and no `DELETE`.

Each service directory may contain:

- `CHARTER.md` — semantic boundary and proving narrative;
- `contracts/` — interface and assessment contracts;
- `src/` — a reference participant only after fixtures exist;
- `tests/` — participant tests that establish `BUILT` evidence, never witness themselves;
- `KNOWN-GAPS.md` — observed differences from the charter and governing specification.

`contracts/service.json` is the service's specification. There is no per-service
`SPEC.md`: the root `SPEC.md` owns the kernel, and a second prose authority per service
would restate rules nothing could check.

Deployment does not define service identity or node identity. One process may host several
services, and one service may later use several processes, without changing the classification
contract. Likewise, a second process is not a second node. A distinct Node requires its own
durable record, local settlement Root, and governed crossing Surface.
