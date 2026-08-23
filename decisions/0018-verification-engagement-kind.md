# 0018 · Verification engagement as a ticket kind

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Numbering note: decisions 0014 and 0015 are held for questions drafted on
concurrent branches. This decision uses 0018 so those histories can merge
without address collision.

## Decision

Add `verification-engagement` to the ticket kind enum in
`contracts/issue-metadata.schema.json`, with its own identity field
`engagement_id` matching `^RED-[A-Z0-9-]+$`, and two required target fields
`target_pr` and `target_head`.

A verification engagement constructs nothing. Its output is a finding, not an
artifact. It is therefore not an implementation stub, and the schema now refuses
`stub_id` on an engagement outright rather than admitting it unchecked.

`target_head` must be a full forty-character commit id. An engagement that does
not pin the exact commit it attacked cannot be reproduced, and an unreproducible
engagement cannot promote a `PROPOSED` finding to a confirmed one.

## Why this rather than a rename

Issue #57 is a live Red engagement against pull request #43. It was written as
`kind: verification-engagement` with `stub_id: RED-CHARTING-001`, and the ticket
contract refused both. The cheap repair was to rename it `STUB-RED-CHARTING-001`
and re-declare it an implementation stub.

That repair would have been a lie the `kind` field exists specifically to
prevent. `SDLC.md` already charters Red as a first-class stance, and the
transition table already reserves construction moves to construction actors:
`WORKER` may perform exactly one transition in the whole table,
`CHARTERED_NOT_IMPLEMENTED -> BUILT_SELF_TESTED_NOT_WITNESSED`. Nothing in the
table advances a ticket whose output is a finding. Filing an engagement as a
stub would have hidden that gap behind vocabulary rather than exposing it.

## What this decision does not do

It does not declare engagement-specific standing transitions. An engagement
ticket moves through the ordinary lifecycle; what its findings do to *another*
ticket's standing is already governed by `requires_purple`,
`FINDING_WITHOUT_FIXTURE`, and `FINDING_NOT_REPRODUCED`. Whether an engagement
needs its own transitions is a separate question and is not answered here.

It does not grant any actor the authority to open, take, or settle an
engagement. Kind is vocabulary, not authority.

## Consequences

- The metadata schema gains its first offline fixture corpus,
  `conformance/fixtures/tickets/metadata-cases.json`, wired into
  `sov_ticket.py selfcheck` and therefore into `scripts/verify.py` and the
  `contract` job. Before this, `issue-metadata.schema.json` was exercised only
  against the live board, so a change to it could be judged only after it had
  already reached GitHub. Ten cases, two positive and eight defeating.
- Each defeating case declares the substring its refusal must contain, so a case
  cannot pass by raising some unrelated defect elsewhere in the instance.
- `.github/labels.yml` gains `type: engagement` and
  `contracts/ticket-label-projection.json` maps the new kind to it, so the
  projection stays total rather than silently dropping a kind.
- Issue #57 becomes contract-satisfying without being misdescribed.

## Residuals

- `effect_class` admits `RESOURCE_CONSUMPTION` and `EXTERNAL_WORLD`, but
  `ticket-label-projection.json` maps neither. A ticket declaring either would
  project no effect label. Pre-existing, unrelated to this decision, and
  recorded here because this decision touched the projection.
- The schema states conditional *requirements* per kind but, apart from the
  `stub_id` guard added here, no conditional *prohibitions*. A bit may still
  carry a `stub_id` and validate. Pre-existing.
- `#51` and `#52` carry no metadata block at all, so the queue silently omits
  them. Whether the ticket contract should judge closed tickets is unanswered.

## Open review

The kind, its identity pattern, and the two target fields are proposed, not
ratified. `contracts/` is owner-reviewed; this decision reaches `RATIFIED` only
through owner judgement on the pull request, never through a green check.

## Source and authority

- `SDLC.md` verification dyad, Red stance, and the Purple release gate
- `AGENTS.md` change protocol, standing lifecycle, and evidence and standing
- `CONTRIBUTING.md` issue coordination contract
- `decisions/0016-github-coordination-registrar.md` registrar, typed ticket
  workflow, and label projection
- `contracts/ticket-transitions.json` actor kinds, refusal codes, and
  `requires_distinct_actor`
- issues #40, #41, #43, and #57
- Bdo's 2026-08-23 direction to grow the schema rather than rename the ticket
