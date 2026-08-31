---
name: sdlc-feedback
description: Feedback domain competence for the SDLC loop - review standing, capture residuals and seams, route correction proposals into the owning documents, and compress repeated observations before they become new policy or work. Use when a concern digests outcomes, residuals, contradictions, lessons, or repeated operating friction back into the System of Record.
---

# Feedback Domain Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

Feedback closes the loop by landing what was learned in the documents that
own it. It creates no side ledger and has no authority of its own.

## Duties

1. Review standing honestly: what is `OPEN`, `BUILT`, `WITNESSED`,
   `RATIFIED`, and on what evidence. Never advance standing by summary.
2. Record residual failures, contradictions, and deliberate ambiguities in
   `OPEN-SEAMS.md`; an implementation must not choose a side silently.
3. Route policy-shaped learnings into `decisions/` as proposals and standing
   changes into `STATUS.yaml`; link, do not duplicate, per the
   System-of-Record rule in `AGENTS.md`.
4. Convert confirmed Red findings into permanent defeating fixtures in the
   owning conformance/test surface when the finding is mechanically checkable,
   so a demonstrated defeat cannot recur silently.
5. Produce handoffs per `AGENTS.md` context hygiene: current standing,
   changed files, observed checks, residuals, next bounded operation.
6. Compress observations before creating more surface. Several observations
   may describe one underlying defect; preserve useful corroboration while
   avoiding duplicate concerns, rules, and truth producers.

## Learning routes

A compression pass classifies a finding before it creates anything durable:

- **Report** — observes one bounded window or subject. A report does not govern.
- **Lesson** — generalizes an evidenced invariant. `LESSONS.md` is an inbox;
  `EFFECTIVE` still requires the executable carrier `LESSONS.md` declares.
- **Decision** — changes policy, permission, boundary, or governing meaning.
  It belongs to the owning decision/governance path and remains a proposal
  until the applicable authority settles it.
- **Concern** — creates work because a concrete residual remains. It enters the
  existing concern -> custody -> lease -> closure -> landing -> settlement
  lifecycle; feedback does not create a parallel queue.

Do not promote a finding merely because it is interesting. Conversely, a
single causally demonstrated integrity, identity, authority, security, or
self-witness defect may justify an invariant immediately; repetition is not a
safety prerequisite. Repetition is evidence that an operating **procedure** is
stable enough to consider extracting as a skill.

## Compression cadence

### Daily compression

Read the delta since the prior daily review. Prefer a small correction over a
new campaign.

Return, at minimum:

1. genuinely new findings;
2. repeated observations correlated to an existing finding;
3. stale or duplicate representations that can be rebuilt, removed, or linked
   to one authoritative producer;
4. lessons that moved, were superseded, or still claim more standing than their
   executable carrier supports;
5. owner-held decisions that materially block the current proving/opening path,
   excluding unrelated owner backlog;
6. the smallest next compression or settlement operation;
7. whether a fresh participant would still notice a historical/gap seam while
   trying to orient and begin ordinary work.

Daily compression is a reading. It may recommend a concern or decision, but it
must not mint one merely to give the ritual output.

### Weekly super compression

Read the week as one system rather than seven independent reports. Group defects
by immutable subject/revision plus the failing predicate or normalized symptom,
and distinguish **useful corroboration** from **redundant recomputation**.

Look especially for:

- multiple authoritative producers for one fact;
- repeated whole-system checks rediscovering an already sufficient defect;
- branches, worktrees, projections, documents, fixtures, or status copies that
  have become separate truth populations;
- gates that block despite lacking an explicit risk, scope, pass criterion, or
  proportionate cost;
- procedures repeated often enough to be candidates for a thin skill;
- concerns opened faster than they settle;
- representations that can disappear because their value is now derived.

Useful control signals include unique defects versus repeated red observations,
runner effort after sufficient detection, concerns opened versus settled, and
representations removed/derived versus added. These are diagnostic readings,
not standing or release gates unless separately governed.

## Gap terminal

The gap between historical Phase I and a successor opening is **operationally
invisible** when a fresh participant can enter through the current progressive
path without oral history, current lessons no longer overclaim effectiveness,
material owner decisions for the proving vertical are either settled or named
at the exact gated transition, and surviving work is ordinary readiness rather
than archaeology/reconciliation.

A compression review may report the literal reading
`GAP_OPERATIONALLY_INVISIBLE`. That reading does **not** open a successor phase,
change `contracts/phases.json`, or create acceptance. Once reached, stop
manufacturing gap work merely to keep the ritual alive.

## Skill extraction

Do not mint a skill because a finding exists. Keep a small procedure ledger in
review output. A useful heuristic is three or more repetitions of the same
bounded procedure with stable inputs, outputs, refusals, and owner boundaries.
Then propose a thin skill that composes the owning rules rather than copying
them. The repetition count is a skill-extraction heuristic, not a requirement
for recognizing a safety invariant.

## Refusals

Refuse to soften residuals, to close a seam without the authority its owner
requires, to create a competing status or learning ledger, to treat recency,
repetition, consensus, metrics, or a green check as authority, to turn the daily
ritual into a mandatory new work item, or to keep the gap alive after its
observable terminal is reached.
