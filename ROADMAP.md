# Product Roadmap

Status: `PRODUCT PHASES CANDIDATE` · artifact standing `OPEN`, not owner-accepted
Owner: Bdo, root seat · Drafted 2026-08-28 · lanes added 2026-08-28

`PRD.md` says what Soveraeign must become. This document is a candidate estimate
of how it gets there; A20 still asks the root seat whether this decomposition is
the accepted forward product model. Historical `Now`/`Next` lane text below is
therefore forecast, not the live work queue. While `STATUS.yaml` says
`phase: NONE_ACTIVE`, issue #148 is the boundary-closure ledger and no product
phase is active. If a successor is opened, #173 is the first proposed construction
gate. The estimate is expected to be wrong in detail and revised often; the PRD is not.

The previous decomposition, F0 through F6, is archived byte-identical at
`archives/ROADMAP-F0-F6.md`, where it remains a pinned definition of the
closed `phase:i` in `contracts/phases.json`. It was a good ladder for getting out of ideation and
the repository has overtaken it: F5 still reads "First enterprise service" while
several services are implemented, and federation is listed as deferred while
federation-crossing and node-identity contracts already exist experimentally.
The name crosswalk is carried forward below, re-keyed onto this ladder;
`archives/ROADMAP-F0-F6.md` holds its original keying.

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
document on 2026-08-28, and they separate four questions that a single
"remaining" list runs together. `contracts/roadmap-lanes.json` is the machine
copy, and `python scripts/sov_next.py --strict` fails when a subject is missing
a lane, so the shape cannot quietly rot back into a list. What that check proves
is presence and never truth: whether a Now item can really be finished with what
exists is judgement over evidence, and no parser settles it. It also reads the
phase roster out of this document's own table and headings, so an edit to both
can still rename a phase — it can no longer empty the roster, which a witness
demonstrated on 2026-08-28 and which is now refused by name.

- **Now** - what is on the board: available, and workable from start to finish
  with what exists today. Not what is in progress, and not what is most
  important. Startable is not the test: an item that can be begun and not
  finished waits in Needed until the thing it needs exists.
- **Next** - what becomes available once *this item's own* Now clears, and has
  already been chosen as the next target. Both conditions. An item that is
  merely unblocked is not Next; neither is a favourite that Now does not
  release; and neither is something a sibling's Now would release.
- **Needed** - a future item already known to be a need of ours, and neither
  selected nor scheduled. This is where honest future work waits without being
  promoted by enthusiasm.
- **Never** - what is held out of this item's scope. Usually a never: it holds
  by default and it is not a claim to be permanent. It is the lane that does
  the most work, because a phase fails by absorbing its neighbour more often
  than by running out of effort.

### How something leaves Never

Discovery moves it, and only into Needed. His words, in full:

> Never is Usually a never. It means discovery selects it and pressures it from
> what is needed based on what was now.

What is unambiguously his: Never holds by default, it is not permanent, and
discovery is what moves it, into Needed. The three exclusions this document
draws around that - not a preference, not a date, not the phase number arriving
- are read out of "discovery" being the only mover, and they are the builder's
reading of his sentence rather than words in it.

The reading that follows is drafted from that sentence and he has not ruled on
it: Now is the only lane being worked, so it is the only lane that produces
findings, and what is learned there is the only thing that pressures an
exclusion out of Never. It is a claim about how work happens, not a restatement,
and it is the fourth of the readings under *Standing* this document cannot
settle for itself.

The lanes are a cycle rather than a list, and Now drives it. Discovery under Now
pressures Never into Needed; selecting a known need moves it to Next; Next
becomes Now when this item's own Now clears. An exclusion that jumps straight to
Now or Next is scope creep on a shorter path: passing through Needed is what
puts the admission on the page as a known need before anyone works it, which is
the whole reason the exclusion was written down.

None of that is checked. A lane change is an edit to prose, and whether a
finding really pressured an exclusion is judgement.

### What the lanes do not claim

An empty Now or Next is a reading, not an omission. A phase whose Now is empty
is saying that nothing in it can be finished with what exists, which is worth
knowing and is stated rather than left to be inferred. A Never is never empty,
because a scope with no stated edge has no edge.

An item sits in exactly one lane at one level, and a subject opens each lane
once. Moving an item between lanes is an edit to an estimate, not a change of
standing: `STATUS.yaml` owns standing and `contracts/custodies.json` owns who is
on the hook for a piece of work.

This document is a candidate, so "already chosen" in a Next lane means chosen by
this document and not yet ruled on by Bdo. Where he has chosen, the phase says
so by name. That distinction is the second of the three readings under
*Standing* that this document cannot settle for itself.

