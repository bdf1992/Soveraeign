# Product Requirements

Status: `PROPOSED · REVISION 2 · NOT OWNER-ACCEPTED`
Owner: Bdo, root seat · Drafted by Claude, 2026-08-28 · Applies to: the whole
product, no phase

This document describes Soveraeign as a product. It is not scoped to a campaign.
Revision 1 was `Product Requirements — Founding and Phase I`; it is archived
byte-identical at `PRD-PHASE-I.md`, where it remains the pinned definition of
`phase:i` in `contracts/phases.json`. Read that file for what Phase I committed
to and how it closed; read this one for what the product is required to do.

## What this document owns, and what it does not

It owns the product's requirements: what Soveraeign must let a person or a model
actually do, how important each one is, how you would know it works, and what is
deliberately not being built.

It does not restate rules other documents own. Each requirement below points at
the document that carries its predicate and the fixture that defeats a false
claim. A rule copied here would be a second authority for the same rule, which
`AGENTS.md` forbids — and being that copy is how revision 1 stopped being a PRD.

| Not owned here | Owned by |
| --- | --- |
| What kind of product this is, permanently | `GROUND.md`, sixteen claims |
| The exact wording of what the product undertakes | `CANON.md`, promises and journeys |
| The system boundary and operating model | `SYSTEM.md` |
| The invariants | `CONTRACT.md` |
| Vocabulary, standing ladders, artifact lifecycle | `CLASSIFICATION.md` |
| The predicate each requirement must satisfy | `SPEC.md` |
| The fixture that proves or defeats it | `conformance/` |
| The order the work is attempted in | `ROADMAP.md`, F0–F6 |
| Current standing and what waits on the owner | `STATUS.yaml` |
| What a closed campaign committed to | `PRD-PHASE-I.md`, `contracts/phases.json` |

The admission test for anything on this page is Bdo's, ruled in
`decisions/0052` and recorded in `CLASSIFICATION.md`, Two requirement ladders:
**would failing it mean the product is not done?** A statement that would make
Soveraeign a *different product* if it changed belongs one level up, in
`GROUND.md`.

## Summary

Soveraeign is a locally sovereign environment in which a person and the models
they choose operate one governed record. Both act through the same state, the
same permissions, the same transitions, the same evidence and the same history.
Compute is borrowed from wherever is convenient; custody of the record, the
authority over it, and the ability to keep operating are not.

The first deployment is one person's node on one machine. The same node contract
supports a team later without the personal case having been a reduced edition.

## Problem statement

An enterprise that wants models doing substantive work today chooses between two
bad options.

**Adopt a provider's platform,** and the operational memory, the permission
model, the audit trail and the continuity of the business come to live inside
someone else's system. Changing providers becomes a migration. Losing one
becomes an outage of the enterprise, not of a vendor.

**Bolt an assistant onto existing software,** and the model is not an operator
at all. It drafts, suggests and summarizes beside a system it cannot act in.
Removing it removes a convenience rather than a capability, which is the test
`AI-NATIVE.md` applies and most surfaces fail.

Underneath both sits the same unsolved problem: **nothing distinguishes a model
that did the work from a model that says it did.** A confident report, a
successful execution, a green build and an agreed-with answer all arrive looking
identical. Without a way to tell them apart, delegation to a model cannot be
scaled past what one person can personally re-check — and that ceiling, not
model capability, is what limits how much work can actually be handed over.

Soveraeign's claim is that these are one problem. A record that can say who did
what, under whose authority, over exactly what state, and whether anyone
independent confirmed it, is the same record that makes the provider
substitutable — because everything that matters is held locally in a form no
provider defines.

