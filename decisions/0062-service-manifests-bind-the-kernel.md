# 0062 · Service manifests bind the Kernel

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

This decision follows `0051-root-kernel-and-node-surface.md` and the first Gateway
Vertical in PR #87. It proposes the mechanism by which distributed services participate
in one Shared Kernel without turning the Kernel into a service, shared runtime object,
or privileged network hop.

## Problem

The repository already requires every service manifest to declare what record kinds it
owns, which Kernel contracts it uses, which operations it exposes, which named Kernel
transitions some operations realize, which ports it crosses, and which shortcuts it
forbids. That is already most of a semantic binding, but nothing named it as such or
compiled all services together.

Without a common composition check, a distributed system can drift unevenly: one service
can privately reinterpret authority, another can claim a record kind a sibling owns, a
third can expose an endpoint whose identity no longer matches its operation, and every
individual file can remain locally well formed.

## Proposed ruling

### 1. A service manifest is the authored Kernel Binding for that service

No second hand-authored `kernel-binding.json` is introduced. The existing
`services/<service>/contracts/service.json` is the service's declaration of how it
participates in the Shared Kernel.

That binding states, using the fields already present today:

- `owns` — the record kinds for which the service is the domain owner;
- `uses_kernel_contracts` — the Kernel paradigms the service binds;
- `operations` — the service-owned operation surface;
- `kernel_transition` — where an operation realizes one currently named Kernel traversal;
- `ports` and `depends_on` — declared relationships to other participants/boundaries; and
- `forbids` — shortcuts the participant explicitly refuses to acquire.

A manifest still grants nothing and opens nothing. Binding is semantic participation,
not authority or reachability.

### 2. Paradigms index coherent Kernel definitions

`contracts/kernel-paradigms.json` resolves the seven stable names already used in
`uses_kernel_contracts` to their governing repository sources.

A **Kernel paradigm** is a coherent slice of the available Kernel grammar: some
combination of typology, topology, traversal, and invariants. The registry indexes those
definitions for humans and machines; the source files remain authoritative.

This introduces no new service requirement merely by naming the existing contract ids as
paradigms. The registry is `PROPOSED`, and its ids are checked against the enum already
carried by `service-manifest.schema.json` so the two machine indexes cannot silently
diverge.

### 3. The Kernel Closure is derived, never authored

`scripts/sovkernel/kernel_binding.py` rebuilds a Node-wide closure from:

- every discovered service manifest;
- `contracts/kernel-paradigms.json`; and
- `contracts/kernel-transitions.json`.

`python scripts/sov_kernel.py closure` emits that closure as JSON. It is a projection for
discovery, agent context, conformance, Registry projection, and later Node description.
It is not a System of Record and carries an input-state digest so stale output is
recognizable.

The closure currently exposes:

- every service participant and its standing;
- every declared record kind and its owning service(s);
- every Kernel paradigm and the services that bind it;
- every service operation and logical endpoint;
- every named Kernel transition and the operations that realize it; and
- every operation that currently declares no named Kernel transition.

An unmapped operation remains visible rather than receiving an invented transition. This
decision does **not** yet require every service operation to map to one transition.

### 4. Binding and parity are different evidence

Kernel Binding asks: **does the participant declare itself coherently in the shared
semantic grammar?**

`contracts/kernel-parity.json` asks: **does an executable/declarative participant actually
make the same decision as a Kernel rule on a driven fact?**

A service can have a structurally sound binding and still fail executable parity. Passing
one never implies the other.

## Distributed equality invariant

Every service gets the same relationship to the Kernel:

`Kernel grammar -> service manifest binding -> service implementation`

No service receives a privileged private Kernel, and no central Kernel process becomes a
network dependency. Implementations may differ by language, process, storage, or runtime,
but their semantic participation is compiled through the same manifest contract.

The binding compiler therefore refuses cross-participant contradictions that a per-file
schema cannot see, including:

- service-directory / `service_id` identity drift;
- two services claiming ownership of the same record kind;
- an operation acting on or additionally reading a record kind its service does not own;
- a logical endpoint that is not exactly `sov://<service>/<operation>`;
- duplicate logical endpoints or operations;
- a service privately naming a Kernel paradigm not present in the paradigm registry;
- an operation naming a transition absent from the Kernel traversal projection; and
- an operation mapping to a transition while its service does not bind the `operation`
  paradigm.

## AI-native consequence

An agent should not need to infer the Node's semantic architecture by reading every
service implementation. It can ask for the derived closure and traverse:

`paradigm -> participant -> operation -> subject/type -> transition -> endpoint`

or the reverse path:

`type -> owning service -> operations -> bound paradigms -> governing sources`.

Because every edge resolves to authored inputs, the closure is useful compression without
becoming a second authority source.

## Relationship to crossings

Kernel Binding does not own crossings. It makes crossing roles legible.

- Kernel paradigms define what a crossing, authority check, receipt, and settlement may
  mean.
- Gateway or another Surface participant carries its part of a crossing.
- The destination service owns its domain operation and state.
- Record/evidence participants preserve the appropriate account.
- Root settles local judgement where the governing transition requires it.

The closure lets a reader see those participant obligations without collapsing them into
one god-service.

## Defeating cases

This proposal is defeated if evidence shows that:

- a second authored binding file is necessary to state service participation without
  duplicating the manifest;
- a valid Node requires a central Kernel runtime service through which every operation must
  synchronously pass;
- two services must legitimately own the same record kind without a more precise ownership
  relation;
- a service must privately extend Kernel typology/topology without that extension becoming a
  Kernel proposal visible to other participants;
- the closure cannot be deterministically rebuilt from its declared inputs; or
- agents require implementation-specific knowledge for ordinary semantic discovery that the
  closure claims to provide.

## Evidence expected before acceptance

1. the current repository's service manifests compile with no cross-binding contradiction;
2. synthetic defeating mutations are rejected for ownership, identity, endpoint, paradigm,
   and transition drift;
3. the derived closure satisfies `contracts/kernel-closure.schema.json`;
4. every paradigm source address resolves and the service-manifest paradigm vocabulary cannot
   drift from the registry silently;
5. both supported Python construction lanes remain green; and
6. a later Horizontal proof can consume the closure without making it authoritative.

Until accepted, this is a proposed mechanism and vocabulary reading. Tests establish evidence,
not standing.
