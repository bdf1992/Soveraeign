# 0065 · The standing landing grant is ratified

Status: `OWNER-DIRECTED · ACCEPTED POLICY`

## Decision

`grant:standing-landing-loop` moves from `PROPOSED` to `RATIFIED` in
`contracts/standing-grants.json`. Bdo ratified it on 2026-08-25, in session, having been
shown the grant's exact scope, exclusions, type, effect ceiling, budget, and expiry, and
having been offered a narrower variant and the option of leaving it inert. He chose the
grant as shipped.

His instruction, recorded verbatim as the act this record settles:

> Ratify as shipped

The edit itself was made by Claude Code acting as scribe on that instruction and on no
other authority. That distinction is the whole of what `decisions/0064` was protecting:
it forbids *the loop* from ratifying the grant the loop is about to spend, because a
participant that can widen its own authority has none. It does not forbid the owner from
saying yes and someone else typing it, any more than `AGENTS.md` forbids a direct commit
to `main` that Bdo explicitly instructed. The refusal is against self-grant, not against
transcription.

Two mechanisms make the distinction checkable rather than asserted. The grant excludes
`contracts/standing-grants.json` and `contracts/authority-grant.schema.json` from its own
scope, so no exercise of the grant could have produced this edit. And the grant's
`VERIFICATION` type cannot ratify a `JUDGEMENT` claim (`SPEC.md`, PROD-I-5), so it could
not have recorded this standing even if a path had slipped through. This change is
therefore only reachable by the route it actually took.

## What changes, and what does not

What changes is one thing: a witnessed, green, in-scope change on `main` no longer needs a
conversation to become a commit. `scripts/sov_land.py` stops refusing with
`AUTHORITY_REFUSED` and starts grading the landing on its merits.

What does not change is every gate `decisions/0064` enumerated. The excluded paths keep the
loop out of `decisions/`, `lineage/`, `STATUS.yaml`, `.github/`, and every root governing
document. `requires_independent_observation` still means a build cannot close itself. A
landed commit is `BUILT` plus an independent observation; it is not `WITNESSED` in the sense
the artifact lifecycle reserves, and it is not `RATIFIED`. Landing removed a conversation
about merging. It removed no gate.

## The remote is a separate crossing

One fact `decisions/0064` did not carry, observed here on 2026-08-25.

The `main` branch on `github.com/bdf1992/Soveraeign` is governed by ruleset `Gate`, which
requires a pull request and passing status checks and forbids non-fast-forward pushes. A
direct push to `origin/main` is refused by GitHub before any grant is consulted. Ruling
`O16b` separately refuses merging by name.

So this grant's `main` is the local branch, and it reaches the remote only through a pull
request somebody merges. That is not a defect in the grant and it is not a gap this record
closes; it is the boundary between a record-local effect and an external-world one, landing
exactly where `CONTRACT.md` puts it. The practical consequence is worth stating plainly: the
loop can land any number of concerns without asking, and each still arrives at the remote as
a pull request awaiting a merge that is Bdo's.

## Defaults taken

- The grant is ratified as shipped rather than narrowed. Dropping `docs/` from scope was
  offered and declined: `docs/documentation.html` is a generated projection that goes stale
  on any repository text change, so a loop without it would leave `verify.py` red and then be
  refused for the failing check it was not permitted to repair.
- `decisions/0064` keeps its original Residual text rather than being rewritten. A decision
  record states what was true when it was made; this record supersedes that paragraph and
  says so, which is the same treatment `0045` gave `0023`.

## What would defeat this ruling

- A landed commit that touches `decisions/`, `STATUS.yaml`, or any root governing document.
  That would mean the scope exclusions are decorative and the loop can record its own
  standing.
- A landing carrying an observation from a participant that also built the change.
- A landing while `verify` or `lint` is red.
- The grant's 2026-11-23 expiry being extended without anyone deciding again. The expiry is
  the mechanism that keeps this a decision rather than a habit, and renewing it silently is
  the failure `decisions/0064` named.
- Any exercise of the grant that edits `contracts/standing-grants.json`. That would mean the
  self-exclusion does not hold, and this record's central claim is false.

## What still waits on Bdo

- Merging each pull request the loop produces. `O16b` refuses merging by name and ruleset
  `Gate` requires a pull request, so the remote crossing stays his.
- Whether the loop should be able to reach `origin/main` at all without him, which is a
  question about `O16b` and not about this grant. It is not asked here and no default is
  taken on it.
