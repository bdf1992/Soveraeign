# Product Roadmap

Status: `PRODUCT PHASES CANDIDATE` · artifact standing `OPEN`, not owner-accepted
Owner: Bdo, root seat · Drafted 2026-08-28

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

**Remaining.** Census and grounding of what exists, reconciling newer rules
against older documents, and closing the residual founding debt. Five custodies
inherited from `phase:i` are attached and `PROPOSED`
(`contracts/custodies.json`).

**Exits when** a fresh reader can determine what the product is, what it
promises, and what would defeat any claim in the governing set, without asking a
person — and the census shows nothing in the repository that no governing
document accounts for.

### `P1` · Local service fabric

**Result.** A service uses another service's capability through a declared
crossing, under identity, policy and authority, and the record holds the receipt.

**Remaining.** Normalize service interfaces, activate more declared operations,
build the identity, policy and record crossings, and remove the direct shortcuts
that currently bypass them.

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

**Remaining.** The work-to-run joins, the custody primitive as a first-class
object, actionable refusals, closure receipts, and an end-to-end circuit
qualification.

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

**Remaining.** A skill registry and contract, dependencies, versions, capability
resolution, declared evidence requirements, and skill mutation tests.

**Exits when** a fresh agent given *"prepare this asset for review"* can
discover the appropriate skill, resolve the available services and assets, carry
the work, hit a missing prerequisite, determine what it can do about that
prerequisite, and either finish or close custody with a precise actionable
remainder.

It does not exit because there are fifty `SKILL.md` files.

### `P4` · Board and operating interface

**Result.** A person sees the real system — assets, skills, work, evidence,
circuits — and acts on it through the same transitions an agent uses.

**Remaining.** The board intermediate representation, cards, real asset
rendering, circuitry, gestures, and custody and evidence views.

**Exits when** every object on a board resolves to an addressed system object
and every gesture resolves to a declared operation, so the interface holds no
authority of its own and creates no parallel state.

### `P5` · Complete sovereign node

**Result.** One node is a thing a person can install, use daily, recover, and
trust.

**Remaining.** Packaging, lifecycle, persistent services, security boundaries,
backup and restore, health, and upgrade or version migration.

**Exits when** a node can be stood up from the artifact, survive a restart and a
restore from backup with its record intact, and report its own health honestly —
including when it is unhealthy.

### `P6` · Enterprise operations

**Result.** The node does ongoing work, not only demonstrations.

**Remaining.** Scheduler and runtime integration, richer workflows, accounting,
queues, operational interfaces, and production effects.

**Exits when** a workflow runs unattended on a schedule, produces effects that
matter, accounts for what it consumed, and every run is attributable and
countermandable after the fact.

*Repository reading.* Scheduled runs exist as a pattern with every schedule
disabled, and Phase I admits no unattended external effect. This phase is where
that constraint is deliberately lifted, which makes it the first phase whose
entry is an owner decision rather than an engineering one.

### `P7` · Federation

**Result.** Two sovereign nodes cross without either absorbing the other.

**Remaining.** Transport, trust establishment, remote capability resolution,
policy negotiation, version compatibility, and receipts that hold across nodes.

**Exits when** a capability on node B is reached from node A under an
authorization both nodes recorded, and neither node's authoritative record moved.

*Repository reading.* Federation-crossing and node-identity contracts exist,
self-tested, with no transport. `PROMISE-15` is the canon's only `LATER` promise.

### `P8` · Enterprise scale and hardening

**Result.** More than one person, more than one node, under real conditions.

**Remaining.** High availability, scale, observability, tenancy and isolation,
key and secret management, disaster recovery, performance, and operational
service objectives.

**Exits when** the node survives a deliberate failure drill — including the loss
of every model provider — without losing custody, and the drill is repeatable.

### `P9` · Ecosystem

**Result.** Other people extend Soveraeign without Soveraeign vouching for them
by accident.

**Remaining.** Packaging standards, compatibility, signing, distribution,
registries, and certification.

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

Carried forward from `ROADMAP-F0-F6.md`, still deferred:

- Distributed consensus.
- A graphical production interface ahead of `P4`.
- Remote databases, queues, containers or orchestration ahead of a conformance
  case that requires them (`ENGINEERING.md`, Growth triggers).
- Performance work ahead of semantic conformance.

## Standing

`PRODUCT PHASES CANDIDATE`. The ten phases, their results and their exit shapes
are Bdo's, stated on 2026-08-28. The per-phase remaining work, the repository
readings, and the exit-condition wording are drafted from the repository and are
proposed. Nothing here is owner-accepted, and this document changes no standing
in `STATUS.yaml`.

What would defeat it:

- a phase that exits on component percentages rather than a demonstrated result;
- a phase whose result is not something a person or an agent can do;
- an estimate presented as a measurement, or a repository reading that
  contradicts an estimate without saying so;
- a phase in this ladder that serves no product area in `PRD.md`.
