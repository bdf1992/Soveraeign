# 0051 · Workers own closure and recruit their own counterpart

Status: `OWNER-DIRECTED · BUILT, NOT YET OWNER-ACCEPTED`

## Decision

A worker that accepts a bounded concern owns the concern through a landable
result. Branches, issues, pull requests, review requests, and acceptance packets
are coordination surfaces inside that work; creating one is not completion.

The default worker loop is:

`inspect -> build -> test -> recruit helper -> repair -> freeze -> witness -> land`

Ordinary engineering work must not be externalized into new WIP merely because a
worker encounters uncertainty, a follow-up, or another logical implementation
step. When the discovered work remains inside the current concern, service and
effect boundary and does not change owner-held intent, the worker completes it on
the current branch. A separate issue is reserved for an independently durable
concern: a different service lifecycle, owner-held decision, effect boundary,
unresolvable deferred dependency, or coordination need that should survive the
current branch.

A worker normally carries one implementation branch and one pull request for its
current concern. Parallel branches require independently mergeable work or an
explicit isolation reason. The repository should optimize for short-lived work
objects and landed results rather than maximizing decomposition.

## Counterpart expectation

When the host can invoke another model participant, every model worker is
expected to request its own bounded counterpart before treating implementation as
ready to land. The owner does not broker this help.

The counterpart receives the claim, relevant paths, current diff or revision,
and a defeating question. It searches for defects, missing cases, unnecessary
abstraction, authority leakage, scope drift, and simpler closure paths. A smaller
or cheaper model is acceptable when it can understand the bounded contract and
observation. Model size is not authority.

The primary worker owns every repair and the final branch.

## Helper is not witness

A participant that writes, edits, or directs implementation may help critique the
result but may not independently witness that same result.

When `WITNESSED` standing is required, the primary worker freezes a commit or
digest and requests a fresh, non-editing invocation against that exact revision.
The witness receives the exact claim and defeating observation and produces an
attributable report. If the witness defeats the claim, the worker repairs the same
concern, freezes a new revision, and requests a new witness pass.

If the host cannot invoke another model, the worker records that capability as
unavailable and uses the strongest independent local checks available. That may
support `BUILT`; it does not turn self-review into `WITNESSED`.

## Landing rule

For reversible work inside the live grant that does not cross an owner-acceptance
boundary, the worker is expected to chase CI and review findings, repair failures,
update or rebase, and land the pull request once required checks pass, the head
revision is known, no genuine open seam is silently decided, and the merge itself
is permitted.

Owner-acceptance PRs remain open until the owner explicitly accepts or lands
them. This decision therefore reduces owner involvement rather than expanding it:
ordinary work closes at the worker; only genuine acceptance boundaries travel
upward.

## Consequences

- `AGENTS.md` makes closure ownership normative for all repository agents.
- `CONTRIBUTING.md` teaches the same loop to human and model contributors.
- `CLAUDE.md` binds Claude-hosted workers to proactive subagent/model assistance.
- A logical next step inside a current concern is implemented rather than turned
  into a new issue by default.
- A PR is a temporary working surface, not a place to park routine engineering
  judgement for the owner.
- Helper participation does not weaken the prohibition on self-witness.

## What this decision does not do

- It does not let a worker widen a grant or cross an effect boundary.
- It does not let confidence, model consensus, review, tests, or CI grant
  authority.
- It does not let the builder or an editing helper claim independent witness.
- It does not remove genuine open seams or owner-held acceptance boundaries.
- It does not require a particular provider, model family, or model size.
- It does not require opening a new tracking issue for this policy; the policy
  change itself is carried by the branch and pull request that implement it.

## Demotion

Demote this policy if closure ownership causes workers to hide genuine seams,
merge across live authority boundaries, or treat a subordinate helper as
independent evidence without role separation and a frozen revision. Also demote
it if the one-concern WIP default materially prevents independent parallel work
that would otherwise be safely mergeable.

## Source and authority

Bdo's direction, 2026-08-24: the growing branch, PR, issue, and WIP surface is
creating unnecessary difficulty; contributors should land their own bounded work
using their tools, environment, agency, and helpers, and even a worker should be
expected to request its own junior-model counterpart or witness rather than
pushing routine decisions upward.

This record preserves that direction while keeping the existing distinction
between helper evidence, independent witness, and owner acceptance.
