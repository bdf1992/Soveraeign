# Record Service Charter

Status: `BUILT_SELF_TESTED_NOT_WITNESSED`

## Role in Soveraeign

`ENGINEERING.md` names two Systems of Record. The design one is the governing
repository set: documents that say what the system must be. The operational one
is this service: the append-preserving journal of what actually happened and
under what authority.

Keeping them apart is the point. A governing document is not event storage, and
an event is not a governing claim. This service refuses to journal a source
whose name is one of the governing documents, so the confusion fails loudly
rather than accumulating.

## What append-preserving means here

It is enforced, not promised.

- No method updates or deletes a journal row. The only `DELETE` in the service
  is against projections.
- Retraction appends a counter-record and leaves the original exactly where it
  was, readable, with its payload intact.
- Every entry carries the digest of the entry before it. A rewritten history
  stops verifying rather than quietly replacing the real one, and `reconstruct`
  raises `BrokenChain` at the first link that does not hold.
- A transaction that never commits leaves nothing behind, so an interrupted
  write cannot become an effective record.

## Authoritative versus derived

The journal is authoritative. `subject_projection` is derived: dropped and
rebuilt from the journal alone, and identical each time it is rebuilt.

A projection can never be promoted to the record. `append_from_projection`
exists only to refuse, because the failure it prevents - a projection becoming
authoritative because it was convenient - is a declared defeating case on issue
#7 rather than a hypothetical.

## What it does not do

It does not decide legality. `contracts/kernel-transitions.json` and
`scripts/sovkernel/` own whether a transition may happen; this service records
that it was attempted and how it ended. A receipt here is evidence of an
attempt, never a grant of authority.

It does not carry identity. Every actor is a string until Identity (#11) exists,
which is the same limitation the rest of the system currently has.

It does not durably guarantee media beyond detectable corruption. `SPEC.md`
places that outside the logical specification.

## Reaching it

`src/soveraeign_record_service/cli.py` is the declared invocation surface. Every
command reads JSON arguments and prints one JSON object, refusals included, and
`operations` answers what may be done out of `contracts/service.json` rather than
out of the CLI, so the declared surface and the reachable surface cannot drift
apart quietly.

Before it existed, everything that needed the journal imported `core.py`. That
put every reader inside the participant, and it meant the witness procedure could
only be performed by the code being witnessed.

## The digest chain

Every entry's digest is `sha256` over `prev_digest`, `kind`, `subject`, `actor`,
and the entry payload as canonical JSON, joined by `|`. The first entry chains
from a genesis digest of sixty-four zeroes. It is stated here because an outside
observer has to be able to recompute the chain without reading `core.py`;
`scripts/witness_record.py` does exactly that.

## Proving operation

Two paths, and the difference between them is the whole point.

`tests/test_journal.py` is the participant's own: eight tests covering the five
acceptance criteria and all five declared defeating cases, driving the Python API
directly. It establishes `BUILT` and nothing further.

`scripts/witness_record.py` performs the witness procedure declared on issue #7 -
commit, interrupt, restart, reconstruct, retract, drop every projection, rebuild
them, compare the resulting record addresses and terminal receipts - without
importing this service. It reaches the service only as a subprocess through the
CLI, recomputes every digest from the chain rule stated above, and stages the
interrupt against the SQLite file from outside. Twenty-one observations hold.
`scripts/tests/test_witness_record.py` proves the walk can fail: a rewritten
payload, actor, or removed entry all stop verifying.

An independent observation proposes at most `BUILT -> WITNESSED`. It does not
settle it, and Bdo's recorded decision is what makes anything `RATIFIED`.