*Derived from `GROUND.md` (each claim's "what changing it would mean" line),
`SYSTEM.md` Scope, and `AI-NATIVE.md` Definition. Marked proposed: the problem a
product solves is owner-held intent, and this is a reading of accepted material
rather than a statement Bdo has made in these words.*

## Goals

The product's undertakings are the promises in `CANON.md`, owner-accepted
2026-08-24. They are stated there and registered here; this document adds
priority, acceptance and current state to each rather than restating it.

## Users

Ten participants, defined in `CANON.md`, Who this is for. Owner is deliberately
not among them: it is a context that sets which binding and projection a person
arrives through, over whatever role they hold (`decisions/0020`).

| Participant | What they came here to do |
| --- | --- |
| `human-operator` | Do domain work without learning the node's internals first; see what happened while away; decide what only a person can decide |
| `model-operator` | Discover the legal operations from the artifact alone; act inside a live grant; be refused legibly outside one |
| `model-bringer` | Keep custody of the record while changing which model runs; know what each model consumed |
| `agent` | Choose among reachable operations without widening its own authority; escalate without stalling everything else |
| `worker` | One bounded task, one unambiguous input state, a lease that fences it against a newer holder |
| `witness` | Reach the durable output without relying on the executor's account of it; record a dissent that stays visible |
| `domain-owner` | A mandate narrow enough to finish; a resource envelope with a visible remainder; a witness who is not themselves |
| `node-owner` | Stand a node up and know it is theirs; grow or federate without migrating authority elsewhere |
| `external-system` | Be reached only through a declared crossing that leaves a receipt |
| `peer-node` | Cross into another node without either absorbing the other |

## User journeys

Fourteen, defined in `CANON.md`, How a promise becomes usable. A journey is one
participant's complete intention, not a screen. `python scripts/sov_canon.py
trace JOURNEY-nn` walks one down to the operations it needs and says which are
reachable, which are declared and unbuilt, and which no service declares at all.

Two are walkable today: `JOURNEY-03`, picking up work left in another session,
and `JOURNEY-04`, putting something under governed custody. The other twelve are
one to eight operations short. That table is the scope conversation this
document exists to make possible, and it is regenerated rather than copied here.

## Requirements

The requirements **are** the promises. Minting a second identifier for the same
undertaking would create exactly the ladder collision `CLASSIFICATION.md` warns
about, and `CANON.md`'s promises are already owner-accepted, already
product-wide, and already carry a phase marker.

`PROD-I-1` through `PROD-I-9` are not retired and not renamed. They are the
Phase-I *acceptance set* — nine predicates with fixtures — and each appears below
under the requirement it evidences. `conformance/requirements.py` still
enumerates exactly those nine.

Priority is `P0` when the product is not the product without it, `P1` when the
product works but cannot be trusted without it, `P2` when it is genuinely
wanted later. **Priority is proposed, not accepted.** Nothing in this repository
has ever ranked one requirement above another, and that absence is the most
likely mechanism behind the ruling that closed Phase I: work went where it went
because nothing said what mattered more.

| # | Requirement | Pri | Phase | Evidenced by | State |
| --- | --- | --- | --- | --- | --- |
| `PROMISE-04` | One world | P0 | now | `PROD-I-3` | 8 of 11 operations reachable |
| `PROMISE-07` | Every crossing returns a receipt | P0 | now | `PROD-I-4` | 13 reachable, 1 missing |
| `PROMISE-02` | Custody stays here | P0 | now | `PROD-I-9` | 2 of 4, 4 missing |
| `PROMISE-03` | You can find out what can be asked | P0 | now | `PROD-I-7` (thin) | 2 of 9 |
| `PROMISE-11` | Delegate and check | P0 | now | `PROD-I-7`, `PROD-I-8` | 1 of 7 |
| `PROMISE-05` | You can find out why | P1 | now | `PROD-I-2` | 10 of 11 |
| `PROMISE-08` | Correction never erases | P1 | now | `PROD-I-4` | 4 of 9 |
| `PROMISE-09` | Your judgement is the scarce thing | P1 | now | `PROD-I-6` | 0 of 5 |
| `PROMISE-01` | Bring your own participant | P1 | now | `PROD-I-9` | 18 of 25, 5 missing |
| `PROMISE-06` | The model is swappable | P1 | now | `PROD-I-9` | 2 of 2, 2 missing |
| `PROMISE-10` | Useful from the artifact alone | P2 | now | `PROD-I-7` | 2 of 7 |
| `PROMISE-12` | Work carries across a boundary | P2 | now | **none** | delivered |
| `PROMISE-16` | Decide against exact state | P2 | now | **none** | 1 of 8 |
| `PROMISE-15` | Cross to another node | P2 | later | none needed yet | 2 reachable |

Reach figures are from `python scripts/sov_canon.py promises` and move as the
node changes; treat the column as a pointer to that command, not as a fact this
document holds.

### P0 · The product is not the product without these

**`PROMISE-04` · One world.** People and models act through the same records,
permissions, transitions, evidence and history. Neither gets a private door. A
surface that reaches authoritative state without crossing a declared operation
fails this outright.
*Acceptance:* `SPEC.md` PROD-I-3 and Interface parity ·
`conformance/scenarios.json` CONF-I3 · today the reference participant fails it:
no second binding and no fully declared crossing exist.

**`PROMISE-07` · Every crossing returns a receipt,** including the ones that
refuse, fail, or leave a judgement unresolved. A refusal is a result, not an
absence of one.
*Acceptance:* `SPEC.md` PROD-I-4 · CONF-I4 · today the original and counter both
survive but the counter receipt does not link the receipt it counters.

**`PROMISE-02` · Custody stays here.** Custody of the record, the authority over
it, and the ability to keep operating stay with the node. Losing a provider
costs that provider, not the enterprise. This is the requirement the word
sovereign refers to.
*Acceptance:* `SPEC.md` PROD-I-9, provider-loss clause · CONF-I9 · `JOURNEY-12`,
standing up a node, needs two operations no service declares.

**`PROMISE-03` · You can find out what can be asked** of this node, by whom, and
over what, without being told by a person who already knows. This is what makes
a model an operator rather than a guest.
*Acceptance:* carried thinly by `SPEC.md` PROD-I-7, which is about qualifying
the requirements rather than discovering operations. `GROUND-006` already cites
PROD-I-7 for this. **A first-class predicate for discovery does not exist and is
the clearest gap in the acceptance set.**

**`PROMISE-11` · Delegate and check.** Bounded work can be handed to someone or
something else and the result checked through a path they did not control. A
build never witnesses itself.
*Acceptance:* `SPEC.md` PROD-I-7 and PROD-I-8 · CONF-I7, CONF-I8 · `GROUND.md`
records this as a claim the node cannot presently keep. Runtime attestation is
not implemented and no clean-room witness run exists. Of the five P0
requirements this is the furthest from met and the one the whole delegation
argument rests on.

### P1 · Works, but cannot be trusted without these

**`PROMISE-05` · You can find out why** anything is what it is: its source, its
version, who read it, what was left out, and what it cost.
*Acceptance:* `SPEC.md` PROD-I-2 · CONF-I2 · the only requirement the reference
participant currently passes.

**`PROMISE-08` · Correction never erases.** What the node did can be corrected
without pretending it never happened and without a false claim that consumed
resources came back.
*Acceptance:* `SPEC.md` PROD-I-4 · CONF-I4.

**`PROMISE-09` · Your judgement is the scarce thing.** Requests for a person's
decision queue without stopping unrelated work, and where judgement was spent is
visible. No invented quota.
*Acceptance:* `SPEC.md` PROD-I-6 · CONF-I6 · a missing judgement currently
refuses on the spot instead of leaving a visible pending right. Note a
disagreement worth resolving: `contracts/phases.json` grades judgement
visibility `SUBSTANTIALLY_EARNED` while the canon reads zero of five operations
reachable. The two are measuring different things and neither is wrong.

**`PROMISE-01` · Bring your own participant** into a node you control, discover
what it may do under its actual authority, do substantive governed work, and
inspect the resulting history without surrendering custody to the model or its
provider.
*Acceptance:* `SPEC.md` PROD-I-9 · CONF-I9 · `model.invoke` and
`model.declare-binding` are declared by no service.
`contracts/kernel-transitions.json` declares `invoke_model` and no kernel
implements it.

**`PROMISE-06` · The model is swappable.** Changing which model runs changes
quality, latency and cost and changes nothing about state, standing, authority,
receipts or contracts. An unavailable model refuses visibly; substitution is
never silent.
*Acceptance:* `SPEC.md` PROD-I-9 · CONF-I9 · the two-binding proof below.

### P2 · Genuinely wanted, genuinely later

**`PROMISE-10` · Useful from the artifact alone,** and how long that took is
measured rather than assumed. The cold-start benchmark exists and is a governed
surface; the measurement has no fixture that fails when it is absent.
*Acceptance:* `SPEC.md` PROD-I-7 · CONF-I7.

**`PROMISE-12` · Work carries across a boundary** — a new session, a new
operator, a new model, tomorrow. **Delivered.** The Console continuity path is
built and self-tested, `JOURNEY-03` is walkable, and no requirement ever asked
for it. Registering it here is the repair.

**`PROMISE-16` · Decide against exact state:** decide against an exact version
rather than the thing in general, have the decision attached to that version,
and have someone who was not you inspect or counter it. This is the Proofing
Service. `GROUND.md` says explicitly that proofing belongs in a journey and this
document; `JOURNEY-11` exists and the requirement did not until now.
*Acceptance:* no predicate covers it. Proofing is a boundary with one of eight
operations reachable.

**`PROMISE-15` · Cross to another node** without either node absorbing the
other. Marked `LATER` in the canon so the product world is whole while this
document deliberately does not require it yet.

## The acceptance set

Nine named criteria, `PROD-I-1` through `PROD-I-9`. They are what the
requirements above are graded against, and they are the identifiers the service
manifests, the conformance oracle, the traceability table and the epic tree all
address. Each names the requirement it evidences and points at the document that
states the predicate; the predicate itself is `SPEC.md`'s and the defeating
fixture is `conformance/`'s, and restating either here is what ended revision 1.

`Today` is the reference participant's standing from
`services/asset/conformance/BASELINE.md`. This document may not advance it.

### PROD-I-1 · Propose

A model session that has never run here before can enter a proposal that carries
its author, its sources, its cost and no authority.
Evidences `PROMISE-04`, `PROMISE-07` · predicate `SPEC.md` PROD-I-1 · fixture
`CONF-I1` · today `FAIL`: no content address, no source addresses, no cost.

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

Someone who was not here can find the authority, run the suite, reconstruct the
evidence and reach a verdict with no oral explanation.
Evidences `PROMISE-10`, `PROMISE-11`, and thinly `PROMISE-03` · predicate
`SPEC.md` PROD-I-7 · fixture `CONF-I7` · today `FAIL`: no clean-room witness run
and no competence measurement exist.

### PROD-I-8 · Joint sign

A ratified claim is checked again at runtime, naming validator, version, inputs
and run, returning reproduced, dissented or unattestable.
Evidences `PROMISE-11` · predicate `SPEC.md` PROD-I-8 · fixture `CONF-I8` ·
today `FAIL`: general runtime attestation is not implemented.

### PROD-I-9 · Bring your own model

From one unchanged node, two materially different model bindings attempt the
same named operation through the same transitions, checks and receipts, each run
recording what it used and what it cost. Provider loss costs the provider.
Evidences `PROMISE-01`, `PROMISE-02`, `PROMISE-06` · predicate `SPEC.md`
PROD-I-9 · fixture `CONF-I9` · today `FAIL`: no model-binding contract and no
two-model portability run.

**Two requirements have no criterion.** `PROMISE-12` is delivered and was never
graded; `PROMISE-16` is a boundary with no predicate.
`conformance/requirements.py` enumerates exactly nine, so minting a tenth changes
the oracle as well as this document. Which of the three admissible resolutions
applies — mint, record as carried, or move out of scope — is Bdo's.

## The two-binding proof

One human-facing binding and two materially different model bindings must run
the same authoritative transitions and return compatible receipts. One of the
two models arrives through the BYOM contract. Three bindings in total: it is
same-world parity and two-model substitutability proved at once, because either
alone is cheap and the pair is not. This is the single hardest acceptance in the
document and it evidences `PROMISE-01`, `PROMISE-04` and `PROMISE-06` together.

## Success metrics

Usage metrics would be theatre on a node with one human and some models. These
are evidence metrics, and every one is computable today from something that
already exists. **Proposed, not accepted** — whether the standard's metrics
section may be satisfied this way is Bdo's call.

| Measure | Read by | Today | Target |
| --- | --- | --- | --- |
| Journeys walkable end to end | `sov_canon.py trace` | 2 of 14 | every `now`-phase journey |
| Declared operations reachable | the operation surface | 5 of 140 | every operation a `now` journey needs |
| Requirements with an independent observation | `sov_standing.py` | 0 | every P0 |
| Promises carried by no requirement | this document | 0, after this revision | stays 0 |
| Reference participant conformance | the asset baseline | 1 of 9 | 9 of 9 |
| Time for a fresh participant to become useful | the cold-start benchmark | measured daily | falling, drift explained |
| Node operable with every provider removed | a drill, does not exist | unmeasured | passes |

The last row is the honest gap: `PROMISE-02` is the product's central claim and
nothing currently tests it by actually removing the providers.

## Non-functional requirements

Real and long-standing, and never collected in one place before. Stated here in
one line each; the owning document is authority.

- **Local-first.** Tests use temporary directories, fixed inputs, bounded waits
  and no network. No external-world effect without a declared adapter, a data
  boundary, and a receipt (`AGENTS.md`).
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
  prompts, fixtures or snapshots. Only opaque credential references (`AGENTS.md`).
- **Portability.** No provider SDK type may enter a kernel or service contract.
- **Storage.** SQLite for the reference record, content-addressed filesystem for
  payload bytes. Search, graph and UI stores are rebuildable projections unless
  a contract says otherwise.
- **Module budget.** Production modules under 300 lines, split by owned
  responsibility. Named debt is recorded rather than grandfathered.

## Surfaces

Human and model bindings may present different projections and must resolve the
same transitions, authority checks and receipts (`SPEC.md`, Interface parity).
Phase-I surfaces are a CLI and declared machine interfaces; a graphical
production interface is out of scope. The Console Service owns the operator
surface — sessions, threads, posts, notifications, judgement requests, and
declared dashboard and activity projections — and its continuity path is the
only part built.

## Dependencies and constraints

- Every requirement above depends on the kernel transitions in
  `contracts/kernel-transitions.json`. `invoke_model` is declared and
  unimplemented, which blocks `PROMISE-01` and `PROMISE-06` at the same point.
- `PROMISE-11` depends on an observation service that does not exist:
  `observe_run` has no service behind it and `AI-NATIVE.md` check 3 reads
  `UNATTESTABLE` on every service assessment.
- `PROMISE-16` depends on the Proofing Service, and Proofing depends on Asset
  version identity, which exists.
- Five service boundaries — Gateway, Observation, Proofing, Projection, Registry
  — are declared with no implementation.
- `ENGINEERING.md` owns the growth triggers that decide when HTTP, queues,
  containers or a remote database become admissible. None has fired.

## Assumptions

- One person and their models are a sufficient first market; a node whole at any
  size is not a reduced edition (`GROUND-016`).
- Local models will remain capable enough to make provider substitution real
  rather than nominal. Unproven and load-bearing for `PROMISE-02`.
- The governing document set can carry product meaning without a database in
  front of it. This has already strained once — the disconnection this revision
  repairs went unnoticed for four days.
- Independent observation can be automated well enough to be routine. If it
  cannot, `PROMISE-11` reduces to a human re-checking everything, and the
  delegation argument fails.

## Risks and open questions

`OPEN-SEAMS.md` is the register — nineteen seams open, one closed. The ones that
bear on requirements:

- **The witness gap.** `GROUND-010` is a claim the node cannot presently keep,
  said so in the accepted Ground itself. Highest-consequence open item.
- **Two things are named gateway** (S18), a naming collision caught before both
  halves exist.
- **Unattestable effectiveness** (S4) and **cold-start semantics** (S5) both
  gate `PROMISE-10`.
- **Phase I closed incomplete** with no successor named
  (`contracts/phases.json`). Five residual custodies are attached and
  `PROPOSED`. Which campaign comes next is Bdo's to set and this document does
  not presume it.
- **Prioritization above is proposed and unaccepted.** If it is wrong, the
  requirement register is misleading in the most consequential way a PRD can be.

## Release plan

This document does not schedule. `ROADMAP.md` owns the sequence, F0 through F6,
and `contracts/phases.json` owns what each campaign committed to and how it
ended. `phase:i` is closed `CLOSED_INCOMPLETE`; `succeeded_by` is null.

## Out of scope

- A graphical production interface.
- Automated external-world effects.
- World rollback.
- Distributed consensus. Federation between nodes is `LATER`, not never.
- A universal ontology or a frozen encoding.
- Importing a predecessor implementation wholesale.
- Optimizing performance ahead of semantic conformance.
- Treating the chosen name as evidence of maturity or public clearance.
- Treating any one subsystem — Gauge, Definition, Atlas, Asset — as the product.

## References

`GROUND.md` · `CANON.md` · `SYSTEM.md` · `CONTRACT.md` · `CLASSIFICATION.md` ·
`SPEC.md` · `AI-NATIVE.md` · `BYOM.md` · `ENGINEERING.md` · `ROADMAP.md` ·
`SDLC.md` · `OPEN-SEAMS.md` · `STATUS.yaml` · `PRD-PHASE-I.md` ·
`contracts/phases.json` · `contracts/product-canon.json` ·
`contracts/product-ground.json` · `conformance/requirements.py` ·
`services/asset/conformance/BASELINE.md` · `decisions/0052` · `decisions/0081`

## Standing

`PROPOSED`. Nothing here is owner-accepted until Bdo accepts it. `PRD.md` is a
root governing document and sits outside the standing landing grant
(`contracts/standing-grants.json`), so this revision lands by his hand and not by
the loop.

Carried forward unchanged in meaning from revision 1: the two-binding proof and
the out-of-scope list. Moved out: the nine predicates and their defeating cases,
which `SPEC.md` and `conformance/` already owned. Added: a problem statement,
success metrics, prioritization, non-functional requirements, surfaces,
dependencies, assumptions, risks, and the joins to `GROUND.md` and `CANON.md`
that revision 1 never had.

What would defeat this revision:

- a requirement here that fails the admission test — failing it would not mean
  the product is unfinished;
- a requirement that is not a promise in `CANON.md`, which would mean product
  intent was invented below the layer that holds it;
- a `CANON.md` promise absent from the register above;
- a predicate or defeating case restated here rather than cited, which is the
  defect that ended revision 1;
- a priority ordering Bdo rejects, which is the most likely correction and the
  cheapest to make.
