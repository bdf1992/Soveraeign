# Asset Service Specification

Status: `PROPOSED · BUILT AT MOST · NOT WITNESSED · NOT RATIFIED`

A service-scoped projection of `SPEC.md`'s shape onto the Asset Service, under
`decisions/0093-service-srd-spec-ground.md`. It cites
`contracts/kernel-transitions.json` and `services/asset/contracts/service.json`
rather than re-deriving their content, and it does not select a storage
mechanism `ENGINEERING.md` and this participant have not already chosen. Named
`SERVICE-SPEC.md`, not `SPEC.md` — the root document owns that name.

## Owned domain records

Exactly the `owns` list in `service.json`, no more and no less:

```text
asset, asset-version, payload-custody, source, derivation-lineage,
asset-relationship, asset-use-record, collection-type, asset-collection,
collection-membership, library-conformance
```

`asset` is a governed enterprise identity with a version history; `asset
version` is one immutable state of it (`CLASSIFICATION.md`). An asset is not
its payload: distinct assets may reference the same bytes while keeping
distinct identity, use, permissions, and history (`identity.py`). Composition —
one asset assembled from several — is not a separate record kind; it is
derivation with more than one input (`identity.py`, `runs.py`).

`service.json` declares one reference (`references: ["shared-kernel-contracts"]`)
and no owned subject outside this list. Two subjects this service reads but
does not own or settle: `authority.grant`/`authority.revoke` (issuance is
implemented in `authority.py`, but whether that authority belongs here or on a
separate permits surface is named open in `service.json`'s
`undeclared_events`) and independent `operation.observe` (chartered to the
Observation Service, `decisions/0041`).

## Service-local states

