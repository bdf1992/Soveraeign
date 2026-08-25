# Asset Projection Service

Status: `CHARTERED · NOT IMPLEMENTED`

This directory is reserved for the Asset Projection Service contract and
future reference participant. The service boundary, owned records, lanes,
proving narrative, and defeating cases are in `CHARTER.md`; `PARITY.md` is
the owner-directed capability target against Polygres; `contracts/` holds
the manifest; `conformance/` holds declarative seed fixtures a future
participant must satisfy.

The service owns retrieval over asset records: text, graph, vector, fused
ranking, and context packages. It reads the Asset Service through a declared
read-only crossing and never writes asset state. Everything it holds is a
rebuildable projection.

Implementation begins once:

1. the Asset Service `core.py` split lands, so the stream this service reads
   has a stable owner (`ENGINEERING.md`, Context and module budget);
2. projection-specific positive and defeating fixtures are executable.

Ratification of the boundary (`decisions/0021`, O21) gates only
`projection.ratify_boundary`: the standing word, not the build. The dense and
sparse lanes wait on O12 for embeddings; every row in `PARITY.md` names its
own gate. No placeholder implementation is treated as progress toward those
gates.
