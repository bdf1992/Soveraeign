# Soveraeign

**A local-first system where people and AI work through the same records, permissions,
operations, and history.**

Soveraeign is built for work shared by people and models. They may use different
interfaces, but neither gets a separate copy of the enterprise or a private path around
its rules.

The node keeps its authoritative records and permissions under the owner's control. A
model can inspect, propose, build, verify, and act when a live grant allows it. Producing
a good answer or successfully running code does not create authority.

## What the product is trying to guarantee

The stable product claims live in `GROUND.md`. In plain language:

- the owner keeps custody of the record, authority, operation, and continuity;
- people and models act on the same governed state;
- authority comes from explicit grants, never confidence or capability;
- meaningful work happens through declared operations with known inputs, limits, and
  expected results;
- important actions bind to exact source state and leave durable receipts;
- a fresh participant can discover what it may do from the artifact itself;
- refusal and failure are recorded results, not missing information;
- corrections preserve what happened instead of rewriting history;
- executors do not get to certify their own success;
- drafts, accepted claims, and currently effective state remain distinct;
- human judgement is reserved for the transitions that actually require it;
- models are replaceable without moving authoritative state into the provider;
- work and resource use can be traced back to the product intent that justified them;
- work survives a new session, operator, model, or day; and
- a one-person node is a complete node, not a reduced edition.

`CANON.md` turns those product claims into promises and user journeys. Requirements,
services, and implementation sit below that.

## What AI-native means here

Soveraeign calls a named operation AI-native when a model can discover and perform that
operation through a declared machine-usable interface while using the same authoritative
state, rules, and history as a human operator.

A chat box or generated suggestion is not enough. The model path must expose real domain
capability, and the system must preserve evidence about what the model read, what it did,
what authority it used, and how the result can be corrected.

Soveraeign's own bar is stricter than that minimum. It also requires full reachability,
typed authority, independent observation, complete receipts, honest treatment of
external effects, cold-start use, human/model parity, model portability, and local
custody.

See [`AI-NATIVE.md`](AI-NATIVE.md) for the exact scoring and qualification rules.

## Local use and Bring Your Own Model

The first deployment target is a personally owned local node. The same node contract can
later support more people or federation without moving its authority or record into a
provider-owned system.

Bring Your Own Model means the owner can bind a compatible local or remote model without
changing the node's authoritative state, service contracts, grants, receipts, or
retraction rules. Each invocation records the model, runtime, host, data boundary, usage,
and cost.

Remote compute is allowed. Remote ownership of the node is not.

See [`BYOM.md`](BYOM.md).

## Sov

**Sov** is the portable operating profile for a model working inside Soveraeign. It helps
the model choose context, select permitted operations, refuse, and hand work off.

Loading Sov grants nothing. Every consequential operation still needs a live typed grant,
and the node remains the authority over its own state.

See [`SOV.md`](SOV.md).

## How governed work moves

The system keeps several steps separate on purpose:

```text
source
-> reading
-> recording or proposal
-> admission
-> ratification
-> runtime attestation
-> effective state
-> operation
-> independent observation
-> receipt
-> correction or retraction
```

A source can be read without being changed. A proposal can exist without being accepted.
An accepted claim can stop being effective. An executor can report success without an
independent observer confirming it. A correction can change current state without
pretending the original event never happened.

Those distinctions are part of the product, not implementation detail.

## Current state

Phase I is closed. `contracts/phases.json` records the terminal state as
`CLOSED_INCOMPLETE`: the phase ended without earning its qualification exit. No successor
phase is active.

That result is intentional. The repository keeps partial implementation evidence without
rounding it up to acceptance. Opening the next phase remains an explicit owner action.
Candidate future work, including issue #173, is not current phase authority merely because
it exists.

`STATUS.yaml` is the machine-readable source for current standing and owner-held items.
`contracts/SUCCESSOR-PREP.md` is the current closed-books gap synthesis; it grants no successor-phase standing.
Issue #148 is the Phase-I boundary-closure ledger.

## Start here

A participant should not need to ingest the governance corpus before learning where they
are or what this node exposes. Start from the live boundary and deepen context only when
the operation in front of you requires it.

### 1. Establish your session boundary