Reuses `SPEC.md`'s standing ladder unchanged — `RECORDED → ADMITTED → RATIFIED
→ EFFECTIVE` — and its collapse rule: nothing here treats being written, being
confident, or being agreed with as entry into that ladder (`GROUND-011`).
`KNOWN-GAPS.md`'s "Admission standing" row records that the current
participant updates `RECORDED` directly to `RATIFIED`, so `ADMITTED` is not
yet a separately visible transition in this service today; the ladder is the
target, not yet the observed behavior.

One additional state set is local to this service and has no root `SPEC.md`
analog — the library conformance verdict (`librarian.py`), read fresh on every
call and never stored:

```text
CONFORMING | CLAIMED_UNRATIFIED | MISSING_FIELD | VOCABULARY_REFUSED | MEMBER_KIND_REFUSED
```

`CONFORMING` requires a ratified description carrying a value the type's
vocabulary admits. `CLAIMED_UNRATIFIED` is the deliberately named middle
state: someone recorded the field, nobody ratified it, and it must never be
counted as conformance (`librarian.py`; `AGENTS.md`, Evidence and standing).
`MEMBER_KIND_REFUSED` is refused earlier, at filing time, by
`organization.py`, and appears here only on a type re-read after members were
declared.

## Legal transitions

`SPEC.md`'s transition contract, restricted to the rows this service's
manifest declares, plus the exact preconditions, commit outcome, and refusal
set `service.json` carries per operation (not re-derived here):

| Operation | Kernel transition | Precondition summary | Commit | Refusals |
| --- | --- | --- | --- | --- |
| `ingest-asset` | `capture_source` | readable bytes, label, locator, live grant | `COMMITTED` | `DIGEST_MISMATCH`, `GRANT_NOT_COVERED`, `MISSING_PRECONDITION`, `PAYLOAD_ABSENT` |
| `propose-description` | `submit_proposal` | asset exists, declared actor and payload | `RECORDED` | `INCOMPLETE_PROPOSAL`, `GRANT_NOT_COVERED` |
| `ratify-proposal` | `ratify` | proposal recorded, live matching grant, human actor | `EFFECTIVE` | `AUTHORITY_REFUSED`, `GRANT_NOT_COVERED`, `STALE_STATE` |
| `read-version` | `read_source` | version exists, stored digest verifies | `DERIVED` | `PAYLOAD_ABSENT`, `DIGEST_MISMATCH`, `SOURCE_UNREACHABLE`, `SOURCE_CHANGED`, `VERSION_UNKNOWN` |
| `request-derivative` | `begin_run` | source version exists, declared plan, live grant | `COMMITTED` | `GRANT_NOT_COVERED`, `STALE_LEASE` |
| `retract-record` | `retract` | target exists, live retraction grant, declared reason | `COUNTERED` | `AUTHORITY_REFUSED`, `GRANT_NOT_COVERED` |
| `remove-member` | `retract` | membership exists, live retraction grant, declared reason | `COUNTERED` | `AUTHORITY_REFUSED`, `GRANT_NOT_COVERED` |

The remaining ten operations (`read-asset`, `read-shared-custody`,
`read-use-record`, `read-version-history`, `rebuild-projection`,
`declare-collection-type`, `declare-collection`, `add-member`,
`read-collection`, `read-library-conformance`) are reads, a rebuild, or
organizational creates that carry their own precondition and refusal sets in
`service.json` without naming a `kernel_transition`; they resolve to `DERIVED`,
`REBUILT`, or `COMMITTED` per that manifest.

No interface, adapter, worker, projection, or graph store may bypass these
transitions to change authoritative state (`SPEC.md`, Transition contract;
enforced here by `forbids: ["direct-projection-authority", ...]` in
`service.json`).

### Internal phases that are not separate operations

`service.json`'s `undeclared_events` names ten lifecycle phases this service's
implementation performs but does not expose as a callable operation, each with
a stated reason: `authority.check` (a gate inside every consequential
operation, not an operation itself), `authority.grant`/`authority.revoke`
(open ownership seam), `federation.cross` (the refusal path of an inactive
port), `lease.claim` (a phase of `request-derivative`), `operation.observe`
and `operation.report` (chartered elsewhere or settle nothing), `session.open`
and `session.close` (implemented but not manifest-declared, matching a gap
`bindings/mcp/manifest.json` also records), and `source.reread` (proves a
source has not moved, over a subject the manifest does not declare an
operation for).

## Refusal reason codes

Per-operation refusals are the `refusals` arrays in the table above and in
`service.json`. `local_refusals` aliases service-specific codes onto the
shared kernel vocabulary rather than minting parallel meaning:

```text
GRANT_NOT_COVERED     -> AUTHORITY_REFUSED
PAYLOAD_ABSENT        -> UNREADABLE
SOURCE_UNREACHABLE    -> UNREADABLE
TYPE_UNDECLARED       -> MISSING_PRECONDITION
MEMBER_KIND_REFUSED   -> POLICY_REFUSED
DUPLICATE_MEMBERSHIP  -> STALE_STATE
VERSION_UNKNOWN       -> MISSING_PRECONDITION
```

`GROUND-008` — refusal is an outcome, not a silence — applies at this local
alias layer exactly as it applies at the kernel layer: every refusal above
still resolves to a receipted, reasoned outcome.

## Persistence

- **Payload bytes**: a local content-addressed store; authoritative payload
  custody (`CHARTER.md`, Authoritative versus derived stores).
- **Assets, versions, operations, authority, receipts**: the SQLite ledger in
  `store.py`; canonical reference binding for this participant.
- **Search and relationship traversal**: `projections.py`'s two SQLite tables,
  dropped and rebuilt from ratified records on every rebuild — "a row written
  straight into one survives only until the next rebuild and carries no
  receipt behind it" (`projections.py`). Never authoritative
  (`SPEC.md`, Projection rule).
- **Library conformance**: never stored; recomputed on every
  `read-library-conformance` call (`librarian.py`).
- **External graph database**: an optional `GraphProjection` adapter port,
  never authoritative even when configured (`CHARTER.md`).

## Authority notes

Grants are typed, capability- and scope-bound, session-bound, and expiring
(`authority.py`). An issuer other than the recorded root may issue only what
one of its own live grants already covers — same capability, no wider scope,
no later expiry — so delegation attenuates and never widens. A grant with no
expiry is treated as expired on migration rather than read as a permanent
credential (`authority.py`). `KNOWN-GAPS.md`'s "Authority envelope" row
records that type, issuer authority, and scope are enforced today; budget and
revocation enforcement are not yet complete. Machine (`VERIFICATION`) and
human (`JUDGEMENT`) authority types are distinct at the manifest level
(`ratify-proposal` requires `human_actor`); the general rule that
`VERIFICATION` cannot ratify `JUDGEMENT` is `PRD.md` `PROD-I-5`'s defeating
case and is not yet demonstrated end to end for this participant
(`conformance/BASELINE.md`, `PROD-I-5 FAIL`).

## Conformance boundary

Every requirement in `SRD.md` needs a positive and a defeating fixture, the
same rule `SPEC.md`'s Conformance boundary states at root scope. Passing this
participant's own `tests/` establishes `BUILT`
(`python -m unittest discover -s tests`; `conformance/PROD-I-2-BUILD.md`
records 96 passing after the current-main reconciliation it covers); an
independent run is required for
`WITNESSED`; Bdo's recorded decision is required for `RATIFIED`. The frozen
scenario source is `conformance/scenarios.json` at root scope, graded against
this participant by `conformance/run.py` and this service's own
`scripts/conformance_observations.py` (`conformance/README.md`).
