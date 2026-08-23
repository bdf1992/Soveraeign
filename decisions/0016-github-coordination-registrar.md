# 0016 · GitHub coordination registrar and the typed ticket workflow

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Numbering note: `0014` and `0015` are reserved for the Console Service boundary and
the scheduled-runs pattern, which exist as local drafts and are not yet on `main`.

## Decision

Make the GitHub coordination surface machine-checkable without making it
authoritative, through four declared artifacts and one crossing.

**One registrar.** `adapters/github/` becomes the single declared crossing to the
GitHub coordination surface, extending the existing `GitHub` adapter row in
`adapters/README.md` from source capture to coordination capture. It is the only code
permitted to call the GitHub API. It captures with exact provenance, emits a capture
receipt, refuses visibly through `REGISTRAR_UNAVAILABLE`,
`REGISTRAR_UNAUTHENTICATED`, and `REGISTRAR_EMPTY`, and never falls back to a cached
board. Everything else reads its export from disk and runs offline, so every check
survives a sealed CI job, the day-zero budget, and a fresh witness.

**A typed ticket workflow.** `contracts/ticket-transitions.json` declares the legal
standing transitions over the `soveraeign-ticket/v1` lifecycle: which pairs exist, which
`actor_kind` may perform each, and which evidence each requires.
`contracts/ticket-transition.schema.json` types the request that proposes one. Twelve
refusal codes are declared, and
`conformance/fixtures/tickets/transition-cases.json` proves each one fires.

**Owner approval where judgement actually lives.** `WITNESSED -> RATIFIED` admits only
`actor_kind: HUMAN` whose `actor_id` is the declared owner; every other request is
refused as `OWNER_RATIFICATION_REQUIRED` or `ACTOR_KIND_REFUSED`. That refusal is a
statement, not an enforcement: ratification enters the repository through `CODEOWNERS`
review on `STATUS.yaml`, `decisions/`, and the governing set, and becomes binding only
when branch protection on `main` requires code owner review.

**Projections, declared as data.** `contracts/ticket-label-projection.json` derives the
visible label set from ticket metadata, making `CONTRIBUTING.md`'s "labels are
projections, not a second authority" mechanically true; a live label the metadata does
not imply is reported as drift. `contracts/ticket-queue-policy.json` declares the
ordering that turns the board into a takeable queue. Both are declared data rather than
code, because both change what work is offered first and to whom.

**Two lanes and a gate.** `.github/workflows/qa-lanes.yml` runs the `SDLC.md`
verification dyad per pull request. Blue runs `scripts/verify.py` and establishes
`BUILT` evidence only. Red screens adversarially and emits `PROPOSED` findings; it is
opt-in behind a secret and a repository variable, and an unconfigured lane declares
`RED_LANE_UNCONFIGURED` visibly rather than skipping silently. Purple evaluates any
standing change proposed in the pull request body and refuses what the table forbids.

## Consequences

- The board becomes a queue that can be taken from: `sov_ticket.py queue` reports which
  tickets are takeable, which are blocked and by what, and which unblock the most.
  Position in the queue is a projection and grants nothing.
- A confirmed Red finding cannot close without a permanent defeating fixture, and cannot
  be confirmed by the operator that raised it. `FINDING_WITHOUT_FIXTURE` and
  `FINDING_NOT_REPRODUCED` make `SDLC.md`'s release-gate rules 2 and 3 executable.
- A CI adversarial pass is screening, not a Red engagement. Its findings stay `PROPOSED`
  because independent reproduction is what promotes them, and CI reviewing its own
  repository is not independent.
- Three live tickets already violate the ticket contract and carry no labels. Turning
  the `ticket contract` workflow on makes the board red until they are repaired. That
  visibility is the point; it is not a reason to weaken the check.
- The bounded JSON Schema validator refuses any keyword it does not implement. Adding a
  keyword to a contract without adding it to the validator fails loudly rather than
  passing an unchecked constraint.
- Nothing in this decision writes to GitHub. Label synchronization, project field
  updates, issue comments, and branch protection are queued as owner actions.
- An MCP server over the coordination surface is bound in advance to the registrar's
  declared projection and refusals, and to transport-only standing. It is not built.

## Source and authority

- `AGENTS.md` change protocol, standing lifecycle, evidence and standing, directory
  boundaries, and the secrets and local boundaries rules
- `SDLC.md` two dyads, combination outcomes, and the release gate
- `CONTRIBUTING.md` issue coordination contract and the labels-as-projection rule
- `contracts/issue-metadata.schema.json` the `soveraeign-ticket/v1` type
- `contracts/event-envelope.schema.json` the shared `actor_kind` and `effect_class`
  vocabularies, reused rather than duplicated
- `adapters/README.md` the existing GitHub adapter row and the no-silent-fallback rule
- `STATUS.yaml` protected boundary `no_external_effects_in_phase_i`
- Bdo's 2026-08-23 direction to automate issue, pull request, and commit coordination
  with QA and code review on commits, validated QA, ticket updates from pull requests,
  a typed workflow with owner approvals, and a prioritized queue over one GitHub
  registrar and MCP connection
