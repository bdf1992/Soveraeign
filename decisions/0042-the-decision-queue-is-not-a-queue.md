# 0042 · The decision queue is not a queue

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

Numbering note: minted on `feat/acceptance-docket` off `c296c25`, which holds
records through `0040`. `0041` exists uncommitted in the shared tree. `OPEN-SEAMS.md`
S16 carries the allocation seam; this record renumbers rather than contests.

Drafted after Bdo asked whether "nothing I can do moves those" was true of the
stack of unruled decision records. It is not true, and the reason it is not true
is worth a record.

## What was observed

Forty decision records carry **twenty-two distinct status strings**. Six different
phrasings mean "drafted, nobody has ruled": `PROPOSED FOR BDO RATIFICATION`,
`PROPOSED · OWNER RATIFICATION PENDING`, `PROPOSED · OWNER FREEZE PENDING`,
`PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`, `PROPOSED · BDO HAS NOT RULED`, and
`SOURCE-GROUNDED PROPOSAL`. Nothing parses any of them. The status line is free
prose in a file nobody counts.

Seventeen records read as open. Reading each one against
`decisions/0023-acceptance-not-approval.md` and
`decisions/0033-close-the-founding-docket.md` Ruling 1 gives a different picture:

- **six** genuinely need Bdo — `0020` seat topology, `0035` seat etiquette,
  `0036-B` the automatic console session, `0038` the authority assignment, `0039`
  the node surface, and `0042` itself;
- **nine** already have his answer recorded in `STATUS.yaml` while the record's
  own status line still says pending, including `0001`, the founding boundary,
  which `STATUS.yaml` has listed under `accepted_repository_claims` since day one;
- **four** touch no owner-held category at all and can be settled at Control or
  Work, which is where Ruling 1 says they belong.

So the queue that looked like seventeen judgements owed by one person is six
judgements, nine edits, and four rulings nobody asked for.

The first draft of this record said three, nine and five. An independent witness
found two of the three counts wrong, and section 4 below is why: routing records
instead of questions loses whichever question disagrees with a record's headline.
The numbers here are the ones `scripts/sov_docket.py queue` prints, and if they
ever disagree again the tool is right and this prose is stale.

The other half of the cause is rate. Seven records were minted on 2026-08-23
alone. Ruling 1 already says to settle at the lowest tier that can produce
defeating evidence, but nothing applies that rule at drafting time, so a record
gets written and joins a pile whether or not it needed to exist.

## Decision

Five parts, none of which settles a decision.

### 1. A decision record's standing is a closed set, adopted by crosswalk

`contracts/decision-standing.json` declares five standings — `PROPOSED`,
`RULED_BELOW`, `OWNER_DIRECTED`, `OWNER_ACCEPTED`, `SUPERSEDED` — each with a
plain gloss and whether it counts as settled. It also carries a crosswalk from
every one of the twenty-two strings the existing records already use.

The crosswalk is the point. It means this contract can be adopted without editing
a single decision record: a record keeps its own prose and this file says what
that prose means. A status string absent from the crosswalk is reported as a
defect rather than guessed at.

### 2. Every open question declares who settles it, and why

`contracts/acceptance-routing.json` carries one entry per open **question**:
which record it comes from, whether it reaches the owner, which of the five
owner-held categories it touches, a reason a reader can disagree with, the
`STATUS.yaml` field that already answers it if one does, and what to do if the
routing is confirmed.

The unit is a question rather than a record, and that correction came from an
independent witness of this branch rather than from its author. The first version
routed records, and `decisions/0036` shows why that fails: it names three things
waiting on Bdo, of which the first is sequencing that Control settles and the
second — whether every Claude Code session in this repository should open and
close a console session automatically — is a default applied to anyone who clones
the repository. A per-record boolean answered the first and silently dropped the
second. A record with mixed questions loses the ones that disagree with its
headline.

Bare ratification is not routed. Every `PROPOSED` record needs it by definition,
so counting it would mark all eighteen and say nothing. The file answers the
narrower question: does this need a judgement from Bdo *other* than the
ratification every proposal already needs.

