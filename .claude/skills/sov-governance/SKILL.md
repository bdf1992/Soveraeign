---
name: sov-governance
description: Governance domain of the Soveraeign design System of Record - coherence of the governing document set (SYSTEM.md, CONTRACT.md, CLASSIFICATION.md, PRD.md, SPEC.md, STATUS.yaml, OPEN-SEAMS.md, NAMING.md, PUBLICATION.md, ROADMAP.md), drafting decision records in decisions/, maintaining STATUS.yaml standing fields, owner-held judgement routing, and compression of duplicated governing truth. Load on "sov-governance", "governance domain", "decision record", "STATUS.yaml standing", "owner decision", "document coherence", "OPEN-SEAMS", "naming collision screen", "one fact one producer", or phase-gap/opening-boundary questions. Not for building services, contracts/, conformance/, or BYOM work - those belong to sibling sov-* skills.
---

# sov-governance

## Purpose

Keep the Soveraeign design System of Record coherent: one governing meaning,
one authoritative producer for that meaning, contradictions carried visibly,
and projections derived rather than promoted into competing truth. Draft decision
records and keep STATUS.yaml standing fields honest. Rule what this tier can rule
and record what defeats it; escalate only an owner-held boundary
(`decisions/0033-close-the-founding-docket.md`, Ruling 1).

Independent evidence is not a competing producer. A witness may independently
reconstruct or refute a claim. The compression rule is about authoritative
meaning and state, not about suppressing corroboration.

## Owns / Must not

Owns: coherence of the governing set listed above; `decisions/` drafting;
STATUS.yaml standing fields and `owner_holds`; seam registration in
OPEN-SEAMS.md; and routing of owner decisions to the exact transition they gate.
Per AGENTS.md directory boundaries, `/decisions` owns consequential choices,
status, rationale, and consequences - never mutable runtime state.

Must not: ratify judgement-typed claims (Bdo-only); present agent synthesis as
Bdo judgement; duplicate a rule in a second document as competing authority
(link to the owning document); erase or rewrite history (evidence files are
immutable; superseded records stay); write runtime code (that belongs to
service domains, and requires prior spec and defeating fixtures); publish or
enable external effects; turn a weekly report into policy; or make unrelated
owner backlog block a transition that does not consume it.

## Key files

- `AGENTS.md`, `STATUS.yaml`, `contracts/phases.json` - read before any consequential change
- `SYSTEM.md`, `CONTRACT.md`, `CLASSIFICATION.md`, `PRD.md`, `SPEC.md`,
  `OPEN-SEAMS.md`, `NAMING.md`, `PUBLICATION.md`, and current `ROADMAP.md`
- `decisions/` and `acceptance/` for consequential choices and root packets;
  archived Phase-I definitions live under `archives/` and are not current policy
- `LESSONS.md` and `scripts/sov_lessons.py` for the lesson inbox/effectiveness
  distinction; governance does not turn the inbox into a rulebook
- `scripts/verify.py`, `scripts/lint.py`

## Standing and phase boundary

`contracts/phases.json` records Phase I as `CLOSED_INCOMPLETE` with
`succeeded_by: null`. Until the root seat opens a successor, `STATUS.yaml`
projects `phase: NONE_ACTIVE` and `next_gate: SUCCESSOR_PHASE_OPENING`.

This creates three deliberately distinct readings:

1. **Historical Phase I** — terminal and evidence-only; unfinished work cannot
   reopen it by continuing to build.
2. **Current gap/successor preparation** — may reconcile lessons, orientation,
   participant/session joins, owner decisions, and permanent cross-phase
   substrate; it may not mint successor standing.
3. **Successor phase** — does not exist until an explicit root opening act.

A gap review may conclude `GAP_OPERATIONALLY_INVISIBLE`; that is a readiness
reading only. It does not mutate `contracts/phases.json`, create a phase, or
constitute owner acceptance.

`open_decisions` is empty and the `O<n>` identifiers are retired
(`decisions/0033-close-the-founding-docket.md`). The current owner docket lives
in `owner_acceptance_queue`; the separate `PUBLIC-CLEARANCE` hold blocks public
release only and does not block repository-local closure or successor engineering.

