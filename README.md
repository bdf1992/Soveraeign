# Soveraeign

**A local-first operating environment where people and AI systems work through
the same governed enterprise state.**

Soveraeign is an attempt to make AI a native enterprise operator without making
the enterprise dependent on an AI provider. Humans and models receive different
interfaces, but they act through the same records, permissions, transitions,
evidence, and history.

The enterprise keeps custody of its operational memory and authority. A model
may propose, inspect, verify, and act within a delegated scope; it cannot turn
its own confidence, output, or successful execution into authority.

## AI-native, precisely

An enterprise surface is **AI-native** when a model can reach and perform a
substantive domain operation through the system's declared interfaces while
remaining inside the same authoritative state, constraints, and history as a
human operator—and the resulting operation is attributable, inspectable, and
correctable.

The verdict is applied to a **named operation on a surface**, not loosely to an
entire company or product. At minimum:

- the operation must be reachable through a declared machine-usable path;
- commitment, provenance, or retraction must be materially present;
- and removing the AI path must remove substantive domain capability rather
  than a decorative assistant.

Soveraeign holds itself to a stricter bar: same-world human/model parity, typed
authority, independent observation, complete receipts, effect honesty,
cold-start competence, two-binding proof, and local sovereignty.

**[Read the complete AI-Native Standard →](AI-NATIVE.md)**

## Local, personal, and BYOM

The first intended deployment is a personally owned local node. The same node
contract can later support a team or enterprise without turning personal use
into a separate edition or surrendering the record to a central provider.

Soveraeign practices **Bring Your Own Model**: an owner can bind a compatible
local or remote model while keeping the same authoritative state, service
contracts, typed authority, provenance, receipts, and retraction rules. Every
run declares its exact model, runtime, host, data boundary, usage, and cost.

**[Read the Local, Personal, and BYOM pattern →](BYOM.md)**

## Sov, the main operating agent

**Sov** is the portable agency profile loaded by the current underlying model.
It gives the model room to direct its own bounded participation — attention,
context selection, legal next actions, refusal, and handoff — without turning
the profile, prompt, provider, or model into authority. The node still owns its
world; every consequential operation still requires a typed live grant.

**[Load the Sov operating profile →](SOV.md)**

## Why this exists

Most software still assumes one kind of operator: a persistent, accountable
human using screens designed for human perception. AI is then attached beside
that system as a chat box, copilot, or automation layer.

That arrangement can be useful, but it is not AI-native. The model sees a
partial imitation of the enterprise, works through exceptional paths, and
leaves humans to reconstruct what happened afterward.

Soveraeign changes the operator model instead. It asks what an enterprise system
must become when both people and models are expected to operate it directly,
safely, and accountably.

## The governing loop

```text
source
→ declared reading
→ derived recording or proposal
→ admission
→ typed ratification
→ runtime attestation
→ effective operation
→ independent observation
→ receipt
→ correction or retraction
→ revised enterprise state
```

Each step is distinct:

- A source can be read without being changed.
- A recording can exist without being admitted.
- An admitted proposal can remain unratified.
- A ratified claim can stop applying to the present state.
- An operation can report success without independent observation confirming it.
- A record can be retracted without pretending its external effects were undone.

These distinctions are the foundation of the system—not implementation detail.

## What “algorithmic” means here

Soveraeign is algorithmic because consequential work is expressed through
inspectable state, declared inputs, typed authority, executable transitions,
observable outcomes, and attributable receipts.

It does **not** mean removing human judgement. Human judgement is the scarce
resource the system protects: machines should perform the work that can be
verified, while decisions that genuinely require a person remain visible,
bounded, and assigned.

## What Phase I established — and did not

Phase I is closed. `contracts/phases.json` records its terminal as
`CLOSED_INCOMPLETE`: the operating window ended, the qualification exit was not
earned, and no successor phase is named. Its pinned first requirements remain in
`archives/PRD-PHASE-I.md` and `archives/ROADMAP-F0-F6.md`; they are historical
definition, not current work authority.

The closure campaign preserves that result rather than rounding partial evidence
up to acceptance. The next construction aperture, if and when the root seat opens
a successor phase, is issue #173: prove and freeze one deliberately small,
Record-backed, independently observed vertical with one human and two materially
different model bindings before broad architecture expands again.

## Current repository state

This repository is **between phases**. Historical Phase I is terminal
`CLOSED_INCOMPLETE`; no successor phase is active. Issue #148 is the boundary
closure ledger. The repository contains substantial governing and self-tested
implementation evidence, but independent operational qualification remains
narrow and owner acceptance is never inferred from implementation.

The governing and operating set contains:

- `GROUND.md` — the sixteen claims that say what product Soveraeign is;
- `CANON.md` — who a node is for, what Soveraeign undertakes, and the journeys
  an undertaking is reached by;
