# Product Roadmap

Status: `PRODUCT PHASES CANDIDATE` · artifact standing `OPEN`, not owner-accepted
Owner: Bdo, root seat · Drafted 2026-08-28 · lanes added 2026-08-29

`PRD.md` says what Soveraeign must become. This document is the current estimate
of how it gets there. The estimate is expected to be wrong in detail and revised
often; the PRD is not.

The previous decomposition, F0 through F6, is archived byte-identical at
`ROADMAP-F0-F6.md`, where it remains a pinned definition of the closed `phase:i`
in `contracts/phases.json`. It was a good ladder for getting out of ideation and
the repository has overtaken it: F5 still reads "First enterprise service" while
several services are implemented, and federation is listed as deferred while
federation-crossing and node-identity contracts already exist experimentally.
The name crosswalk is carried forward below, re-keyed onto this ladder;
`ROADMAP-F0-F6.md` holds its original keying.

## What a phase is here

A phase is an increasingly complete operating environment, not an implementation
layer. Each one names a **product result** — something a person or an agent can
do that they could not before — and exits on a demonstration of that result, not
on component percentages.

The distinction matters because the last campaign failed on exactly this point.
`phase:i` closed `CLOSED_INCOMPLETE` with the ruling that the repository
"optimised the wrong unit of progress, and the exit predicates were never on the
critical path of work" (`contracts/phases.json`). Component completion is the
wrong unit. A circuit that runs end to end and fails correctly when you break it
is the right one.

## Now, next, needed, never

Every phase below carries four lanes. They are Bdo's shape, added to this
document on 2026-08-29, and they separate four questions that a single
"remaining" list runs together. `contracts/roadmap-lanes.json` is the machine
copy, and `python scripts/sov_next.py --strict` fails when a phase is missing a
lane, so the shape cannot quietly rot back into a list.

- **Now** - what is on the board: available, and workable from start to finish
  with what exists today. Not what is in progress, and not what is most
  important. If it needs something that does not exist yet, it is not Now.
- **Next** - what becomes available once Now clears, *and* has already been
  chosen as the next target. Both conditions. An item that is merely unblocked
  is not Next, and neither is a favourite that Now does not release.
- **Needed** - a future item already known to be a need of ours, and neither
  selected nor scheduled. This is where honest future work waits without being
  promoted by enthusiasm.
- **Never** - what will never be allowed to creep into this item's scope. It is
  a constraint rather than a plan, and it is the lane that does the most work:
  a phase usually fails by absorbing the next one, not by running out of effort.

An empty Now or Next is a reading, not an omission. A phase whose Now is empty
is saying that nothing in it can be finished with what exists, which is worth
knowing and is stated here rather than left to be inferred. A Never is never
empty, because a scope with no stated edge has no edge.

An item sits in exactly one lane at one level. Moving it between lanes is an
edit to an estimate, not a change of standing: `STATUS.yaml` owns standing and
`contracts/custodies.json` owns who is on the hook for a piece of work.

### The shape recurses

The four lanes apply at every level, not only to a phase. The roadmap as a whole
has them, each phase has them, each item inside a lane has them, and so on down
to whatever grain someone is actually working at. The rule is identical at every
depth, so it is stated once here instead of restated per level.

An item's lanes are scoped to that item. `P1`'s Now is the Now of the service
fabric, not of the repository, and the Now of an item inside `P1` is narrower
again. A child's Never may be tighter than its parent's; it may not be looser,
because a child cannot admit what its parent excluded.

Worked one level down, inside `P1`'s Now:

> **Normalize the service interfaces.**
>
> *Now* - bring the ten `service.json` manifests to one declared shape, which
> `python scripts/sov_service.py check` already grades.
>
> *Next* - activate the declared operations the normalized shape makes
> reachable. The surface reads 134 declared and 5 reachable.
>
> *Needed* - a manifest version and a migration path, once a second participant
> reads the same manifests.
>
> *Never* - a manifest that describes an operation the service cannot perform.
> A declared surface is not a built one, and the manifest never becomes the
> place that claim gets made.

