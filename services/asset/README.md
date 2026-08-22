# Soveraeign Asset Service

Status: `EXPERIMENTAL REFERENCE PARTICIPANT · NOT PRODUCTION`

This directory is the first executable stack-slice experiment for Soveraeign: a local
asset service with immutable bytes, a canonical event ledger, authority-aware
operations, worker leases, independent observation, receipts, retraction,
search, graph projection, and a refused-until-configured federation seam.

It is intentionally dependency-free. Its tests are implementation self-reports:
they establish `BUILT`, not `WITNESSED`, `RATIFIED`, or Phase-I qualification.

```bash
cd services/asset
python -m unittest discover -s tests -v
PYTHONPATH=src python scripts/demo.py
```

The graph is a rebuildable SQLite projection, not authoritative state. A later
`GraphProjection` adapter may target Neo4j Community or another local graph
service without changing the asset contract.

The proving narrative is described in `CHARTER.md` and evaluated by
`../../AI-NATIVE.md`. Known differences from the proposed logical specification
are recorded in `KNOWN-GAPS.md`; those gaps must be fixed in the participant,
not hidden by weakening the conformance oracle.
