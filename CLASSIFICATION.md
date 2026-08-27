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

### Root and local settlement

**Root** is not another level in the structural scale. It is the irreducible
local settlement locus for one Node: the point against which that Node settles
the judgement and verification rights its topology actually assigns there. A
Node identity names the root seat that settles for it; Root and Node are not
synonyms.

A Root does not cross into another Node. A governed crossing relates Node
surfaces. The receiving Node resolves and admits what crossed under its own
Kernel and settles its side against its own Root. A peer root's identity or
evidence may be represented locally, but that never imports the peer root's
authority.

## Ownership profiles and model practice

`Personal`, `team`, and `enterprise` are ownership and operating profiles of a
node. They do not create new structural levels:

- **Personal node** — one person owns and administers the local sovereign node.
- **Team node** — several people operate one node through typed authority.
- **Enterprise node** — an organization governs one or more nodes and their
  crossings.

**BYOM** is a model-selection practice, not a service or node type. A **Model
Binding** realizes the operator interface for a configured model. A **Model
Adapter** translates that binding to a named local runtime or remote provider.
Neither owns authoritative state or gains authority from provider credentials.

## Cross-cutting foundations

- **Shared Kernel** is the available typology, topology, traversal, and invariant
  grammar used by every Node, Service, operation, and crossing. It defines what
  kinds may exist, how those kinds may relate, which transitions are legal, and
  which distinctions may never collapse. Its executable enforcement includes
  gates, standing, typed authority, transitions, observation, settlement,
  receipts, and retraction. It is neither a structural scale nor a deployment
  unit.
- **Runtime** is the execution contract that makes computation, operator,
  inputs, configuration, authority, resources, state, time, observation, and
  effects one attributable event. It is not merely a lower architecture box.
- **Record substrate** preserves addressed sources, immutable payloads,
  revisioned records, provenance, and reconstruction authority.
- **Atlas, Gauge, definition, pedagogy, and observation** are capabilities
  until evidence gives one an independently useful service boundary.

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

## Operating-loop roles and stances

`SDLC.md` owns the loop's semantics, gates, and derivations; this contract
owns only the terms.

| Term | Use |
| --- | --- |
| **Concern** | A registered unit of monitored work with an owning domain, governing contract, standing, next gate, and effect envelope |
| **Controller** | The operator holding the loop's Control tier; never ratifies judgement, may machine-ratify verification-typed claims only under explicit delegation |
| **Orchestrator** | The operator holding the loop's Orchestration tier for one launched operation |

Stances are typed hands an operator holds under grant, never a named person,
model, or provider:

| Stance | Dyad | Use |
| --- | --- | --- |
| `LEFT` | Authority | Synthesis: inspect, compare, draft, implement, propose |
| `RIGHT` | Authority | Judgement: intent, naming, ratification, phase gates |
| `BLUE` | Verification | Construction: build the positive path and its declared positive and defeating cases |
| `RED` | Verification | Adversarial witnessing: seek undeclared defeats of the built artifact |

Combination outcomes name receipts and derived state, never a stance an
operator holds and never a new standing:

| Outcome | Combination | Names |
| --- | --- | --- |
| `PURPLE` | `RED` + `BLUE` | The settled verification engagement receipt |
| `JOINED` | `LEFT` + `RIGHT` | The ratification receipt over a synthesis proposal |
| `GREEN` | `PURPLE` + `JOINED` | The derived go-state of a concern at its current gate |

`RED`/`BLUE` are engagement stances; `positive` and `defeating` remain the
artifact-level terms. `JOINED` names a combination receipt; `RATIFIED`
remains the standing term.

## Information roles

| Term | Meaning |
| --- | --- |
| **Referent** | The real thing a representation addresses |
| **Asset** | A governed enterprise identity with a version history |
| **Payload** | Exact bytes under custody |
| **Source** | The addressed origin read or transformed |
| **Asset version** | An immutable state of an asset |
| **Asset type** | A declared schema an asset is held to, including its constituent roles |
| **Asset part** | A constituent identity within an asset, held apart from anything that expresses it |
| **Asset part version** | An immutable content state of one constituent |
| **Placement** | Where a constituent sits in one asset version |
| **Source observation** | An attributed record that a source carried a content state |
| **Reading** | An interpretation that leaves its source unchanged |
| **View** | A presentation or projection of authoritative records |
| **Recording** | A deposited result of a declared derivation |
| **Proposal** | An attributed claim without ratified standing |
| **Receipt** | The record returned by an attempted crossing or operation |
| **Observation** | Independent evidence of what occurred |
| **Retraction** | A counter-record that changes effective standing without erasing history |
| **Collection type** | A declared schema a collection holds its members to |
| **Asset collection** | A named, typed, curated set of assets |
| **Collection membership** | One asset filed into one collection by one actor |

