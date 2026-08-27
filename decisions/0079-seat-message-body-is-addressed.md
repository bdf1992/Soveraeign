# 0079 · A seat message body is addressed, not carried

Status: `PROPOSED · BDO HAS NOT RULED`
Date: 2026-08-26
Supersedes: nothing. Narrows `decisions/0035-seat-message-etiquette.md`.
Drafted from `.claude/drafts/messaging-placement-ticket.md`, which reached this as its one
governed change. Witnessed with that draft at `cc95d85`:
`reports/observations/2026-08-27-messaging-placement-witness-observation.json`. The findings
it raised against this record are folded in below and marked.

Number minted from `scripts/sov_session.py reserve-decision` against a live collision field:
ten sessions were writing this tree, and 0076 through 0078 were claimed between the session
briefing and the reservation. `decisions/0020` and `decisions/0035` set the precedent of
saying so.

## What was found

`contracts/seat-message.schema.json` carries its `body` inline, and three places in the
governed set say that is deliberate:

| Where | What it says |
| --- | --- |
| the schema's own `body` description | freeform on purpose, and no checker reads inside it |
| `contracts/seat-etiquette.json`, `generative_rule` | nothing in that file constrains a message body, and no checker reads inside one |
| `contracts/seat-etiquette.json`, `not_in_scope[0]` | the content, shape, length, or wording of a message body is out of scope |

That was the right call for admissibility. Etiquette decides who may say a thing, never
what the thing says, and a table that reached inside bodies would be deciding both.

The cost lands elsewhere. A statement between seats is as large as everything it means,
because it carries its meaning rather than addressing it. A receiver holding drifted
contracts expands nothing, notices nothing, and reads a token as whatever that token means
to it today.

Both repairs already exist in this repository and neither is on the seat message:

- `services/console/contracts/post.schema.json` requires `content_address` and
  `content_digest`. The content lives in the store; the record carries the address and the
  digest. Built and self-tested (`decisions/0036`).
- `contracts/node-interface.schema.json` requires `source_digests` and one sha256
  `input_state_digest` over everything it was derived from.

## Ruling proposed

**A seat message addresses its body instead of carrying it, and pins the vocabulary it was
written against.** `body` is replaced by four fields:

| Field | Holds |
| --- | --- |
| `body_address` | where the body bytes are stored |
| `body_digest` | sha256 of those bytes |
| `references` | the declared identifiers the body resolves against, typed |
| `vocabulary_digest` | sha256 over the contracts the sender wrote against |

A receiver whose `vocabulary_digest` does not match refuses. It does not expand under its
own vocabulary and it does not guess, because a compact message has no redundancy left in
it to catch the mismatch.

**The etiquette table does not change and the checker still reads nothing inside a body.**
The three statements above stay literally true of
`scripts/sovkernel/seat_etiquette.py`. What changes is that a body becomes readable *later*
by whoever holds the store, which is a different reader with different authority. This
ruling narrows `decisions/0035` on one point only: a body is addressed. It does not open
bodies to the admissibility check.

## Defaults taken

- **`references` is typed against the fifteen identifier families already declared in
  `contracts/`** — `GROUND`, `EPOCH`, `CANON`, `PROMISE`, `JOURNEY`, `FACT`, `PROD`, `RED`,
  `VILLAGE`, `EPIC`, `STORY`, `CHORE`, `UNBLOCK`, `STUB`, `BIT` — plus capability names,
  seat ids, principal ids, node ids and receipt refs. No new registry is minted. `AGENTS.md`
  forbids a second competing semantic contract; a projection over declared vocabulary is
  not one. Reversible: add a family if a body needs one nothing declares.
- **sha256 for both digests**, matching `node-interface.schema.json` rather than choosing a
  second algorithm for one schema.
- **The pin covers the vocabulary the sender wrote against, not the repository.** A
  whole-tree digest would refuse on every unrelated commit and be turned off within a week.
- **`act`, `subject`, `carries`, `aggregates`, `standing_proposed` and the etiquette table
  are untouched.** The closed set of thirteen acts is unchanged.

## The fixture consequence

*Raised by the witness; this record did not name it and should have.*

`contracts/fixtures/seat-message.fixtures.json` holds nineteen cases and every one of them
carries an inline `body`. Under this ruling all nineteen need rewriting, which is the real
cost of the change and is larger than the schema edit.

One of the nineteen also settles a question this record first listed as open.
`SEATMSG-DEF-EMPTY-BODY` is an existing defeating case whose stated reason is that "the body
is freeform, not optional; a seat that says nothing has not spoken." So a bodyless seat
message is already a declared defect, and the objection that `REFUSE` or `STALL` might
legitimately carry nothing is answered in the repository, against itself. That objection is
withdrawn from the list below rather than left standing as though unresolved.

## What would defeat this ruling

- **A measurement showing size was never the cost.** Nobody has measured a seat message.
  If real bodies are small, the addressing buys nothing and only `vocabulary_digest` earns
  its place.
- **A store not reachable at read time.** If a receiver cannot resolve `body_address`, an
  addressed body is strictly worse than an inline one and this reverses.

## What this does not fix

- **Crossings.** `contracts/federation-crossing.schema.json` addresses nodes, not seats.
  This ruling touches the seat plane only, and whether the same shape belongs on a crossing
  is open.
- **Routing.** Nothing in the repository yet carries a message from one seat to another.
- **The name.** `NAMING.md` reserves it to Bdo. Nothing here names anything new.

## What still waits on Bdo

Nothing in this ruling. The change is `RECORD_LOCAL`, reversible by restoring one schema
field, and names no reason from the seven in `contracts/acceptance-policy.json`. Under
`decisions/0023-acceptance-not-approval.md` that makes it work to do and present, not work
to ask about, and the three defeating conditions above are available to any tier.

One adjacent thing is owner-held and is deliberately absent here: what this family of work
is called. `NAMING.md` reserves that, `.claude/drafts/messaging-placement-ticket.md` carries
the collision screen, and this decision names nothing new so that it does not prejudge it.

## The seam this record depends on

*Raised by the witness, which found this written as a residual when it is a named seam.*

`DEPENDENCY_SEAM`, per `contracts/closure-ownership.json`. `body_address` names a location
that no participant in this repository is yet obliged to keep, because nothing holds a
conversation. The placement study recommends the Record Service for that, on the grounds
that the three carriage duties — `CARRY_EVERYTHING_RECEIVED`, `NO_EDIT_IN_TRANSIT` and
`NO_SELF_WITNESS` — are only checkable against earlier messages.

Naming it as a seam rather than a residual states the honest order: the schema change is
implementable, but a message that addresses a body nothing stores is worse than one that
carries it. The store lands first, or the two land together.

Provision asked: a conversation store. Tier that can serve it: whoever holds the Record
Service concern. Not asked of Bdo, and not a hold.

## Residual

This ruling changes one schema and settles nothing about the store above, nothing about
routing, and nothing about whether the same shape belongs on a federation crossing.