Below that grain the lanes are carried by `contracts/custodies.json` and the
ticket queue rather than by this document, which is why the recursion stated
here has a floor in practice and none in principle.

### The roadmap's own lanes

- **Now** - `P0` and `P1`. Each has items that can be finished with what exists,
  and each gates everything above it.
- **Next** - `P2`, then `P3`. Chosen, and each opens as the phase below it
  clears. `P5` runs alongside rather than after, because packaging a node is
  largely independent of what the node can do.
- **Needed** - `P4`, and `P6` through `P9`. Known needs of ours, none scoped.
  `P6` is the first whose entry is an owner decision rather than an engineering
  one.
- **Never** - the rows under *Deferred until earned* below. Each is an ordering
  constraint rather than a refusal, which is what a Never is here: not "we will
  not", but "never before the thing that earns it".

## The phases

Percentages are Bdo's rough maturity estimates from what is currently visible in
the repository. They are not calendar promises, not measurements, and not
derived from any counter in this repository — where a repository reading
disagrees, it is noted under the phase. **The exit shape is the load-bearing
part; the percentage is orientation.**

| Phase | Product result | Estimate |
| --- | --- | ---: |
| `P0` Ground and govern | Product definitions, contracts, evidence rules, authority model, engineering and SDLC baseline | 85–90% |
| `P1` Local service fabric | Independently bounded services discover and use each other under shared contracts | 55–65% |
| `P2` Custody and closed circuits | Work travels intent → execution → evidence → closure without disappearing between systems | 40–50% |
| `P3` Composable skills | Agents discover domain skills that compose real services, assets and tools, and recover from blockers | 30–40% |
| `P4` Board and operating interface | Humans see and act on assets, skills, work, evidence and circuits without creating parallel authority | 15–25% |
| `P5` Complete sovereign node | One deployable node is personally useful, recoverable, secure and operationally coherent | 30–40% |
| `P6` Enterprise operations | Workflows, automations and agents perform meaningful ongoing domain work through the fabric | 20–30% |
| `P7` Federation | Sovereign nodes discover and cross to other sovereign nodes without collapsing ownership | 10–20% |
| `P8` Enterprise scale and hardening | Multi-user, multi-node deployments withstand load, failure, upgrade, attack and long life | 5–15% |
| `P9` Ecosystem | Third parties safely publish services, skills, adapters, models and domain packages | <10% |

Phases are not strictly sequential. `P5` overlaps `P2` and `P3` because packaging
a node is largely independent of what the node can do, and its estimate is
already ahead of the phases before it for that reason.

### `P0` · Ground and govern

**Result.** The product knows what it is, what it undertakes, what counts as
evidence, and who may decide what.

`GROUND.md`, `CANON.md`, `CONTRACT.md`, `CLASSIFICATION.md`, `SPEC.md`,
`ENGINEERING.md` and `SDLC.md` are in place; ground and canon are owner-accepted.

**Now.** The census: grounding what is in the repository against what a
governing document actually accounts for, and reconciling newer rules against
older documents. Workable from start to finish today -
`python scripts/sov_custody.py orphans` already names 20 declared items no
custody holds, every one of them an `OPEN-SEAMS.md` row.

**Next.** The five `phase:i` exit custodies, attached and `PROPOSED` in
`contracts/custodies.json`, each driven to a stated terminal. Selected; it opens
as the census stops turning up items nobody holds.

**Needed.** A fresh-reader test that is run rather than asserted. The cold-start
benchmark (`scripts/sov_coldstart.py`) is the instrument that exists; pointing it
at the whole governing set is not scoped.

**Never.** New product scope. `P0` settles what the product is and never decides
what to build next, and it never accepts its own documents - acceptance is the
root seat's act over a presented result.

**Exits when** a fresh reader can determine what the product is, what it
promises, and what would defeat any claim in the governing set, without asking a
person — and the census shows nothing in the repository that no governing
document accounts for.

### `P1` · Local service fabric