`enumerated_from` records where each question came from — the record's own
declared list, or its headline where the record does not enumerate. Exactly one
open record of eighteen enumerates its own owner questions today, so the field is
honest rather than decorative, and a record marked `headline` may not be split
into several here: claiming otherwise would assert a reading nobody performed.

Every entry is a claim, not a settlement. `reaches_owner: false` does not close a
question; it says the question can be settled below the owner and names why.
Someone at that tier still has to do it, and Bdo may reject any routing in the
file.

### 3. The docket is rebuilt, never written out

`scripts/sov_docket.py queue` builds the queue from `decisions/` and the two
contracts at the moment it runs. `reports/2026-08-23-ratification-docket.md` is
the same artifact written by hand at 16:06 and stale by 19:00, because a docket
assembled by hand rots the moment a record is minted. A projection does not.

`scripts/sov_docket.py check` runs in `scripts/verify.py`. It proves the crosswalk
is total, that no routing entry names a record that does not exist, that a
`reaches_owner` claim names a category and a category claim reaches the owner, and
that any `already_recorded_as` key is genuinely present in `STATUS.yaml`.

That last check found an error in this record's own routing table on its first
run: `0036` claimed `console_service_boundary` and the real key is
`console_service_operator_surface_boundary`. A routing file that could assert
`STATUS.yaml already answers this` without proving it would be worse than no file.

### 4. A decision record states its own owner questions

`contracts/decision-standing.json` declares the heading `What still waits on Bdo`
and requires it from record `0043` onward. One bullet per question; a bullet
saying only that the record awaits ratification is not a question.

This is the durable half of the enumeration finding. Today routing is one reader
inferring questions from someone else's prose, and that interpretive step
produced both defects the witness of this branch found. A record that states its
questions turns routing into reading a list.

`0001` through `0042` are exempt and stay exempt. Two of them carry the section:
`0036`, whose author happened to write it with nothing asking for it, and this
record, which follows its own rule rather than exempting itself. Retrofitting the other seventeen would mean one reader inventing
questions on behalf of records other people wrote, which is the failure the rule
exists to end. Named as debt rather than silently forgiven, the way
`scripts/lint.py` handles module size.

### 5. One merged list, ruled by Bdo

Bdo ruled on 2026-08-24 that he wants one list, not two that disagree. So a
question enters `contracts/acceptance-routing.json` whether it comes from a
decision record or from anywhere else, `source` says which, and `queue` prints
one list.

Two mechanisms may still exist, and the distinction is worth keeping: PR #81 is
a **gate** that stops work being parked on an owner seat without a reason, and
runs at the moment work would stall. This is a **census** of what is already
written, and runs over history. They have different failure modes — a gate that
goes red blocks a build, a census that is wrong only misinforms — and collapsing
them would couple the two. What Bdo ruled out is two published counts, not two
mechanisms, and only this one publishes a number.

Twelve items from `reports/2026-08-23-qa-witness-sweep-c296c25.md` are now in the
list. Two of them are questions a decision record already carries — the sweep's
item 16 is `0036-B`, its item 3 is `0038-A`. Those are kept as duplicates rather
than deleted, so the agreement between two independent readings stays visible,
and they are excluded from every count.

The count is now derived rather than argued. Two readers produced fifteen and
sixteen from the same file by hand within an hour of each other; `queue` prints
sixteen and shows its working.

## Why the check is the part that lasts

Minting a decision record now costs a routing entry with a reason, because an open
record with no entry is reported by `unrouted` and fails `check`. Writing that
reason is where Ruling 1 gets applied — at drafting time, by the drafter, while
the question is fresh — instead of months later by whoever tries to read the pile.

## Relationship to PR #81

This was drafted without knowing PR #81 (`feat/acceptance-gate`, opened 21:49 the
same evening) existed. It does, and it reaches the same headline from the other
direction: its description says seventeen questions sat addressed to the owner and
roughly two needed to be. Two readers arriving at three and two independently is
corroboration, and the agreement is worth more than either count.

