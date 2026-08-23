# 0023 · Owner acceptance, not work approval

Status: `OWNER-DIRECTED · ACCEPTED POLICY`

## Decision

The human owner gate in Soveraeign is an **acceptance gate over evidenced results**, not a
pre-approval gate over ordinary work.

Within an already declared product direction, repository boundary, effect envelope, and available
host capability, Sov and other eligible agents may choose, sequence, implement, test, repair,
refactor, document, branch, and propose the next bounded operation without waiting for Bdo to
approve each step. Their choices remain attributable and may not manufacture authority, standing,
or evidence.

Bdo retains the right to **accept, reject, strike, or redirect** outcomes that require owner
judgement. Acceptance occurs after the work has produced inspectable evidence. It is not permission
to begin.

## Self-directed judgement

A participant may make judgement about its own bounded participation: what to inspect, which legal
operation to attempt next, how to sequence reversible work, what hypothesis to test, when to stop a
failed line, and what implementation choice best satisfies an already accepted contract.

That self-directed judgement does not bind Bdo, another participant, or shared authoritative state
as owner judgement. A transition that changes owner-held product intent, public naming, external
commitment, irreversible external-world effect, or the acceptance standing itself still requires
the corresponding right.

The invariant is therefore not "models cannot exercise judgement." It is:

> A participant may decide for itself. Binding another sovereign or claiming owner acceptance
> requires the applicable right.

## Acceptance packet

Every owner acceptance request MUST arrive as an evidence-backed presentation rather than a bare
question. The packet is designed to make the decision nearly self-evident from the observed output.
It contains:

1. **Claim** — the single thing the owner is being asked to accept.
2. **Visible result** — a demo, rendered artifact, before/after, replay, trace, or similarly direct
   presentation of what changed.
3. **Evidence** — exact revision/digests, relevant positive and defeating controls, independent
   observation where the standing requires it, and unresolved residuals.
4. **Why it matters** — one short connection to the accepted product outcome or current trajectory.
5. **What could defeat it** — the strongest known failure, dissent, or demotion condition.
6. **Owner action** — `ACCEPT`, `REJECT`, `STRIKE`, or `REDIRECT`; no approval-before-work option.

The presentation should be concise, legible, and engaging enough that the owner can understand the
result from the output itself before reading supporting internals. "Entertaining" means the demo
earns attention through clarity, movement, contrast, narrative, or direct manipulation; it does not
mean hiding defects or replacing evidence with polish.

## Operating consequences

- `Bdo/phase-gate` on ordinary implementation work means **acceptance at the named phase boundary**,
  not permission to start each operation.
- Missing owner acceptance must not block unrelated or safely reversible work. The result remains
  pending acceptance while the controller advances another eligible concern.
- Agents may resolve implementation choices and reversible design choices when governing contracts
  constrain the acceptable outcome strongly enough to test the choice.
- If multiple choices remain materially product-defining and cannot be defeated by existing
  requirements, the agent may pick a reversible candidate, build enough evidence to compare it,
  and present the comparison at acceptance instead of escalating before learning.
- Evidence gates remain real. Blue cannot call itself witnessed; Red cannot ratify; a green build
  cannot claim owner acceptance.
- Public release, owner identity/naming changes, secrets, destructive repository administration,
  and unbounded or irreversible external-world effects remain explicit owner boundaries.

## Twenty-four-hour operating rule

For the next operating window, the controller should prefer **motion over escalation**:

1. select the highest-leverage unblocked concern;
2. make the smallest evidence-producing change;
3. verify it independently enough for its claimed standing;
4. repair or record residuals;
5. continue to the next concern without asking Bdo for intermediate approval;
6. queue owner acceptance only when a coherent evidenced result exists.

When an owner-only decision appears, first ask whether work can produce evidence that narrows or
eliminates the choice. Escalate immediately only when proceeding would itself cross the protected
owner boundary.

## Demotion

Demote this policy if agents begin treating the absence of pre-approval as permission for external
world effects, owner impersonation, evidence inflation, destructive changes, secret exposure, or
self-ratification; or if acceptance packets become polished narratives that hide defeating evidence.

## Source

Bdo's 2026-08-23 direction: the human gate should only be acceptance, not approval; acceptance
requires evidence and an owner presentation that is entertaining and nearly self-evident from the
output.
