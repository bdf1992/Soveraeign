# Experimental Typed-Contract Charting

Status: `EXPERIMENTAL · NON-CANONICAL · ISSUES #40/#41`

This directory tests whether current Soveraeign operating semantics can be derived into a small typed relation graph and projected into bounded local Charts without turning the projection into authority or creating a second System of Record.

It does **not** define the canonical Atlas contract, Registry contract, authority model, prompt format, operator binding, Skill schema, or Capability receipt model. Governing documents remain authoritative.

## Current slice

- `derive.py` reads the existing `SDLC.md` skill axes, workflow templates, and verification/authority stances plus the provisional `.claude` binding declarations.
- The derivation produces canonical Skill/Workflow/Stance points from `SDLC.md` and binding-specific implementation points from `.claude/skills/*/SKILL.md`.
- Each Claude Skill implementation must resolve to exactly one Skill already declared by `SDLC.md`; an unknown implementation fails closed instead of silently extending policy.
- `experiments/qa.skill.json` is a temporary, partial, `PROPOSAL` sidecar owned semantically by `SDLC.md`. It exists only to prove the #41 relation shape and is tracked for removal/relocation by #47/#52.
- The QA sidecar derives `Skill -> requires -> Requirement -> binds -> Capability` without treating a Capability declaration as runtime availability.
- `model.py` validates point/crossing identities and an explicit semantic relation matrix, then projects a bounded Chart under a named paradigm.
- `skill-forest` can now traverse Binding -> implementation -> declared Skill -> explicit Requirement -> declared Capability.
- `operator-navigation` remains intentionally incomplete until live Registry, Broker, Authority, and Binding dependencies close.
- Every derived graph carries a SHA-256 revision over the exact source files used to build it.

There is deliberately no hand-maintained semantic catalog. A generated graph can be inspected at any time with:

```text
python -m charting.derive
```

## Experimental chain

```text
Governing documents + declared binding + explicit experimental declaration
                             ↓
                    deterministic derivation
                             ↓
                    typed points + crossings
                             ↓
                       contract graph
                             ↓
                    chart(root, paradigm)
                             ↓
                     bounded projection
```

A Chart is a projection only. It grants no authority, creates no standing, and cannot make a stale or otherwise illegal transition legal.

## What is derived now

From `SDLC.md`:

- three tier Skills;
- five domain Skills;
- five Workflow templates;
- LEFT, RIGHT, BLUE, and RED stances.

From the provisional Claude binding:

- one Binding point;
- one implementation point per `.claude/skills/sdlc-*/SKILL.md`;
- explicit `provides` and `realizes` crossings that bind those implementations back to the already-declared SDLC Skill identities.

From the temporary QA competence sidecar:

- two Requirement points: repository verification and independent observation;
- two Capability declaration points;
- explicit `requires` and `binds` crossings;
- declared effect classes only (`RESOURCE_CONSUMPTION` and `RECORD_LOCAL`);
- explicit `declaration_only: true` and `live_availability: false` on Capability points.

The derivation still does **not** infer undeclared capability requirements, live capability availability, authority grants, operator possession, workflow eligibility, concern standing, or implementation equivalence from prose.

## Requirement is not Capability

The experiment deliberately rejects a direct `Skill -> Capability` requirement relation. The current admissible competence path is:

```text
Skill
  -> requires -> Requirement
  -> binds    -> Capability declaration
```

A later runtime resolution path belongs to #49 and must remain distinct:

```text
Capability declaration
  -> Registry/Broker resolution
  -> concrete Capability receipt
  -> live Authority/Scope check
  -> operation evidence
```

A Skill, Requirement, Capability declaration, implementation suggestion, live Capability receipt, and evidence are not interchangeable.

## Why trees and forests are projections

The relation space may later be charted by concern, Skill, Capability, Workflow, operator, or authority position. A tree/forest is therefore a useful UI representation, not canonical hierarchy.

The current forest proves two independent crossings: provider-specific `.skills` packaging can resolve to provider-neutral Skill identities, and an explicitly declared Skill competence branch can extend into Requirements and Capability declarations without importing live runtime state.

## Dependency boundary

- #40 decides the canonical charting vocabulary and whether Covering becomes an explicit logical object.
- #41 owns Skill/Capability graph semantics, requirements, possession, and live resolution boundaries.
- #42 owns lowering governed Charts into human/model/worker operator environments.
- #47 decides canonical ownership/location for machine-readable Skill declarations.
- #48 owns promotion of the experimental Requirement/Capability relation shape into shared validated contracts.
- #49 owns live Capability receipt resolution.
- #50 owns the configurable Skill-forest UI projection.
- #52 removes or relocates the temporary QA sidecar after #47 decides ownership.
- #14/#15 provide Registry and Capability Broker semantics required for live capability resolution.
- #12 owns live authority semantics.
- #25 owns shared canonical machine-boundary contracts.

Until those close, this package must refuse to infer live authority, Capability possession, implementation availability, or prompt compilation from the static graph.

## Local tests

```text
python -m unittest discover -s charting/tests -v
```

The tests watch the current SDLC shape, exact binding-to-Skill resolution, explicit QA Requirement/Capability separation, source-content revision pinning, declared effect vocabulary, non-authoritative Chart governance, and fail-closed relation validation.

`python scripts/verify.py` includes this suite. Self-tests establish implementation evidence only; they do not witness or ratify #40/#41.
