# Placement draft · Messaging

Status: `PROPOSED · DRAFT · TESTS ANSWERED · NOT REGISTERED · NOT OWNER-RATIFIED`

A placement study, drafted for Bdo, now carrying its own answers. It is not an issue: no
GitHub issue is created, no number is claimed, and nothing here changes `STATUS.yaml`, a
charter, or the epic tree. `AGENTS.md` Authority — a draft proposes, it does not register
or ratify.

## Owned scope

Owned: the statement of what is being placed, the four discriminating tests, the evidence
that answers them, a placement recommendation taken as a reversible default, and a naming
collision screen. Not owned: the name, the decision record that one change below requires,
and any claim that this is admitted work.

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

## The four tests, answered

### 1 · Is there state to own? Yes — the conversation.

`contracts/seat-etiquette.json` declares two carriage duties, `CARRY_EVERYTHING_RECEIVED`
and `NO_EDIT_IN_TRANSIT`, whose stated rule is that a listener owes its own listener
everything it heard, byte-identical. Neither is checkable against a single message.
`scripts/sovkernel/seat_etiquette.py` proves it: `_carriage_defects` takes `by_id`, an index
over the whole conversation, and reports that a message forwards something which is not in
this conversation; `_self_witness_defects` takes `earlier`, the prior messages, to catch an
actor speaking independently about work it performed.

Today that history arrives as an in-memory fixture list and nothing persists it. The state
is required for correctness, not convenience. **Candidate B — contracts only, no service —
is eliminated.**

### 2 · Is a human-facing post the same lifecycle as a seat statement? No.

Field-by-field, from the two schemas:

| Console Post | Seat Message |
| --- | --- |
| `content_address`, `content_digest` — content stored elsewhere and addressed | `body` — inline and freeform |
| `thread_id` — belongs to a durable conversation | no thread; addressed `to_seat` about a `subject` |
| `receipt_id` — the post produced a receipt | none; the statement is not itself a recorded transition |
| `standing` — settled | `standing_proposed` — a proposal only |
| no verb | `act` — a closed set of thirteen |
| `mentions`, `proposal_id` | `carries`, `aggregates` |

A post is a recorded artifact with a receipt and settled standing inside a thread. A seat
message is a speech act that proposes standing and carries items onward. Different
lifecycles. **Candidate A — extend the Console Service — is eliminated.**

The finding worth keeping: the Console's post already does the compaction this item wants.
`content_address` plus `content_digest` is exactly the property of a small message whose
content is resolved elsewhere, and it is built and self-tested. Seat messages are the ones
still carrying their body inline.

### 3 · Does anything address a participant that is not a seat? Yes.

`contracts/federation-crossing.schema.json` addresses `from_node` to `to_node` and states
that the crossing endpoints are Nodes, never Roots.
`contracts/seat-message.schema.json` addresses `to_seat`, a seat id in a registry that
currently holds four seats.

Two addressing planes already exist — seat to seat inside a node, node to node across
nodes — and `seat-etiquette.json` governs only the first. Whatever owns this must cover
both planes or state plainly that it declines crossings.

### 4 · Does the compacted body need authority nothing owns? No.

Fifteen identifier families are already declared with patterns in `contracts/`: `GROUND`,
`EPOCH`, `CANON`, `PROMISE`, `JOURNEY`, `FACT`, `PROD`, `RED`, `VILLAGE`, `EPIC`, `STORY`,
`CHORE`, `UNBLOCK`, `STUB`, `BIT` — plus capability names, seat ids, principal ids, node
ids and receipt refs. Every reference a compacted body would carry resolves against a
contract that exists.

A body contract is therefore a projection over declared vocabulary, not a new semantic
authority. `AGENTS.md` forbids the second; it does not forbid the first.

## Recommendation — no new service boundary

Taken as a reversible default under `decisions/0023-acceptance-not-approval.md` and
`decisions/0033`, Ruling 1. Service placement is not on the owner-hold list in
`contracts/acceptance-policy.json`, so it is settled here rather than escalated. The name
is not, and stays with Bdo.

The work splits across services that are already built:

| Piece | Home | Why | Standing today |
| --- | --- | --- | --- |
| The conversation as durable ordered history | Record Service | Its charter is the append-preserving spine, and a conversation is exactly that | `BUILT_SELF_TESTED_NOT_WITNESSED` |
| Expanding a reference into its meaning | Registry Service | `resolve` is the operation, and expansion is a resolve | `resolve` `BUILT` |
| Carrying a statement from A to B, and across nodes | Gateway Service | It owns the crossing and has one `IN_PROCESS` slice built end to end | first slice `BUILT` |
| Which act is admissible from which seat | `contracts/seat-etiquette.json` and `scripts/sovkernel/seat_etiquette.py` | Already there, already pressed by fourteen defeating fixtures | `PROPOSED`, checker built |

Candidate F, a new boundary, is refused: every piece has a home with a built operation
behind it, and a twelfth boundary would own only the seam between them. Candidate C is
accepted for carriage only, not for vocabulary, which keeps `OPEN-SEAMS.md` S18 from
gaining a third referent named gateway.

## The one governed change

`seat-message.schema.json` must stop carrying its body inline. The change is to replace
`body` with an address, a digest, and typed references — the shape Console's post already
uses — plus the `input_state_digest` pin that `node-interface.schema.json` already carries,
so a receiver refuses rather than guesses when its vocabulary has drifted from the sender's.

This reverses a deliberate choice, stated three times in the governed set: the schema calls
`body` freeform on purpose and says no checker reads inside it, `seat-etiquette.json`
repeats it in `generative_rule`, and `not_in_scope` states it a third time. Reversing it
needs a decision record, not a schema edit. That record is the next thing to write, and it
is the only part of this item that changes policy.

## Naming collision screen

Recorded, not decided:

- `contracts/seat-message.schema.json` uses **message** for the seat-to-seat envelope.
- The Console Service uses **post**, **thread**, **channel** and **notification**.
- `contracts/federation-crossing.schema.json` uses **crossing** for a node-to-node offer.

A single name over all three would have to say why a crossing and a post are the same kind
of thing. Test 2 says they are not. `OPEN-SEAMS.md` S18 is the standing example of one word
over two referents. Bdo settles the name.

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

## What this does not settle

The name. Whether the body change is adopted, which needs the decision record above. Any
standing for the pieces named, all of which keep the standing they already hold. Whether
crossings are in scope for the same vocabulary, which test 3 raised and did not answer.

## Next bounded operation

Draft the decision record that reverses the freeform body, stating the three places the
current rule is written and what evidence would defeat the reversal. Everything else in the
recommendation uses operations that are already built.