**Result.** A service uses another service's capability through a declared
crossing, under identity, policy and authority, and the record holds the receipt.

**Now.** Normalizing the service interfaces so the ten manifests declare one
shape. The manifest contract exists and grades itself -
`python scripts/sov_service.py check` reads 10 manifests and 134 declared
operations - so this is workable from start to finish today.

**Next.** The Gateway crossing: identity, policy and authority checked at the
boundary rather than advertised at it. Chartered, not implemented; it opens once
the manifests agree on a shape worth checking.

**Needed.** The record crossing that holds the receipt, and the removal of the
direct shortcuts that currently bypass all of it.

**Never.** Transport off the node. A second node, a wire between hosts, remote
capability resolution - those are `P7`. A fabric that reaches another node is not
this phase finishing; it is a later phase starting early.

**Exits when** this circuit runs, and mutating any piece of it produces the
correct failure rather than a silent success:

```text
Service A
   ↓ discovers capability
Gateway
   ↓ identity / policy / authority
Service B
   ↓
Record
   ↓
receipt
```

It does not exit because Gateway is 80%, Asset 90% and Record 85%.

*Repository reading.* The operation surface currently reads 134 declared and 5
reachable, and Gateway, Observation, Projection and Registry are boundaries with
no implementation. That is a lower reading than 55–65% and the two are measuring
different things: the estimate counts contracts and design settled, the surface
counts operations a caller can actually reach.

### `P2` · Custody and closed circuits

**Result.** An accepted unit of work has a custodian at every moment, and it
terminates in a named way rather than disappearing.

**Now.** Attaching the twenty declared items no custody holds, so that work
stops being visible and unheld at the same time.

**Next.** The work-to-run joins and the closure receipt: a run that names the
work it served, and a terminal that is recorded rather than inferred from
silence.

**Needed.** The custody primitive as a first-class object, actionable refusals
that name the next admissible operation, and an end-to-end circuit
qualification.

**Never.** A second System of Record. A board is projected from authoritative
records and never stores its own truth (`contracts/concern-admission.json`,
`boards_are_derived`). A stored board goes stale silently, and it does so
precisely when it looks busiest.

**Exits when** a work item can be followed from the intent that created it to a
receipt that closes it, through at least one handoff between operators, and when
an unavailable transition produces a named next admissible operation rather than
an unexplained blocked state.

*Repository reading.* `contracts/custodies.json`, `contracts/closure-ownership.json`
and `scripts/sov_closure.py` exist; `custody` appears across 39 files under
`contracts/` and `services/`. The vocabulary is further along than the
mechanism.

### `P3` · Composable skills

**Result.** An agent that has never run here receives a domain instruction,
finds the skill that covers it, resolves the services and assets it needs, and
carries the work.

**Now.** A skill contract and registry: what a skill declares, what it depends
on, and what evidence it owes. Twenty-five skills sit under `.claude/skills` with
no contract between them, so this is startable today and does not wait on `P1`.

**Next.** Capability resolution - a skill resolving the services and assets it
names, against the surface `P1` normalizes.

**Needed.** Dependencies, versions, declared evidence requirements, and skill
mutation tests.

**Never.** File count as progress. Fifty `SKILL.md` files exit nothing. A skill
also never carries authority of its own; it composes operations that do.

**Exits when** a fresh agent given *"prepare this asset for review"* can
discover the appropriate skill, resolve the available services and assets, carry
the work, hit a missing prerequisite, determine what it can do about that
prerequisite, and either finish or close custody with a precise actionable
remainder.

It does not exit because there are fifty `SKILL.md` files.

### `P4` · Board and operating interface

**Result.** A person sees the real system — assets, skills, work, evidence,
circuits — and acts on it through the same transitions an agent uses.

**Now.** Nothing. The first item is the board intermediate representation, and
an IR drawn before `P2` has custody objects and circuits to render would be a
guess wearing a contract's clothes. The empty lane is a reading, not an
oversight.

**Next.** Nothing selected. `P2`'s closure receipts are what make a next target
choosable here.