The overlap was also literal. Both defined `scripts/sov_accept.py`, so this one
was renamed to `scripts/sov_docket.py` before landing. That collision is the same
allocation seam as `OPEN-SEAMS.md` S16, one layer down: concurrent branches mint
file names as well as decision numbers.

What they actually own is different, and both are needed:

- **#81 polices the gate going forward.** `contracts/acceptance-policy.json` names
  seven admissible reasons a transition may wait on an owner seat, and its `audit`
  fails the build when work parks on Bdo without one. It also carries the
  acceptance packet schema that `decisions/0023` requires and nothing had built.
- **This record polices the records already written.** #81 reads an owner-queue
  register and the packets under `acceptance/`; nothing in it parses a decision
  record's status line, which is where the twenty-two phrasings and the nine
  lagging records live.

Neither subsumes the other. If both land, `sov_docket.py check` answers "whose is
each of the forty records" and `sov_accept.py audit` answers "is this new block
legitimate". If only one lands, the nine records whose status line contradicts
`STATUS.yaml` stay contradictory under #81 alone.

## What the witness changed

`06be56c` was witnessed by a session that did not write it. It attested the
crosswalk, the routing mechanics, and that nothing here can express a
settlement. It dissented on the counts, with two confirmed defects and one
structural finding, and all three are in this record because they improved it:

- **`0036` was routed on one of its three questions.** Confirmed by reading the
  record's own `What still waits on Bdo` section. Now two entries, `0036-A` at
  Control and `0036-B` reaching Bdo.
- **`0038` was routed wrongly, on a ground its author had not examined.** The v1
  reason argued that a rebuildable projection touches nothing owner-held.
  `contracts/capability-offices.json` is not the projection — it is an authored
  input carrying 79 assignments, every one setting `required_authority`.
  Assigning an authority type to every operation in the node is typed authority,
  which `AGENTS.md` reserves. Now `reaches_owner: true`, and the original
  challenge stays on the entry as `contested_by`.
- **The unit was wrong**, which is section 2 above.

`0040` was flagged rather than dissented — it declares per-operation refusal
codes and `CLASSIFICATION.md` owns vocabulary — and the doubt is recorded on the
entry without moving it.

That the sharpest correction to this record came from outside it is the argument
for the practice, not an embarrassment to it.

## What could defeat this

- **The routing is wrong.** Every entry is one reader's judgement about someone
  else's question. If Bdo says `0038` is product intent after all, the entry is
  wrong and the file changes. That is the intended failure mode.
- **The crosswalk hides drift.** Mapping six phrasings to one standing loses
  whatever distinction the author of `PROPOSED · OWNER FREEZE PENDING` intended
  against `PROPOSED · OWNER RATIFICATION PENDING`. `0009` is exactly that case:
  accepted is recorded, frozen is not, and the crosswalk flattens them. The
  routing entry carries the distinction the crosswalk drops, which works only as
  long as someone writes it down.
- **A closed standing set is a new vocabulary**, and `AGENTS.md` says not to
  create a competing authority. This one is a projection *over* the status lines
  rather than a replacement for them; if it ever becomes the thing records are
  written against, `CLASSIFICATION.md` should own it, not a contract file.
- **Three is not obviously right.** The count depends on reading `0023`'s five
  owner-held categories narrowly. A wider reading puts more back on Bdo.

## What this does not do

It ratifies nothing, accepts nothing, and closes no record. It does not update a
single status line — every one of the nine lagging records still says what it
said, because editing a record to say Bdo accepted it is exactly the move
`AGENTS.md` forbids without him. It produces the queue and names what each item
needs. Acting on it is a separate operation for whoever holds the tier.

## What still waits on Bdo

- Whether routing questions to tiers is a thing this repository should do at all,
  given #81 is already building an adjacent mechanism and two counts of what
  waits on him is worse than one.
- Whether the routing judgements in `contracts/acceptance-routing.json` are
  right. Each is one reader's claim about someone else's question, and `0040`
  carries a recorded doubt nobody has settled.
- Whether requiring `What still waits on Bdo` from `0043` is worth the line it
  costs every future record.
