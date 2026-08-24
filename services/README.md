# Services

Services are bounded enterprise capabilities inside a local Soveraeign Node.
They share the kernel's standing, authority, transition, observation, receipt,
and retraction semantics; no service creates a private authority system.

## Current boundaries

| Service | Standing | Owns |
| --- | --- | --- |
| `asset/` | experimental reference participant | asset identity, payload custody, versions, derivation lineage, discovery, and asset-use records |
| `record/` | experimental reference participant | the append-preserving journal, terminal receipts, counter-records, the digest chain, and subject projections |
| `console/` | built in part, remainder chartered | operator sessions, channels, threads, posts, notifications, judgement requests, authority grants, operator settings, and dashboard and activity projections |
| `gateway/` | proposed boundary; first IN_PROCESS route pattern built and self-tested | the node's door: requests admitted, capabilities resolved, authority checked, routes recorded, receipts returned, transports bound |
| `registry/` | chartered and contracted; implementation not yet present | versioned name resolution, source-owned registry entries and relations, owner records, rebuildable indexes, and drift findings |
| `observation/` | chartered, not implemented | independent observation: observer registrations, declared predicates, observation requests, independence checks, observations, and attestations. Not the log - the journal is the Record Service's |
| `proofing/` | chartered, not implemented | version-pinned review sessions, annotations, rounds, and decision history |
| `projection/` | chartered, not implemented | projection collections, text, graph, and vector configurations, builds, retrieval receipts, context packages, and fidelity observations over asset records; parity target in `PARITY.md` |

A service's repository implementation and its standing are separate facts. A participant can
exist under `src/` and pass its own tests while its manifest remains `PROPOSED`; tests are
evidence for a standing transition, not the transition itself.

## Construction view: kernel, vertical, horizontal, node surface

This is a construction vocabulary, not a new structural scale. `CLASSIFICATION.md` still owns
`System > Federation > Node > Service > Component`.

- **Kernel** — the irreducible shared semantics: standing, typed authority, transition,
  observation, receipt, and retraction. Geometrically, the point: no service identity and no
  deployment claim, just the invariants every valid operation must pass through.
- **Vertical** — one declared operation carried end to end through those invariants: request,
  resolution, authority, service execution, terminal receipt. A completed vertical closes back
  on durable evidence rather than ending at an executor return. Geometrically, a closed loop.
- **Horizontal** — several service-owned verticals composed inside one node through shared
  resolution, authority, record, and routing semantics. Horizontal growth adds capabilities
  without turning Gateway into a domain service or giving any service private kernel rules.
- **Node surface** — the usable boundary of that horizontal composition: the Console and
  bindings for actors, the Gateway for governed ingress/egress, and declared projections for
  what the node exposes. The surface is a boundary over the node; it is not a new authority
  layer.

The useful geometric progression is therefore `point -> circle -> sphere -> ball` if the filled
**ball** names the Node itself and the **sphere** names its surface. That avoids calling a filled
volume a surface: the Node contains the services, durable record, runtime, and crossing policy;
its surface is what actors or another node may address through governed interfaces.

This view also keeps a root distinct from a node. A root seat is the local settlement root in a
seat topology. The node is the locally sovereign instance that the root settles for. A crossing
between roots does not merge them: each node retains its own record and authority and settles
its own side.

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
durable record, local settlement root, and governed crossing boundary.