An asset is not its payload. Distinct assets may intentionally reference the
same bytes while preserving distinct identity, use, permissions, and history.

An asset part is not a file. A filename, a logical path, a locator and a source
address are placement or observation about a part version; none of them is the
part's identity. How a payload is stored - one blob, a manifest of chunks, or a
later content-addressed form - sits below the asset contract and is not asset
vocabulary. `SPEC.md` owns the objects; this table owns only the terms.

An **asset collection** is not a **projection collection**. The first is curated:
somebody decided each member belongs, and only a counter-record undoes it. The
second, owned by the Asset Projection Service below, is a declared retrieval
scope that is rebuilt rather than decided. Machine surfaces always carry the
qualified name; seam S22 holds the collision open.

## Record standing, artifact lifecycle, and outcomes

Operational record standing is orthogonal to information role:

`RECORDED → ADMITTED → RATIFIED → EFFECTIVE`

The transition is not automatic. Each step requires its declared gate and
receipt. Ratification remains historical even when a later observation changes
current effectiveness.

Repository requirements and concerns use a separate artifact lifecycle:

`OPEN → BUILT → WITNESSED → RATIFIED`

The shared word `RATIFIED` names a typed authority decision, but the authority
and carrier differ. An operational record may be ratified under a matching live
grant; a design artifact or concern requires Bdo's judgement. Advancing one
never advances the other implicitly.

Event outcome is recorded separately:

`ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED`

`COUNTERED` is an event outcome: it prevents an earlier effective record from
continuing to condition current operation while preserving the act, standing,
and counter-record. It is not a fifth authority standing.

## Initial service map

The **Asset Service** owns asset identity, immutable versions, payload custody,
source and derivation lineage, technical metadata, relationships, derivatives,
discovery, asset-use records, and the organizational layer over them: collection
types, asset collections, membership, and the conformance read that judges each
member against the schema its type declares
(`decisions/0063-asset-collections-and-the-librarian.md`).

The **Proofing Service** owns proofing sessions, review rounds, annotations,
version comparisons, reviewer assignments, requested changes, approval or
rejection proposals, decisions, and proofing history. It references exact Asset
Service version identifiers and does not create a second authoritative asset.

The **Console Service** owns operator sessions, channels, threads, posts,
notifications, judgement requests, operator settings, and declared dashboard
and activity projections. It reads sibling-service events and receipts through
a declared crossing and does not hold, infer, or delegate authority.

The **Asset Projection Service** owns projection collections, text, graph,
and vector configurations, index declarations, builds, retrieval receipts,
context packages, and fidelity observations over asset records. It reads the
Asset Service through a declared crossing; everything it holds is a
rebuildable projection and never an authoritative record.

All four are sibling services inside one local node. All use the shared
Kernel. None is independently a federation, node, platform, or complete
product.

## Two requirement ladders

Bare `Requirement` means the **product** ladder. Ruled by Bdo, 2026-08-24
(`decisions/0052`), because the `PROD-I-*` meaning is older, owner-visible, and already
load-bearing in the attribution spine.

| Term | Means | Identity test |
| --- | --- | --- |
| **ProductRequirement** | Something the product or the current phase must prove. `PRD.md`'s `PROD-I-*`. | Would failing it mean the phase is not done? |
| **CompetenceRequirement** | An obligation a skill, capability or competence relation carries — repository verification, independent observation, and their kin. | Would failing it mean a participant is not qualified to act? |

`PROD-I-*` is **not** renamed and its identity in `PRD.md` is unchanged. In a typed graph
either term may be written out where disambiguation helps, and `ProductRequirement` is the
explicit form of the bare word.

The invariant: **no unqualified `Requirement` edge may ambiguously cross those two
ladders.** A reader following one has to know which ladder it is on before it resolves.
`OPEN-SEAMS.md` S18 records what happens when two layers share a word; this is that
failure caught before both halves exist.

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
- product obligation: `ProductRequirement`, and bare `Requirement`
- competence obligation: `CompetenceRequirement`, never bare

Reserve `platform` for the federated product context. Reserve `engine` for a
specific algorithmic component. Do not create a new architectural class merely
to make a component sound substantial.

## Source and policy boundary

System identity, shared human/model operation, local sovereign nodes,
federation at node two, stack-neutral logical specification, runtime semantics,
and the distinction between authoritative records and projections are grounded
in `ANCHOR.md`, `SUBSTRATE.md`, `PRODUCT(1).md`, and `PRD-PRODUCT(1).md`.

The concrete `Service`/`Component` normalization, the initial
Asset/Proofing/Console/Asset Projection split, the Root/Kernel construction
vocabulary, and the operating-loop role and stance vocabulary are new proposed
policy. Bdo's ratification is required before this file becomes authoritative
vocabulary.
