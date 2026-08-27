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
places that outside the logical specification — correctly, for a *logical*
specification, which is why `decisions/0049` puts the concern in the technical
baseline instead and `custody.py` realizes it. The service still guarantees no
medium; it now gives an operator the means to stop depending on one.

## Export and restore

`custody.py` renders the whole journal as a portable document and replays one
into an empty store. Neither adds technology: every entry already carries the
digest of the one before it, so a copy either replays into the same chain or
visibly does not. An unverifiable journal is never exported — a copy of a broken
chain is a broken chain that now exists twice — and a restore refuses a store
that already holds entries, since interleaving two histories yields one chain
that verifies as neither.

What self-verification reaches, and what it cannot, is worth stating exactly.
An export detects an edited field, a reordered pair, and an entry cut from the
middle: each breaks a link. It cannot detect **truncation**. Drop the last
entries and the remainder is a perfectly valid shorter journal — every link
holds, and nothing inside the document knows how long it was meant to be.
Rewriting the declared head is as easy as dropping the entries.

So `verify_export` accepts a head digest held *outside* the document, and only
that catches a truncation. This is not a defect of the chain; it is what a chain
is. A record cannot certify its own completeness from the inside — the same
shape as `decisions/0048` ID-11, where the root cannot recover itself from
inside the node. The practical consequence is small and worth saying plainly:
write the head digest down next to the recovery secrets.

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

The first entry chains from a genesis digest of sixty-four zeroes. Every row
names the exact profile used to hash it:

- `soveraeign-record-chain/v1` is the legacy Python representation: compact,
  key-sorted JSON payload text joined with `prev_digest`, `kind`, `subject`, and
  `actor` by `|`. It is superseded because field values containing `|` make the
  tuple ambiguous.
- `soveraeign-record-chain/v2`: UTF-8 bytes of compact JSON for
  `[profile, prev_digest, kind, subject, actor, payload]`, with object keys
  sorted, non-finite numbers refused, and Unicode code points preserved. The
  profile string domain-separates the hash input. It is superseded because it
  binds none of the entry's own identity.
- `soveraeign-record-chain/v3` is the current representation: the same compact
  JSON with `entry_id`, `source_address` and `recorded_at` bound in, as
  `[profile, prev_digest, entry_id, kind, subject, actor, source_address,
  recorded_at, payload]`. Under v2 two entries could exchange their identifiers
  and the chain still verified, so every receipt citing one could be repointed at
  other content (`decisions/0072`).

The entry digest is lowercase SHA-256 hex over those exact bytes. Opening a
pre-profile database adds `digest_profile` and marks only the existing rows v1.
A version-1 export is read as v1, while a version-2 export carries every row's
profile. Verification never tries both algorithms, so compatibility cannot make a
row pass under a weaker profile's rule.

**Which profile a new row uses is the store's answer, not the library's.**
`append` writes the profile of the store's newest entry, so an empty store starts
at v3 and an existing one keeps its own however new the code opening it is. A
store moves forward only through `adopt_profile`, which appends the first entry
under the new profile and states in it what was superseded and that a reader
implementing only the old profile stops verifying there. Superseded therefore
means "not chosen for a new store", not "never written again": a v1 journal keeps
writing v1, with v1's weaker coverage, until somebody moves it.

The reason is symmetrical with the reason profiles are immutable. Editing a
profile in place invalidates its own history; adopting one in place invalidates
its own readers. Both are silent, and the second has already happened here — six
v3 rows appended to the live `.local/console` journal left every older checkout
unable to read past them, over a journal that was never damaged
(`decisions/0072`).

Every profile binds the payload's *parsed value*, not the bytes the column holds,
so verification separately requires those bytes to be the profile's canonical
encoding of that value. Without it, byte-different but value-identical JSON went
undetected — including duplicate-key injection, where one committed row is read
two ways and the chain endorses both.

The encodings differ, and an implementer reading only this page has to be able to
tell them apart, because writing a row under the wrong one produces bytes that
parse correctly and verify as tampered:

- `record-chain/v1` stores `json.dumps(payload, sort_keys=True,
  separators=(",", ":"))` — non-ASCII code points are **escaped**, and non-finite
  numbers are permitted by the *encoder*, which is a known divergence: `NaN` and
  `Infinity` are not valid JSON, every strict reader refuses them, and a v1 row
  carrying one verifies here. It is a divergence rather than a forgery, since
  changing a value still changes the digest.
- `record-chain/v2` and `record-chain/v3` store the same form with
  `ensure_ascii=False` and `allow_nan=False` — non-ASCII code points are
  **preserved** and the encoder itself refuses non-finite numbers.

`append` refuses a non-finite payload under **every** profile, v1 included. The
encoder cannot carry that refusal, because v1 rows already exist carrying such a
value and a profile that stopped accepting them would stop verifying its own
history; the refusal is therefore made at admission, in
`digest.refuse_non_finite`. `custody.restore` is the exception and is deliberate:
it reproduces what an export holds, so a v1 row carrying `NaN` can still enter a
new store — and `write_export` will then emit a file no strict JSON reader
parses. Whether restore should refuse that is an open judgement recorded in
`decisions/0072`, not a settled rule.

A row's encoder is chosen by that row's own `digest_profile`, never by the schema
of the document carrying it. Choosing by the export schema is what made a
faithful restore of a v1 row holding a non-ASCII payload write bytes its own
verification then refused.

What no profile detects: an outsider with write access to the database file can
append a well-formed entry, or rewrite the whole chain from genesis, and every
verification here reports clean. Only a head held outside the store catches that,
which is what `custody.verify_export` uses `expected_head` for.

The rule is stated here because an outside observer has to recompute the chain
without reading `core.py`; `scripts/witness_record.py` does exactly that.

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
