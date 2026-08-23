# Services

Services are bounded enterprise capabilities inside a local Soveraeign Node.
They share the kernel's standing, authority, transition, observation, receipt,
and retraction semantics; no service creates a private authority system.

## Current boundaries

| Service | Standing | Owns |
| --- | --- | --- |
| `asset/` | experimental reference participant | asset identity, payload custody, versions, derivation lineage, discovery, and asset-use records |
| `proofing/` | chartered, not implemented | version-pinned review sessions, annotations, rounds, and decision history |
| `console/` | chartered, not implemented | operator sessions, channels, threads, posts, notifications, judgement requests, operator settings, and dashboard and activity projections |

Each service directory may contain:

- `CHARTER.md` — semantic boundary and proving narrative;
- `contracts/` — interface and assessment contracts;
- `src/` — a reference participant only after fixtures exist;
- `tests/` — participant tests that establish `BUILT`, never witness themselves;
- `KNOWN-GAPS.md` — observed differences from `SPEC.md`.

Deployment does not define service identity. One process may host several
services, and one service may later use several processes, without changing the
classification contract.
