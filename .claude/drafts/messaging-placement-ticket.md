# Placement draft · Messaging

Status: `PROPOSED · DRAFT · TESTS ANSWERED · WITNESSED · NOT REGISTERED · NOT OWNER-RATIFIED`

A placement study, drafted for Bdo, carrying its own answers and the corrections an
independent witness made to them. It is not an issue: no GitHub issue is created, no
number is claimed, and nothing here changes `STATUS.yaml`, a charter, or the epic tree.
`AGENTS.md` Authority — a draft proposes, it does not register or ratify.

Witnessed at `cc95d85` by a participant that did not build it:
`reports/observations/2026-08-27-messaging-placement-witness-observation.json`. Six claims
pressed, five confirmed, one confirmed narrowly and refuted as stated. Every correction it
made is folded in below and marked. It supports `OPEN -> BUILT` and nothing further.

## Owned scope

Owned: the statement of what is being placed, the six candidates, the four discriminating
tests, the evidence that answers them, a placement recommendation taken as a reversible
default, and a naming collision screen. Not owned: the name, the decision record the one
governed change required, and any claim that this is admitted work.

## What is being placed

A way for one participant to ask another a question and receive an answer, where the
message on the wire is small because both ends already hold the vocabulary needed to
expand it. A reference such as `GROUND-006` travels as a token and the receiver resolves
it locally against contracts it already has.

Bdo's words, 2026-08-26: call this **communication** or **messaging**, not a language
service, because it is close to what it is. Recorded as given. `NAMING.md` reserves naming
to the owner and forbids an agent respelling a selection by convenience.

## The morphology already exists

`contracts/seat-etiquette.json` carries a field named `generative_rule` that states it
outright: a seat type absent from `seats` has no admissible acts, an act absent from `acts`
cannot be spoken, and adding either is a change to that table alone, because the message
schema, the fixtures format, and the checker all read from there.

One table generates the legal message space and three readers derive from it. That is the
shared kernel this item was reaching for, and it is already built and checked. The gap is
narrower than it first looked.

## The six candidates

Ruled on below. Listed here so the eliminations can be re-derived by someone other than
the author — the witness found this set missing from an earlier revision and it is the
finding that most weakened the study.

| Candidate | Placement |
| --- | --- |
| A | Extend the Console Service |
| B | Contracts only, no service |
| C | Gateway Service |
| D | Registry Service |
| E | Record Service |
| F | A new boundary under `services/` |

## The four tests, answered

### 1 · Is there state to own? Yes — the conversation.

`contracts/seat-etiquette.json` declares three carriage duties:
`CARRY_EVERYTHING_RECEIVED`, `NO_EDIT_IN_TRANSIT` and `NO_SELF_WITNESS`. None is checkable
against a single message. `scripts/sovkernel/seat_etiquette.py` shows why:
`_carriage_defects` takes `by_id`, an index over the whole conversation, and
`_self_witness_defects` takes `earlier`, the prior messages, to catch an actor speaking
independently about work it performed.

*Witness correction.* The checker proves the state must be **conversation-scoped**, not
that it must be **durable**. One process holding a conversation in memory satisfies both
functions. Durability is an inference, sound for messaging that outlives a process and
unsound if it never does, and it is not read off the code. Stated here rather than left
implicit.

Either way the state is required for correctness, not convenience. **Candidate B is
eliminated:** a contracts-only placement has nowhere for a conversation to live.

### 2 · Is a human-facing post the same lifecycle as a seat statement? No.

Field-by-field, from the two schemas, with two rows corrected by the witness:

| Console Post | Seat Message |
| --- | --- |
| `content_address`, `content_digest` — content stored elsewhere and addressed | `body` — inline and freeform |
| `thread_id` — belongs to a durable conversation | `$defs.subject.in_reply_to` — reply linkage exists, unused by all 19 fixtures |
| `receipt_id` — the post produced a receipt | none; the statement is not itself a recorded transition |
| `standing` — operational standing, bottoming at `RECORDED` | `standing_proposed` — artifact standing, proposed only |
| no verb | `act` — a closed set of thirteen |
| `mentions`, `proposal_id` | `carries`, `aggregates` |

An earlier revision claimed the seat plane had no reply linkage and that a post's standing
is settled. Both were wrong: `in_reply_to` exists, and `SPEC.md:227` states a record at
`RECORDED` claims no authority.

The sharper contrast the witness supplied: the two `standing` fields run on **different
vocabularies** — operational standing on the post, artifact standing on the seat message.
A post is a recorded artifact inside a thread; a seat message is a speech act that proposes
a transition and carries items onward. **Candidate A is eliminated**, on firmer ground than
the original argument gave it.

### 3 · Does anything address a participant that is not a seat? Yes.

`contracts/federation-crossing.schema.json` addresses `from_node` to `to_node` and states
at line 5 that its endpoints are Nodes rather than Roots.
`contracts/seat-message.schema.json` addresses `to_seat`, a seat id in a registry that
currently holds four seats.

Two addressing planes exist — seat to seat inside a node, node to node across nodes — and
`seat-etiquette.json` governs only the first. *Witness addition:* the planes already touch.
A crossing record carries `origin_seat`, matching `^seat:`, for attribution. So the
question is not whether the planes meet but whether one vocabulary serves both.

This test eliminates no candidate. It is the test that would decide candidate F, and it is
unanswered. That is stated plainly here because the recommendation below rests on it.

### 4 · Does the compacted body need authority nothing owns? No, for the identifiers it would carry.

