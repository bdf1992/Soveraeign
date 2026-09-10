# Composition collapse: the common ground it stands on

Branch `claude/ecs-oop-architecture-j5jwtn`, 2026-09-10. Companion to
`decisions/0105-composition-collapse.md`. Bdo asked that ECS and OOP stay pinned
as the two anchors and that the definition be refined by finding which other
established methods already hold part of the ground the style claims. This is
that survey. It changes no standing and adopts nothing; it names what to borrow
and what each source is missing so that 0105's grammar can be corrected against
prior art rather than restated from memory.

## The two anchors, restated as questions

ECS answers *what is a thing made of, and what runs over it*. OOP answers *what
can I hold, and what may I ask it*. The style needs both answers and needs each
answer not to smuggle in the other's. Every method below was read against five
questions the anchors leave open:

1. Can a relation carry its own rules, so "sensible relations" are checked and
   not just drawn?
2. Is there a named act that turns a composition into a holdable thing in a
   context, and does that act record what it lost?
3. Is the holdable thing rebuildable from its sources, with laws?
4. Can meaning (authority, standing, refusal) ride alongside composition
   without being inferred from it?
5. Do small local rules produce a domain instance nobody enumerated?

## Where the ground already exists

| Method | Holds | Borrow | Missing |
| --- | --- | --- | --- |
| **Flecs relationships** (an ECS with first-class relations) | A relation is an entity pair `(Relation, Target)` and a relation can carry traits: `Transitive`, `Symmetric`, `Exclusive`, `Acyclic`, `OneOf`, `Traversable`. `ChildOf` and `IsA` are acyclic by declaration. | The exact answer to question 1. A relation type is itself an entity with components that say how it behaves. This is the "specific type of component for sensible relations" Bdo asked for, already shipped in a production ECS. | No grant, no receipt, no refusal record. A relation's traits constrain shape, not authority. |
| **Flecs prefabs and `IsA`** | An instance is spawned from a prefab through `IsA`; inherited components are stored once and shared; an instance may override; a prefab's subtree is copied on instantiate. | The "object spawned from an entity process": instantiation is a declared act over a named base, and override is explicit. | The act is not recorded. Nothing says what the instance did not inherit, and the base can change under the instance. |
| **Bevy archetypes and bundles** | An archetype is the unique set of component types an entity carries; entities of one archetype share a table; a bundle is the set of components an entity is spawned with. | Archetype is the template computed from composition rather than declared over it: the shape falls out of the parts. Bundle is the spawn-time template. | Archetype is storage, not meaning. It is the collapse without the record of it. |
| **DCI, Data Context Interaction** (Reenskaug, Coplien) | Data objects hold no use-case behaviour. A Context casts data objects into Roles for one interaction and then triggers it. Roles carry the code a class would have carried. | The closest prior art to "contextual collapse into an object template." Context is the explicit thing that does the casting, and the cast is scoped to one use case. | Casting leaves no record and no standing. Roles are code, not data, so the cast cannot be drawn from data. |
| **Context-oriented programming** (Hirschfeld, Costanza) | Behavioural variations live in layers that crosscut classes; layers are activated for the dynamic extent of a block; the whole system's behaviour changes with the active layer set. | Context as a first-class activation, scoped in time. Deactivation is the reverse act. | Activation is a control-flow fact, not a recorded one; layers are behaviour, not composition. |
| **Bigraphs** (Milner) | One node set, two graphs over it: a place graph (a forest, nesting) and a link graph (a hypergraph, connection). Reaction rules rewrite graphs, not terms. | Formal backing for "the same participants appear in several graphs and the edges mean different things." Rewriting rules are systems declared over graph shape. | Two graphs only, fixed by the theory. Soveraeign already needs more than two: ownership, witness, custody, routing. |
| **SysML v2 and KerML** | Every element is a Definition or a Usage; a usage is defined by at least one definition, explicitly or by the most general one of its kind; Occurrence is the thing in space and time. | The definition-usage split is template-instance stated as a language rule, not a convention, and a usage always names its definition. schematically's Component would be a usage. | No act between definition and usage; a usage is authored, not computed, so nothing records what context selected it. |
| **Object-Process Methodology**, ISO 19450 | Two kinds only, stateful objects and processes that create, consume or affect them, in one diagram with an equivalent generated English text. | Diagram equals data, with the text as a second projection of the same model. Process is separate from object by construction. | No relation typology beyond the fixed OPM link set; no authority. |
| **Wiring diagrams and operads** (Spivak) | Boxes with typed ports; a wiring diagram is a morphism that says how boxes compose into a box; algebras assign behaviour to boxes so composition of behaviour follows composition of diagrams. | The formal claim behind "diagrammable and executable": composition of the drawing and composition of the meaning are the same operation. schematically's Ports and Wires are this. | Behaviour follows structure with no room for refusal or standing. |
| **Wave function collapse** (Gumin), **Model synthesis** (Merrell) | Every cell starts as the set of all allowed states; local adjacency rules propagate; a cell is collapsed to one state and its neighbours lose options; the result is a global structure no rule stated. | The answer to question 5, and the word "collapse" itself. Emergence comes from adjacency rules, which are relations with traits. A palette from a colour-adjacency rule is a WFC problem. | Choice under underdetermination is random. Under the style it must refuse `UNDERDETERMINED` or take context as the tiebreak, and either way record it. |
| **OWL 2 property characteristics** | An object property may be Functional, InverseFunctional, Transitive, Symmetric, Asymmetric, Reflexive, Irreflexive; a reasoner derives what follows. | The same relation typology Flecs ships, standardised, with inference defined. | Open-world inference derives facts nobody recorded; the style wants derivations addressed and digested. |
| **SHACL shapes** | A node shape constrains a focus node; a property shape constrains values reached by a path; a shapes graph validates a data graph and reports every violation. | A template as a shape: the axes and relations an instance must carry, checked from outside. | Validation, not construction: SHACL tells you an instance is wrong and does not build one. |
| **Datomic** | A database is a set of immutable datoms `(entity, attribute, value, transaction)`; transactions only add; removal is a new retraction datom; any past state is queryable as-of. | Entity-attribute-value is a component per axis; accumulate-only is the append-preserving record; retraction as a new fact is `CONTRACT.md` retraction. | Attributes have no traits and transactions have no authority. |
| **Datalog** | Stored relations are extensional; derived relations are intensional, defined by rules; stratified programs derive deterministically to a fixpoint. | A collapse is an intensional relation: derived, deterministic, rebuildable by re-running the rules. | Derivation records no provenance by default and carries no standing. |
| **Out of the Tar Pit** (Moseley, Marks) | Essential state is relational; essential logic is derived relations, integrity constraints and pure functions; everything else is accidental. | The discipline for rule 6 of 0105: an instance is derived state, and derived state that is stored is accidental complexity unless it is rebuildable. | Says nothing about who may derive or who witnessed it. |
| **Event sourcing and CQRS** | Events are appended; read models are projections rebuilt by replay from event zero; a projection that cannot be rebuilt means you do not own your system. | The operational form of rule 6, with the test stated as a slogan. | Projections are typed by hand, not derived from a template. |
| **Lenses and bidirectional transformations** | A lens is `get` and `put` with laws: GetPut, a view that did not change puts back the same source; PutGet, a put source shows the view it was given. | The laws a collapse must satisfy if an instance is ever edited and pushed back to its components. Without them, editing an instance is a hidden write to a component. | Laws only; no record of which law a given round trip was checked against. |
| **Algebraic databases, CQL** (Spivak, Wisnesky) | A schema is a category, an instance is a functor from it to sets, a schema map induces three migration functors, and the migrations are structure-preserving by construction. | The strongest formal candidate for what a collapse is: a functor from a template to an instance, with template-to-template maps inducing instance-to-instance maps. | Heavy. Adopt the shape of the claim, not the machinery. |
| **Production rule systems, Rete** (Forgy) | Rules match working memory; every match goes on an agenda; conflict resolution, salience or recency, decides which fires. | Where ECS has no answer for two systems that both match, rule systems do: an explicit agenda and a declared ordering. | Salience is a number, not a grant; firing leaves no receipt. |
| **Pattern languages and generative codes** (Alexander) | Patterns at several scales; a generative sequence unfolds a whole through context-dependent steps; each step depends on what came before; the result is unique to its place. | The design-side statement of emergence: small patterns, an unfolding order, a whole nobody drew. A collapse under context is one unfolding step. | Prose, not data. |