```sh
python scripts/sov_session.py register --intent "<what you are doing>"
python scripts/sov_session.py brief
```

The session registry tells you who else is live, which working tree you occupy, what paths
or non-file resources are held, and which durable principal this session resolves to. It
is coordination plumbing only: presence, identity resolution, or a path claim grants no
authority. For sustained parallel writing, use separate worktrees and explicit claims.

### 2. Discover the node, not a hand-maintained operation list

```sh
python scripts/sov_interface.py show
```

The Node Interface is rebuilt from the repository's declared capability and route sources.
It is a non-authoritative discovery projection: it tells a participant what is declared,
bound, policy-active, reachable, observed, or omitted without turning any of those facts
into permission.

Once an operation is relevant, inspect that operation directly:

```sh
python scripts/sov_interface.py show <operation-id> --binding human
# or
python scripts/sov_interface.py show <operation-id> --binding model
```

Human and model bindings read the same operation. The rendering may differ; the operation,
required inputs, authority requirement, and route do not.

### 3. Load only the owner of the concern you are changing

Follow the discovered operation to its owning service, contract, schema, decision, or
status record. Do not pre-load unrelated governance. The separation is intentional:

```text
principal -> session -> grant -> operation -> Record Service journal -> projection
```

A principal says who the participant is. A session isolates one continuity boundary. A
grant says what an operator may do. The operation belongs to its service. The Record
Service preserves what happened. A projection makes that record easier to read and never
becomes authority merely because it is convenient.

### 4. Before landing, run the repository-owned checks

Python 3.11 or newer is enough:

```sh
python scripts/verify.py
python scripts/sov_next.py
python scripts/sov_traps.py
```

`verify.py` is the required gate. It runs the repository-owned checks and records timing.
The total wall time earns `PLATINUM`, `GOLD`, or `SILVER`; a slow host does not by itself
make the repository semantically wrong. Per-check catastrophic limits still refuse.

`sov_next.py` compares the repository's current signposts instead of guessing what should
happen next. `sov_traps.py` checks repository facts that have repeatedly produced confident
but wrong answers.

[`scripts/README.md`](scripts/README.md) indexes the repository commands. The document map
below is for deeper lookup when a discovered concern actually reaches one of those owners;
it is not a prerequisite reading queue.

## Document map

| Path | What it owns |
| --- | --- |
| `GROUND.md` | The stable claims that define the product |
| `CANON.md` | Participants, promises, and product journeys |
| `SYSTEM.md` | System boundary and operating model |
| `CONTRACT.md` | Invariants implementations must preserve |
| `CLASSIFICATION.md` | Canonical architecture and lifecycle vocabulary |
| `PRD.md` | Current product requirements and success measures |
| `SPEC.md` | Logical objects, transitions, predicates, and refusals |
| `AI-NATIVE.md` | AI-native evaluation and Soveraeign qualification |
| `BYOM.md` | Local ownership and model portability |
| `ENGINEERING.md` | Current replaceable implementation choices |
| `SDLC.md` | Repository delivery and evidence loop |
| `STATUS.yaml` | Current authority, standing, and open owner items |
| `OPEN-SEAMS.md` | Known contradictions that must stay visible |
| `AGENTS.md` | Rules for model contributors |
| `CONTRIBUTING.md` | Working contribution path for people and models |
| `SOV.md`, `bindings/sov/` | Portable Sov profile and host bindings |
| `services/` | Service contracts, implementations, and tests |
| `conformance/` | Positive and defeating semantic cases |
| `decisions/` | Consequential choices and their rationale |
| `diagrams/` | Rebuildable views derived from declared sources |

## What this is not

Soveraeign is not a chatbot, a generic agent framework, a model-owned memory layer, an
ERP rewrite, a universal ontology, a simulation standing in for operation, or a promise
that external effects can always be undone.

Previous work may be kept as evidence or lineage. It enters the current system only
through an explicit claim, decision, contract, test, schema, or reviewed implementation.

## Publication boundary

The public repository contains the current synthesis, contracts, logical testbed, and
reference implementation. Historical evidence and ancestor material are not published by
default. When they are absent, verification reports them as unavailable rather than
claiming they were checked. See `PUBLICATION.md`.
