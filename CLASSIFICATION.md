# Classification Contract

Status: `PROPOSED CANONICAL VOCABULARY`

This contract keeps architectural scale, execution roles, information roles,
standing, interfaces, and deployment choices from being mistaken for one
another. It normalizes the source documents without changing their immutable
historical wording.

## Structural scale

| Term | Meaning | Identity test |
| --- | --- | --- |
| **System** | The complete working product: shared record, operation, authority, interfaces, and history | Is this the whole environment humans and models jointly operate? |
| **Federation** | Two or more sovereign nodes joined by governed crossings | Is a distinct second node actually participating? |
| **Node** | A locally sovereign operating instance | Does it own a durable record, operate locally, and govern crossings? |
| **Service** | A bounded enterprise capability inside a node | Does it own a distinct domain lifecycle and expose a contract? |
| **Component** | A replaceable implementation part inside a service | Can it be replaced without changing the service's semantic identity? |

`Subsystem` is the generic architectural class. Concrete executable subsystems
are named `<Domain> Service`. It is not a separate level between service and
component.

A process, container, function, or microservice is a deployment choice. It does
not acquire semantic identity, authority, or sovereignty from its deployment
boundary.

## Cross-cutting foundations

- **Shared kernel** enforces gates, standing, typed authority, transitions,
  observation, settlement, receipts, and retraction across services.
- **Runtime** is the execution contract that makes computation, operator,
  inputs, configuration, authority, resources, state, time, observation, and
  effects one attributable event. It is not merely a lower architecture box.
- **Record substrate** preserves addressed sources, immutable payloads,
  revisioned records, provenance, and reconstruction authority.
- **Atlas, Gauge, definition, pedagogy, and observation** are concerns or
  capabilities until evidence gives one an independently useful service
  boundary.

## Participation and boundary roles

| Term | Use |
| --- | --- |
| **Operator** | A human or model acting in the shared system |
| **Actor** | The attributed identity responsible for an action |
| **Agent** | An operator selecting or requesting actions within granted authority |
| **Worker** | An executor assigned a scoped, leased operation; its report is not observation |
| **Witness** | An independent verifier depositing evidence |
| **Interface** | A declared contract or operating surface |
| **Binding** | A concrete realization of an interface for an operator type |
| **Port** | An internal seam whose implementation may be supplied or visibly unconfigured |
| **Adapter** | Translation between Soveraeign and a named external system |
| **Projection** | A rebuildable derived view that never becomes authoritative by convenience |

## Information roles

| Term | Meaning |
| --- | --- |
| **Referent** | The real thing a representation addresses |
| **Asset** | A governed enterprise identity with a version history |
| **Payload** | Exact bytes under custody |
| **Source** | The addressed origin read or transformed |
| **Asset version** | An immutable state of an asset |
| **Reading** | An interpretation that leaves its source unchanged |
| **View** | A presentation or projection of authoritative records |
| **Recording** | A deposited result of a declared derivation |
| **Proposal** | An attributed claim without ratified standing |
| **Receipt** | The record returned by an attempted crossing or operation |
| **Observation** | Independent evidence of what occurred |
| **Retraction** | A counter-record that changes effective standing without erasing history |

An asset is not its payload. Distinct assets may intentionally reference the
same bytes while preserving distinct identity, use, permissions, and history.

## Standing and outcomes

Historical standing is orthogonal to information role:

`RECORDED → ADMITTED → RATIFIED → EFFECTIVE`

The transition is not automatic. Each step requires its declared gate and
receipt. Ratification remains historical even when a later observation changes
current effectiveness.

Event outcome is recorded separately:

`ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED`

`COUNTERED` is an event outcome: it prevents an earlier effective record from
continuing to condition current operation while preserving the act, standing,
and counter-record. It is not a fifth authority standing.

## Initial service map

The **Asset Service** owns asset identity, immutable versions, payload custody,
source and derivation lineage, technical metadata, relationships, derivatives,
discovery, and asset-use records.

The **Proofing Service** owns proofing sessions, review rounds, annotations,
version comparisons, reviewer assignments, requested changes, approval or
rejection proposals, decisions, and proofing history. It references exact Asset
Service version identifiers and does not create a second authoritative asset.

Both are sibling services inside one local node. Both use the shared kernel.
Neither is independently a federation, node, platform, or complete product.

## Naming rules

- whole product: `Soveraeign System`
- sovereign participant: `Soveraeign Node`
- bounded capability: `<Domain> Service`
- internal implementation: `<Purpose> Component`
- external translation: `<System> Adapter`
- operator realization: `<Operator> Binding`
- rebuildable read model: `<Purpose> Projection`
- scoped executor: `<Purpose> Worker`
- declared optional boundary: `<Purpose> Port`

Reserve `platform` for the federated product context. Reserve `engine` for a
specific algorithmic component. Do not create a new architectural class merely
to make a component sound substantial.

## Source and policy boundary

System identity, shared human/model operation, local sovereign nodes,
federation at node two, stack-neutral logical specification, runtime semantics,
and the distinction between authoritative records and projections are grounded
in `ANCHOR.md`, `SUBSTRATE.md`, `PRODUCT(1).md`, and `PRD-PRODUCT(1).md`.

The concrete `Service`/`Component` normalization and the initial Asset/Proofing
split are new proposed policy. Bdo's ratification is required before this file
becomes authoritative vocabulary.
