# 0066 · Chore as a ticket kind, and the projection the walk restated

Status: `RULED AT CONTROL RESOLUTION · OWNER ACCEPTANCE OVER EVIDENCE`

## Decision

Add `chore` to the ticket kind enum in `contracts/issue-metadata.schema.json`,
and make `scripts/sovepic/walk.py` read `contracts/ticket-label-projection.json`
rather than restate it.

A chore maintains or retires a repository surface. It names the `path` it acts
on and carries a `chore_id`; it closes no obligation, so `parent_bits`,
`stub_id`, `bit_id`, `engagement_id`, and `story_id` are refused on it. It may
carry `requires`, because housekeeping often waits on a decision nobody has
taken. It is takeable work and enters the queue, sorting last among equally
urgent tickets.

Positive and defeating cases: `conformance/fixtures/tickets/metadata-cases.json`
MC-032 through MC-037. Each of the five guards was mutation-tested: dropping
the `chore_id` requirement, dropping the `path` requirement, admitting
`stub_id`, admitting `parent_bits`, and widening the `chore_id` pattern were
each caught by exactly one case.

## Why a kind and not a stub

Issue #52 asks for the removal of `charting/experiments/qa.skill.json` once #47
settles where skill declarations canonically live. It has carried no metadata
block since it was filed, because no kind fitted it: `implementation-stub`
requires a `path`, `parent_bits`, and the bits the surface closes, and a
removal closes nothing. The ticket was invisible to the work queue for three
days as a result, which the first board survey already reported and nobody
could repair without inventing a lie in the `kind` field.

The line between a chore and a demotion is what the surface's absence leaves
behind. If removing it leaves a bit unclosed, the stub that closed that bit is
demoted and the bit reopens; that is a standing change, not housekeeping. A
chore is admitted only where nothing was standing on the surface.

## The projection defect this repairs

`scripts/sovepic/walk.py` carried its own copy of the metadata-to-label tables
with a comment claiming the copy could not drift silently, because a test
asserted every label in it existed in `.github/labels.yml`. That check runs in
one direction only. When decision 0018 added `verification-engagement` to the
schema, `.github/labels.yml`, and `contracts/ticket-label-projection.json`, the
copy in the walk was not updated, and no test could see it: every name in the
copy still existed in the catalogue.

The consequence was a false accusation. Issue #57 is correctly filed and
correctly labelled, and `sov_epic.py validate` reported `label 'type:
engagement' contradicts kind 'verification-engagement'` against it. A
reconciliation whose defects are partly its own is worse than none, because the
real defects sit in the same list.

The walk now reads the contract. Two further gaps surfaced the moment the
totality check ran in the direction that had been missing:

- `effect_class` admits `RESOURCE_CONSUMPTION` and `EXTERNAL_WORLD`, and
  `contracts/ticket-label-projection.json` mapped neither. This was recorded as
  a residual in decision 0018 and left. Both now have declared labels, and a
  ticket that acts outside the node is visible on the board as one.
- `contracts/ticket-queue-policy.json` `kind_rank` never learned
  `verification-engagement`, and the lookup falls back to 99. A Red engagement
  gates a release under `SDLC.md` and has been sorting below everything since
  decision 0018 without saying so. Every dispatchable kind is now ranked.

`scripts/tests/test_sov_ticket_labels.py` asserts that every value the issue
schema admits on a projected axis is mapped. That is the direction a catalogue
check cannot see, and it is the check that would have caught all three.

A third gap turned up while applying the repair. `scripts/sovboard/survey.py`
read only open tickets, on the stated ground that "closed tickets are surveyed
for nothing". That is right for a contract defect - authoring a metadata block
for work nobody will take is not work - and wrong for a label. A closed ticket
keeps its labels, keeps appearing under a standing filter, and keeps being read,
so its labels were the one part of the coordination surface that could drift
with nothing watching. #6, #7, and #51 each sat mislabelled and each needed a
hand-built action, because the survey that exists to catch exactly that could
not see them. The two readings now have different populations, paired by
`BOARD-006` and `BOARD-014`.