### The shape recurses

The four lanes apply at every level, not only to a phase. The roadmap as a whole
has them, each phase has them, each item inside a lane has them, and so on down
to whatever grain someone is actually working at. The rule is identical at every
depth, so it is stated once here instead of restated per level.

An item's lanes are scoped to that item. `P1`'s Now is the Now of the service
fabric, not of the repository, and the Now of an item inside `P1` is narrower
again. A parent's Never binds its children: a child may add exclusions and may
not admit what its parent excluded.

Nothing enforces that last rule and nothing here can. A Never is a prose
paragraph, there is no ordering on prose, and comparing a child's with its
parent's would need Nevers written as enumerated typed exclusions first. It is
recorded as a stated limit rather than left to look enforced.

Worked one level down, inside `P1`'s Now. The lanes below are graded like any
other subject, because the document's only instance of the recursion is the one
place the shape could rot while the check stayed green:

> **Replicate the Gateway route pattern.**
>
> **Now.** Carry the built `RECORD_LOCAL` in-process route to a second
> service-owned operation. `services/gateway/KNOWN-GAPS.md` names the remaining
> work as adding same-class routes mechanically, so the shape to copy exists.
>
> **Next.** A third route in a second service family, which is what
> `services/gateway/KNOWN-GAPS.md` says must happen before the convention is
> treated as generic substrate. Released by the second route, and chosen here.
>
> **Needed.** Whatever the receipt question settles.
> `services/gateway/KNOWN-GAPS.md` has not decided whether a gateway receipt is
> a distinct owned record, a kernel receipt form, or unnecessary beyond crossing
> evidence, and the answer is a need this route will have.
>
> **Never.** Service-specific logic inside Gateway. A route that needs the door
> to know something about the service behind it is not a route; it is the
> service leaking through, and the gap table refuses it by name.

Below that grain the lanes are carried by `contracts/custodies.json` and the
ticket queue rather than by this document, which is why the recursion stated
here has a floor in practice and none in principle.

### The roadmap's own lanes

**Now.** `P0` and `P1`. Each has items that can be finished with what exists,
and each gates everything above it.

**Next.** `P2`, then `P3`. Each opens as the phase below it clears. `P5` runs
alongside rather than after, because packaging a node is largely independent of
what the node can do.

**Needed.** `P4`, and `P6` through `P9`, plus every row under *Deferred until
earned* below except the first, which this roadmap's Never holds. Known needs of
ours, none scoped. `P6` is the first whose entry is an owner decision rather than
an engineering one.

**Never.** Distributed consensus. A phase that exits on component percentages
rather than a demonstrated result. And this document acquiring standing: it is
an estimate, and the day it starts settling what is built rather than
describing it, `STATUS.yaml` has a rival.

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

**Now.** Reconciling governing prose that a newer ruling moved past, over a
closed population: the documents `AGENTS.md` names as the governing set, plus the
domain skills under `.claude/skills/` that route readers into them. The list is
fixed, so the sweep finishes. Two live instances:
`.claude/skills/sov-governance/SKILL.md` still routes readers to `F0`-`F6` and to
ten open seams where `OPEN-SEAMS.md` now carries twenty-five, and
`infrastructure/README.md` still reads `O14 OPEN` against an identifier
`decisions/0033` retired.

**Next.** The five `phase:i` exit custodies, attached and `PROPOSED` in
`contracts/custodies.json`, each driven to a stated terminal. Released by the
reconciliation, because a custody whose exit clause cites a superseded document
inherits the superseded reading.

**Needed.** Two things, neither scoped. A census instrument that reads the
repository rather than a declared list - `python scripts/sov_custody.py orphans`
answers "declared work no custody holds" and this phase's exit asks "anything at
all no governing document accounts for", which is the wider question and has no
instrument. And a fresh-reader test that is run rather than asserted; the
cold-start benchmark (`scripts/sov_coldstart.py`) is the instrument that exists,
pointed at one corpus rather than the governing set.

**Never.** New product scope. `P0` settles what the product is and never decides
what to build next, and it never accepts its own documents - acceptance is the
root seat's act over a presented result. Attaching the twenty orphan seam rows
is `P2`'s Now and not this phase's; every one of them is an `OPEN-SEAMS.md` row,
so a governing document already accounts for them and this phase's exit does not
wait on who holds them.

**Exits when** a fresh reader can determine what the product is, what it
promises, and what would defeat any claim in the governing set, without asking a
person — and the census shows nothing in the repository that no governing
document accounts for.

### `P1` · Local service fabric