**Needed.** The board intermediate representation, cards, real asset rendering,
circuitry, gestures, and custody and evidence views.

**Never.** Authority of its own. Every gesture resolves to a declared operation
and every object to an addressed system object, so the interface holds no
permission the kernel lacks and creates no state the record does not have.

**Exits when** every object on a board resolves to an addressed system object
and every gesture resolves to a declared operation, so the interface holds no
authority of its own and creates no parallel state.

### `P5` · Complete sovereign node

**Result.** One node is a thing a person can install, use daily, recover, and
trust.

**Now.** Packaging, and a node that survives a restart with its record intact.
Both are largely independent of what the node can do, which is why this phase's
estimate already runs ahead of the ones beneath it.

**Next.** Backup and restore, proved by restoring rather than by describing the
procedure.

**Needed.** Security boundaries, lifecycle and persistent services, health that
reports honestly when the answer is unhealthy, and upgrade or version migration.

**Never.** A second user or a second node. One node, one person, recoverable.
Tenancy, high availability and scale are `P8`, and admitting them here is how a
personal node quietly becomes a server nobody asked for.

**Exits when** a node can be stood up from the artifact, survive a restart and a
restore from backup with its record intact, and report its own health honestly —
including when it is unhealthy.

### `P6` · Enterprise operations

**Result.** The node does ongoing work, not only demonstrations.

**Now.** Nothing, and not for an engineering reason. This is the first phase
whose entry is an owner decision: it lifts the constraint admitting no unattended
external effect. Until Bdo lifts it, every item here is held rather than blocked,
and the neighbouring phases stay reachable.

**Next.** Nothing until that decision.

**Needed.** Scheduler and runtime integration, richer workflows, accounting,
queues, operational interfaces, and production effects.

**Never.** An effect that cannot be counted or countermanded. Retraction adds a
counter-record; it never claims that resource consumption or an external effect
was reversed.

**Exits when** a workflow runs unattended on a schedule, produces effects that
matter, accounts for what it consumed, and every run is attributable and
countermandable after the fact.

*Repository reading.* Scheduled runs exist as a pattern with every schedule
disabled, and Phase I admits no unattended external effect. This phase is where
that constraint is deliberately lifted, which makes it the first phase whose
entry is an owner decision rather than an engineering one.

### `P7` · Federation

**Result.** Two sovereign nodes cross without either absorbing the other.

**Now.** Nothing. The federation-crossing and node-identity contracts are
self-tested against no wire, so no item here runs from start to finish.

**Next.** Nothing selected. Transport is the gate, and choosing one is a
commitment `P5` packaging should make first.

**Needed.** Transport, trust establishment, remote capability resolution, policy
negotiation, version compatibility, and receipts that hold across nodes.

**Never.** Either node's authoritative record moving. Federation crosses; it does
not merge. No shared database, no distributed consensus, and no node that becomes
authoritative over another node's memory.

**Exits when** a capability on node B is reached from node A under an
authorization both nodes recorded, and neither node's authoritative record moved.

*Repository reading.* Federation-crossing and node-identity contracts exist,
self-tested, with no transport. `PROMISE-15` is the canon's only `LATER` promise.

### `P8` · Enterprise scale and hardening

**Result.** More than one person, more than one node, under real conditions.

**Now.** Nothing.

**Next.** Nothing selected.

**Needed.** High availability, scale, observability, tenancy and isolation, key
and secret management, disaster recovery, performance, and operational service
objectives.

**Never.** Performance work ahead of semantic conformance, and any optimization
that makes a refusal cheaper to skip than to honour.

**Exits when** the node survives a deliberate failure drill — including the loss
of every model provider — without losing custody, and the drill is repeatable.

### `P9` · Ecosystem

**Result.** Other people extend Soveraeign without Soveraeign vouching for them
by accident.

**Now.** Nothing.

**Next.** Nothing selected.

**Needed.** Packaging standards, compatibility, signing, distribution,
registries, and certification.

**Never.** Vouching by accident. Installing a third-party thing never grants it
authority, and removing it leaves the node exactly as it was.