## Change protocol record

1. **Requested outcome and current state.** Before: seven kinds, one of them
   unprojectable by the walk, two effect classes unlabelled, one kind unranked,
   and one open ticket with no admissible kind. After: eight kinds, every
   admitted value on every projected axis mapped and asserted, and the walk
   reading the contract instead of a copy of it.
2. **Affected.** `contracts/issue-metadata.schema.json` (the kind, `chore_id`,
   one conditional rule with five refusals),
   `conformance/fixtures/tickets/metadata-cases.json` (six cases),
   `contracts/ticket-label-projection.json` (`kind_to_type`, two effect
   classes), `contracts/ticket-queue-policy.json` (`kind_rank` completed),
   `.github/labels.yml` (three labels), `scripts/sovepic/walk.py` (reads the
   contract; `label_defects` takes it), `scripts/sovepic/survey.py`,
   `conformance/fixtures/board/survey-cases.json` (captures carry the three new
   labels), `scripts/tests/test_sov_epic.py`,
   `scripts/tests/test_sov_ticket_labels.py`, `scripts/sovboard/survey.py`
   (labels surveyed on closed tickets, defects not), `CONTRIBUTING.md`.
3. **Preconditions and expected result.** Before: 31 metadata cases;
   `sov_epic.py validate` reports a label defect against a correctly filed
   ticket. After: 37 metadata cases; `sov_ticket.py selfcheck` green;
   `verify.py` green; the walk reports no label defect against #57.
4. **Effect class.** `RECORD_LOCAL`. Creating the three labels on the
   coordination surface is `EXTERNAL_WORLD` under
   `coordination.issue_metadata` and leaves a receipt.
5. **Rollback.** Revert the files above. No standing, grant, or protected
   boundary changed; no ticket declared `chore` before this landed.

## Defaults taken

- Kind name `chore`, matching the commit-type vocabulary already in
  `AGENTS.md`, Branch and commit strategy. Alternatives considered:
  `maintenance`, `retirement`.
- `path` required. A chore that does not name its surface cannot be judged
  done.
- `requires` admitted, unlike `story` and `unblock`. A chore genuinely waits on
  decisions, and #52 waits on #47 today.
- `type: chore` is `6E7781`, the neutral family `type: stub` already sits in.
  Chore and stub are both repository-surface work; one builds and one retires.
- `kind_rank` 6, last. Rank is only a tiebreaker after blocked, horizon, what
  a ticket unblocks, and standing, so this says what to prefer between equally
  urgent tickets, not what matters least.
- `verification-engagement` stays out of `WORKABLE_KINDS` in
  `scripts/sovepic/survey.py`. `SDLC.md` requires the Red operator to be
  independent of the builder, and a build walk handing one to a `sov-worker`
  would defeat that. The exclusion is now commented as deliberate rather than
  reading as another gap.

## Residual

`conformance/fixtures/board/survey-cases.json` embeds the whole label catalogue
in each of its thirteen captures, so every catalogue addition edits thirteen
fixtures. That is brittle and was not refactored here; the corpus format is its
own concern.

## What would defeat this

A chore whose surface, once removed, leaves a bit unclosed — which would mean
the kind is admitting demotions as housekeeping. Or a projected axis value that
the schema admits and the totality check does not reach, which would mean the
check names the wrong set of axes.

## What still waits on Bdo

- Whether `chore` earns a place in the queue at all, or whether housekeeping should
  stay off the takeable board and be absorbed by whoever holds the surrounding
  concern under `AGENTS.md`, Closure ownership.
- Whether the three labels this adds should be created on the coordination surface
  now or held until a ticket actually carries one.

These defaults remain proposals. Work continues unless a governing constraint
is violated; Bdo may counter any of them in review.
