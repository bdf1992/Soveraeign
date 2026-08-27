# Asset Service Ground

Status: `PROPOSED · BUILT AT MOST · NOT WITNESSED · NOT RATIFIED`

A short, service-scoped list of claims the Asset Service commits to always
being true for its callers, under `decisions/0093-service-srd-spec-ground.md`.
Not forced to sixteen, and not a fourth ladder competing with root `GROUND.md`
— each claim below specializes exactly one root `GROUND-<nnn>` claim to this
service's own owned records and transitions. Accepting this list is not a
claim that the participant currently keeps every one of them without
exception; several carry a named, evidenced residual below their defeat
condition, in the same spirit `GROUND.md` itself states about `GROUND-010`.

### AG-1 — Captured bytes stay exactly what was captured

> What `ingest-asset` stores under a payload digest is what a later
> `read-version` or `read-shared-custody` returns, or the read refuses rather
> than returning something else.

Specializes `GROUND-005` (a consequential act binds to exact state) and
`GROUND-001` (custody stays with the enterprise).

What would defeat it: a stored payload rereads with a different digest and
the read still succeeds (`custody.py`'s `DigestMismatch` refusal exists
precisely to keep this from happening; `conformance/BASELINE.md` records
`PROD-I-2` as the one requirement this participant currently passes).

### AG-2 — A recording is never called that unless it can be reconstructed

> A `Recording` always resolves its exact source, reader identity and
> version, configuration digest, fidelity, and recoverable omissions, or the
> derivative stays an ordinary Asset Version and is never given the name
> `Recording`.

Specializes `GROUND-005`.

What would defeat it: a recording exists whose source, reader, or
configuration cannot be resolved and re-verified (`recording.py`'s
`ReconstructionError` family; `conformance/PROD-I-2-BUILD.md` names reader
substitution, source corruption, and omission erasure as the attacks an
independent Red engagement must still attempt against this claim).

### AG-3 — Nothing here is authoritative merely by being claimed

> A description recorded by a human or a model actor is `CLAIMED_UNRATIFIED`
> until a live, typed, human-held grant ratifies it, and the conformance read
> never reports the claim as the fact.

Specializes `GROUND-003` (authority is granted, never acquired) and
`GROUND-011` (standing does not collapse).

What would defeat it: `read-library-conformance` reports `CONFORMING` for a
field nobody ratified (`librarian.py` keeps `CONFORMING`, `CLAIMED_UNRATIFIED`,
and `MISSING_FIELD` as three distinct verdicts for exactly this reason), or
`ratify-proposal` accepts a `VERIFICATION`-typed grant for a judgement-typed
claim.

### AG-4 — Every attempted operation leaves a receipt, refusal included

> Whatever a caller attempts against this service's seventeen declared
> operations, the attempt resolves to a durable, addressable receipt row —
> not only on success.

Specializes `GROUND-007` (every crossing leaves a record) and `GROUND-008`
(refusal is an outcome).

What would defeat it: an attempted operation returns without a receipt that
can later be looked up (`routes.py`'s `_receipt` helper raises rather than
returning silently if the receipt is not durable). Named residual: the
receipt this claim guarantees does not yet carry every field `CONTRACT.md`
C6-C8 requires — exact input state, authority grants, preconditions, and
effect class are still missing from some receipts (`KNOWN-GAPS.md`, "Receipt
completeness"). The receipt exists; its completeness is a separate, tracked
gap, not a defeat of this narrower claim.

### AG-5 — Retraction never deletes the record it counters

> `retract-record` and `remove-member` add a counter-record. They never
> remove the original row, and they never claim that a consumed resource or
> an external effect came back.

Specializes `GROUND-009` (correction never erases occurrence).

What would defeat it: a retraction deletes or overwrites the original row.
Named residual: `conformance/BASELINE.md` records that today's counter
receipt does not yet link back to the prior receipt it counters — the
original is preserved (the claim holds), but the two are not yet joined by an
addressable reference (`PROD-I-4 FAIL`, "the original and counter-record
survive, but the counter receipt does not link the prior receipt").

### AG-6 — Search and graph results here are never a second authoritative store

> The SQLite FTS and edge tables `rebuild-projection` produces are dropped and
> rebuilt from ratified records on every rebuild. A row written straight into
> one of them without a receipt behind it does not survive the next rebuild
> and never conditions another operation's authoritative state.

Specializes `GROUND-005` and `SPEC.md`'s Projection rule.

What would defeat it: an edit to `search_projection` or the edge table
persists across a rebuild, or a graph-originated edit changes effective state
without first returning through the transition contract as a proposal
(`projections.py`; `CHARTER.md`, Authoritative versus derived stores). Named
scope, not a defeat: these two tables are a `LIKE`-substring compatibility
path, not ranked or multi-hop retrieval — that quality bar belongs to the
chartered Asset Projection Service (`KNOWN-GAPS.md`, "Search and graph
projections"; `OPEN-SEAMS.md` S14).

### AG-7 — A grant here expires; it is never a permanent credential

> Every authority grant this service checks carries an expiry, and a store
> written before that rule existed migrates as already expired rather than
> read as still live.

Specializes `GROUND-003`.

What would defeat it: an authorized actor keeps acting under a grant that has
passed `valid_until`, been revoked, or lost its session
(`authority.py`: "Before this module a grant row had `created_at` and no
expiry... A store written under that schema migrates with `expires_at = 0`,
so those grants read as expired rather than silently outliving the rule.").
Named residual: budget and revocation enforcement are not yet complete
alongside type, scope, and expiry (`KNOWN-GAPS.md`, "Authority envelope").
