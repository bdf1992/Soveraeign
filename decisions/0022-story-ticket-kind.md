# 0022 · Story as a ticket kind

Status: `RULED AT CONTROL RESOLUTION · OWNER ACCEPTANCE OVER EVIDENCE`

Ruled by `decisions/0033-close-the-founding-docket.md`; the identifier O22 is
retired with the rest of the founding docket.

Revised 2026-08-23: the teller is now `actor_kind` + `role`; the first-cut
`participant` cast is withdrawn. See "What this decision does not do".

## Decision

Add `story` to the ticket kind enum in `contracts/issue-metadata.schema.json`,
with its own identity `story_id` (`^STORY-[A-Z0-9-]+$`) and eight required
fields beyond the common set: `actor_kind`, `role`, `parent`, `expected`,
`found`, `leans_on`, `asks`, and `scenario`.

The teller is named in vocabulary the kernel already owns: `actor_kind` is
`SPEC.md`'s `HUMAN | MODEL | WORKER | SYSTEM`, and `role` is a participation
or boundary role from `CLASSIFICATION.md` (`operator`, `agent`, `worker`,
`witness`, `node`). The kind coins no new role and no new word for who shows
up at a counter.

A story is one actor crossing one counter and finding the substrate
short. It is told from the actor's side: what they expected to be able
to do, where the realization was not there, and what they ask of the ground
underneath. Each ask is addressed to the issue that owns the substrate it
wants changed. The scenario in `conformance/scenarios.json` says what the
system promised; the story says what the actor found; the gap between
them is the ask.

A story is never taken as work. It carries no `requires`, enters no queue,
blocks nothing, and closes no repository surface. The schema refuses
`requires`, `stub_id`, `bit_id`, and `engagement_id` on it outright. A story
above `PROPOSED` must name the scenario that walks it.

## Why a kind and not a field

Bdo's 2026-08-23 direction: build a narrative layer over the epic tree so the
conversation can be about actors meeting counters and the supports
behind them, rather than about `requires` edges. The first cut
(`.claude/epic/NARRATIVE.md`) showed the shape but nothing validated it.

Three cheaper repairs were available and each hides something:

- A `story:` prose field on bits would make the story the bit's own account
  of itself. A story is the actor's account, and a counter cannot tell
  its own customer's story any more than a build can witness itself.
- Filing stories as stubs would put them in the dispatch DAG. A story is not
  takeable; a worker assigned one would have nothing to build and would close
  it by writing the thing the story complained about, which is the ask, not
  the story.
- Keeping stories in the repository beside scenarios would keep them off the
  coordination surface where the bits and stubs they address live. The whole
  value of a story is that its asks point at tickets.

So the schema grows, as it did for `verification-engagement` (decision 0018).
Kind is vocabulary, not authority.

## What this decision does not do

It does not give a story its own standing transitions. A story reuses the
standing enum, read as: `PROPOSED` told; `DECLARED_NOT_IMPLEMENTED` bound to a
scenario; `BUILT_SELF_TESTED_NOT_WITNESSED` walked by its builder;
`WITNESSED` walked under independent observation; `RATIFIED` Bdo. The epic
walk derives **told / walkable / walked** from that plus the standing of the
supports, the way it derives ready / held / unrouted for bits and stubs. A
derived reading is evidence about the tree and settles nothing.

It does not add a row to `CLASSIFICATION.md`. A first cut declared a
seven-value `participant` enum that flattened actor kind and role into one
list and added `owner` and `peer-node` as words of its own; that collided
with the conformance sense of participant (the implementation under
qualification, `participant_id`) and with the naming rule's "sovereign
participant: Soveraeign Node". It was withdrawn the same day.

Owner is not a role and is refused as one (`MC-014`). Bdo's reading,
2026-08-23: Owner is a context over Operator, Actor, and the related
participation and boundary roles; it sets Bdo's Binding and Projection. Bdo
at a counter is a `HUMAN` / `operator`; Owner is what shapes the counter for
them, as the Sov profile shapes a model's seat. On a ticket it travels in the
existing `authority` field. Its realized form is already chartered as the
Console Service's operator settings and dashboard projections (O18). Whether
`CLASSIFICATION.md` should say this in its own words is a one-sentence
proposal for the governance domain, not part of this decision.

