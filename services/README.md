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
| `gateway/` | chartered, not implemented | the node's door: requests admitted, capabilities resolved, authority checked, routes recorded, receipts returned, transports bound |
| `proofing/` | chartered, not implemented | version-pinned review sessions, annotations, rounds, and decision history |
| `projection/` | chartered, not implemented | projection collections, text, graph, and vector configurations, builds, retrieval receipts, context packages, and fidelity observations over asset records; parity target in `PARITY.md` |

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
- `tests/` — participant tests that establish `BUILT`, never witness themselves;
- `KNOWN-GAPS.md` — observed differences from `SPEC.md`.

`contracts/service.json` is the service's specification. There is no per-service
`SPEC.md`: the root `SPEC.md` owns the kernel, and a second prose authority per service
would restate rules nothing could check.

Deployment does not define service identity. One process may host several
services, and one service may later use several processes, without changing the
classification contract.
