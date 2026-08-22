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

Passing tests is necessary but not sufficient. The evidence must be
reconstructable by an independent witness, and Bdo retains the judgement call
on whether Phase I is operationally accepted.

## Current repository state

This repository is in **founding**. It establishes the product boundary and the
evidence needed to derive a logical specification. It intentionally contains no
production runtime implementation and makes no production stack choice.

The founding set contains:

- `SYSTEM.md` — the system boundary and operational model;
- `CONTRACT.md` — invariants implementations must preserve;
- `PRD.md` — the normalized Phase-I requirements;
- `ROADMAP.md` — evidence-gated construction phases;
- `STATUS.yaml` — machine-readable authority, standing, and open decisions;
- `OPEN-SEAMS.md` — contradictions that must remain visible;
- `decisions/` — consequential choices and their authority;
- `conformance/` — positive and defeating scenario seeds;
- `lineage/` — predecessor standings and immutable source evidence;
- `AGENTS.md` — the operating contract for human and model contributors.

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

1. Read `AGENTS.md` and `STATUS.yaml`.
2. Read `SYSTEM.md`, `CONTRACT.md`, and `PRD.md` as one governing set.
3. Inspect `OPEN-SEAMS.md` before making architectural decisions.
4. Run `python scripts/verify_bootstrap.py`.
5. Work the next declared gate in `ROADMAP.md`; do not skip ahead by selecting a
   stack or importing an ancestor implementation.

## Immediate objective

Close the founding layer without inventing implementation policy:

- reconcile the canonical documents against the locked evidence;
- resolve stale revision references;
- preserve unresolved semantic disagreements;
- compile each Phase-I requirement into state, transitions, checks, receipts,
  and defeating fixtures;
- then derive the smallest logical specification capable of supporting two
  independent bindings.

The first code should satisfy an already-visible conformance failure. It should
not be the act that decides what the product means.

