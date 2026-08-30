# Soveraeign Product Requirements

## A Locally Sovereign Enterprise Operating Environment for Humans, Agents, Services, and Skills

Status: `PRODUCT SCOPE CANDIDATE` · artifact standing `OPEN`, not owner-accepted
Owner: Bdo, root seat · Scope: the whole product, no phase · 2026-08-28

Revision 1 was `Product Requirements — Founding and Phase I`. The exact bytes the
campaign closed against are preserved at `archives/PRD-PHASE-I-TERMINAL.txt` and
pinned by `contracts/phases.json`. `archives/PRD-PHASE-I.md` preserves the later
post-terminal strengthening as historical evidence. The nine requirements are not
retired: they remain the first qualification profile under this document, below.

`ROADMAP.md` is the current estimate of how the product gets built. This
document is what it must become. The roadmap is expected to be revised often;
this is not.

## Product outcome

Soveraeign is a locally sovereign enterprise operating environment in which
humans, agents, skills, services, and federated nodes can perform useful work
through the same governed system.

The product provides a composable network of independently bounded services for
identity, assets, records, discovery, policy, authority, routing, observation,
models, workflows, automation, interfaces, and other enterprise capabilities.
Services may use capabilities provided by other services without absorbing their
state, policy, or authority.

Skills compose those capabilities with versioned assets, instructions, tools,
policies, and evidence requirements to describe how domain work can be performed.

Agents and human operators execute that work under explicit custody. Custody
gives an operator authority and responsibility to carry its work toward closure:
complete it, repair what prevents completion, gather the required evidence,
redirect through another admissible operation, refuse safely, or return the
smallest genuinely unresolved remainder.

Every consequential crossing remains attributable and reconstructable. The
system can answer:

- what happened;
- who or what acted;
- under what custody and authority;
- which skill, service, operation, asset, model, policy, and version
  participated;
- what crossed each boundary;
- what evidence supports the result;
- what remains unresolved;
- and what operation can happen next.

A personal deployment and an enterprise deployment use the same fundamental node
model. A node may begin as one person's locally operated environment, grow into
a network of services and operators, and later federate with other sovereign
nodes without surrendering custody of its authoritative record to a model
vendor, cloud provider, or external platform.

The long-term product is not a collection of applications surrounding an AI
assistant. It is an operating environment in which enterprise capabilities are
discoverable and composable, agents can competently use them, work carries
custody from intent to closure, and the resulting system remains inspectable by
the humans responsible for it.

*Owner-directed, stated by Bdo 2026-08-28.*

## What this document owns

The enduring product requirements: what Soveraeign must let a person, an agent,
a service or a peer node actually do; which of those matter more; how anyone
would know it works; and what is deliberately not being built.

It does not restate rules other documents own. Each requirement points at the
document carrying its predicate and the fixture that defeats a false claim. A
rule copied here becomes a second authority for the same rule, which `AGENTS.md`
forbids — and being that copy is how revision 1 stopped being a PRD.

| Not owned here | Owned by |
| --- | --- |
| What kind of product this is, permanently | `GROUND.md`, sixteen claims |
| The exact wording of what the product undertakes to a person | `CANON.md` |
| The system boundary and operating model | `SYSTEM.md` |
| The invariants | `CONTRACT.md` |
| Vocabulary, standing ladders, artifact lifecycle | `CLASSIFICATION.md` |
| The predicate a requirement must satisfy | `SPEC.md` |
| The fixture that proves or defeats it | `conformance/` |
| How and when the work happens | `ROADMAP.md`, P0–P9 |
| Current standing and what waits on the owner | `STATUS.yaml` |
| What the closed founding campaign committed to | `archives/PRD-PHASE-I-TERMINAL.txt`, `contracts/phases.json` |

The admission test is Bdo's, ruled in `decisions/0052` and recorded in
`CLASSIFICATION.md`: **would failing it mean the product is not done?** A
statement that would make Soveraeign a *different product* if it changed belongs
one level up, in `GROUND.md`.