A `SYSTEM` actor has no expectations of its own. An external system's or
peer node's story is told on its behalf by the operator who integrated it or
crosses from it; `actor_kind: SYSTEM` records whose crossing it was, not who
wrote the story.

It does not make `.claude/epic/offices.json` load-bearing. The walk checks
that a story's `parent` is a live bit; it does not check that the bit is a
front-office counter. Enforcing that would move `offices.json` out of
plumbing, which is a separate call.

## Consequences

- `conformance/fixtures/tickets/metadata-cases.json` gains ten cases: two
  positive (a told story; a bound story leaving `PROPOSED`) and eight
  defeating (no actor; `owner` offered as a role; no ask; an ask with no
  owner; above `PROPOSED` without a scenario; construction identity; a
  `requires` edge; no `found`). Each defeating case names the substring its
  refusal must contain. Six guard mutations were tried; each was caught by
  exactly the case that claims it.
- `.github/labels.yml` gains `type: story`;
  `contracts/ticket-label-projection.json` maps the kind to it.
- `contracts/ticket-queue-policy.json` declares `kinds_outside_dispatch:
  ["story"]`; `scripts/sovticket/queue.py` honors it. A story never appears
  in the takeable queue and never credits or debits a blocker.
- `scripts/sovepic/walk.py` projects the label, reports a story whose parent
  is not a live bit or whose `leans_on` names an absent issue as a
  containment defect, and reads each story as told / walkable / walked with
  the supports still short. `survey.py` and `sov_epic.py status` carry a
  `stories` count and a `STORY` line per open story.
- `CONTRIBUTING.md` Issue coordination contract states the kind and its
  closing rule. `STATUS.yaml` gains `story_ticket_kind_status` and O22.
- `.claude/epic/NARRATIVE.md` six-line shape is realigned to the shipped
  fields.
- Verification: 28 metadata cases (with decision 0024's), 70 tooling
  tests, `scripts/verify.py` green.

## Residuals

- The first story is filed: `#67`, `Operator Desk - a human raises a
  judgement request` (`HUMAN` / `operator` at `#30`, told, short on `#7`,
  `#11`, `#12`, `#13` at the 2026-08-23 sync). Filing it required extending
  the metadata parser subset to block sequences of flat mappings for `asks`
  (`scripts/sovepic/metadata.py`, three unit tests).
- `#67` stands as one containment defect by design: its parent `#30` is an
  implementation stub, and the contract says a story walks up to a bit. The
  tree has no bit for the operator surface - the Console exists only as a
  charter (O18) and a closing stub (`#30`, closing `#19` and `#23`). The
  story's first finding is that its own counter is not chartered in the
  tree. Owner judgement: add an operator-surface bit to reach-and-motion, or
  rule that a story may walk up to a stub. The rule was not weakened to make
  the filing pass.
- `type: story` was created on the board attended for this filing. The
  remote label set still lacks `type: engagement` and `type: unblock`; full
  label synchronization stays gated behind O16.
- `walk.KIND_LABEL` does not project `verification-engagement`, so an
  engagement's `type: engagement` label is never expected by the epic walk.
  Pre-existing since decision 0018; recorded here because this decision
  touched the table and left it alone.
- The front-office-counter check (above).
- `decisions/0032-unblock-ticket-kind.md` grew the same schema and fixture
  corpus on the same day in a concurrent session. Both kinds validate
  together (28 metadata cases); the two decisions were not reconciled by
  hand and should be read side by side at review.

## Source and authority

- `AGENTS.md` change protocol, evidence and standing, implementation order
- `CONTRIBUTING.md` issue coordination contract
- `CLASSIFICATION.md` participation and boundary roles
- `decisions/0018-verification-engagement-kind.md` as the precedent for
  growing the kind enum
- `conformance/scenarios.json` as the thing a story binds to
- `.claude/epic/NARRATIVE.md`, `.claude/epic/offices.json`,
  `.claude/drafts/story-ticket-standard.md`
- Bdo's 2026-08-23 direction: a story narrates a participant crossing a
  domain and finding it lacking in realization, from the participant's
  expectations over the scenario, asking for extensions or adjustments of the
  substrate.
- Bdo's 2026-08-23 reading of Owner: a context for Operator, Actor, and the
  related participation and boundary roles; it sets Bdo's Binding and
  Projection.
