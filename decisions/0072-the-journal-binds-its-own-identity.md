# 0072 · The journal binds its own identity

Status: `PROPOSED · BUILT AND SELF-TESTED · RATIFICATION PENDING`

## Decision

`soveraeign-record-chain/v3` becomes the profile a new journal is written under.
It binds three columns `v2` recorded but never protected: `entry_id`,
`source_address`, and `recorded_at`. `v1` and `v2` are unchanged and still verify
the entries already written under them, because a profile edited in place
silently invalidates its own history.

**A store keeps writing the profile it already writes**, which is the strongest
profile any of its rows carries — not whatever the library calls current, and not
the profile on its newest row. An existing journal therefore does not change
profile because the code that opened it was upgraded, and its answer does not
depend on which of several checkouts sharing it wrote last. Moving one forward is
`RecordService.adopt_profile`, reachable as `adopt-profile` on the CLI, which
appends the first entry under the new profile and names in that entry which
profile it supersedes and that a reader implementing only the old one stops
verifying there. The boundary is inside the journal instead of being discovered by
whoever opens the store next.

Alongside it, `digest.COVERAGE` states per profile which journal columns that
profile's verification detects a change to, and `digest.uncovered` returns the
complement. The declaration is not documentation: `services/record/tests/
test_digest_coverage.py` tampers with every column of a real journal under every
profile and fails if the declaration and the behaviour disagree in either
direction.

`RecordService.reconstruct` additionally requires each row's stored
`payload_json` bytes to be its profile's canonical encoding of the value the
digest binds. Every profile binds the *parsed value*, so without this a
byte-different, value-identical payload passed unnoticed — including duplicate-key
injection, where a JSON parser reads the last key, anything taking the first key
reads another number, and one committed row is therefore read two ways with the
chain endorsing both. All 412 entries in this repository's live journal are
already canonical — verified with the byte rule applied over the raw rows — so
the requirement costs no history.

## What defeated the previous arrangement

Under `v2` the digest material was `[profile, previous, kind, subject, actor,
payload]`. Six inputs, five journal columns. The remaining columns were written
to the row and never hashed, so they could be rewritten in place and every
verification in this repository still passed.

The demonstration that settled it, reproducible against `v2`:

    small = append(RECEIPT, "payment_to_alice", "alice", {"amount": 5})
    large = append(RECEIPT, "payment_to_bob",   "bob",   {"amount": 5000})
    # exchange the two entry_id values, touch nothing else
    reconstruct()          -> 2 entries, no complaint
    entry(small.entry_id)  -> payment_to_bob, amount 5000

`entry_id` is how every receipt, observation and counter-record in the system
cites the journal. An identifier that is not bound to its content makes every one
of those citations forgeable, and the forgery leaves the chain verifying clean.
`recorded_at` was the same defect with a smaller blast radius: a timestamp could
be moved to any value, and the console surface rendered it inside a region
labelled authoritative.

The reason it survived this long is worth recording, because it is not specific
to the record service. The service had exactly one tamper test. It changed
`payload_json` and asserted the chain broke. One column was proven; the other ten
were assumed from it. `AGENTS.md` already requires a case proving the refusal
fires — that rule had been applied once per mechanism rather than once per claim.

## Defaults taken

- **`seq` stays uncovered, and its two answers are stated separately.** It is a
  local autoincrement meaning nothing after a restore into another database, so
  binding it would make a faithful restore verify as tampered. Its *value* is
  genuinely unprotected: renumbering that preserves order is undetected and hides
  nothing. Its *order* is protected, by the `prev_digest` link rather than by any
  digest — every reordering breaks the chain. An independent witness proved the
  first draft of this record wrong to imply the second followed from the first,
  and `TheOrderOfEntries` now grades both.
- **`recorded_at` is bound as its exact float**, not a rounded or formatted form,
  so a change below display resolution is still detected.
- **No migration, and no rewrite of existing entries.** Each row records its own
  profile and is verified under it. A journal written before this change keeps
  exactly the coverage it always had, which is the honest outcome; claiming
  otherwise would require rewriting history to assert it.
- **An existing store stays on its profile until somebody moves it; an empty one
  starts at the strongest.** The alternative — every store upgrading on its next
  write — is what broke the live console journal, and it also makes the moment a
  reader stops working depend on when a library happened to be updated rather than
  on a decision anybody took. The cost is real and is accepted: a store that
  already exists keeps `v2`'s weaker coverage until it is deliberately moved, so
  the identifier hole this record closes stays open in it. Adoption being one call
  with a recorded entry is what keeps that cost payable.