Fifteen uppercase `FAMILY-<id>` identifier families are declared with patterns in
`contracts/`: `GROUND`, `EPOCH`, `CANON`, `PROMISE`, `JOURNEY`, `FACT`, `PROD`, `RED`,
`VILLAGE`, `EPIC`, `STORY`, `CHORE`, `UNBLOCK`, `STUB`, `BIT`. The witness parsed all 71
JSON files under `contracts/` — 45 distinct patterns, none unparsed — and confirmed the
list exactly.

*Witness correction to the scope of that claim.* Fifteen is right for that shape and wrong
as a census of declared identifiers. Other pattern-declared forms exist — `^A[0-9]+$` for
acceptance packets, `grant:`, `lease:`, `#<n>`, `sov://` — and two families used in
governed contract files, `FOUND-001..003` in `ai-native-qualifications.json` and
`SWEEP-01..03` in `acceptance-routing.json`, carry no pattern at all. An earlier revision
also wrote "plus receipt refs", which names something with no declared pattern anywhere;
that clause is withdrawn.

The conclusion survives the correction: every identifier a compacted body would carry
resolves against a contract that exists, so a body contract is a projection over declared
vocabulary rather than a new semantic authority. `AGENTS.md` forbids the second and permits
the first. This test selects no home.

## Recommendation — do not mint a new boundary

Taken as a reversible default under `decisions/0023-acceptance-not-approval.md` and
`decisions/0033`, Ruling 1. Service placement is not on the owner-hold list in
`contracts/acceptance-policy.json`, so it is settled here rather than escalated. The name
is not, and stays with Bdo.

The work splits across services that already exist:

| Piece | Home | Why | Standing today |
| --- | --- | --- | --- |
| The conversation as ordered history | Record Service (E) | Its charter is the append-preserving spine, and a conversation is exactly that | `BUILT_SELF_TESTED_NOT_WITNESSED` |
| Expanding a reference into its meaning | Registry Service (D) | `resolve` is the operation, and expansion is a resolve | charter says `resolve` `BUILT`; `STATUS.yaml` carries no `registry_service_status` key |
| Carrying a statement from A to B | Gateway Service (C) | It owns the crossing | `STATUS.yaml:30` reads `CHARTERED_BOUNDARY_NOT_IMPLEMENTED`, contradicting its charter and `services/README.md`, which say a first `IN_PROCESS` slice is built |
| Which act is admissible from which seat | `contracts/seat-etiquette.json` and `scripts/sovkernel/seat_etiquette.py` | Already there, already pressed by fourteen defeating fixtures | `PROPOSED`, checker built |

Two corrections the witness forced, both recorded rather than smoothed over.

**The Gateway cell disagrees with itself.** `AGENTS.md` gives `STATUS.yaml` ownership of
standing, so on the owning document the Gateway is not implemented. The charter and
`services/README.md` say otherwise. That contradiction is pre-existing, was unreported
before this study, and is not repaired here because it belongs to the governance domain,
not to this concern.

**Candidate F is not minted; it is not refused.** An earlier revision wrote that a new
boundary "is refused", which overstates the evidence. Tests 1 and 2 eliminate B and A on
evidence. Test 4 selects nothing. Test 3 eliminates nothing and is the test that would
decide F — whether one vocabulary serves both addressing planes — and it is unanswered.
Not minting an eleventh boundary is the right reversible default at this tier; it is not a
proven refusal, and the study should not be read as one. A new boundary would be the
**eleventh**: `services/` holds ten at `cc95d85`. An earlier revision said twelfth, having
counted directories in a working tree that ten sessions were writing.

Note also what the Gateway cell rests on: `decisions/0079` states that nothing in the
repository yet carries a message from one seat to another. That cell is a plan, not an
observed placement.

## The one governed change

Recorded as `decisions/0079-seat-message-body-is-addressed.md` in the same commit as this
draft: a seat message addresses its body instead of carrying it, and pins the vocabulary it
was written against. `PROPOSED`. That record carries the argument, the defeating
conditions, and the fixture consequence.

## Naming collision screen

Recorded, not decided:

- `contracts/seat-message.schema.json` uses **message** for the seat-to-seat envelope.
- The Console Service uses **post**, **thread**, **channel** and **notification**.
- `contracts/federation-crossing.schema.json` uses **crossing** for a node-to-node offer.

A single name over all three would have to say why a crossing and a post are the same kind
of thing. Test 2 says a post and a seat message are not. `OPEN-SEAMS.md` S18 is the standing
example of one word over two referents. Bdo settles the name.

## Change protocol

- Effect class: `RECORD_LOCAL`.
- Observable result: one file under `.claude/drafts/`. No contract, charter, service,
  schema, standing or status field changed.
- Rollback: delete the file.
- Refusal boundary: this draft creates no boundary and proposes no standing transition.

## Defaults taken

- Placement settled here as a reversible default rather than escalated, because it is not
  an admissible owner hold under `contracts/acceptance-policy.json`.
- Filed as a draft rather than a GitHub issue, because Phase I refuses network effects.
- Named for the owner's word without respelling it, per `NAMING.md`.
- No charter and no `services/` directory created, consistent with the recommendation.
- Committed to `feat/federation-harness-and-hardening` rather than a `docs/` branch,
  because ten live sessions share this exact working tree and switching HEAD moves it for
  all of them. A separate branch here needs a worktree.

## What this does not settle

The name. Whether the body change in `decisions/0079` is adopted. Any standing for the
pieces named, all of which keep the standing they already hold. Whether one vocabulary
serves both addressing planes, which test 3 raised and did not answer, and which is what
would decide candidate F. The Gateway standing contradiction, which belongs to governance.

## What still waits on Bdo

The name, and nothing else in this draft. The witness routed four judgement items,
including whether one vocabulary serves both addressing planes. Everything else here is
reversible record-local work already done.
