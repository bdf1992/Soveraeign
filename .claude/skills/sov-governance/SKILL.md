---
name: sov-governance
description: Governance domain of the Soveraeign design System of Record - coherence of the governing document set (SYSTEM.md, CONTRACT.md, CLASSIFICATION.md, PRD.md, SPEC.md, STATUS.yaml, OPEN-SEAMS.md, NAMING.md, PUBLICATION.md, ROADMAP.md), drafting decision records in decisions/, maintaining STATUS.yaml standing fields, and the open-decision judgement queue for Bdo. Load on "sov-governance", "governance domain", "decision record", "STATUS.yaml standing", "open decisions", "judgement queue", "document coherence", "OPEN-SEAMS", or "naming collision screen". Not for building services, contracts/, conformance/, or BYOM work - those belong to sibling sov-* skills.
---

# sov-governance

## Purpose

Keep the Soveraeign design System of Record coherent: one rule, one owning
document, contradictions carried visibly. Draft decision records, keep
STATUS.yaml standing fields honest. Rule what this tier can rule and record
what defeats it; escalate only an owner-held boundary
(`decisions/0033-close-the-founding-docket.md`, Ruling 1).

## Owns / Must not

Owns: coherence of the governing set listed above; `decisions/` drafting;
STATUS.yaml standing fields and `owner_holds`; seam registration in
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

- `AGENTS.md`, `STATUS.yaml`, `contracts/phases.json` - read before any consequential change
- `SYSTEM.md`, `CONTRACT.md`, `CLASSIFICATION.md`, `PRD.md`, `SPEC.md`,
  `OPEN-SEAMS.md`, `NAMING.md`, `PUBLICATION.md`, and current `ROADMAP.md`
- `decisions/` and `acceptance/` for consequential choices and root packets;
  archived Phase-I definitions live under `archives/` and are not current policy
- `scripts/verify.py`, `scripts/lint.py`

## Standing and constraints

`contracts/phases.json` records Phase I as `CLOSED_INCOMPLETE` with
`succeeded_by: null`. Until the root seat opens a successor, `STATUS.yaml`
projects `phase: NONE_ACTIVE` and `next_gate: SUCCESSOR_PHASE_OPENING`.

`open_decisions` is empty and the `O<n>` identifiers are retired
(`decisions/0033-close-the-founding-docket.md`). The current owner docket lives
in `owner_acceptance_queue`; the separate `PUBLIC-CLEARANCE` hold blocks public
release only and does not block repository-local closure or successor engineering.

This domain settles what evidence can settle and records what would defeat each
ruling. It never publishes, never claims legal clearance, and never presents its
own synthesis as Bdo's judgement.

## Named operations (available now)

1. Coherence sweep: find a rule duplicated across two governing documents,
   keep it in the owning document, and replace the duplicate with a link.
2. Seam registration: record a newly observed contradiction as a numbered seam
   in OPEN-SEAMS.md instead of silently choosing a side.
3. Decision drafting: draft a new `decisions/NNNN-<slug>.md` with Status,
   Decision, Evidence, and Consequence sections, marked PROPOSED, citing
   evidence paths and clause identifiers.
4. Docket discipline: rule a newly surfaced question at this tier and record
   the observation that would defeat the ruling. Never mint an `O<n>`; the
   O-space is retired. Only an owner-held boundary (public naming, external
   commitment, irreversible external effect, secrets, destructive repository
   administration) enters `owner_holds`, and it must state what
   it does not block.
5. Standing proposal: update a STATUS.yaml `*_status` field to match
   independently observed standing (e.g. BUILT_SELF_TESTED_NOT_WITNESSED),
   as a proposal with the observation cited.
6. Acceptance packet: assemble the six-part packet of
   `decisions/0023-acceptance-not-approval.md` - claim, visible result,
   evidence, why it matters, what could defeat it, owner action - over a
   result that is already built and observed. Never over unstarted work.
7. Collision-screen evidence prep for PUBLIC-CLEARANCE: record screening
   results and objections under the NAMING.md process without publishing
   anything and without claiming clearance.
8. Vocabulary drift check: grep canonical documents for synonyms of standing,
   event, effect, or role terms and align them to CLASSIFICATION.md/SPEC.md
   wording. `CLASSIFICATION.md` is accepted, so a synonym is a defect to fix,
   not a question to raise.

## Verification

- `python scripts/verify.py` - required, from repository root, graded budget (PLATINUM 3 s, GOLD 6 s, SILVER 15 s)
  after Python starts.
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