- **A store's profile is the strongest any row carries, not the newest row's.**
  Rows arrive in whatever order the checkouts sharing a store happen to write
  them, so the newest row names the last writer rather than the store. The
  maximum can only move forward, which matches what is actually true: a store
  that has ever written `v3` can never be read by a `v1`-only reader again.
- **An unimplemented profile found in a store refuses rather than sorting to the
  bottom.** A row this service cannot verify is not a row it may quietly write
  past, so `writing_profile` raises `BrokenChain` naming the profile.
- **`adopt-profile` is reachable from the CLI, and answers without moving
  anything when `--to` is omitted.** An independent witness pointed out that a
  store was otherwise stuck for any operator not writing Python — including the
  one store this record says is stuck. Asking what a store writes must not be an
  act that changes it.
- **Adoption refuses to stand still or go backwards.** Both would append an entry
  claiming a transition that is not happening, and a journal that records a move
  which did not occur is worse than one that never raises the question.
- **The two independent verifiers were updated separately.**
  `scripts/witness_record.py` and `scripts/gateway_observe.py` each reimplement
  the chain rule deliberately so a witness does not borrow the participant's own
  arithmetic. Each got its own `v3` branch rather than being collapsed into an
  import, and each returns an explicit unknown-profile result rather than falling
  back to a weaker digest.

## Consequences

- Entries written before this change remain `v2` and remain exactly as protected
  as they were. `uncovered("soveraeign-record-chain/v2")` names what that means
  for any surface displaying them.
- A caller verifying a `v3` entry without supplying `entry_id` and `recorded_at`
  raises rather than silently grading it under `v2`.
- Adding a column to the journal table now fails
  `test_journal_columns_match_the_table_the_service_creates` until its coverage
  is ruled on, which is the point.
- `ENGINEERING.md` names `v3` as the profile in use;
  `scripts/sov_precedent.py` pins its material so the byte format cannot drift
  unrecorded.

## What v3 still does not detect

Stated because the framing above — that an unbound identifier made every citation
forgeable — invites reading v3 as making them unforgeable. It does not.

An outsider with write access to the database file can append a well-formed entry
to the end of the chain, or rewrite the whole chain from genesis, and every
verification in this repository reports clean. The chain proves internal
consistency, not that the head is the head anyone else last saw. Only a head held
outside the store catches either, which is what `custody.verify_export` takes
`expected_head` for. `services/record/CHARTER.md` now says this beside the
profiles rather than only here.

## What would defeat this

- A column in `COVERAGE` that the tamper test cannot actually break, or one
  outside it that breaks anyway. An earlier draft of this record claimed the
  suite caught that "by construction"; it caught it by fixture, and an
  independent witness showed the fixtures were too weak to catch either of the
  two cases that were actually wrong — one tamper value per column, applied only
  to the last row, where a value that would reorder the journal cannot. The sweep
  now runs several replacements per column at the first row and the last, refuses
  a replacement equal to what is already stored (one case was grading a no-op as
  evidence), and fails if any journal column is graded by no case at all.
- A faithful export/restore cycle that verifies as tampered. `custody.py` carries
  `entry_id`, `source_address` and `recorded_at` through the export, and
  `verify_export` recomputes with them, so a round trip preserves the digest — if
  it did not, binding the moment would be wrong and this record should be
  reversed.
- A demonstration that binding `recorded_at` blocks a legitimate correction. An
  append-preserving journal corrects by counter-record and never by editing a
  row, so no such correction should exist; one would defeat this.
- An append that changes the profile a store writes without anyone adopting it.
  `test_appending_to_a_v1_store_writes_v1_and_leaves_old_readers_working` runs a
  pre-profile reader over the journal after the append and requires it to verify
  every entry; that reader stopping is the defect returning.

## What adopting v3 silently broke, and what fixed it

The first arrangement wrote `CURRENT_PROFILE` on every append. Nothing consulted
the store, so opening an existing journal with this branch's service upgraded it
from the next row on.

It did that to the live operator journal, and the exact shape matters because two
independent readings used it to defeat the first repair. `.local/console` holds
412 entries, and its profiles run:

    v1   seq 1   - 404    404 rows
    v3   seq 405 - 408      4 rows
    v1   seq 409 - 410      2 rows
    v3   seq 411 - 412      2 rows