## Problem statement

An enterprise that wants models doing substantive work today chooses between two
bad options.

**Adopt a provider's platform,** and the operational memory, the permission
model, the audit trail and the continuity of the business come to live inside
someone else's system. Changing providers becomes a migration; losing one
becomes an outage of the enterprise rather than of a vendor.

**Bolt an assistant onto existing software,** and the model is not an operator
at all. It drafts, suggests and summarizes beside a system it cannot act in.
Removing it removes a convenience rather than a capability, which is the test
`AI-NATIVE.md` applies and most surfaces fail.

Underneath both sits the same unsolved problem: **nothing distinguishes a model
that did the work from a model that says it did.** A confident report, a
successful execution, a green build and an agreed-with answer all arrive looking
identical. Without a way to tell them apart, delegation cannot scale past what
one person can personally re-check — and that ceiling, not model capability, is
what limits how much work can actually be handed over.

Soveraeign's claim is that these are one problem. A record that can say who did
what, under whose authority, over exactly what state, and whether anyone
independent confirmed it, is the same record that makes the provider
substitutable, because everything that matters is held locally in a form no
provider defines.

*Derived from `GROUND.md`, `SYSTEM.md` Scope and `AI-NATIVE.md` Definition, not
stated by Bdo in these words. Proposed.*

## Custody and closure

The requirement that ties agents, services, workflows, skills, boards and
records together, and the reason a blocked state is not an acceptable terminal.

> **Every accepted unit of work has a current custodian. The custodian has
> bounded authority to carry that work toward closure. When the requested
> transition is unavailable, the system helps resolve the reason into another
> admissible operation. A work item may terminate successfully, refused,
> superseded, absorbed, retired, or unresolved, but it may not disappear into an
> unexplained blocked state.**

*Owner-directed, stated by Bdo 2026-08-28. Top-level and not delegated to agent
governance, because it constrains services and interfaces as much as operators.*

Six named terminals — succeeded, refused, superseded, absorbed, retired,
unresolved — and no seventh. `BLOCKED` is a claim to be proven, not a resting
place: it must name the operation, the blocked transition, the missing
precondition, the governing rule, the required authority, the unblock condition,
and that no reachable alternative exists (`AGENTS.md`, Blocked edge is not
blocked frontier).

*Standing.* `contracts/closure-ownership.json` and `contracts/custodies.json`
exist, `scripts/sov_closure.py` grades a handoff, and custody appears across 39
files under `contracts/` and `services/`. The vocabulary is well ahead of the
mechanism: no work item currently carries a custodian through a handoff, and the
resolve-into-another-admissible-operation behaviour is described and unbuilt.
`CANON.md` has no promise for this, which is discussed under Coverage below.

## Product areas

Twenty-two bounded areas. None of them is the product; each is a capability of
it. The Asset Service is not a product, Gateway is not a product, skills are not
the product, boards are not the product, federation is not the product.

`Serves` names the `CANON.md` promises an area makes good, where one exists.
`Standing` is read from `STATUS.yaml` and the operation surface and moves as the
node changes.

