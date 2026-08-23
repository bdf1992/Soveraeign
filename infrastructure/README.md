# Phase-I Local Infrastructure

Status: `BUILT SELF-TESTED · PROVISIONAL · NOT OWNER-RATIFIED`

This directory is the smallest infrastructure-as-code surface required to give
Soveraeign requirement work a reproducible local custody boundary. It declares
the node envelope as data and uses a dependency-free planner to materialize and
verify it.

It does not select a cloud, container runtime, orchestrator, HTTP framework,
queue, graph database, identity provider, or model provider. Those remain
unearned until a conformance case requires them.

## Operations

```bash
python scripts/infrastructure.py validate
python scripts/infrastructure.py plan --root /path/to/node
python scripts/infrastructure.py apply --root /path/to/node
python scripts/infrastructure.py verify --root /path/to/node
```

`plan` is observation-only. `apply` may create an empty node root and its
declared directories, then writes an attributable manifest receipt. It refuses
to adopt a non-empty unmanaged root. Reapplying the same manifest is
idempotent. Concurrent applies are fenced by an exclusive local lock. `verify`
detects missing paths, symlinks, incomplete applies, receipt drift, and unsafe
permissions.

No destroy operation is supplied: authoritative state and payload custody must
not become deletable merely because a provisioning tool created their
directories.

## Phase-I envelope

`phase-i.local.json` declares:

- local custody with no required network or provider;
- separate record, payload, projection, receipt, and work paths;
- external effects refused;
- projections explicitly non-authoritative;
- private owner-only filesystem permissions.

The manifest is infrastructure configuration, not an authority grant or an
operational System of Record.
