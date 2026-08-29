# 0098 · Witness milestones, not every increment

Status: `OWNER-DIRECTED · CONTRACT WORDING PROPOSED`

Bdo ruled on 2026-08-28 that ordinary work should not stop after every built
increment to wait for independent QA. Expected tests remain part of every unit
of work. Independent witnessing is instead queued over named, immutable
milestones large enough to make an adversarial reading meaningful.

This changes verification cadence, not the evidence bar.

## The defect

`SDLC.md` currently says a concern may not advance past `BUILT` until Red and
Blue combine to `PURPLE`, and `contracts/ticket-queue-policy.json` turns every
`BUILT_SELF_TESTED_NOT_WITNESSED` item into an immediate instruction to run Red.
The GitHub QA workflow then performs expensive adversarial work on every pull
request.

Those three statements collapse two different obligations:

1. **continuous engineering verification** — the positive path, declared
   defeating cases, unit/conformance tests, and repository verification that
   make an increment `BUILT`; and
2. **independent witnessing** — an outside attempt to defeat an accumulated
   claim before the system promotes that claim to `WITNESSED` or crosses a
   boundary that explicitly requires outside observation.

The first belongs to every work unit. The second belongs to a named evidence
boundary.

## Decision

### 1. Blue is continuous

Every consequential work unit still carries its expected tests, positive and
defeating cases, and `python scripts/verify.py`. A passing builder-owned run can
establish `BUILT` evidence and nothing beyond it.

Deferring witness never defers ordinary tests.

### 2. Red is a queued milestone operation

Independent adversarial verification is represented by the existing
`verification-engagement` work kind. It targets an immutable revision and a
named milestone claim. The engagement may aggregate several self-tested work
units when they compose one meaningful surface.

The current ticket schema remains PR/head-shaped in this change. A milestone
may therefore use an integration PR and its pinned `target_head` as its carrier.
Generalising the engagement target beyond PRs is a separate concern and is not
required to establish this cadence.

### 3. Unwitnessed is not blocked

A target at `BUILT_SELF_TESTED_NOT_WITNESSED` may continue to move in circuit
stage, scope, and implementation state while its standing remains `BUILT`.
Outstanding witness work is debt with an address, not a frozen frontier.

Witness becomes a gate only when the next requested transition consumes it,
including:

- `BUILT_SELF_TESTED_NOT_WITNESSED -> WITNESSED`;
- owner acceptance or release rules that explicitly require witnessed evidence;
- `CAPABLE_NODE`, whose work-circuit admission requires outside observation;
- any other contract that explicitly names an independent observation as a
  precondition.

This is the same shape as `AGENTS.md`'s blocked-edge rule: an unavailable edge
never implies an unavailable frontier.

### 4. A failed witness defeats the named claim, not unrelated work

A Red finding or defeating observation holds or demotes the milestone and the
dependent descendants that rely on the defeated predicate. It does not
implicitly freeze unrelated reachable work.

Confirmed findings still become permanent defeating fixtures. The builder still
cannot witness itself. Nothing here changes `OPEN -> BUILT -> WITNESSED ->
RATIFIED`, and nothing makes `WITNESSED` reachable without an independent
record.

### 5. Long-horizon obligations should not be permanent-red increment gates

Decision 0087 already rejected making the phase exit itself a check that would
stay red for months, because a permanently red check teaches participants to
ignore it. It records the obligation continuously and refuses only regression
until the actual phase boundary consumes the full requirement.

Witnessing follows the same generalized rule:

> Queue an obligation when it becomes known. Gate the transition that consumes
> it. Continue every other reachable path.

This applies to witness debt, owner judgement, phase qualification, grounding
residuals, missing automation with a lawful manual route, and other deferred
obligations unless their owning contract explicitly makes them immediate.

## Consequences

- `SDLC.md` separates continuous Blue from milestone Red and scopes `PURPLE` to
  the milestone target it actually witnessed.
- `contracts/ticket-queue-policy.json` stops treating every BUILT concern as an
  immediate witness job. A `verification-engagement` remains high-priority once
  it is actually queued.
- `.github/workflows/qa-lanes.yml` keeps Blue on every pull request and moves the
  expensive Red/mutation pass to an explicit milestone dispatch.
- `.claude/skills/sdlc-qa/SKILL.md` teaches the same cadence without becoming a
  second authority.
- `contracts/ticket-transitions.json`, `scripts/sov_standing.py`, historical
  witness records, and existing `BUILT_SELF_TESTED_NOT_WITNESSED` status claims
  do not change.

## Defeating cases

This decision is wrong if any of the following becomes possible:

1. a work unit lands without its expected positive/defeating tests because
   witness was deferred;
2. a claim reaches `WITNESSED` without an independent witness receipt;
3. a contractually witness-gated transition proceeds merely because ordinary
   development is allowed to continue;
4. milestone Red cannot pin the exact bytes it attacked;
5. a failed milestone witness silently leaves dependent claims promoted;
6. witness work is deferred without an address until nobody can tell what is
   still owed.

## Source and authority

- Bdo, 2026-08-28: work should be queued for witnessing later in larger named
  sections; QA should not block ordinary work between those milestones.
- `SDLC.md` — verification dyad and release gate.
- `contracts/work-circuit.json` — circuit stage and standing are independent;
  outside observation is required at `CAPABLE_NODE`.
- `decisions/0087-lessons-enforced-and-the-phase-floor.md` — a long-horizon
  obligation should not become a permanently red per-change gate.
- `AGENTS.md` — blocked edge is not blocked frontier; a builder cannot witness
  its own work.