| Area | What this document establishes | Serves | Standing |
| --- | --- | --- | --- |
| **Node** | The sovereign unit of operation, custody, continuity, deployment and eventual federation. A node is whole at any size. | 02, 15 | contract built, no admission transition |
| **Services** | Independently bounded capabilities with owned state, contracts, declared operations and declared refusals. | — | 11 boundaries, 140 declared operations, 5 reachable |
| **Components** | Internal decomposition of a service without creating accidental parallel authority. | — | undeclared |
| **Composition** | Service A uses Service B through a declared capability and a receipted crossing, absorbing none of its state, policy or authority. | — | declared, unreached |
| **Assets** | Versioned, addressable things with provenance, relationships and custody. | 05, 16 | built, self-tested |
| **Skills** | Versioned compositions of assets, knowledge, services, tools and completion rules that describe how domain work is performed. | — | harness skills exist, no product contract |
| **Agents and operators** | Actors that discover capabilities and carry bounded work toward closure under an explicit grant. | 01, 04 | profile accepted, not live |
| **Custody and closure** | Who owns the current work, what closure means, and what happens when a transition cannot occur. | — | contracts built, mechanism open |
| **Gateway and discovery** | How an operator finds and reaches available capabilities without being told by a person who already knows. | 03 | chartered boundary, not implemented |
| **Identity** | Who is acting, and how identity stays attributable across a crossing. | — | contract built, registry read only |
| **Authority and policy** | What an actor may do, scoped independently of which model or intelligence it is running. | — | typed grants built, one ratified |
| **Record** | The durable account of consequential actions, receipts, observations and counter-records. | 07, 08 | built, self-tested, not the kernel's |
| **Evidence** | What supports a claim, and how independent witnessing works. | 11 | witness tooling exists, no observation service |
| **Grounding** | Whether an asset, file, service or claim can explain its place in the system. | — | **new; no contract, no implementation** |
| **Models and BYOM** | Replaceable model compute without provider ownership of authoritative state. | 01, 06 | contract accepted, `invoke_model` unimplemented |
| **Workflow and automation** | Durable compositions that execute work repeatedly. | — | pattern accepted, every schedule disabled |
| **Boards and interfaces** | Human-visible projections of real system objects, paths, custody and evidence, holding no authority of their own. | — | console continuity path built, four surfaces text |
| **Federation** | Governed crossings between independently sovereign nodes. | 15 | contract built, no transport |
| **External effects** | How the system acts safely on systems outside itself. | — | refused in Phase I; adapters declared |
| **Security and reliability** | Isolation, access, durability, recovery, failure behaviour and operational expectations. | — | secret rules enforced; no drill, no recovery path |
| **Accounting** | Cost, usage, attribution, work, time, model and resource accounting. | — | seven resource words defined; receipts cannot record consumption |
| **Qualification** | How the product proves it works rather than claiming completion. | 10, 11 | oracle executable, participant binding open |

### Coverage: thirteen areas serve no promise

Thirteen of the twenty-two areas above make good no promise in `CANON.md`. That
is a real gap and it resolves two different ways, which should not be conflated.

**Most are structure, not undertaking.** *Services*, *Components*,
*Composition*, *Identity*, *Authority and policy*, *Workflow*, *Boards*,
*External effects*, *Security and reliability* and *Accounting* are how the
product is built rather than what it undertakes to a person. A PRD legitimately
holds both kinds. They need requirements here; they do not need promises minted
above them.

**Three are genuine undertakings with no promise, and want one.**

- **Custody and closure.** "Your work will not vanish into an unexplained
  blocked state" is said to a person and belongs in the canon.
- **Skills.** "You can hand the node a domain instruction and it will know how
  the work is done" is an undertaking, not an architecture.
- **Grounding.** "Anything in the node can explain its place in the system" is
  an undertaking. It is also entirely new: `grounding` appears in no contract or
  service today and would be the first area introduced by this document rather
  than read out of the repository.

Minting a promise is `CANON.md`'s business and Bdo's act. This document records
the three rather than assuming them.

## Requirements

The user-facing requirements **are** `CANON.md`'s promises, owner-accepted
2026-08-24. Minting a parallel identifier for the same undertaking would create
the second requirement ladder `CLASSIFICATION.md` warns about. This document
adds what a PRD adds — priority, area, acceptance and current reach — rather
than restating them.

Priority is `P0` when the product is not the product without it, `P1` when the
product works but cannot be trusted without it, `P2` when it is genuinely wanted
later. **Priority is proposed, not accepted.** Nothing in this repository has
ever ranked one requirement above another, and that absence is the likeliest
mechanism behind the ruling that closed `phase:i` for optimising the wrong unit
of progress.

