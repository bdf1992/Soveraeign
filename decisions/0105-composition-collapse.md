# 0105 · Composition collapse: the style this system is built in

Status: `OWNER-DIRECTED · PROPOSED`

Bdo asked on 2026-09-10 whether Soveraeign is programmed as an entity component
system or as object-oriented code, and proposed a style of his own: an entity
component system whose compositions collapse, under a context, into an
object-shaped template that a domain can instantiate. This record names that
style, says why neither standard style meets the need, states the rules learned
from the styles it draws on, and names the one primitive the style adds that
the repositories do not yet declare. It proposes; it ratifies nothing.

## Decision

**The style is composition collapse.** Data, relations, process and meaning are
kept as four separate kinds of record, and an object-shaped instance is a
computed projection over them, produced by a declared function that records
what it kept and what it lost.

```text
Entity      := an address; no fields, no behaviour
Component   := (entity, axis, typed record); one axis per component
Relation    := (from, type, to); a typed edge in a named graph
System      := a declared operation: axes read, preconditions, refusals,
               kernel transition, receipt
Invariant   := a distinction that may never collapse
Template    := a named pattern: the axes, relations and systems an instance
               of it carries; it names no domain

Collapse(template, context, components, relations) -> instance
    preserves  the axes the template names, verbatim
    projects   every other axis, and lists each one it dropped
    records    the digest of every source record and of the context
    standing   never higher than the weakest source it read
```

An instance is a projection under the `SPEC.md` Projection rule: rebuildable
from its sources, addressable, and never authoritative by convenience. The
template is the reusable thing. The instance is what a person or a domain
holds. The collapse is the only place the two meet, and it is a function, not a
class.

The four kinds of record are the four axes `contracts/kernel-paradigms.json`
already grades every kernel slice on: typology (what kinds exist), topology
(what may relate), traversal (which transitions are legal), invariant (what may
never collapse). This record gives the shape a name and a fifth rule for how the
four fold into a usable object without one becoming another.

## Why neither standard style is enough

Object-oriented design gives a thing its identity from its class. Inheritance
fuses typology with topology: `is-a` fixes what a thing is and where it sits in
one stroke, and a subclass silently inherits reach its parent had. Behaviour
lives inside the object, so the relation graph cannot be drawn from the data and
must be read out of code. State mutates in place, which is the opposite of an
append-preserving record. The lesson `decisions/0104` recorded, that a witness
could not witness a controller because every statement had to travel the
ownership tree, is an inheritance defect: hierarchy inferred from structure.

An entity component system fixes the first half. Entities are addresses,
components are flat data on one axis each, systems are the only behaviour, and
composition replaces inheritance. It has no meaning layer. A system fires on
component match with no grant, no refusal and no receipt; any system may read
any component, so there are no boundaries; the world mutates in place; relations
are second-class or absent; and which composition is legal is implicit in
whatever happens to match. An ECS can say what a thing is made of and cannot say
what it is allowed to do, who said so, or whether that claim was witnessed.

Data-driven design moves declarations into tables and files, which this
repository already does, and then hides the meaning in the interpreter that
reads them. A table with no invariants is configuration, not a model.

The actor model gives identity and a mailbox and hides behaviour again, and its
supervision trees invite the same hierarchy inference that `decisions/0104`
refused.

Each of them solves one separation and loses another. The need here is all
four at once, drawn as data and executed from the same data, with standing and
authority carried alongside the composition rather than inferred from it.

## What the style keeps from each

| From | Kept | Refused |
| --- | --- | --- |
| ECS | entity as address; one axis per component; behaviour only in declared systems | firing on match; unbounded reads; in-place worlds |
| OOP | the template as the unit of reuse; an instance with a stable surface a person can hold | identity from class; inheritance; behaviour hidden in state |
| Data-driven | every declaration in JSON and JSON Schema; code as host | meaning hidden in the interpreter |
| Relational and graph models | typed relations in separate named graphs | one graph standing in for all of them |
| This repository's own lessons | `RELATION_GRANTS_NOTHING`; projections rebuildable; `CONTRACT.md` C4 standing does not collapse; one fact, one producer | authority inferred from interaction, deployment or success |

## Where the style is already practised

The four repositories already carry this shape. What they lack is the name and
the fifth rule.

| Repository | Entity, components, relations, systems | The collapse, hand-built |
| --- | --- | --- |
| Soveraeign | seats, manifests, the event envelope, typed seat edges, kernel transitions | `contracts/fixtures/capability-map.reference.json` derived from eleven manifests with an input digest; a seat's occupant |
| schematically | Point, Path, Plane; Form with dimension, body, frame, regions kept apart from content and presentation; ports with direction, access and authority as three independent axes | Component: a typed Plane with a Form and behaviour |
| bdos | a core's four kernel axes, role, activation, control and reach, as four fields | `map.yaml`, generated from the cores, never authored |
| ide | `architecture/TYPOLOGY.md` and `TOPOLOGY.md`; surface syntax elaborated to a canonical program before it gets standing | the admitted semantic program |

