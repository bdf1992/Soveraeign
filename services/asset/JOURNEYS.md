# Asset Service Journeys

Status: `PROPOSED · BUILT AT MOST · NOT WITNESSED · NOT RATIFIED`

This is the piece `decisions/0067-service-srd-spec-ground.md` names as having
no root-level analog. Each journey below is the abstract path a caller takes
through
this service — discover, authority-check, invoke, report/observe, receipt,
and sometimes retract or reconstruct — stated as it actually behaves in the
current reference participant, not as `CHARTER.md` aspires for it to behave.
`COMPLETES` means the journey reaches a terminal, receipted outcome as
described. `DEAD-ENDS-AT-<step>` means it does not, and names the exact gap
and its citation. Naming an open custody or ownership question here does not
assign, resolve, or answer it — it routes to a decision record the ordinary
way (`decisions/0067`, "What this is not").

## J1 · Discover what this service will let a caller do

**Path:** read `services/asset/contracts/service.json` alone, with no oral
briefing.

**COMPLETES.** The manifest declares all seventeen operations with logical
endpoint, subject, CRUD kind, preconditions, commit outcome, and refusal set,
plus an `undeclared_events` list explaining why ten adjacent lifecycle phases
are not themselves callable operations. This is `GROUND-006` exercised
directly: "a participant arriving with no briefing can determine what it may
do."

## J2 · Capture an original asset

**Path:** discover `ingest-asset` → hold a live grant → invoke → receipt →
reread to verify.

**COMPLETES**, through two different reachable routes with different reach
today:

- Direct Python API/CLI: `service.json`'s stated preconditions
  (`payload_bytes_readable`, `declared_label`, `declared_locator`,
  `live_grant`) gate the call; `custody.py` and `store.py` verify the digest
  on ingest and on every later read.
- Gateway-routed: `services/gateway/CHARTER.md`'s built walking skeleton is
  exactly this path — `IN_PROCESS -> sov://asset/ingest-asset -> Asset
  Service -> terminal receipt` — proven both ways in
  `tests/test_walking_skeleton.py`: "without a covering grant, ... leaves
  durable Gateway refusal evidence and the Asset Service does not execute;
  with a live exact grant, the same logical endpoint reaches the Asset-owned
  route."

