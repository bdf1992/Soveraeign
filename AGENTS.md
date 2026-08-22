# Agent Operating Contract

Read `STATUS.yaml`, `SYSTEM.md`, `CONTRACT.md`, `PRD.md`, and `OPEN-SEAMS.md`
before making consequential changes.

## Authority

Bdo holds product-intent, naming, judgement, and phase-gate authority. Agents may
inspect, compare, draft, implement, test, and machine-ratify verification-typed
claims only when explicitly delegated. No agent may represent its synthesis as
Bdo's judgement.

## Evidence

- Treat `lineage/evidence/` as immutable attributed input.
- Verify it against `lineage/SOURCES.lock` before relying on it.
- Cite evidence paths and clause or section identifiers in governing changes.
- Mark new claims as proposals.
- Preserve contradictions and stale claims until their standing is decided.
- Never treat recency, repetition, eloquence, confidence, or model consensus as
  authority.

## Change protocol

Before a consequential change, state:

1. the requested outcome;
2. current authoritative state;
3. affected contracts and sources;
4. preconditions and expected observable result;
5. effect class and rollback or refusal boundary.

Afterward, inspect the result independently, record the residual, and change
only what the observation disproves.

## Repository rules

- Preserve `product_name: Soveraeign` and `repository_name: Soveraeign` unless
  Bdo explicitly changes the name.
- Do not add production runtime code before F1 and F2 close.
- Write conformance fixtures before implementing the behavior they require.
- Do not import a predecessor repository wholesale.
- Carry an ancestor forward through an invariant, decision, fixture, schema, or
  explicitly reviewed implementation adoption.
- Preserve the standing lifecycle: `OPEN → BUILT → WITNESSED → RATIFIED`.
- A build report cannot witness itself.
- Record substantial policy changes in `decisions/`.
- Do not initialize a remote, publish, or enable external effects without an
  explicit user instruction.
- Public publication includes canonical synthesis and implementation artifacts
  only. Publishing `lineage/`, ancestor registries, raw evidence, or source-lock
  inventories requires a separate explicit owner instruction.

## Completion report

Report:

- files changed;
- checks executed and their observations;
- requirements whose standing changed;
- open decisions needing owner judgement;
- assumptions introduced;
- the next bounded operation.

Do not say the work is complete merely because files were written or tests
returned zero.