Eleven sessions share that working tree, so the v3 rows did not land *on top of*
the v1 rows: an older checkout kept writing v1 in between. The journal is not
damaged — a `v3`-aware reader verifies all 412 — but every session running an
older checkout gets `BrokenChain` at `seq` 405, and the operator continuity
surface has been down for all of them since.

    old reader on the live store   BrokenChain entry_80767935e18c488fb45502df9d5c385e
    v3-aware reader, same bytes    412 entries verified

That is the same shape as the rule this record already rests on. A profile edited
in place invalidates its own history; a profile adopted in place invalidates its
own readers. The first was stated and enforced, the second was neither.

`append` now writes `writing_profile()`, `adopt_profile` is the deliberate move,
and `services/record/src/soveraeign_record_service/profiles.py` carries the
reasoning beside the code. `test_appending_to_a_v1_store_writes_v1_and_leaves_old_
readers_working` is the failing case stated as a fixture: it reconstructs a
pre-profile reader and asserts it still verifies the whole chain after a new
append. `test_an_old_reader_stops_exactly_at_the_adopted_entry` measures the
consequence the adoption entry claims, rather than asserting it in prose.

**The first repair read only the newest row, and two witnesses defeated it with
this store.** Under that rule `.local/console` answers `v3`, because `seq` 412 is
v3 — so the store the record argues from was one row-ordering away from proving
its own fix wrong, and every fixture defending it built a homogeneous journal
where the one row read is representative by construction. `writing_profile()` now
takes the strongest profile any row carries. That is also the true property:
once a single v3 row exists no v1-only reader can verify through it, so writing
v1 afterwards restores nobody, and what a store can still be read by only ever
narrows. `test_the_profile_is_the_strongest_any_row_carries_not_the_newest`
builds the live journal's actual v1/v3/v1 shape, with the trailing v1 rows written
by straight SQL the way a pre-profile service wrote them.

One thing followed. Refusing `NaN` and `Infinity` at write time had been a side
effect of always encoding with `canonical`; a store writing `v1` would have
regained the divergence, because `legacy_canonical` permits both and has to keep
permitting them for the rows already carrying one. `digest.refuse_non_finite` now
makes the refusal explicit at admission, where it belongs, and
`test_a_v1_store_still_refuses_a_non_finite_payload` pins it.

The six rows already written are left exactly where they are. Removing them to
please an older reader would be the one thing an append-preserving journal must
never do, and `.local/` is runtime state rather than a governed record. What
remains for Bdo is under **What still waits on Bdo** below.

## What the canonical requirement broke, and what fixed it

Requiring canonical bytes regressed `custody.restore`, and a re-witness caught it
at `66b260e`. `export_document` always emits schema v2, so `restore` chose the v2
encoder for every row it wrote — including v1 rows. v1 escapes non-ASCII and v2
does not, so a faithful restore of a v1 row holding `{"text": "café"}` wrote bytes
that verification, which picks its encoder by the row's profile, then refused. It
wrote them committed, leaving the target store unverifiable, un-restorable and
un-exportable. The repository's own `test_digest_profiles` fixture is that shape.

`restore` now picks the encoder by the row's own profile, exactly as verification
does. `test_a_v1_row_with_a_non_ascii_payload_still_restores` is the fixture.

Two things followed from the same seam:

- The sweep's payload was ASCII, so the two encoders produced identical bytes and
  the v1 arm was valid only by coincidence. It is now non-ASCII, the fixture
  encodes each row by its own profile, and one tamper case is "the other
  profile's encoding of the same value" — which is what the check could not
  previously express.
- `services/record/CHARTER.md` required "the profile's canonical encoding"
  without saying what each encoding is. It now states both, and states that a
  row's encoder comes from its own profile and never from the schema of the
  document carrying it.

## What still waits on Bdo

- **The live console journal.** `.local/console` cannot be read by any checkout
  older than this branch, and that is not repairable from inside the store: the
  six `v3` rows are real entries and removing them is the one thing forbidden
  here. It becomes readable again when this change lands and the shared checkout
  moves; until then eleven sessions have no operator continuity surface. The
  alternatives are landing an unwitnessed service into the shared tree or
  rebuilding the store from empty and losing 412 entries of continuity, and
  neither is a call this seat makes.