**Result.** A service uses another service's capability through a declared
crossing, under identity, policy and authority, and the record holds the receipt.

**Now.** Replicating the Gateway route. One reusable `RECORD_LOCAL` in-process
vertical is built and self-tested for `sov://asset/ingest-asset`, with authority
checked at the door and absence defaulting to refusal;
`services/gateway/KNOWN-GAPS.md` names the remaining work as adding same-class
service-owned routes mechanically. The pattern exists, so carrying it to a
second operation runs from start to finish today.

**Next.** The record crossing that holds the receipt. Released by the second
route, because the crossing has to record something and a route is what produces
it. It is not released by any claim that two routes make the convention generic:
`services/gateway/KNOWN-GAPS.md` asks for a second operation *and then* a second
service family before that. Chosen here, not yet ruled on.

**Needed.** Removing the direct shortcuts that bypass the door - above all
`bindings/mcp/gateway.py`, which is still an older ingress with its own
resolution, authority and journal behaviour. Known, and not scoped. A canonical
request schema is not here: `services/gateway/KNOWN-GAPS.md` files it as a
question to decide rather than a need, and an undecided question is not a known
need.

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
reachable. Observation, Proofing and Projection are boundaries with no
implementation; Gateway and Registry are not - `services/README.md` records a
first in-process route built and self-tested for Gateway and a read-only resolve
slice for Registry. That is a lower reading than 55–65% and the two are measuring
different things: the estimate counts contracts and design settled, the surface
counts operations a caller can actually reach.

### `P2` · Custody and closed circuits

**Result.** An accepted unit of work has a custodian at every moment, and it
terminates in a named way rather than disappearing.

**Now.** Attaching the twenty declared items no custody holds, so that work
stops being visible and unheld at once. `python scripts/sov_custody.py orphans`
names all twenty and every one is an `OPEN-SEAMS.md` row, so the population is
closed and the work finishes.

**Next.** The closure receipt: a terminal that is recorded rather than inferred
from silence. Released by the attachment, because the receipt has to be proved
against the whole population and the twenty are the part of it with no
custodian; `contracts/custodies.json` already holds sixteen attached and
`PROPOSED`, so there is plenty to close and not yet everything. Chosen here, not
yet ruled on.

**Needed.** The work-to-run joins, the custody primitive as a first-class object,
actionable refusals that name the next admissible operation, and an end-to-end
circuit qualification.

**Never.** A second System of Record. A board is projected from authoritative
records and never stores its own truth (`contracts/concern-admission.json`,
`boards_are_derived`). A stored board goes stale silently, and it does so
precisely when it looks busiest.

**Exits when** a work item can be followed from the intent that created it to a
receipt that closes it, through at least one handoff between operators, and when
an unavailable transition produces a named next admissible operation rather than
an unexplained blocked state.

*Repository reading.* `contracts/custodies.json`, `contracts/closure-ownership.json`
and `scripts/sov_closure.py` exist, and `custody` appears as a whole word in 64
files under `contracts/` and `services/`. The vocabulary is further along than
the mechanism. The count read 39 when this paragraph was written on 2026-08-28
and no pattern reproduces it; 64 is `grep -rlw` over those two directories,
measured 2026-08-28.

### `P3` · Composable skills

**Result.** An agent that has never run here receives a domain instruction,
finds the skill that covers it, resolves the services and assets it needs, and
carries the work.

**Now.** A skill contract and registry: what a skill declares, what it depends
on, and what evidence it owes. Twenty-five skills sit under `.claude/skills`
with no contract between them and no grader anywhere in `scripts/`, and the work
is a schema plus a grader over a closed population - the same shape
`contracts/service-manifest.schema.json` and `python scripts/sov_service.py
check` already have over the ten `services/<domain>/contracts/service.json`
manifests. It finishes, and it does not wait on `P1`.

**Next.** Capability resolution: a skill resolving the services and assets it
names against the registry this phase's Now produces. Released by that registry
and by nothing else. Chosen here, not yet ruled on.

**Needed.** Dependencies, versions, declared evidence requirements, and skill
mutation tests.

**Never.** Authority. A skill composes operations that carry authority and never
carries any itself, so a skill can never be the reason something was permitted.
That is the edge against `P1`, where authority actually lives; counting
`SKILL.md` files is a bad measure but it is a warning, not a boundary.

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

**Never.** Covering for a gap underneath it. A gesture with no declared
operation behind it is a defect in `P2` to be reported, never a capability this
phase adds so the screen looks whole. That is the edge that matters, because an
interface is where a missing transition is cheapest to fake and most expensive
to find later.