- `SYSTEM.md` — the system boundary and operational model;
- `CLASSIFICATION.md` — the proposed controlled vocabulary and identity tests;
- `AI-NATIVE.md` — the falsifiable per-surface standard and verdict derivation;
- `BYOM.md` — the personal-local ownership and model-portability pattern;
- `ENGINEERING.md` — the minimal reference stack and composable kernel primitives;
- `services/asset/` — the Asset Service charter, contract, reference participant, and tests;
- `services/proofing/` — the proposed sibling review-and-approval service boundary;
- `CONTRACT.md` — invariants implementations must preserve;
- `PRD.md` — the product's requirements, priority, and success measures;
- `SPEC.md` — the current stack-neutral logical contract; the closed Phase-I
  definition is pinned separately in `contracts/phases.json`;
- `ROADMAP.md` — evidence-gated construction phases and the name crosswalk;
- `SDLC.md` — the operating loop: tiers, dyads, and the Red-gated release requirement;
- `services/console/` — the proposed third sibling operator-surface boundary;
- `diagrams/` — rebuildable views of the corpus, each declaring its source digests;
- `STATUS.yaml` — machine-readable authority, standing, and open decisions;
- `OPEN-SEAMS.md` — contradictions that must remain visible;
- `decisions/` — consequential choices and their authority;
- `conformance/` — executable positive and defeating logical controls;
- `lineage/`, when present — predecessor standings and immutable source evidence;
- `AGENTS.md` — the normative operating contract for model contributors;
- `SOV.md` and `bindings/sov/` — the portable main operating-agent profile;
- `CONTRIBUTING.md` — the contribution workflow for humans and models;
- `.cursorrules` — a concise editor-facing mirror of the root rules.

## What this is not

Soveraeign is not:

- a chatbot or generic agent framework;
- a model-owned memory layer;
- a knowledge graph presented as an enterprise;
- an ERP rewrite undertaken all at once;
- a universal ontology or frozen encoding;
- a simulation standing in for real operation;
- a merger of the predecessor repositories;
- or a claim that external-world effects can always be rolled back.

Previous work is preserved as evidence and lineage. It enters the current
system only through an explicit invariant, decision, conformance case, schema,
or reviewed implementation adoption.

## Start here

Run it before you read it. Python 3.11 or newer, no dependencies to install.

```sh
python scripts/verify.py     # the required gate; graded on wall time, not just pass/fail
python scripts/sov_next.py   # what happens next, and where the signposts disagree
python scripts/sov_traps.py  # facts about this repository that answer confidently and wrongly
```

`verify.py` grades itself `PLATINUM` at three seconds, `GOLD` at six, and
`SILVER` at fifteen. Past fifteen it records debt rather than failing, because a
wall-clock reading measures the host at that instant and not the repository; the
pressure sits on per-check ceilings instead (`decisions/0081`, superseding
`decisions/0050`). One timing condition still refuses: a single check past
thirty seconds. `sov_next.py`
reconciles five signposts and prints one answer with every alias the job travels
under; where the declared gate and the reachable work name different jobs it
reports the disagreement rather than resolving it, because that choice is owner
judgement.

[`scripts/README.md`](scripts/README.md) indexes the whole command surface —
thirty-six entrypoints grouped by the question each one answers.

Then read, in this order:

1. `GROUND.md` and `CANON.md` — what product this is, and what it undertakes.
2. `AGENTS.md`, `SOV.md`, `CONTRIBUTING.md`, and `STATUS.yaml` — how work is
   done here. These govern participants, not the product.
3. `SYSTEM.md`, `CONTRACT.md`, `PRD.md`, and `SPEC.md` as one governing set.
4. `ENGINEERING.md` and `OPEN-SEAMS.md` before implementation.

Use the proposed reference baseline without treating it as owner-ratified or
importing an ancestor implementation.

Writing a binding or an adapter is a different path:
[`bindings/INTEGRATING.md`](bindings/INTEGRATING.md).

## Immediate objective

Finish the phase boundary without silently opening its successor:

- keep current-reader documents, host prompts, issue horizons, and executable
  policy projections consistent with the recorded Phase-I terminal;
- preserve unresolved root judgements as a small explicit docket rather than
  executable branch or phase debris;
- finish the retrospective and exact-main closure receipt in issue #148;
- leave successor-phase opening as an explicit root-seat act.

After that opening, issue #173 is the first construction gate: close one minimal
witnessed kernel vertical before broad service or architecture expansion. The
next code change must satisfy a visible contract or defeating case; it must not
manufacture product meaning merely to create work.

## Publication boundary

The public repository contains the canonical synthesis, contracts, logical
testbed, and reference participant. The historical evidence archive and
ancestor registry are not published by default. When absent, verification
reports the archive as unavailable rather than claiming its source hashes were
checked. See `PUBLICATION.md`.
