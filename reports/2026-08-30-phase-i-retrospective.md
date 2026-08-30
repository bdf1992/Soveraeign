# Phase-I Retrospective — Founding Campaign

Status: `REPORT · HISTORICAL · NON-GOVERNING`

Date: 2026-08-30

Controller: GitHub issue #148

## Purpose

This report closes the historical reading of Phase I. It records what the founding campaign demonstrated, what it did not demonstrate, and what its closure teaches about the unit of progress for later work.

It grants no standing, opens no successor phase, and does not reinterpret a failed exit clause as earned. `contracts/phases.json` remains authoritative for the Phase-I terminal: execution `CLOSED`, acceptance `NOT_EARNED`, terminal `CLOSED_INCOMPLETE`, settled by `seat:root`, with no successor named.

## What the campaign proved

Phase I proved that the project can express a meaningful locally sovereign operating model in executable pieces rather than only in prose.

The repository produced reusable evidence for:

- typed, scoped authority and explicit refusal;
- attributable receipts and durable record semantics;
- separation between proposal, admission, ratification, effectiveness, observation, and retraction;
- local-first operation and owner-selected model bindings;
- service manifests, capability projection, and participant-facing discovery;
- an Asset participant with real custody behavior;
- a Record participant with journal and receipt behavior;
- a Console continuity path and operator-facing coordination surfaces;
- a Host read-health path through the Node/Gateway/Host boundary;
- a first Gateway route pattern;
- executable conformance, verification, mutation, and repository hygiene machinery;
- issue, branch, custody, and acceptance records rich enough to reconstruct a large cleanup campaign rather than simply discard it.

Those are real accomplishments. They survive as evidence and reference participants after Phase I closes.

## What the campaign did not prove

Phase I did not prove its own exit.

The terminal record is intentionally explicit:

- X1, predicate-level positive and defeating fixture coverage, was not earned.
- X2, one human-facing binding plus two materially different model bindings through the same transitions, was not earned.
- X3, independent reconstruction of receipts, was not earned.
- X4, judgement visibility, was substantially earned but not fully earned.
- X5, owner operational acceptance, was never reached and must not be retroactively attempted.

The campaign therefore cannot be described as a qualified Phase-I product merely because many components exist or many checks pass.

Several service implementations also remained participant evidence rather than independently witnessed standing. A directory being present, a service reporting `BUILT`, or a test suite passing is not by itself proof that the service boundary is the right boundary, that its crossings are complete, or that a fresh independent participant can reconstruct what happened.

## The central failure: the wrong unit of progress

The founding campaign optimized breadth of construction before it optimized closure density against the exit predicates.

Progress was often counted as:

- another service directory;
- another operation declaration;
- another contract or fixture;
- another branch or worktree carrying a plausible slice;
- another locally green implementation;
- another projection of state.

Those were useful construction signals, but they were not the unit the phase ultimately had to satisfy.

The phase actually needed closed, witnessed verticals in which a claim could travel end to end through identity, authority, execution, record, independent observation, settlement, and receipt reconstruction. Because that shape was not kept on the critical path, the repository accumulated many partially coherent horizontal surfaces while the phase exit remained distant.

This is the main retrospective result:

> The next unit of progress must be a bounded contract plus its crossings and independently readable evidence, not the amount of implementation accumulated behind a service name.

## What the debris taught

### 1. Implementation is evidence about a boundary, not authority for the boundary

Asset, Record, Console, Host, Gateway, adapters, tests, and fixtures are valuable because they expose concrete pressure. They do not become the successor architecture merely because they survived Phase I.

A later service boundary should be re-derived from what it owns, refuses, receives, emits, and must share with other services. Existing code is then tested against that boundary as a reference participant.

### 2. Crossings are first-class architecture

Many hard questions appeared between services rather than inside them: who supplies identity, where authority is checked, what is recorded, which transport is admitted, who owns observation, and what receipt proves the crossing.

When those relationships remain implicit in implementation or fixtures, local correctness can hide system ambiguity.