**Exits when** every object on a board resolves to an addressed system object
and every gesture resolves to a declared operation, so the interface holds no
authority of its own and creates no parallel state.

### `P5` · Complete sovereign node

**Result.** One node is a thing a person can install, use daily, recover, and
trust.

**Now.** Packaging to the local process target, and to that one only:
`python scripts/deployment.py --target local`, whose execution mode is
`LOCAL_PROCESS`. The container renderer is a different artifact and this phase
may not reach for it - see the Never below. `infrastructure/` already declares
the node envelope as data with a dependency-free planner that materializes and
verifies it, and `scripts/node_runtime.py` proves the listener and health seam,
so the remaining work is bounded and independent of what the node can do, which
is why this phase's estimate runs ahead of the ones beneath it. The evidence
carries one caveat this phase inherits rather than fixes:
`infrastructure/README.md` is itself governing prose `P0`'s Now must sweep.

**Next.** Surviving a restart with the record intact. Released by packaging,
because a restart is only meaningful against something that was stood up rather
than something that was already running. Chosen here, not yet ruled on.

**Needed.** Backup and restore proved by restoring, lifecycle and persistent
services, security boundaries, health that reports honestly when the answer is
unhealthy, and upgrade or version migration.

**Never.** A second user or a second node. One node, one person, recoverable.
Tenancy, high availability and scale are `P8`, and admitting them here is how a
personal node quietly becomes a server nobody asked for. Nor a container or an
orchestrator: the roadmap holds those out until a conformance case needs one, and
this phase adds the exclusion rather than inheriting it — the roadmap files them
under Needed, so nothing above forbids them and `P5` is choosing to.

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

**Never.** Undoing. Retraction adds a counter-record and never claims that
resource consumption or an external effect was reversed, so nothing in this
phase may offer a caller a way to make an effect not have happened. That is the
edge against the record: an operation that reads as reversal would put a lie in
the journal, which is a worse outcome than an effect nobody can take back.

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

**Never.** Shared state between nodes. No common database, no distributed
consensus, no replicated journal, and no node that becomes authoritative over
another's memory. That is the edge against `P8`, which will want exactly those
things for availability and must get them inside one node's boundary.

**Exits when** a capability on node B is reached from node A under an
authorization both nodes recorded, and neither node's authoritative record moved.

*Repository reading.* Federation-crossing and node-identity contracts exist,
self-tested, with no transport. `PROMISE-15` is the canon's only `LATER` promise.

### `P8` · Enterprise scale and hardening

**Result.** More than one person, more than one node, under real conditions.

**Now.** Nothing. Every item here is measured against a load, a failure drill
or a second operator, and none of the three exists to measure against.

**Next.** Nothing selected. `P5` has to produce a node that can be stood up
before anything can be stood up twice.

**Needed.** High availability, scale, observability, tenancy and isolation, key
and secret management, disaster recovery, performance, and operational service
objectives.

**Never.** An optimization that makes a refusal cheaper to skip than to honour,
and distributed consensus - which the roadmap excludes outright, and which
needing tenancy here does not reopen.

**Exits when** the node survives a deliberate failure drill — including the loss
of every model provider — without losing custody, and the drill is repeatable.

### `P9` · Ecosystem

**Result.** Other people extend Soveraeign without Soveraeign vouching for them
by accident.

**Now.** Nothing. There is no third party, and no package format for one to
publish into.

**Next.** Nothing selected. `P8` has to settle isolation before anything
untrusted is admitted at all.

**Needed.** Packaging standards, compatibility, signing, distribution,
registries, and certification.

**Never.** Relaxing what `P5` and `P8` settled about authority and isolation. A
third-party package is admitted through the same grants as anything else, and
"it came from the registry" never becomes a reason to widen one.

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
filed under. `archives/ROADMAP-F0-F6.md` holds the original keying.

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

Held out until something is learned that pressures them back in. Every row here
except the first sits in the roadmap's **Needed** lane rather than its **Never**:
each names what would earn it, so each is a known need with an unmet condition.
Distributed consensus names no such condition and is the roadmap's Never.

Carried forward from `archives/ROADMAP-F0-F6.md`, still deferred:

- Distributed consensus.
- A graphical production interface ahead of `P4`.
- Remote databases, queues, containers or orchestration ahead of a conformance
  case that requires them (`ENGINEERING.md`, Growth triggers).
- Performance work ahead of semantic conformance.

## Standing

