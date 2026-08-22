# 0012 · Engineering framework and Phase-I baseline

Status: `OWNER-DIRECTED · EXACT BASELINE PROPOSED`

## Decision

Place the engineering constitution at repository root before further business
logic: `AGENTS.md` for normative operation, `CONTRIBUTING.md` for the human
workflow, `.cursorrules` as an editor-facing mirror, and `ENGINEERING.md` for
the proposed stack and composable primitives.

Treat the governing repository set as the design System of Record and the
append-preserving event/receipt journal as the operational System of Record.
The latter records standing and evidence; it is not an undifferentiated source
of truth.

Propose Python 3.11+, standard-library-first implementation, SQLite, local
filesystem content-addressed storage, JSON Schema Draft 2020-12, CLI/API
bindings, and dependency-free `unittest` as the Phase-I reference baseline.

Compose behavior from addressed sources, event envelopes, recordings or
proposals, typed authority, plans, runs and leases, independent observations,
receipts, counter-records, bindings, adapters, and rebuildable projections.

## Verification and hygiene

The root verification command runs dependency-free lint, structure checks,
oracle controls, and participant tests with a default three-second execution
budget. Day-0 CI invokes the same command. Production modules remain below 300
lines; current larger modules are named debt rather than silently exempted.

Repository ignores and a safe `.env.example` prevent secrets, local state,
payloads, paths, logs, and credentials from entering commits. Common secret
shapes are checked locally without transmitting content.

## Consequences

- Business logic follows a contract and positive/defeating fixture.
- Execution is separated from the operational record and cannot self-settle.
- Runtime dependencies and infrastructure additions require observed need, a
  named boundary, and a decision record.
- The logical specification remains stack-neutral.
- Exact technical choices remain proposed until Bdo ratifies the baseline.

## Source and authority

- `SYSTEM.md` operating model and Phase-I boundary
- `CLASSIFICATION.md` structural, role, and boundary distinctions
- `CONTRACT.md` founding invariants
- `SPEC.md` logical objects, transitions, fault model, and local operation
- `BYOM.md` model binding and adapter boundary
- Bdo's 2026-08-22 instructions to establish repository rules, a fast Day-0
  verification loop, first-class state, context hygiene, secrets boundaries,
  and a minimal recomposable technical baseline before further business logic