This domain settles what evidence can settle and records what would defeat each
ruling. It never publishes, never claims legal clearance, and never presents its
own synthesis as Bdo's judgement.

## One authoritative producer

When several artifacts state the same current fact, identify the artifact that
owns producing that fact and turn the others into one of:

- a deterministic projection of the owner;
- a reader that cites the owner;
- historical evidence explicitly stripped of current authority; or
- a contradiction/seam if the ownership cannot yet be resolved.

Do not delete independent observation merely because it repeats a claim. The
observer produces evidence about the fact, not the governing fact itself.

Before adding a new governance artifact, ask whether it is actually a new fact
or only another representation. Prefer a new address only for new meaning,
state, evidence, or a genuinely distinct owner.

## Owner-decision routing

An unresolved owner item blocks only a transition whose legality or meaning
actually depends on that item. During successor preparation, filter the owner
queue against the proposed proving/opening path:

- **material blocker** — changing the answer changes the proving circuit,
  authority aperture, selected participant/operation, acceptance terminal, or
  other exact opening condition;
- **named later judgement** — real owner work, but no current transition consumes
  it; preserve it without pulling it onto the critical path;
- **superseded/answered** — current owner direction or stronger accepted policy
  already settles the question; reconcile the stale carrier rather than ask it
  again.

Do not use an old owner queue as a generic reason the repository cannot proceed.

## Named operations (available now)

1. Coherence sweep: find a rule duplicated across two governing documents,
   keep it in the owning document, and replace the duplicate with a link.
2. Producer compression: identify several current representations of one fact,
   name the authoritative producer, and convert the rest to projections/readers
   without erasing independent evidence.
3. Seam registration: record a newly observed contradiction as a numbered seam
   in OPEN-SEAMS.md instead of silently choosing a side.
4. Decision drafting: draft a new `decisions/NNNN-<slug>.md` with Status,
   Decision, Evidence, and Consequence sections, marked PROPOSED, citing
   evidence paths and clause identifiers.
5. Docket discipline: rule a newly surfaced question at this tier and record
   the observation that would defeat the ruling. Never mint an `O<n>`; the
   O-space is retired. Only an owner-held boundary (public naming, external
   commitment, irreversible external effect, secrets, destructive repository
   administration, or an explicit root phase/acceptance act) enters
   `owner_holds`, and it must state what it does not block.
6. Opening-decision filter: classify owner items as material to the exact
   successor-opening/proving path, later/non-blocking, or already answered by
   current authority. Do not settle Bdo's decision; narrow where it is required.
7. Standing proposal: update a STATUS.yaml `*_status` field to match
   independently observed standing (e.g. BUILT_SELF_TESTED_NOT_WITNESSED),
   as a proposal with the observation cited.
8. Acceptance packet: assemble the six-part packet of
   `decisions/0023-acceptance-not-approval.md` - claim, visible result,
   evidence, why it matters, what could defeat it, owner action - over a
   result that is already built and observed. Never over unstarted work.
9. Collision-screen evidence prep for PUBLIC-CLEARANCE: record screening
   results and objections under the NAMING.md process without publishing
   anything and without claiming clearance.
10. Vocabulary drift check: grep canonical documents for synonyms of standing,
    event, effect, or role terms and align them to CLASSIFICATION.md/SPEC.md
    wording. `CLASSIFICATION.md` is accepted, so a synonym is a defect to fix,
    not a question to raise.
11. Gap-terminal reading: independently test whether a fresh participant can
    orient from current entry documents into the principal/session -> grant ->
    operation -> record/projection path, whether EFFECTIVE lessons have real
    carriers, and whether remaining owner items are attached only to the exact
    transitions they gate. Report readiness; never open the phase from this
    operation.

## Verification

- `python scripts/verify.py` - required, from repository root.
- `python scripts/lint.py` - text, syntax, module size, and secret shapes.
- `python scripts/sov_lessons.py check` - lesson standing/effectiveness reading
  when the operation touches gap learning.
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
codes); authoritative producers changed or clarified; standing proposals
(transition supported, never RATIFIED); owner items split into material blockers
and later/non-blocking items; next bounded operation; gap visibility reading when
requested.