The Python under `services/` is host code. `AssetService` composes seven
collaborators and holds no claim the manifest does not state. Delete every class
and the semantics survive in the contracts; delete the contracts and the classes
mean nothing. That is the test for host code under this style.

## Rules

1. **An entity is an address and nothing else.** Fields and behaviour on the
   entity itself are a class in disguise.
2. **One component, one axis.** Direction, access and authority are three
   components, never three fields of one. An axis is named in a contract before
   a component uses it.
3. **Relations are typed edges in named graphs.** No hierarchy is inferred from
   an edge, from co-location, or from interaction. A relation is a route and
   never a grant.
4. **A system is a declared operation.** It names the axes it reads, its
   preconditions, its refusals, the kernel transition it performs, and it emits
   a receipt. Nothing fires because components happen to match.
5. **A collapse is a declared, deterministic function.** It names its template
   and its context, digests every source, preserves the template's axes
   verbatim, lists every axis it projected, and yields an instance whose
   standing is no higher than its weakest source.
6. **An instance is a projection.** Deleting every instance and rebuilding from
   components and relations must reproduce it byte for byte. An instance that
   cannot be rebuilt is a hidden component.
7. **A template names no domain.** A domain instance is the same template
   collapsed under domain context. Domain-universal means one template, many
   contexts, and never a template per domain.
8. **Code is host.** A class, module or process carries no claim a contract
   does not state, and deployment confers no identity (`CLASSIFICATION.md`).
9. **Diagram equals data.** A view renders components and relations that
   records carry, and a drawn edge no record carries is stale
   (`diagrams/README.md`). Under this rule a diagram is an executable input, not
   a picture of one.
10. **Invariants are checked from outside their fixtures.** Every rule above
    has a defeating case, and the checker that presses it did not write the
    fixture it presses.

## What this adds that does not yet exist

Every collapse named above is hand-built and unnamed, so none has a contract,
none has a defeating fixture, and none states which axes it was allowed to
lose. The style adds one primitive: a collapse contract.

Proposed shape, for a later concern to build and not adopted here:

```text
contracts/collapse.schema.json
    collapse_id, template_id, context (addressed), sources[] (address + digest),
    preserved_axes[], projected_axes[], instance_address, instance_digest,
    standing (derived), produced_by, produced_at
```

Defeating fixtures that concern owes before the schema is admitted: a collapse
that raises standing above a source; one that drops an axis without listing it;
one whose instance carries a relation no source graph holds; one whose template
names a domain; one whose instance cannot be rebuilt from its sources.

The capability map derivation is the first candidate to be rewritten as a
declared collapse, because it already digests its inputs and already refuses
staleness.

## Workflow authoring under this style

A schematically document is a composition: Components, Wires, boundaries and
Ports on declared axes. A workflow is that composition collapsed, under a
context that names the actor, the grant, the diagram revision and the inputs
that may cross, into an operation plan
(`contracts/operation-plan.schema.json`). The ide repository already performs
the same move from surface syntax to canonical program, and its rule carries
over: a model may propose new expressions of existing meaning and may not
silently create new meaning. `ROADMAP.md` names the adapter contract that move
needs, and this record does not build it.

## What would defeat this

A composition the four repositories genuinely need that cannot be expressed as
entities, single-axis components, typed relations and declared systems, or a
useful instance whose reconstruction from its sources necessarily loses
information no axis could carry. Either would mean the style is incomplete
rather than a naming exercise.

## What still waits on Bdo

- **Naming.** "Composition collapse" is the name this record proposes; the
  style's public name is his.
- **Adoption across four repositories.** This record binds Soveraeign only.
  Whether bdos, ide and schematically adopt the same rules and the shared
  collapse contract is a cross-repository product choice.
- **Whether the collapse contract is Phase 1.5 work.** Phase II is not open
  and product milestone P2 is not Phase II
  (`contracts/phase-1-5-phase-ii-horizon.md`). The style is policy for how
  things are built, not phase work, and this record claims no exit clause.

## Residuals

1. No collapse contract or fixture is built here; the style is stated and its
   evidence is the existing hand-built collapses.
2. The seat registry's `occupant` and schematically's Component both fold
   several axes into one record today. Under rule 2 they are collapses with no
   declaration, and the projected axes are not listed anywhere.
3. `contracts/kernel-paradigms.json` is `PROPOSED`. This record leans on its
   four axes and does not promote it.
