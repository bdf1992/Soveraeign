# 0051 · Root, Kernel, and the Node Surface

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

This clarification follows the Gateway vertical work in PR #87 and the cleanup of
`CLASSIFICATION.md`, `services/README.md`, the node/federation contracts, and the Kernel
transition tooling. It does not ratify that vocabulary by being written. It proposes one
consistent reading for owner acceptance and makes the contradictions it replaces explicit.

## Problem

Three useful ideas had begun to collapse into one another:

1. the **Root** was being spoken of as though it were the whole Node or as though roots crossed
   during federation;
2. the **Kernel** was being spoken of as though `contracts/kernel-transitions.json` were the
   whole Kernel rather than one executable projection of it; and
3. `decisions/0039-the-node-surface.md` used **node surface** to mean the Console's channel,
   thread, and post experience even though Gateway ingress, federation crossings, and public
   projections are also boundaries through which the Node is addressed.

Those readings cannot all remain true if the architecture is to compose cleanly.

## Proposed clarification

### 1. Root is the local settlement point

A **Root** is the irreducible local settlement locus for one Node. In the current reference
node it is realized by `seat:root`, but Root is the semantic role and the seat record is its
current representation.

Root is not a structural level between Node and Service. Root is not the whole Node. It does
not acquire service state, runtime state, or transport behavior merely because final local
judgement can settle there.

Geometrically, Root is the **point**.

### 2. Kernel is the available grammar, not the point

The **Shared Kernel** is the available grammar under which Nodes, services, operations, and
crossings are legal. It comprises:

- **typology** — what kinds may exist;
- **topology** — how those kinds may relate;
- **traversal** — which paths and transitions through those relations are admissible; and
- **invariants** — distinctions that may never collapse merely because an implementation can
  represent them the same way.

`SPEC.md` is already the principal stack-neutral logical source for this grammar: it fixes
logical objects, roles, states, transitions, predicates, receipts, and refusal behavior while
refusing storage, language, process, transport, and provider choices.

`CLASSIFICATION.md` proposes the canonical names used to read that grammar. Schemas, tables,
fixtures, and checkers are machine-readable **projections** of particular Kernel concerns.
They do not become the whole Kernel by being executable.

In particular, `contracts/kernel-transitions.json` and `scripts/sov_kernel.py` are the current
**traversal projection** of the Kernel's transition contract. Passing that projection proves
transition correspondence, not completeness of Kernel typology or topology.

### 3. Construction is Root → Vertical → Horizontal → Surface → Node

This is a construction view, not a replacement for the structural scale
`System > Federation > Node > Service > Component`.

- **Root** — local settlement point.
- **Vertical** — one operation carried end to end through the Kernel and closed on durable
  evidence: request, resolution, authority, execution, terminal receipt.
- **Horizontal** — multiple service-owned Verticals composed through shared node-local
  resolution, authority, record, and routing semantics.
- **Surface** — the addressable actor- and crossing-facing boundary of that composition.
- **Node** — the filled locally sovereign operating volume: Root, durable record, services,
  runtime/custody, history, and crossing policy bounded by that Surface.

The geometric mnemonic is:

`point -> closed path -> extent -> sphere -> ball`

Kernel is not another item in that sequence. Kernel governs which kinds of point, path,
relation, boundary, and traversal are admissible throughout it.

### 4. Node Surface is broader than Console

This clarifies, rather than erases, Decision 0039's useful product claim.

The Console's channel/thread/post experience is the Node's **primary operator surface** for
human and model participants. It is not the entire Node Surface.

The Node Surface is the union of declared boundary realizations, including at least:

- **operator surface** — Console and Human/Model Bindings;
- **service ingress surface** — Gateway resolving and carrying declared `sov://` operations;
- **federation crossing surface** — governed offers between independently sovereign Nodes; and
- **public projection surface** — read-only/public views derived from local authoritative
  records when such publication is admitted.

No single service owns the semantic Node Surface merely because it realizes one part of it.
A process, listener, ingress controller, or UI likewise does not become the Surface by hosting
or rendering it.

### 5. Surfaces cross; Roots settle locally

A federation crossing is between Nodes at their Surfaces. `from_node` and `to_node` are the
crossing endpoints. Seats carried on the crossing are attribution, not transported local
membership or authority.

For an inbound offer, the receiving Node:

1. receives the offer at its Surface;
2. interprets it under its own Kernel;
3. admits or refuses it under its own local authority; and
4. settles its local side against its own Root.

The sending Root never becomes authority in the receiving Node. The receiving Root does not
travel back across the crossing. Standing at the sender is evidence about somewhere else and
cannot arrive above `RECORDED` locally.

This is the intended reading of the existing federation schema and checker; their executable
shape already uses Node endpoints and local Root settlement.

## Consequences for existing decisions and code

- `decisions/0039-the-node-surface.md`, claim 1, is read as promoting Console to the **primary
  operator surface**, not as assigning the entire semantic Node Surface to Console.
- `decisions/0019-kernel-transition-contract.md` remains valid as the transition/traversal
  contract. It is not a claim that the transition table exhausts the Shared Kernel.
- `decisions/0020-owner-seat-topology.md` continues to define the local seat topology. A root
  seat is the current representation of Root settlement, not Node identity itself.
- `contracts/node-identity.schema.json` remains identity-only; naming a peer Root imports no
  grant or capability.
- `contracts/federation-crossing.schema.json` remains Node-to-Node and carries an origin seat
  only for attribution.
- Gateway, Console, Registry, and future federation/public bindings remain sibling boundary
  participants. None becomes a god-service for the Node.

## Defeating cases

This clarification is defeated if evidence requires any of the following:

- a peer Root must become a seat or authority source inside the receiving Node for federation to
  work;
- a crossing must use Root identifiers rather than Node identifiers as its endpoints;
- Console must own Gateway or federation semantics in order to remain the primary operator
  experience;
- Gateway must own domain state in order to compose multiple service Verticals;
- a Node can be defined solely by a process/container without a distinct local Root, durable
  record, and governed Surface;
- the Kernel can be fully reconstructed from the transition table while ignoring the logical
  kinds, relations, or invariants that make those transitions meaningful; or
- two Nodes require one shared settlement Root in order to disagree without corrupting either
  local record.

## Evidence expected before acceptance

The vocabulary earns acceptance when the implementation can show, without special cases:

1. a second Asset operation crosses the same Gateway Vertical;
2. an operation owned by a second service family crosses the same Gateway, demonstrating
   Horizontal composition;
3. a Node composition root assembles identity, Root topology, Record, authority, Registry,
   Gateway, and service-owned routes without itself gaining domain authority;
4. a Node can describe its own Surface from authoritative/projection sources; and
5. federation fixtures continue to prove Node-to-Node crossing with local Root settlement and
   no authority import.

Until then this is proposed vocabulary and a construction hypothesis backed by the current
contracts, not an accepted architectural law.
