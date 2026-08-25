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

Derivative recordings are created only for requests carrying a complete
`ReaderDeclaration`. The declaration names the reader and version, supplies a
versioned artifact and secret-free replay configuration, and declares
exact-or-lossy fidelity plus recoverable omissions. The service deposits the
reader, configuration, source, and output in its local CAS. The recording can
be reconstructed by recording or output-version ID without exposing local
filesystem paths. Legacy derivative runs remain versions, not recordings; they
cannot be passed off as reconstructable. This is the substrate for later local
model enrichment; no model output is admitted or ratified by this mechanism.
Configurations use opaque credential references rather than usable secrets.

This layer verifies what reader material a worker declared; it does not yet
attest that the worker semantically executed that artifact. That remains an
observation/model-binding obligation rather than authority granted by storage.

The proving narrative is described in `CHARTER.md` and evaluated by
`../../AI-NATIVE.md`. Known differences from the proposed logical specification
are recorded in `KNOWN-GAPS.md`; those gaps must be fixed in the participant,
not hidden by weakening the conformance oracle.
