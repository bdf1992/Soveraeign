# Asset Service Requirements Document

Status: `PROPOSED · BUILT AT MOST · NOT WITNESSED · NOT RATIFIED`

A service-scoped projection of `PRD.md`'s shape onto the Asset Service, under
`decisions/0093-service-srd-spec-ground.md`. The named user here is the node
itself — the callers listed below — not a human directly. This document grants
no authority and settles no standing; it is `BUILT` because a drafting agent
self-reported it, and stays there until an independent witness reads it against
`services/asset/contracts/service.json` and the running participant.

## Product outcome

One local node's callers — human, model, and leased worker, reached in-process
today and through the Gateway for a first slice — capture, remember, describe,
retract, and organize enterprise assets through one governed transition
contract, with no caller acquiring authority merely by calling it
(`CHARTER.md`; `GROUND-002`, `GROUND-003`).

## Callers

Evidenced callers of `services/asset/contracts/service.json`'s eponymous
operations, not an aspirational list:

- **Human operator**, through the CLI (`services/asset/README.md`: `python -m
  soveraeign_asset_service.cli ... conformance --markdown`; `sov-librarian`
  skill's `declare-type`, `declare-collection`, `add-member`,
  `remove-member`, `conformance` subcommands).
- **Model operator**, as the `MODEL` half of `actor_kind` on a proposal
  (`SPEC.md` `Proposal`; `CHARTER.md`: "allow a model adapter to propose
  metadata and relationships... ratify only through typed authority").
- **Leased worker**, claiming a fenced lease on `request-derivative`
  (`core.py`: "Lease a run to one worker and return its fencing token";
  `runs.py`).
- **Gateway Service**, in-process today, for exactly two of the seventeen
  declared operations (`services/gateway/CHARTER.md`: the built walking
  skeleton is `IN_PROCESS -> sov://asset/ingest-asset -> Asset Service ->
  terminal receipt`; `routes.py` `AssetRoutes.OPERATIONS = ("ingest-asset",
  "read-version")`).
- **Proofing Service**, which "references exact Asset Service version
  identifiers and does not create a second authoritative asset"
  (`CLASSIFICATION.md`, Initial service map).
- **Asset Projection Service**, which "reads the Asset Service through a
  declared crossing; everything it holds is a rebuildable projection"
  (`CLASSIFICATION.md`, Initial service map).
- **GitHub source adapter**, an external-source-provenance port declared in
  `service.json` (`"ports": ["github-source", ...]`) and named in `CHARTER.md`
  as one of the adapter ports the Asset Service holds.

Not yet an evidenced caller: a second, non-Python-API/CLI human or model
binding (`KNOWN-GAPS.md`, "Two bindings" row). See Non-goals.

## Requirements

Lifecycle: `OPEN → BUILT → WITNESSED → RATIFIED`, identical in meaning to
`PRD.md`'s ladder and distinct from the operational record standing in
`SPEC.md`. `BUILT` below means an implementation exists and its own unit
tests pass; it is not independent evidence.

### SVC-ASSET-1 · Capture preserves exact bytes

Standing: `BUILT`. Serves `PROD-I-2`.

`ingest-asset` preserves payload bytes under a content address and digest
before any other transition may reference them (`service.json`
`ingest-asset`: `kernel_transition: capture_source`, preconditions
`payload_bytes_readable`, `declared_label`, `declared_locator`, `live_grant`).

Defeating case: an ingested asset's stored bytes reread differently by digest,
or ingestion is admitted without a live grant, declared label, or locator.

### SVC-ASSET-2 · Reading never mutates and never lies about drift

Standing: `BUILT`. Serves `PROD-I-2`.

`read-version` and `read-shared-custody` verify the stored digest before
returning bytes and refuse `DIGEST_MISMATCH`, `SOURCE_UNREACHABLE`, or
`SOURCE_CHANGED` rather than returning stale or corrupted content
(`custody.py`; `service.json` `read-version` refusals). This requirement is
the one the participant oracle currently passes at the requirement level:
`conformance/BASELINE.md` records `PROD-I-2 · Remember: PASS`.

Defeating case: a source rereads differently and the operation still returns
success, or a reading silently mutates the source it read.

### SVC-ASSET-3 · A derivative recording resolves its exact materials

Standing: `BUILT`. Serves `PROD-I-2`.

`request-derivative` (`kernel_transition: begin_run`) only ever produces a
`Recording` for a request carrying a complete `ReaderDeclaration`; the
recording resolves its immediate source version and digest, output address
and digest, reader identity, configuration digest, fidelity, and omissions,
and both reporting and reconstruction re-verify those materials plus output
bytes (`conformance/PROD-I-2-BUILD.md`; `recording.py`; `reconstruction.py`).
Compatibility output created without a reader remains an Asset Version and
produces no `Recording` rather than inventing provenance
(`services/asset/README.md`).

Defeating case: a recording exists whose source, reader, or configuration
cannot be reconstructed; an incomplete reader is admitted instead of refused;
or output-only success conceals later source corruption
(`conformance/PROD-I-2-BUILD.md`, Residuals).

### SVC-ASSET-4 · A proposal's authority claim is recorded, never honored

Standing: `BUILT`, incompletely. Serves `PROD-I-1`.

`propose-description` records an attributed proposal at `RECORDED` standing
before any ratification (`service.json`: `kernel_transition:
submit_proposal`, `commit: RECORDED`). The participant does not yet meet the
full `PROD-I-1` defeating case: `conformance/BASELINE.md` records `PROD-I-1 ·
Propose: FAIL` — "proposal lacks content address, source addresses, and cost
record."

`PROD-I-1` was rewritten on 2026-08-28 and this clause has not caught up. Two
of its three defeating cases are unserved here: the participant delivers a
proposal to no operator surface, and it records no authority claim at all, so
the distinction between asserting authority and being granted it is not one
this service can currently express. Both are unmeasured rather than failing —
`BASELINE.md` predates the rewrite.

Defeating cases (per `PRD.md`; only the first is observed against this
participant): a proposal missing author, cost, source, or proposal standing is
admitted; a proposal is admitted without reaching an operator surface; an
instanced session's asserted authority is honored as held authority.

### SVC-ASSET-5 · Ratification requires a live matching human grant

Standing: `BUILT`, incompletely. Serves `PROD-I-5`.

`ratify-proposal` requires `proposal_recorded`, `live_matching_grant`, and
`human_actor` (`service.json`). `conformance/BASELINE.md` records `PROD-I-5 ·
Typed authority: FAIL` — "judgement refusal exists, but the participant
cannot demonstrate the paired typed verification grant and commit."
`KNOWN-GAPS.md`'s "Authority envelope" row adds that budget and revocation are
not yet enforced alongside type and scope.

Defeating case: a machine-typed (`VERIFICATION`) grant ratifies a
judgement-typed claim, or a revoked, expired, or out-of-scope grant ratifies
anything.

### SVC-ASSET-6 · Retraction preserves the original record

Standing: `BUILT`, incompletely. Serves `PROD-I-4`.

`retract-record` and `remove-member` counter a record under a live retraction
grant and a declared reason, preserving the act and adding a counter-record
(`service.json`: `kernel_transition: retract`, `commit: COUNTERED`).
`conformance/BASELINE.md` records `PROD-I-4 · Gate and retract: FAIL` — "the
original and counter-record survive, but the counter receipt does not link
the prior receipt."

Defeating case: an unmarked entry is admitted, or a retraction erases history
or claims an external-world or consumed-resource effect was reversed.

### SVC-ASSET-7 · Every attempted operation returns a durable receipt

Standing: `BUILT`, incompletely. Serves `PROD-I-4`; cites `GROUND-007`,
`GROUND-008`.

Every operation in `service.json`, including its declared refusals, resolves
to a receipt row (`store.py`; `routes.py`'s `_receipt` lookup, which raises
rather than returning silently if a receipt is not durable after the
operation). `KNOWN-GAPS.md`'s "Receipt completeness" row records that
receipts currently omit exact input state, authority grants, preconditions,
effect class, and digest, so the receipt exists but does not yet carry every
field `CONTRACT.md` C6-C8 requires.

Defeating case: an attempted operation, success or refusal, leaves no durable,
addressable receipt row.

### SVC-ASSET-8 · A collection conformance verdict never counts a claim as a fact

Standing: `BUILT`. Serves `PROD-I-2` (per `service.json` requirement tags on
the organizational operations); cites `GROUND-011`.

`declare-collection-type`, `declare-collection`, `add-member`,
`remove-member`, `read-collection`, and `read-library-conformance` implement
a curated typed collection and a derived-on-every-call conformance read that
keeps `CONFORMING` (a ratified description carrying an admitted value),
`CLAIMED_UNRATIFIED` (recorded but never ratified), and `MISSING_FIELD`
distinct (`librarian.py`; `decisions/0063-asset-collections-and-the-librarian.md`).

Defeating case: a `CLAIMED_UNRATIFIED` field is reported as `CONFORMING`, or a
stored conformance verdict is read back instead of recomputed and goes stale.

### SVC-ASSET-9 · The service is discoverable from its manifest alone

Standing: `BUILT`. No `PROD-I-<n>` tag on the manifest itself; cites
`GROUND-006`, `PROD-I-7`.

`services/asset/contracts/service.json` declares all seventeen operations
with their logical endpoint, subject, preconditions, commit outcome, and
refusal set, plus an `undeclared_events` list stating why each adjacent
lifecycle phase (`authority.check`, `lease.claim`, `operation.observe`, and
others) is not itself a callable operation.

Defeating case: a caller must be told out-of-band what an operation requires
or refuses, or an operation exists in the running participant that the
manifest does not declare.

## Non-goals

- Independent settlement of a run: `observe_run`'s independent-observer
  obligation is explicitly not a declared Asset Service operation
  (`service.json` `undeclared_events`, `operation.observe`: "`decisions/0041`
  charters the Observation Service to own independent observation").
- Issuing or revoking authority grants as a declared crossing: `service.json`
  names `authority.grant` and `authority.revoke` as undeclared precisely
  because whether the Console or a separate permits surface owns them is open
  (`services/gateway/CHARTER.md`, `services/console/KNOWN-GAPS.md`).
- A second human- or model-facing binding beyond the Python API/CLI
  (`KNOWN-GAPS.md`, "Two bindings"; `PROD-I-3` is not claimed here).
- Production-grade ranked search or multi-hop graph traversal: the SQLite FTS
  and edge tables are a named compatibility path pending the chartered Asset
  Projection Service (`KNOWN-GAPS.md`, "Search and graph projections";
  `OPEN-SEAMS.md` S14).
- Being, or becoming, a sovereign node on its own: `CHARTER.md` states the
  five conditions unmet today and that `FederationPort` refuses
  `UNCONFIGURED` rather than simulating a crossing.
- Writing its lifecycle onto the Record Service's append-preserving journal:
  `KNOWN-GAPS.md`'s "Operational journal" row records that mutable lifecycle
  tables and partial receipts do not yet implement the complete
  `EventEnvelope`; see `JOURNEYS.md` for this as a named dead end.

## Traceability

| Requirement | Serves | Current participant evidence |
| --- | --- | --- |
| SVC-ASSET-1 | PROD-I-2 | `service.json` `ingest-asset` |
| SVC-ASSET-2 | PROD-I-2 | `custody.py`; `BASELINE.md` PASS |
| SVC-ASSET-3 | PROD-I-2 | `PROD-I-2-BUILD.md` |
| SVC-ASSET-4 | PROD-I-1 | `BASELINE.md` FAIL (named defect) |
| SVC-ASSET-5 | PROD-I-5 | `BASELINE.md` FAIL (named defect) |
| SVC-ASSET-6 | PROD-I-4 | `BASELINE.md` FAIL (named defect) |
| SVC-ASSET-7 | PROD-I-4 | `KNOWN-GAPS.md` "Receipt completeness" |
| SVC-ASSET-8 | PROD-I-2 | `librarian.py`; `decisions/0063` |
| SVC-ASSET-9 | PROD-I-7 | `service.json` itself |