**Named scope, not a dead end:** `routes.py`'s `AssetRoutes.OPERATIONS =
("ingest-asset", "read-version")` is the entire Gateway-routed surface today.
The other fifteen declared operations, including every organizational and
proposal operation, are reachable only through the direct Python API/CLI, not
through the Gateway path this journey otherwise completes.

## J3 · Reread a captured version and detect drift

**Path:** discover `read-version` → invoke → digest verification → receipt.

**COMPLETES.** `custody.py` refuses `DIGEST_MISMATCH`, `SOURCE_UNREACHABLE`,
`SOURCE_CHANGED`, and `VERSION_UNKNOWN` rather than returning stale or
corrupted content. This is the one Phase-I requirement the participant oracle
currently passes: `conformance/BASELINE.md` records `PROD-I-2 · Remember:
PASS` — "declared derivative recordings reconstruct exact source, reader
artifact/version, replay configuration, output, fidelity, and recoverable
omissions."

## J4 · Request and reconstruct a derived recording

**Path:** declare a complete `ReaderDeclaration` → `request-derivative`
leases a worker → the worker reports → an independent party observes → the
run settles → a caller reconstructs the recording later.

**DEAD-ENDS-AT-observe.** The declaration, leasing, reporting, and
reconstruction steps all complete and are evidenced
(`conformance/PROD-I-2-BUILD.md`: "Observation settles a derivative only
after reconstructing that complete path; output-only success cannot conceal
later source corruption"; 96 passing unit tests including incomplete-reader,
source-corruption, and tampered-output cases). But the independent-observer
step `SPEC.md`'s `observe_run` requires is not a callable Asset Service
operation at all: `service.json`'s `undeclared_events` names
`operation.observe` as out of scope because "`decisions/0041` charters the
Observation Service to own independent observation," and that service is
boundary-only today. `KNOWN-GAPS.md`'s "Observer independence" row records
the sharper defect in what does exist: "Any named actor can call `observe`,
including the worker" — the executor-only settlement `GROUND-010` forbids is
not yet structurally prevented.

## J5 · Propose a description, then ratify it

**Path:** `propose-description` (human or model actor) → `ratify-proposal`
(human actor, live matching grant) → `EFFECTIVE`.

**DEAD-ENDS-AT-admit.** `KNOWN-GAPS.md`'s "Admission standing" row: "Proposal
ratification updates `RECORDED` directly to `RATIFIED`" — the four-step
ladder `CLASSIFICATION.md` and `SPEC.md` both fix (`RECORDED → ADMITTED →
RATIFIED → EFFECTIVE`) collapses its middle step in this participant.
Separately, the proposal itself does not yet satisfy `PROD-I-1`'s defeating
case: `conformance/BASELINE.md` records `PROD-I-1 · Propose: FAIL` —
"proposal lacks content address, source addresses, and cost record" — and
`PROD-I-5 · Typed authority: FAIL` — "the participant cannot demonstrate the
paired typed verification grant and commit."

## J6 · Retrieve an asset's provenance and lineage

**Path:** `read-asset` (also reads `asset-relationship` and
`derivation-lineage`) → `read-version-history` → `rebuild-projection` for a
fresh traversal.

**COMPLETES for immediate lineage; DEAD-ENDS-AT-multi-hop-traversal for
depth.** Reading an asset's direct relationships and version history is
built and receipted. But `KNOWN-GAPS.md`'s "Search and graph projections" row
states the traversal itself "is a `LIKE` substring scan with no ranking and a
one-hop `neighbors()`" against a chartered target of "ranked text search,
bounded multi-hop traversal, and per-hit source resolution" that belongs to
the Asset Projection Service, not this one (`OPEN-SEAMS.md` S14 names the
same gap as two owners of the asset projections, unresolved until
`decisions/0021` is ruled).

## J7 · Retract an effective relationship or use record

**Path:** `retract-record` or `remove-member` under a live retraction grant
and a declared reason → `COUNTERED` receipt, original preserved.

**COMPLETES**, with a named residual short of full linkage. The core claim —
history is never erased — holds: `conformance/BASELINE.md` confirms "original
and counter-record survive." What is missing is that "the counter receipt
does not link the prior receipt" (same source), so a caller can find both
records but cannot yet walk from one directly to the other through the
receipt chain alone.

## J8 · File an asset into a typed collection and read library conformance

**Path:** `declare-collection-type` → `declare-collection` → `add-member` →
`read-library-conformance` (or `read-collection`).

**COMPLETES for the first declaration of a type; DEAD-ENDS-AT-type-migration
for changing one under existing members.** The curatorial layer and its
three-way conformance verdict are built and evidenced
(`librarian.py`; `decisions/0063-asset-collections-and-the-librarian.md`).
But `KNOWN-GAPS.md`'s "Collection type migration" row: "a collection type
cannot be redeclared: a second declaration is refused `STALE_STATE`, so a
schema change under existing members has no path at all" — the required
behavior (a superseding version, every member re-judged, the earlier version
preserved) is named and not yet built (`decisions/0057`, Defaults taken).

## J9 · Cross between a human binding and a model binding on the same record

**Path:** a human actor and a model actor each invoke the same declared
operation and receive compatible receipts.

**DEAD-ENDS-AT-second-binding.** `KNOWN-GAPS.md`'s "Two bindings" row: "Only
a Python API/CLI participant exists... Human and model bindings must use the
same transition contract." `conformance/BASELINE.md` confirms at the
requirement level: `PROD-I-3 · Cross: FAIL` — "no second binding or fully
declared crossing exists." The `actor_kind: HUMAN | MODEL` distinction is
present in the data model (`SPEC.md`'s `Proposal`) but no second physically
distinct binding has been built to exercise it.

## J10 · The service's own lifecycle becomes the Record Service's journal

**Path:** a consequential decision or state transition in this service is
reconstructable independently of any current projection, through the
append-preserving Event Envelope the Record Service is chartered to own.

**DEAD-ENDS-AT-journal-migration.** `KNOWN-GAPS.md`'s "Operational journal"
row: "Mutable lifecycle tables and partial receipts do not yet implement the
complete append-preserving Event Envelope," citing `CONTRACT.md` C15 and
`SPEC.md`'s `EventEnvelope`. Today's authoritative store for this service is
its own SQLite ledger (`store.py`; `CHARTER.md`'s Authoritative versus
derived stores table: "Assets, versions, operations, authority, receipts |
SQLite ledger | canonical reference binding"), not the Record Service's
journal, even though `STATUS.yaml` records
`record_service_status: BUILT_SELF_TESTED_NOT_WITNESSED` — a sibling service
chartered for exactly this now exists and this service has not yet migrated
onto it. This is the same gap the root `CLAUDE.md` snapshot glosses in
passing as "the Asset Service still keeps its own SQLite tables"; its own
citation in `KNOWN-GAPS.md` is `C15` and `SPEC.md`'s `EventEnvelope`, not a
`PROD-I-<n>` tag, and that discrepancy in labeling is noted here rather than
silently resolved one way or the other.

## Open custody and ownership questions

Each of these is a question this service's own boundary cannot answer, and
naming it here does not answer it either.

1. **Does a source's access credential (for example, a GitHub personal
   access token needed to re-fetch a private repository, commit, or path)
   ever pass through or sit beside this service's payload custody?**
   `CHARTER.md` names `github-source` among this service's adapter ports and
   `service.json` lists it under `ports`. Separately, `README.md` and
   `recording.py` are explicit that the *derivative-recording replay
   configuration* is designed to hold "opaque credential references rather
   than usable secrets" and a "secret-free replay configuration." Neither
   `CHARTER.md`, `KNOWN-GAPS.md`, nor `service.json` says anything about
   whether the *source-capture* path — `ingest-asset` from a GitHub locator —
   has the same guarantee, or where a fetch credential for that source would
   live if one were needed. This is silent in every document read for this
   exercise, not answered either way.

2. **Who migrates this service's own lifecycle onto the Record Service's
   append-preserving journal — this service reaching out, or the Record
   Service reaching in?** Named as a dead end in J10 above. `KNOWN-GAPS.md`
   states the required behavior but not an owner for closing the gap, and
   `STATUS.yaml` records both services as `BUILT_SELF_TESTED_NOT_WITNESSED`
   independently, with no cross-reference between their statuses.

3. **Who owns issuing and revoking authority grants for this service — this
   service's own `authority.py`, or a separate permits surface?**
   `service.json`'s `undeclared_events` states this as open in its own words:
   "whether the Console or a separate permits surface owns authority-grant is
   open (`services/gateway/CHARTER.md`, `services/console/KNOWN-GAPS.md`)."
   Cited verbatim rather than restated, because restating it risks quietly
   picking a side.

4. **Who keeps `rebuild-projection` and this service's own two projection
   tables once the Asset Projection Service is ratified?**
   `OPEN-SEAMS.md` S14 states this plainly: "Which service keeps
   `rebuild-projection` for the Asset Service's own two tables after
   ratification is Bdo's call." Explicitly owner-gated, not this service's
   or this document's to decide.