- **Whether `custody.restore` should refuse a non-finite payload on a new row.**
  An independent witness built an export carrying a `v1` `NaN` row and restored it
  into a brand-new empty store; it verifies, and `write_export` then emits a file
  no strict JSON reader will parse. `refuse_non_finite` closes the `append` path
  and deliberately does not close the restore path, because a restore reproduces
  what was exported and refusing there would make some existing exports
  irrecoverable. Whether that trade is right is a judgement, not an engineering
  default. The charter currently implies the divergence is confined to history,
  and it is not.

## Standing

`PROPOSED`. Built and self-tested: 58 Record Service tests pass, the independent
walk holds 24/24, and 7 gateway observer tests pass.

`python scripts/verify.py` fails no named check in any run. Its exit code carries
the total wall clock on this branch, which straddles the 15-second ceiling
depending on how many sessions are running. That is contention rather than this
change, and it is measured rather than asserted — an earlier draft asserted it,
and an independent witness was right that a claim about a machine needs a
baseline. Runs interleaved back to back against the merge-base `5951bc4`:

    base 14.490 -> branch 13.831        base 14.082 -> branch 14.046
    base 13.922 -> branch 14.509        base 13.876 -> branch 14.407

Within ±0.7s in both directions, all eight exit 0. Under load both sit at 16-21s
and both fail. The record service's own tests do grow, from about 0.95s to about
1.7s, which is under a tenth of the run.

An independent witness examined this change at commit `514d12e` and **refused to
propose `BUILT -> WITNESSED`**. It confirmed C1, C2, C4, C5 and C6 — the defect
was real, v3 fixes it, history is not rewritten, a round trip is not tampering,
and the two independent verifiers agree — and refuted the coverage declaration in
both directions, on `payload_json` and on `seq`. Everything above about canonical
bytes, about `seq`'s two answers, and about the sweep's fixtures is that refusal
repaired inside the concern. The change has not been re-witnessed since.

One thing the earlier draft claimed too much: it offered `scripts/witness_record.py`'s
21/21 as the observation proposing `WITNESSED`. That walk ran `verify_chain` only
over honest data and contained no tamper case, so it established that three
implementations agree about a good chain — not that any of them detects a bad
one. A check never shown failing has not been shown to work.

The repair to that was itself too weak, and a third witness proved it. The stage
named "payload bytes that parse the same" substituted a fixed
`{"x": 1, "forged": 0}` into a row whose payload was something else, so the values
differed and the digest caught it — the byte rule never fired, and the walk still
reported 24/24 with `canonical_bytes_disagree` forced to return `False`. A check
cited as evidence for a rule it did not exercise, which is the same defect one
level down. The stage now re-encodes the target row's own payload with different
spacing, so the parsed value is identical and the whole weight sits on the bytes.
Forcing the byte rule off now yields 23/24 and exit 1; unmodified it is 24/24.

That is the fourth check in this concern found unable to fail — after one tamper
value per column, a note asserted against the constant that generated it, and a
fixture whose ASCII payload made two different encoders coincide. Each was found
by an independent reading and none by the build.

A fourth reading found three more of the same kind, by mutating the service and
watching all 54 tests stay green:

- `scripts/gateway_observe.py` gained the canonical byte rule and no case
  exercised it. Its four behavioural cases change a value or a profile, so the
  digest catches all of them and none reaches the byte comparison. Deleting the
  rule left the suite passing, while this record cited both verifiers' canonical
  rule as evidence. Two cases now write bytes that parse to the row's own value —
  a spaced re-encoding and a duplicate-key injection — and assert
  `JOURNAL_CHAIN_INVALID`.
- The v3 branch raising when `entry_id` and `recorded_at` are absent, stated in
  **Consequences** below, had no fixture. Returning the v2 digest instead broke
  nothing.
- `digest_for_row` turning an unimplemented profile into `BrokenChain` on the
  *read* path had none either; only the adopt path was covered.

`TheRefusalsNothingExercised` carries the last two. That is seven checks in one
concern that could not fail, all found by reading and none by building, which is
the finding this record should be read for as much as for the digest.

Both independent verifiers also gained the canonical rule. Without it they graded
a strictly weaker property than the service — the exact tamper this change exists
to catch passed both checks whose job is to catch it.

Self-tests establish `BUILT`. Nothing here is witnessed. Only Bdo ratifies.