`PRODUCT PHASES CANDIDATE`. The ten phases, their results and their exit shapes
are Bdo's, stated on 2026-08-28. The four lanes, the rule that they recurse, and
the rule that an exclusion leaves Never only by discovery pressuring it into
Needed are Bdo's, stated on 2026-08-28. The derivation around that rule - that
Now is the only lane producing findings, and the ordering of the other three
transitions - is drafted from his sentence and marked as such in
`contracts/roadmap-lanes.json`. The per-phase lane contents, the
repository readings, and the exit-condition wording are drafted from the
repository and are proposed. Nothing here is owner-accepted, and this document
changes no standing in `STATUS.yaml`.

The lanes replaced one **Remaining** paragraph per phase rather than sitting
beside one. A flat list and the lanes that decompose it would be two answers to
one question, and the flat one would go stale first.

The lane contents were rewritten twice on 2026-08-28, after two independent
witnesses. The first found six not holding to the definitions above: `P1`'s Next called the
Gateway crossing unimplemented when a route is built and self-tested, `P1`'s Now
cited a passing check as evidence that work remained, `P3`'s Now said "startable"
where the lane requires finishable, `P3`'s Next was released by `P1`'s Now rather
than its own, `P0` and `P2` both claimed the same twenty orphan items, and `P4`
and `P9` restated their own exit conditions as their Never. It also read Never
as a permanent refusal and reported every conditional exclusion as misfiled; Bdo
corrected that reading, and *How something leaves Never* is his answer.

The second witness graded the repair and dissented four times, each repaired
above: `P3`'s Now cited `contracts/service.json`, which does not exist and never
has; `P2`'s Next claimed there was nothing for a closure receipt to close when
sixteen custodies are attached; `P0`'s Never claimed this phase's exit needs the
twenty orphan items when every one is already an `OPEN-SEAMS.md` row; and
`contracts/roadmap-lanes.json` closed, in passing, the third question below that
this document carries to Bdo as open. It also found `P6` and `P7` stating their
own exit conditions as their Never, which the first witness had caught only in
`P4` and `P9`, and that `P0`'s and `P5`'s Now items named no closed population.
Each is repaired above.

A fourth witness graded the third repair and found the guard closed at zero
only: leaving two phases readable and unbackticking the other eight took the
population from twelve subjects to four and the whole check went quiet. A
heading or table row that names a phase this reader cannot resolve is now
refused by name. It also found the derivation restated unmarked in the contract's
Never lane, one field over from where the previous repair had marked it - the
third time a question this document carries open was answered in the field
nobody was watching. And three reader defects, two of them introduced by the
repair beside them: a stray unclosed code fence silenced every lane after it, an
HTML tag and a reference link counted as words a reader can see, and the claim
that the module split was total was false.

A third witness graded the second repair and found the scope guard could be
walked through: emptying the phase table and the phase headings together silenced all
seven refusals over twelve subjects, and the comment claiming `sov_next` caught
that was false, because the same edit made every crosswalk phase token
unreadable and unreadable rows were skipped. Both halves are closed. It also
found the Never-or-Needed question answered in `NEEDED` one field over from
where the previous repair declined to answer it, this roadmap's Needed sweeping
in a row its own Never holds, `P5` citing inheritance over an item nothing above
it excludes, and three shapes the grader read wrongly: a Never written as a
bullet list graded as abandoned, a link target counted as words a reader can
see, and a lane inside a code fence satisfying the shape.

Six readings this document cannot settle for itself, each carried to Bdo:
whether "already chosen" in a Next lane may mean chosen by this document rather
than by him; whether the twenty orphan seam rows are `P2`'s work as filed here;
whether an exclusion that names what would earn it belongs in Never or, as filed
here, in Needed; whether "Now is the only lane that produces findings" says what
he meant, or is a derivation that must stay marked as drafted; whether "not a
preference, not a date, not the phase number arriving" is his exclusion or the
builder's reading of it; and whether "a phase fails by absorbing its neighbour
more often than by running out of effort", which sits inside what this section
attributes to him, is his.

What would defeat it:

- a phase that exits on component percentages rather than a demonstrated result;
- a phase whose result is not something a person or an agent can do;
- an estimate presented as a measurement, or a repository reading that
  contradicts an estimate without saying so;
- a phase in this ladder that serves no product area in `PRD.md`;
- a Now item that cannot in fact be finished with what exists today, or one
  justified by a passing check, since a green grader is evidence that work is
  done rather than evidence that it remains;
- a Next item that this item's own Now does not release, or that nobody chose;
- an exclusion that left Never with no finding behind it, or that reached Now or
  Next without passing through Needed;
- a Never whose release is a date or a phase number rather than something
  learned;
- a Never that restates the phase's own exit condition, and so does no
  independent work;
- an empty Never, or a child Never looser than the Never above it.
