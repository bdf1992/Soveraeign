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

## What the first operational version must prove

Phase I is qualified when an independent fresh witness can use the repository
alone to demonstrate that:

1. A model can submit an attributed proposal with its cost recorded.
2. Sources and derived records are immutable, addressed, and reconstructable.
3. A human and a model can exchange useful state with provenance intact.
4. Admission is gated and record retraction preserves history.
5. Authority is typed, scoped, recorded, revocable, and correctly refused.
6. Pending human judgement remains visible without blocking unrelated work.
7. Ratified executable claims receive reproducible runtime attestations.
8. Human and model interfaces use the same authoritative kernel semantics.
9. Two different model bindings can perform the same named operation without a
   provider-specific authority path or loss of local continuity.

Passing tests is necessary but not sufficient. The evidence must be
reconstructable by an independent witness, and Bdo retains the judgement call
on whether Phase I is operationally accepted.

## Current repository state

This repository is in **founding**. It now contains a proposed stack-neutral
logical specification, an executable conformance oracle, and an experimental
Asset Service reference participant. It contains no production runtime and
makes no production stack choice. These artifacts are built evidence, not an
independent witness or owner ratification.

The founding set contains:

- `SYSTEM.md` — the system boundary and operational model;
- `CLASSIFICATION.md` — the proposed controlled vocabulary and identity tests;
- `AI-NATIVE.md` — the falsifiable per-surface standard and verdict derivation;
- `BYOM.md` — the personal-local ownership and model-portability pattern;
- `ENGINEERING.md` — the minimal reference stack and composable kernel primitives;
- `services/asset/` — the Asset Service charter, contract, reference participant, and tests;
- `services/proofing/` — the proposed sibling review-and-approval service boundary;
- `CONTRACT.md` — invariants implementations must preserve;
- `PRD.md` — the normalized Phase-I requirements;
- `SPEC.md` — the proposed stack-neutral Phase-I logical specification;
- `ROADMAP.md` — evidence-gated construction phases;
- `STATUS.yaml` — machine-readable authority, standing, and open decisions;
- `OPEN-SEAMS.md` — contradictions that must remain visible;
- `decisions/` — consequential choices and their authority;
- `conformance/` — executable positive and defeating logical controls;
- `lineage/`, when present — predecessor standings and immutable source evidence;
- `AGENTS.md` — the normative operating contract for model contributors;
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

1. Read `AGENTS.md`, `CONTRIBUTING.md`, and `STATUS.yaml`.
2. Read `SYSTEM.md`, `CONTRACT.md`, `PRD.md`, and `SPEC.md` as one governing set.
3. Read `ENGINEERING.md` and inspect `OPEN-SEAMS.md` before implementation.
4. Run `python scripts/verify.py`; the dependency-free local and CI loop is
   budgeted to finish in under three seconds after Python starts.
5. Work the next declared gate in `ROADMAP.md`; use the proposed reference
   baseline without treating it as owner-ratified or importing an ancestor
   implementation.

## Immediate objective

Close the founding layer without promoting implementation into policy:

- reconcile the canonical documents against the locked evidence;
- resolve stale revision references;
- preserve unresolved semantic disagreements;
- review and ratify or strike `CLASSIFICATION.md` and `SPEC.md`;
- bind the executable conformance observations to the reference Asset Service;
- preserve known participant failures instead of weakening the oracle;
- then implement the shared kernel required for two independent bindings.

The next code change must satisfy an already-visible conformance failure. It
must not decide what the product means.

## Publication boundary

The public repository contains the canonical synthesis, contracts, logical
testbed, and reference participant. The historical evidence archive and
ancestor registry are not published by default. When absent, verification
reports the archive as unavailable rather than claiming its source hashes were
checked. See `PUBLICATION.md`.
