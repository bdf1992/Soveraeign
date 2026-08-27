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

- **`seq` stays uncovered, and says so.** It is a local autoincrement that means
  nothing after a restore into another database, and replay order is already
  protected by the `prev_digest` link rather than by the column's value. Binding
  it would make a faithful restore verify as tampered.
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

## What would defeat this

- A column in `COVERAGE` that the tamper test cannot actually break, or one
  outside it that breaks anyway. Either fails the suite by construction.
- A faithful export/restore cycle that verifies as tampered. `custody.py` carries
  `entry_id`, `source_address` and `recorded_at` through the export, and
  `verify_export` recomputes with them, so a round trip preserves the digest — if
  it did not, binding the moment would be wrong and this record should be
  reversed.
- A demonstration that binding `recorded_at` blocks a legitimate correction. An
  append-preserving journal corrects by counter-record and never by editing a
  row, so no such correction should exist; one would defeat this.

## Standing

`PROPOSED`. The change is built, self-tested, and independently observed by
`scripts/witness_record.py`, which recomputes the chain from the charter rather
than from the service and held 21/21. Self-tests establish `BUILT`; the
independent walk proposes `WITNESSED`. Only Bdo ratifies.