## What this changes in the definition

Read together, the sources correct 0105 in six places.

**Relations get a typology, and it is a component.** Flecs and OWL 2 agree on
the same small set of traits: functional or exclusive, inverse-functional,
transitive, symmetric or asymmetric, reflexive or irreflexive, acyclic, and
target-restricted (`OneOf`). Under the style a relation type is an entity, its
traits are components on it, and a system that walks a relation reads the traits
first. `RELATION_GRANTS_NOTHING` stays as the trait none of them have. This is
what makes a chain sensible: a `next` relation declared functional,
inverse-functional and acyclic is a chain by construction, and a system can
refuse a fork or a loop by name.

**The collapse has a shape from prior art, not from us.** DCI names the actor:
a Context casts Data into Roles. SysML v2 names the result: a Usage defined by
a Definition. Flecs names the act: instantiate from a base through `IsA`, with
explicit override. Datalog and CQL name the semantics: a derived relation,
computed deterministically from stored ones. 0105's `Collapse(template, context,
components, relations)` keeps all four and adds the part none of them record:
the digests, the preserved and projected axes, and the standing ceiling.

**Rebuildable needs laws, not a slogan.** Event sourcing says rebuild from
zero; lenses say what rebuild must satisfy. Rule 6 of 0105 should state GetPut
and PutGet: collapsing unchanged components yields the same instance bytes, and
an instance produced by a collapse reads back as the components it was given.
An instance that is edited in place is a `put` and needs a declared lens or it
is a hidden component write.

**Underdetermination is a refusal, not a roll.** WFC picks at random when a
cell has more than one allowed state. The style's collapse is deterministic:
if the template, context and relations leave more than one admissible instance,
the collapse refuses `UNDERDETERMINED` and names the free axis, or the context
supplies the choice and the record says so. This is the one place the style
departs from the method it borrowed its name from.

**Conflict has an agenda.** ECS is silent when two systems match the same
components. Rete is not: matches go on an agenda and a declared strategy orders
them. The style's answer is already in the repository: a system fires only when
its declared preconditions hold and its grant covers it, so two matching
systems are two attempted operations, each with its own receipt, and ordering
is the orchestrator's declared plan, never salience.

**Two graphs is the minimum, not the count.** Bigraphs prove that one node set
under two independent graphs is a sound formal object with rewriting. The style
needs that soundness for every named graph the seat topology already carries.
Nothing in the sources requires the count to be two.

## The inventory and the colour chain, as this survey frames them

These are the two examples Bdo asked for, stated here as what each source
would say about them, so the worked versions are built against the right
questions.

**Inventory.** OOP: a `Bag` with `add(item)` and a capacity check inside it.
ECS: a `Contains` relation from bag to item, `Weight` and `Capacity` components,
one system that sums and refuses. Flecs adds `Contains` declared `Exclusive` on
the item side, so an item is in one bag by construction. DCI adds the Context:
the same item entity is cast as `Cargo` in a shipping use case and `Stock` in a
warehouse one. Under the style the bag a person holds is the collapse of
`(Contains*, Weight, Capacity)` under a context that names which use case, and
the record lists that `Price` was projected away.

**Colour chain.** WFC: each link starts as every colour, an adjacency rule says
which colours may sit next to which, and propagation leaves one palette. Flecs:
`next` declared `Exclusive` and `Acyclic`. OWL: `next` functional and
asymmetric. Under the style the template `chain` names one relation with those
traits and one axis per link; collapsed under a colour context it yields a
palette, under a delegation context it yields the seat chain in
`contracts/fixtures/seat-topology.reference.json`, and under a supply context it
yields the inventory's provenance. Same template, three domains, no template per
domain. That is the emergence Bdo described: a small relation with declared
traits, and domains fall out of context.

## Sources

Flecs relationships and traits: https://www.flecs.dev/flecs/md_docs_2Relationships.html
and https://www.flecs.dev/flecs/group__builtin__tags.html. Flecs prefabs:
https://www.flecs.dev/flecs/md_docs_2PrefabsManual.html. Bevy archetypes:
https://taintedcoders.com/bevy/archetypes and https://docs.rs/bevy_ecs/latest/bevy_ecs/.
DCI: https://dci.github.io/ and https://en.wikipedia.org/wiki/Data,_context_and_interaction.
Context-oriented programming: Hirschfeld, Costanza, Haupt, "An Introduction to
Context-Oriented Programming with ContextS" (2007). Bigraphs:
https://en.wikipedia.org/wiki/Bigraph and BigraphER (CAV 2016). SysML v2
definition and usage: https://roth-soft.de/blog/2025-08-23-sysml-2-definition-usage.html
and https://www.webel.com.au/node/4906. OPM: ISO 19450:2024,
https://www.iso.org/standard/84612.html. Wiring diagrams: Spivak, "Operads of
Wiring Diagrams", https://arxiv.org/pdf/1512.01602; Vagner, Spivak, Lerman,
https://arxiv.org/abs/1408.1598. WFC: https://github.com/mxgmn/WaveFunctionCollapse;
Karth and Smith, "WaveFunctionCollapse is constraint solving in the wild" (2017).
OWL 2 property characteristics: https://www.w3.org/2007/OWL/refcardLetter and
https://www.w3.org/TR/owl2-primer/. SHACL: https://www.w3.org/TR/shacl/.
Datomic: https://docs.datomic.com/transactions/model.html and
https://docs.datomic.com/glossary.html. Datalog: Free University of
Bozen-Bolzano, Foundations of Databases lecture notes,
https://www.inf.unibz.it/~nutt/FDBs0809/FDBsSlides/4-datalog-2.pdf. Out of the
Tar Pit: https://curtclifton.net/papers/MoseleyMarks06a.pdf. Event sourcing:
https://quality.arc42.org/approaches/event-sourcing. Lenses: Gibbons,
"Bidirectional Transformations" (SSBX 2016), https://www.cs.ox.ac.uk/projects/tlcbx/ssbx/intro.pdf.
Algebraic databases: Schultz, Spivak, Wisnesky, https://arxiv.org/pdf/1602.03501;
functorial data migration, https://arxiv.org/pdf/1009.1166. Rete: Forgy (1982),
https://www.csl.sri.com/users/mwfong/public_html/Technical/RETE%20Match%20Algorithm%20-%20Forgy%20OCR.pdf;
Drools conflict resolution, https://docs.drools.org/. Alexander:
https://www.resilience.org/stories/2010-12-23/interview-pattern-language-author-christopher-alexander/.