**Exits when** a third-party skill or service can be installed, its authority
scoped, its provenance checked, and its removal leave the node exactly as it was.

## What the old phases became

`PROD-I-1` through `PROD-I-9` are not retired. They are the first qualification
profile beneath the PRD — `Phase I · Local Sovereign Foundation` — and they keep
their identifiers, their predicates in `SPEC.md`, and their fixtures in
`conformance/`. See `PRD.md`, The Phase I qualification profile.

`phase:i` itself is closed `CLOSED_INCOMPLETE` and `succeeded_by` is null. Which
of the phases above opens next, and when, is Bdo's to set; this document
proposes the ladder, not the entry.

## Name crosswalk

One job carries a different name in each document that mentions it. The names
are not synonyms by accident; each document names the job in its own vocabulary,
and a reader who knows one name cannot find the others. This table is the only
place the identity is asserted, and `scripts/sov_next.py` checks that every row
still resolves, so a rename breaks the check instead of the reader.

Rows were re-keyed onto the `P` ladder on 2026-08-28 when `F0`-`F6` were
archived. The jobs and the tickets did not change; only the phase each one is
filed under. `ROADMAP-F0-F6.md` holds the original keying.

| Phase | Epic ticket | Governing debt or objective | Drawn as |
| --- | --- | --- | --- |
| `P1` Local service fabric | `#25` Shared contracts, carrying `#6` Shared Kernel (closed before its standing settled) | `SPEC.md` transition contract, projected to `contracts/kernel-transitions.json` | `K` in `diagrams/crossing-topology.md` |
| — service-internal | `#27` Asset reference participant | `ENGINEERING.md` named module debt: split `core.py` by owned responsibility | — |
| `P0` Ground and govern | `#26` Conformance harness | `SPEC.md` Conformance boundary | control pairs in `conformance/` |
| `P1` Local service fabric | `#30` Operator bindings | `PRD.md` two-binding proof | `C1` in `diagrams/crossing-typology.md` |

The kernel row names contracts, not a module. `CLASSIFICATION.md` files the
shared kernel under cross-cutting foundations rather than the
System/Node/Service/Component ladder, and `contracts/README.md` disclaims
programming-language classes. The kernel is implemented once per service and its
sameness is proven behaviourally by the conformance oracle, which is why
splitting `core.py` is a separate, service-internal row.

A row is added when a job acquires its second name, not when it acquires its
first. Rows are removed only when the job is `RATIFIED` and the names retire
together.

## Deferred until earned

This is the roadmap's own **Never** lane, kept under the name the F0-F6 ladder
gave it. Every row is an ordering constraint rather than a refusal: never before
the thing that earns it.

Carried forward from `ROADMAP-F0-F6.md`, still deferred:

- Distributed consensus.
- A graphical production interface ahead of `P4`.
- Remote databases, queues, containers or orchestration ahead of a conformance
  case that requires them (`ENGINEERING.md`, Growth triggers).
- Performance work ahead of semantic conformance.

## Standing

`PRODUCT PHASES CANDIDATE`. The ten phases, their results and their exit shapes
are Bdo's, stated on 2026-08-28. The four lanes and the rule that they recurse
are Bdo's, stated on 2026-08-29. The per-phase lane contents, the repository
readings, and the exit-condition wording are drafted from the repository and are
proposed. Nothing here is owner-accepted, and this document changes no standing
in `STATUS.yaml`.

The lanes replaced one **Remaining** paragraph per phase rather than sitting
beside one. A flat list and the lanes that decompose it would be two answers to
one question, and the flat one would go stale first.

What would defeat it:

- a phase that exits on component percentages rather than a demonstrated result;
- a phase whose result is not something a person or an agent can do;
- an estimate presented as a measurement, or a repository reading that
  contradicts an estimate without saying so;
- a phase in this ladder that serves no product area in `PRD.md`;
- a Now item that cannot in fact be finished with what exists today;
- a Next item that nothing in Now releases, or that nobody has actually chosen;
- an empty Never, or a child Never looser than the Never above it.