| # | Requirement | Area | Pri | Criterion | Reach |
| --- | --- | --- | --- | --- | --- |
| `PROMISE-04` | One world | Agents | P0 | `PROD-I-3` | 8 of 11 |
| `PROMISE-07` | Every crossing returns a receipt | Record | P0 | `PROD-I-4` | 13, 1 missing |
| `PROMISE-02` | Custody stays here | Node | P0 | `PROD-I-9` | 2 of 4, 4 missing |
| `PROMISE-03` | You can find out what can be asked | Gateway | P0 | `PROD-I-7` (thin) | 2 of 9 |
| `PROMISE-11` | Delegate and check | Evidence | P0 | `PROD-I-7`, `PROD-I-8` | 1 of 7 |
| `PROMISE-05` | You can find out why | Assets | P1 | `PROD-I-2` | 10 of 11 |
| `PROMISE-08` | Correction never erases | Record | P1 | `PROD-I-4` | 4 of 9 |
| `PROMISE-09` | Your judgement is the scarce thing | Boards | P1 | `PROD-I-6` | 0 of 5 |
| `PROMISE-01` | Bring your own participant | Models | P1 | `PROD-I-9` | 18 of 25, 5 missing |
| `PROMISE-06` | The model is swappable | Models | P1 | `PROD-I-9` | 2 of 2, 2 missing |
| `PROMISE-10` | Useful from the artifact alone | Qualification | P2 | `PROD-I-7` | 2 of 7 |
| `PROMISE-12` | Work carries across a boundary | Boards | P2 | **none** | delivered |
| `PROMISE-16` | Decide against exact state | Assets | P2 | **none** | 1 of 8 |
| `PROMISE-15` | Cross to another node | Federation | P2 | none yet | 2 reachable |

Reach is from `python scripts/sov_canon.py promises` and moves; treat the column
as a pointer to that command rather than a fact this document holds.

`PROMISE-11`, delegate and check, is placed `P0` because the whole delegation
argument rests on it and `GROUND.md` already records `GROUND-010` as a claim the
node cannot presently keep. It is simultaneously the furthest from met. If one
priority call in this table is wrong, it is most likely that one.

`PROMISE-12` and `PROMISE-16` have no criterion. `conformance/requirements.py`
enumerates exactly nine, so minting a tenth changes the oracle as well as this
document, and which of the three admissible resolutions applies — mint, record
as carried by an existing criterion, or move out of scope — is Bdo's.

## The Phase I qualification profile

**`Phase I · Local Sovereign Foundation`.** Nine criteria, `PROD-I-1` through
`PROD-I-9`, retained as the first qualification profile. The exact terminal
profile is preserved at `archives/PRD-PHASE-I-TERMINAL.txt`; the later
`archives/PRD-PHASE-I.md` preserves post-terminal strengthening as historical
evidence. These criteria are not the product and never were; later campaigns
may derive different profiles without rewriting what Phase I closed against.

They keep their identifiers, their predicates in `SPEC.md`, and their fixtures
in `conformance/`. The service manifests, the oracle, the SPEC traceability
table and the epic tree all address them. `Today` is the reference participant's
standing from `services/asset/conformance/BASELINE.md`; this document may not
advance it.

### PROD-I-1 · Propose

A model session that has never run here before enters a proposal carrying its
author, its sources and its cost, claiming no authority it holds, and that
proposal reaches a named operator surface where a human can read it and act. An
instanced session asserts the authority it would need; the record does not grant
it, because a session holds no continuous identity a grant can attach to.
Evidences `PROMISE-04`, `PROMISE-07` · predicate `SPEC.md` PROD-I-1 · fixtures
`CONF-I1`, `CONF-I1-SURFACE-DEF`, `CONF-I1-CLAIM-DEF` · today `FAIL`: no content
address, no source addresses, no cost.

### PROD-I-2 · Remember

