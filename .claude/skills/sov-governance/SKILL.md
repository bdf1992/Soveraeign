---
name: sov-governance
description: Governance domain of the Soveraeign design System of Record - coherence of the governing document set (SYSTEM.md, CONTRACT.md, CLASSIFICATION.md, PRD.md, SPEC.md, STATUS.yaml, OPEN-SEAMS.md, NAMING.md, PUBLICATION.md, ROADMAP.md), drafting decision records in decisions/, maintaining STATUS.yaml standing fields, and the O1-O12 open-decision judgement queue for Bdo. Load on "sov-governance", "governance domain", "decision record", "STATUS.yaml standing", "open decisions", "judgement queue", "document coherence", "OPEN-SEAMS", or "naming collision screen". Not for building services, contracts/, conformance/, or BYOM work - those belong to sibling sov-* skills.
---

# sov-governance

## Purpose

Keep the Soveraeign design System of Record coherent: one rule, one owning
document, contradictions carried visibly. Draft decision records, keep
STATUS.yaml standing fields honest, and keep the judgement queue for Bdo
accurate without ever deciding it.

## Owns / Must not

Owns: coherence of the governing set listed above; `decisions/` drafting;
STATUS.yaml standing fields and `open_decisions`; seam registration in
OPEN-SEAMS.md. Per AGENTS.md directory boundaries, `/decisions` owns
consequential choices, status, rationale, and consequences - never mutable
runtime state.

Must not: ratify judgement-typed claims (Bdo-only); present agent synthesis as
Bdo judgement; duplicate a rule in a second document as competing authority
(link to the owning document); erase or rewrite history (evidence files are
immutable; superseded records stay); write runtime code (that belongs to
service domains, and requires prior spec and defeating fixtures); publish or
enable external effects.

## Key files

- `AGENTS.md`, `STATUS.yaml` - read before any consequential change
- `SYSTEM.md`, `CONTRACT.md` (C1-C15), `CLASSIFICATION.md`, `PRD.md`,
  `SPEC.md`, `OPEN-SEAMS.md` (S1-S10), `NAMING.md`, `PUBLICATION.md`,
  `ROADMAP.md` (F0-F6)
- `decisions/0001-founding-boundary.md` ... `decisions/0012-engineering-baseline.md`
- `scripts/verify.py`, `scripts/lint.py`

## Standing and blockers

STATUS.yaml: `phase: FOUNDING`, `next_gate: F0_FOUNDING_CLOSURE`,
`naming_status: OWNER_SELECTED_COLLISION_SCREEN_OPEN`,
`classification_status: PROPOSED_OWNER_RATIFICATION_PENDING`,
`specification_status: PROPOSED_LOGICAL_SPEC_OWNER_FREEZE_PENDING`.

Gating open decisions (all ratifications are Bdo-only):
- O1 blocks `public_release` - Soveraeign collision screening is open.
- O9 blocks `terminology_freeze` - CLASSIFICATION.md is proposed, not canon.
- O10 blocks `f1_closure` - SPEC.md is proposed, freeze pending.

While these are open, this domain proposes and prepares; it never freezes,
publishes, or ratifies.

## Named operations (available now)

1. Coherence sweep: find a rule duplicated across two governing documents,
   keep it in the owning document, and replace the duplicate with a link.
2. Seam registration: record a newly observed contradiction as a numbered seam
   in OPEN-SEAMS.md instead of silently choosing a side.
3. Decision drafting: draft a new `decisions/NNNN-<slug>.md` with Status,
   Decision, Evidence, and Consequence sections, marked PROPOSED, citing
   evidence paths and clause identifiers.
4. Judgement queue maintenance: add a newly surfaced judgement-typed question
   to `open_decisions` with an `id` and `blocks` field; never remove one
   without a Bdo decision record.
5. Standing proposal: update a STATUS.yaml `*_status` field to match
   independently observed standing (e.g. BUILT_SELF_TESTED_NOT_WITNESSED),
   as a proposal with the observation cited.
6. Ratification package prep for O9 or O10: assemble exactly what Bdo would
   ratify - the document, its evidence citations, and known objections - and
   queue it as a judgement item.
7. Collision-screen evidence prep for O1: record screening results and
   objections under the NAMING.md process without publishing anything.
8. Vocabulary drift check: grep canonical documents for synonyms of standing,
   event, effect, or role terms and align them to CLASSIFICATION.md/SPEC.md
   wording, as a proposal while O9 is open.

## Verification

- `python scripts/verify.py` - required, from repository root, three-second
  budget after Python starts.
- `python scripts/lint.py` - text, syntax, module size, and secret shapes.
- If Ruff is available: `python -m ruff format --check .` and
  `python -m ruff check .` (convenience, not a substitute for verify).
Record the exact command and exit code for every check observed.

## Vocabulary (exact, from CLASSIFICATION.md and SPEC.md)

- Record standing: `RECORDED`, `ADMITTED`, `RATIFIED`, `EFFECTIVE` - distinct,
  never collapsed. Work-standing lifecycle: OPEN -> BUILT -> WITNESSED ->
  RATIFIED.
- Event outcomes: `ATTEMPTED`, `COMMITTED`, `FAILED`, `REFUSED`, `COUNTERED`,
  `UNRESOLVED` (`COUNTERED` is an outcome, not a fifth standing).
- Effect classes: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD`.
- Attestation outcomes: `reproduced`, `dissented`, `unattestable`.
- Roles: `Operator`, `Actor`, `Worker` (report is not observation), `Witness`,
  `Projection` (rebuildable, never authoritative by convenience).
- Information roles: `Proposal`, `Recording`, `Receipt`, `Observation`,
  `Retraction`. Structural: `Node`, `Service`, `Component`.

## Report format

Report: files changed (repo-relative); checks observed (commands with exit
codes); standing proposals (transition supported, never RATIFIED); judgement
items queued for Bdo; next bounded operation.