Later work should therefore treat the crossing itself as an addressable contract.

### 3. Shared primitives must not become private service law

Identity, authority, grants, receipts, record standing, observation, settlement, and refusal semantics recur across boundaries. If one service privately defines them for its own convenience, the system gains incompatible local laws.

The shared kernel should remain the load-bearing semantic substrate. Services may implement domain behavior; they should not silently redefine the meaning of authority or evidence at each boundary.

### 4. Standing must be harder to obtain than code

Phase I repeatedly demonstrated the difference between `BUILT`, `WITNESSED`, and owner-ratified standing. The distinction was useful precisely because many things were built without independent qualification.

Future work should keep that friction. A successful implementation is evidence. Independent reconstruction is different evidence. Human judgement is a separate authority act.

### 5. Branch and worktree concurrency has a real reconciliation cost

The closure campaign began with dozens of non-main refs and required explicit archaeological comparison, branch disposition, rescue-ref retirement, issue refinement, and repeated fresh-reader checks.

Concurrency can increase construction throughput while decreasing confidence about which branch carries the authoritative effect. Later campaigns should prefer bounded concerns and short-lived execution topology, with the durable state returning to `main` quickly.

### 6. Derived projections need explicit parity checks

STATUS, issue labels, documentation, capability maps, diagrams, acceptance queues, and other projections can drift while the underlying source changes. Several closure findings were projection problems rather than core semantic failures.

A derived surface should either be mechanically rebuilt from its source or carry an explicit parity/checking mechanism. A manually maintained duplicate of authority becomes stale authority-shaped debris.

### 7. Verification must measure the change it claims to measure

During final closure, the mutation lane twice exhausted its 35-minute budget because `--changed` effectively mutated historical sites across touched files and routed broad targets through an oversized test suite. Repairing the gate to score mutable sites on changed lines, while preserving the whole-run cap and self-checking the scope, turned a repeated timeout into usable evidence.

The lesson is not to weaken gates when they become expensive. It is to make the instrument correspond precisely to the claim it reports.

## What survives the boundary

Phase-I material falls into three practical classes for later derivation.

### Shared-substrate candidates

Typed identity and authority, refusal semantics, receipts, record/lineage primitives, capability resolution, transition vocabulary, and evidence/provenance shapes are candidates for shared substrate because multiple services need the same meaning.

They remain candidates until a clean successor derivation confirms the boundary.

### Reference participants

Existing service implementations, bindings, adapters, conformance cases, and local workflows remain available as concrete participants against which cleaner contracts can be tested.

They do not carry inherited successor standing. A Phase-I `BUILT` claim may legitimately enter new-zero analysis as `TO_REDERIVE`.

### Historical evidence

Superseded assumptions, phase-specific steering, obsolete projections, branch-specific repair machinery, and rejected or redirected implementation proposals remain history. Their value is explanatory and evidentiary, not operational authority.

## Boundary discipline for the new zero

The repository should reach a literal zero before a successor campaign is opened:

- one default branch: `main`;
- zero open pull requests;
- no active phase;
- Phase I remains terminal by its historical name and definition;
- no surviving ticket, packet, or branch silently carries Phase-I construction authority forward.

At that zero, the next work is derivation, not inherited construction.

The intended order is:

1. derive a complete Service Atlas of independently meaningful boundaries;
2. derive the Crossing Matrix between those boundaries;
3. identify shared primitives that must remain outside any single service;
4. only then propose the smallest coherent successor aperture.

An existing issue, implementation, or roadmap item may turn out to describe the right aperture. It does not gain that status merely by predating the derivation.

## Final retrospective statement

Phase I was productive as a founding architecture campaign and unsuccessful as a closed qualification loop.

Its most important output is therefore not a claim of maturity. It is a better definition of how maturity must be earned:

> define the boundary, define the crossing, define the contract, prove the defeating case, execute the smallest coherent vertical, and let independent evidence determine standing.

That lesson closes the books on Phase I. What follows begins from a deliberate new zero.