What the node holds comes back byte-identical, and anything derived from it
resolves its source, reader, version, fidelity and omissions.
Evidences `PROMISE-05`, `PROMISE-02` · predicate `SPEC.md` PROD-I-2 · fixture
`CONF-I2` · today `PASS`, the only one.

### PROD-I-3 · Cross

A human and a model exchange through the same transition, with origin and
projection visible on both sides and a receipt at the end.
Evidences `PROMISE-04` · predicate `SPEC.md` PROD-I-3 · fixture `CONF-I3` ·
today `FAIL`: no second binding, no fully declared crossing.

### PROD-I-4 · Gate and retract

Every admission is marked and receipted, and a wrong entry is countered without
the original disappearing.
Evidences `PROMISE-07`, `PROMISE-08` · predicate `SPEC.md` PROD-I-4 · fixture
`CONF-I4` · today `FAIL`: the counter receipt does not link what it counters.

### PROD-I-5 · Typed authority

Authority arrives as a typed, scoped, revocable grant. Machine authority may
settle verification-typed truth; judgement-typed truth needs a person.
Evidences `PROMISE-03`, `PROMISE-04` · predicate `SPEC.md` PROD-I-5 · fixtures
`CONF-I5`, `CONF-I5-GRANT` · today `FAIL`: the paired typed verification grant
and commit cannot be demonstrated.

### PROD-I-6 · Founder judgement budget

Work needing a person's decision queues for one and stops only that operation;
where judgement was spent is visible.
Evidences `PROMISE-09` · predicate `SPEC.md` PROD-I-6 · fixture `CONF-I6` ·
today `FAIL`: refuses on the spot instead of leaving a pending right.

### PROD-I-7 · Independent qualification

Someone who was not here finds the authority, runs the suite, reconstructs the
evidence and reaches a verdict with no oral explanation.
Evidences `PROMISE-10`, `PROMISE-11`, thinly `PROMISE-03` · predicate `SPEC.md`
PROD-I-7 · fixture `CONF-I7` · today `FAIL`: no clean-room witness run and no
competence measurement exist.

### PROD-I-8 · Joint sign

A ratified claim is checked again at runtime, naming validator, version, inputs
and run, returning reproduced, dissented or unattestable.
Evidences `PROMISE-11` · predicate `SPEC.md` PROD-I-8 · fixture `CONF-I8` ·
today `FAIL`: general runtime attestation is not implemented.

### PROD-I-9 · Bring your own model

From one unchanged node, two materially different model bindings attempt the
same named operation through the same transitions, checks and receipts, each
recording what it used and what it cost. Provider loss costs the provider.
Evidences `PROMISE-01`, `PROMISE-02`, `PROMISE-06` · predicate `SPEC.md`
PROD-I-9 · fixture `CONF-I9` · today `FAIL`: no model-binding contract and no
two-model portability run.

### The two-binding proof

One human-facing binding and two materially different model bindings run the
same authoritative transitions and return compatible receipts; one model arrives
through the BYOM contract. Three bindings in total, because either half alone is
cheap and the pair is not. This profile's hardest criterion, and it evidences
`PROMISE-01`, `PROMISE-04` and `PROMISE-06` together.

### Later profiles

Each roadmap phase past `P0` earns its own profile, and none exists yet. The
shape is set here: named criteria with predicates in `SPEC.md` and fixtures in
`conformance/`, addressed by identifier, never advanced by the document that
declares them.

## Success metrics

Usage metrics would be theatre on a node with one human and some models. These
are evidence metrics, each computable from something that already exists.
**Proposed, not accepted** — whether the standard's metrics section may be
satisfied this way is Bdo's call.

