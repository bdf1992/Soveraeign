# Phase-I Local Infrastructure

Status: `BUILT SELF-TESTED · PROVISIONAL · NOT OWNER-RATIFIED`

This directory is the smallest infrastructure-as-code surface required to give
Soveraeign requirement work a reproducible local custody boundary. It declares
the node envelope as data and uses a dependency-free planner to materialize and
verify it.

It does not select a cloud, container runtime, HTTP framework, queue product,
graph database, identity provider, or model provider. A provisional
customer-owned Kubernetes renderer makes the deployment boundary inspectable;
it does not contact a cluster or select an ingress, operator, Helm chart, or
managed service.

## Operations

```bash
python scripts/infrastructure.py validate
python scripts/infrastructure.py plan --root /path/to/node
python scripts/infrastructure.py apply --root /path/to/node
python scripts/infrastructure.py verify --root /path/to/node
python scripts/deployment.py validate
python scripts/deployment.py plan --target local
python scripts/deployment.py plan --target customer-kubernetes
python scripts/deployment.py render --target customer-kubernetes \
  --image registry.example/soveraeign@sha256:<64-hex-digest> \
  --custody-claim customer-owned-claim
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

## Portable deployment topology

`phase-i.topology.json` carries one node shape across local and customer-owned
Kubernetes profiles. Gateway is the only rendered Service and remains
cluster-internal. Broker and Queue stay in-process and non-authoritative.
Federation stays disabled. The node stays at one replica until a concurrent
write case earns fencing or compare-and-set.

The Kubernetes command emits a JSON `List` to standard output. Kubernetes
accepts JSON directly, but applying it is deliberately an external owner action.
The repository never invokes `kubectl`. It also does not provision storage: the
customer supplies an existing claim whose storage class, backup, and reclaim
policy they control. The bundle contains no Secret, Ingress, public Service,
cloud resource, or destroy path, and requires an image pinned by digest. An
image/runtime satisfying the application contracts is not yet part of this
founding-phase repository.

## Independent witness

`WITNESS.md` defines the fresh Red protocol. Its runner imports neither
infrastructure implementation module, verifies a clean exact-commit checkout,
performs independent state and bundle inspection, exercises defeating cases,
and emits a candidate receipt outside the repository. A manual read-only GitHub
Actions workflow exposes the same procedure for an independently identified
witness. Neither the runner nor CI can promote its own output to `WITNESSED`.
