# 0015 · Customer-owned local and Kubernetes deployment pattern

Status: `ARCHITECTURE REVIEW CANDIDATE · TOPOLOGY ACCEPTANCE PENDING · O14 OPEN`

## Context

The local custody ground in decision 0014 provides reproducible requirement
work, but it does not yet show how the same node crosses into a customer-owned
orchestrator. The next path must make Gateway, Broker, Queue, Deployment, and
Federation visible without pretending that each name has earned a distributed
product, provider, or authority role.

`ENGINEERING.md` already defines the growth triggers: transport follows a real
second-process operation; a lease-backed queue follows durable work; fencing
precedes concurrent writes; and Federation follows a two-node governed crossing.

## Proposed decision

Admit one portable, single-replica node topology with two profiles:

- local execution stays the reference ground and binds only to loopback;
- customer Kubernetes is rendered as provider-neutral JSON and is applied only
  by the customer as a separately authorized external action;
- Gateway is a policy-guarded, cluster-internal terminal-pull seam;
- Broker and Queue remain in-process and non-authoritative;
- Federation remains disabled and unexposed;
- storage mounts a pre-existing customer-owned claim; provisioning, backup,
  reclaim policy, and deletion remain outside this renderer;
- the renderer loads the exact local custody manifest, embeds its content,
  canonical digest, and five-path mapping, and pins that digest to the pod;
- a non-root init container gates runtime startup on custody verification or an
  explicitly selected empty-root initialization policy;
- activation proves UID/GID `65532` ownership and writability, establishes a
  persistent custody identity, and appends a machine-readable receipt;
- the rendered pod runs without a service-account token, root privileges,
  writable root filesystem, or Linux capabilities;
- default network traffic is denied and the Gateway admits only explicitly
  labelled client namespaces;
- images must be pinned by digest;
- no Ingress, public Service, Secret, cloud resource, Helm chart, operator,
  cluster mutation, or destroy operation is introduced.

This is a deployment compiler and safety contract, not a production runtime,
container image, queue implementation, federation protocol, topology
acceptance, or O2/O14 ratification.

## Consequences

Local and Kubernetes now share one role map and a digest-bound custody
activation contract. A customer may inspect a deterministic Kubernetes bundle without the
repository contacting a cluster. Each role can later be extracted behind its
existing semantic boundary only after its observed trigger and defeating case
exist.

The single replica is intentional. Horizontal scale would otherwise create a
multi-writer claim that the current local record and filesystem custody have
not earned.

The Service's port 8080 remains a topology declaration, not an evidenced
runtime listener. The eventual pinned-image contract must establish an
entrypoint, listener, startup/readiness probes, and health semantics before this
can be called deployable. That gap does not block focused architecture review.

## Defeating cases

- a mutable image tag or unpinned image is accepted;
- a public Service or Ingress is rendered;
- more than one node replica is admitted before write fencing evidence;
- Broker or Queue claims authority or becomes the System of Record;
- Federation is exposed before the two-node crossing contract;
- cluster credentials or Kubernetes Secrets enter the bundle;
- rendering contacts or mutates a cluster;
- the pod carries only a custody filename rather than the exact manifest,
  digest, and path mapping;
- an empty, drifted, incomplete, or UID/GID-unwritable claim starts the runtime;
- restart changes custody identity or activation succeeds without a receipt;
- the Kubernetes profile replaces local custody as the reference ground.