| Measure | Read by | Today | Target |
| --- | --- | --- | --- |
| Journeys walkable end to end | `sov_canon.py trace` | 2 of 14 | every in-scope journey |
| Declared operations reachable | the operation surface | 5 of 140 | every operation a live journey needs |
| Requirements independently observed | `sov_standing.py` | 0 | every P0 |
| Promises carried by no criterion | this document | 2 | 0 |
| Product areas serving no requirement | this document | 0 | stays 0 |
| Reference participant conformance | the asset baseline | 1 of 9 | 9 of 9 |
| Work items closed with a named terminal | does not exist | unmeasured | all |
| Time for a fresh participant to be useful | the cold-start benchmark | measured daily | falling, drift explained |
| Node operable with every provider removed | a drill; does not exist | unmeasured | passes |

The last two rows are the honest gaps. Custody and closure is a top-level
requirement with no counter behind it, and `PROMISE-02` is the product's central
claim with nothing that tests it by actually removing the providers.

## Non-functional requirements

Long-standing, and never collected in one place before. One line each; the
owning document is authority.

- **Local-first.** Tests use temporary directories, fixed inputs, bounded waits
  and no network. No external-world effect without a declared adapter, a data
  boundary and a receipt (`AGENTS.md`).
- **Dependency restraint.** Python 3.11+, standard library by default. A runtime
  dependency requires a named boundary, an observed need, declared failure
  behaviour and a decision record (`ENGINEERING.md`).
- **Verification.** `python scripts/verify.py` is the required gate. Wall time is
  graded, not pass/fail; per-check ceilings in
  `contracts/verification-budget.json` attribute an overrun to the check that
  owns it; one check past thirty seconds refuses (`decisions/0081`).
- **Data boundary.** Every model crossing declares its mode. Silent provider
  fallback is forbidden (`BYOM.md`).
- **Secrets.** Never committed, never printed in logs, receipts, exceptions,
  prompts, fixtures or snapshots. Only opaque credential references.
- **Portability.** No provider SDK type may enter a kernel or service contract.
- **Storage.** SQLite for the reference record, content-addressed filesystem for
  payload bytes. Search, graph and interface stores are rebuildable projections
  unless a contract says otherwise.
- **Module budget.** Production modules under 300 lines, split by owned
  responsibility. Named debt is recorded rather than grandfathered.

Security, reliability and accounting are product areas above with requirements
still to be written. Isolation, recovery, disaster drills, tenancy and
operational objectives are named in `ROADMAP.md` at `P5` and `P8` and have no
requirement here yet. That is a gap, recorded rather than papered over.

## Surfaces

Human and model bindings may present different projections and must resolve the
same transitions, authority checks and receipts (`SPEC.md`, Interface parity). A
board or interface holds no authority of its own: every object on it resolves to
an addressed system object and every gesture to a declared operation. Today the
surfaces are a CLI and declared machine interfaces; the Console Service owns the
operator surface and only its continuity path is built.

## Dependencies and constraints

- Every model requirement depends on `invoke_model`, declared in
  `contracts/kernel-transitions.json` and implemented by no kernel. It blocks
  `PROMISE-01` and `PROMISE-06` at the same point.
- Evidence depends on an observation service that does not exist: `observe_run`
  has no service behind it, and `AI-NATIVE.md` check 3 reads `UNATTESTABLE` on
  every service assessment.
- Composition depends on Gateway, Identity and Authority crossings; four of the
  eleven service boundaries are declared with no implementation.
- Skills depend on a skill contract that does not exist. The `.claude/` harness
  skills are host plumbing holding no standing and are not the product's skills.
- `ENGINEERING.md` owns the growth triggers deciding when HTTP, queues,
  containers or a remote database become admissible. None has fired.

## Assumptions

- One person and their models are a sufficient first market; a node whole at any
  size is not a reduced edition (`GROUND-016`).
- Local models will stay capable enough to make provider substitution real
  rather than nominal. Unproven, and load-bearing for `PROMISE-02`.
- Independent observation can be automated well enough to be routine. If it
  cannot, `PROMISE-11` reduces to a human re-checking everything and the
  delegation argument fails.
