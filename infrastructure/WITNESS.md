# Infrastructure witness protocol

Status: `BUILT PROTOCOL · NOT YET INDEPENDENTLY EXECUTED`

This protocol lets a fresh Red participant reproduce the local custody,
custody-activation, and customer-Kubernetes claims without importing any of
those implementation modules. It
produces a candidate receipt; it cannot grant itself `WITNESSED` standing and
cannot ratify O2 or O14.

## Witness boundary

The witness must use a clean checkout at the exact reviewed commit, must not be
the author of the implementation under review, and must declare a stable
witness identity. Bdo decides whether that identity and observation are
sufficiently independent.

Run from the repository root:

```bash
python scripts/witness_infrastructure.py \
  --witness-id <fresh-red-identity> \
  --expected-commit "$(git rev-parse HEAD)" \
  --declare-independent \
  --output /tmp/soveraeign-infrastructure-witness.json
```

The output must remain outside the repository. Review it, then attach the exact
file to issues #37 and #39 or record its content digest and durable evidence
address. Do not copy a passing receipt into `STATUS.yaml` as owner judgement.

## Observed cases

The runner independently checks:

- clean checkout and exact commit identity;
- the complete repository verifier;
- observation-only local planning;
- local custody paths, permissions, and manifest-digest receipt;
- default refusal of an empty PVC-shaped root, explicit initialization,
  machine-readable activation receipt, and custody identity continuity across
  restart;
- refusal of wrong manifest digest, missing paths, unwritable ownership, and a
  stale identity or infrastructure receipt through the defeating fixtures;
- refusal of unmanaged roots and observation of receipt, manifest, permission,
  and symlink drift plus the real concurrent-apply fixture;
- a rendered Kubernetes bundle with a pinned image, customer-owned claim,
  single writer, hardened pod, ClusterIP Gateway, disabled Federation,
  observe-only patrol, and default-deny egress;
- exact embedding of `phase-i.local.json`, its independently computed digest,
  its five-path mapping, the UID/GID `65532` activation gate, and activation
  receipt location;
- refusal of mutable images, invalid claims, public Services, extra replicas,
  and premature Federation;
- refusal of a force-added ignored synthetic secret.

The runner records digests of command output rather than copying full logs into
the receipt. It performs only `RECORD_LOCAL` effects in temporary directories.

## What it does not establish

- cryptographic proof of witness identity;
- owner ratification;
- a live cluster deployment;
- production fitness;
- an image entrypoint, listener, readiness probe, startup contract, or health
  semantics for port 8080;
- Gateway operation safety;
- Broker, Queue, or Federation activation.

The Gateway remains unearned while Asset Service authority, receipt,
independent-observation, and two-binding gaps remain open.

Passing this protocol repairs the local-to-Kubernetes custody seam. It still
does not accept issue #39 or ratify O14; Bdo retains both judgements.
