# 0072 · The journal binds its own identity

Status: `PROPOSED · BUILT AND SELF-TESTED · RATIFICATION PENDING`

## Decision

`soveraeign-record-chain/v3` becomes the profile new journal entries are written
under. It binds three columns `v2` recorded but never protected: `entry_id`,
`source_address`, and `recorded_at`. `v1` and `v2` are unchanged and still verify
the entries already written under them, because a profile edited in place
silently invalidates its own history.

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
chain endorsing both. All 402 entries in this repository's live journal were
already canonical, so the requirement cost no history.

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

## Standing

`PROPOSED`. Built and self-tested: 46 Record Service tests pass.

An independent witness examined this change at commit `514d12e` and **refused to
propose `BUILT -> WITNESSED`**. It confirmed C1, C2, C4, C5 and C6 — the defect
was real, v3 fixes it, history is not rewritten, a round trip is not tampering,
and the two independent verifiers agree — and refuted the coverage declaration in
both directions, on `payload_json` and on `seq`. Everything above about canonical
bytes, about `seq`'s two answers, and about the sweep's fixtures is that refusal
repaired inside the concern. The change has not been re-witnessed since.

One thing the earlier draft claimed too much: it offered `scripts/witness_record.py`'s
21/21 as the observation proposing `WITNESSED`. That walk runs `verify_chain` only
over honest data and contains no tamper case, so it establishes that three
implementations agree about a good chain — not that any of them detects a bad
one. It is real independent observation, of a narrower claim than it was cited
for.

Self-tests establish `BUILT`. Nothing here is witnessed. Only Bdo ratifies.