- The governing document set can carry product meaning without a database in
  front of it. This has strained once already: the disconnection between
  `CANON.md` and this document went unnoticed for four days.
- Twenty-two areas is a decomposition, not a discovery. If two of them keep
  needing the same contract, they are one area.

## Risks and open questions

`OPEN-SEAMS.md` is the register — nineteen open, one closed. Bearing on
requirements:

- **The witness gap.** `GROUND-010` is a claim the node cannot presently keep,
  said so in the accepted Ground. Highest-consequence open item, and `P0`
  requirement `PROMISE-11` sits on it.
- **Scope has widened faster than the canon.** Thirteen product areas serve no
  promise, three of which are genuine undertakings. If the canon does not grow,
  this document holds product intent the accepted layer above it does not.
- **Grounding is new.** It appears in no contract or service and enters the
  product here. It is the one area not read out of the repository.
- **Priority is proposed and unaccepted.** If it is wrong, the register misleads
  in the most consequential way a PRD can.
- **`phase:i` closed incomplete** with `succeeded_by` null and five residual
  custodies `PROPOSED`. Which roadmap phase opens next is Bdo's to set.
- **Two things are named gateway** (S18); **unattestable effectiveness** (S4)
  and **cold-start semantics** (S5) both gate `PROMISE-10`.

## Release plan

This document does not schedule. `ROADMAP.md` owns the ladder, `P0` through
`P9`, each exiting on a demonstrated product result rather than component
percentages. `contracts/phases.json` owns what a campaign committed to and how
it ended.

## Out of scope

- A graphical production interface ahead of `P4`.
- Automated external-world effects ahead of `P6`, which is an owner decision
  rather than an engineering one.
- World rollback. Retraction adds a counter-record and never claims consumed
  resources came back.
- Distributed consensus.
- A universal ontology or a frozen encoding.
- Importing a predecessor implementation wholesale.
- Optimizing performance ahead of semantic conformance.
- Treating the chosen name as evidence of maturity or public clearance.
- Treating any one area — Asset, Gateway, Skills, Boards, Federation — as the
  product.

## References

`GROUND.md` · `CANON.md` · `SYSTEM.md` · `CONTRACT.md` · `CLASSIFICATION.md` ·
`SPEC.md` · `AI-NATIVE.md` · `BYOM.md` · `ENGINEERING.md` · `SDLC.md` ·
`ROADMAP.md` · `archives/ROADMAP-F0-F6.md` · `OPEN-SEAMS.md` · `STATUS.yaml` ·
`archives/PRD-PHASE-I-TERMINAL.txt` · `archives/PRD-PHASE-I.md` · `contracts/phases.json` · `contracts/product-canon.json` ·
`contracts/product-ground.json` · `contracts/closure-ownership.json` ·
`contracts/custodies.json` · `conformance/requirements.py` ·
`services/asset/conformance/BASELINE.md` · `decisions/0052` · `decisions/0081`

## Standing

`PRODUCT SCOPE CANDIDATE`, artifact standing `OPEN`. `PRD.md` is a root
governing document and sits outside the standing landing grant
(`contracts/standing-grants.json`), so this lands by Bdo's hand and not by the
loop. It changes no standing in `STATUS.yaml`.

Owner-directed: the title, the subtitle, the product outcome, the twenty-two
areas, and the custody and closure requirement, all stated by Bdo on 2026-08-28.
Drafted from the repository and proposed: the problem statement, the priority
ordering, the success metrics, the per-area standing readings, and the coverage
finding.

What would defeat this document:

- a requirement that fails the admission test — failing it would not mean the
  product is unfinished;
- a product area that no requirement serves, or a requirement that belongs to no
  area;
- a user-facing undertaking here that `CANON.md` does not promise, which would
  mean product intent was invented below the layer that holds it;
- a predicate or defeating case restated here rather than cited, which is the
  defect that ended revision 1;
- a priority ordering Bdo rejects, which is the most likely correction and the
  cheapest to make.
