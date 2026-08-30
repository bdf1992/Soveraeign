# Gateway Service Journeys

Status: `BUILT (self-report by the drafting session) · NOT WITNESSED · NOT RATIFIED`

`decisions/0093-service-srd-spec-ground.md` names this document as the one with no analog in the
root pattern. `CHARTER.md` calls this service "the node's door." Today exactly one journey through
that door completes end to end, in process. Every other journey a caller could plausibly attempt
is a door that has not been opened — declared in `contracts/service.json`, described in
`CHARTER.md`, and named as unbuilt in `KNOWN-GAPS.md`. This document maps both kinds plainly
rather than presenting the declared surface as if it were the built one.

## COMPLETES

### J1 — invoke a declared operation and receive its receipt

`accept → resolve → check-authority → route → return-receipt` (or `refuse-request` at any
step), for `sov://asset/ingest-asset`, `IN_PROCESS` transport, actor kind `HUMAN` or `MODEL`.

This is `Gateway.dispatch()` in
`services/gateway/src/soveraeign_gateway_service/core.py`. It is proven both ways:

- with a live exact grant, the request reaches the Asset-owned route and the Asset Service's
  terminal receipt comes back unchanged and attributed to the checked actor
  (`test_human_and_model_take_same_kernel_path_and_get_service_receipts_unchanged`);
- without a covering grant, the request leaves durable refusal evidence and the Asset Service
  never executes (`test_authority_refusal_is_durable_and_asset_never_sees_the_call`).

A refusal along this path — malformed request, unknown endpoint, stale capability state, missing
grant, unreachable route, missing or mismatched receipt — also **completes**, in the sense
`GROUND-008` means: refusal is an outcome, not a dead end. `services/gateway/tests/test_gateway_slice.py`
covers eleven distinct refusal and fault shapes along this same journey, each leaving its own
durable record.

Scope actually proven: one service (`asset`), one operation (`ingest-asset`), one transport
(`IN_PROCESS`), one effect class (`RECORD_LOCAL`). `KNOWN-GAPS.md` "Route coverage" and
"Replication test before abstraction" name the next two repetitions — a second `asset` operation,
then an operation from a different service family — as unproven, not as failed.

## DEAD-ENDS

### J2 — discover what the node offers before invoking anything

A caller who does not already know the address wants to ask the door what it can reach:
`sov://gateway/list-endpoints`, declared in `contracts/service.json` (`crud: READ`,
`commit: DERIVED`).

Dead end. `Gateway.dispatch()` has no case for it; nothing in
`services/gateway/src/soveraeign_gateway_service/core.py` implements `list-endpoints`. The only
way to see the declared surface today is `python scripts/sov_service.py endpoints --service
gateway`, which reads the authored manifests directly through `scripts/sovkernel/manifests.py` —
bypassing the Gateway participant entirely. A caller that only knows how to cross the door, per
`GROUND-004`, cannot discover what the door offers; it has to already know the address, or read
the repository instead of crossing the door.

### J3 — read back a receipt after the fact

A caller that crossed once wants to ask the door for that crossing's record later, without
re-invoking the operation: `sov://gateway/read-receipt`, declared in `contracts/service.json`
(`crud: READ`, `also_reads: gateway-request, routing-record`).

Dead end. `core.py` exposes no read path back into what `evidence.py` wrote to the Record
Service journal. The crossing evidence is durably recorded (`GROUND-007` holds for the write
side), but nothing in this service turns that record back into an answer to a caller asking for
it through the door. Reading it back today means reading the Record Service's journal directly,
which is not a Gateway crossing either.

### J4 — reach a second service family through the same door

A caller wants `sov://registry/resolve` or any `sov://<service>/<operation>` outside `asset` to
take the same route Gateway proves for asset ingest.

Dead end. `KNOWN-GAPS.md` "Route coverage" states plainly: "One reusable `RECORD_LOCAL +
IN_PROCESS` vertical is implemented for `sov://asset/ingest-asset` through an Asset-owned route."
`Gateway.__init__` accepts an injected route map; nothing in the repository binds a second
service's route into it yet. `KNOWN-GAPS.md` "Node composition" is explicit that assembling
routes across services is not this service's job to do unprompted — "Build composition outside
the Gateway service; do not turn Gateway into the Node" — but nothing yet does that assembly
either, for a second service.

### J5 — cross the door over a network transport

A caller outside the local process wants to reach a declared operation over HTTP:
`sov://<service>/<operation>`, transport `HTTP`, declared and named in
`contracts/capability-offices.json` `transport_policy.HTTP` and
`external_transports_refused_in_phase`.

Dead end by design in the current Gateway baseline, not an ambient phase prohibition. The
service has no admitted built HTTP crossing, and `contracts/capability-offices.json` keeps HTTP
outside the reachable transport set. The legacy-named
`test_http_stays_refused_in_phase_one` still guards the same observable fact: an HTTP-addressed
request cannot reach routing. Unlike J2–J4, this dead end is an explicit current service
boundary; opening it later requires a built transport plus scoped authority and receipts.

## Open custody and ownership questions

Per `decisions/0067`, naming a question here does not assign, resolve, or make it this service's
to decide. Each of these is a genuine gap in what I read — `CHARTER.md`, `KNOWN-GAPS.md`,
`contracts/service.json`, `AGENTS.md` — not an invented one.

1. **Who would custody the credential for a future external crossing?** If Gateway ever does
   open a network transport, something has to mint, hold, rotate, and present the credential
   that crossing uses. `CHARTER.md` and `KNOWN-GAPS.md` say the transport stays refused; neither
   says who would hold that credential when it doesn't. `AGENTS.md` "Secrets and local
   boundaries" states the general rule for any remote crossing — "a declared adapter, data-
   boundary mode, exact input projection, authority, and receipt" — but that rule is stated at
   repository scope, for crossings in general, and is not instantiated for Gateway. This is
   open, not silent-by-omission on my part: I read the charter and the gap list looking for an
   answer and did not find one.

2. **Who owns the authority-grant store long-term?** Gateway reads Console-owned grant records
   today and is required to "remain a reader either way." `KNOWN-GAPS.md` "Authority source"
   names that if an Authority Service later supersedes Console's grant surface, long-term
   ownership needs settling — and does not settle it.

3. **Who is the Node's composition root?** `CHARTER.md` "Relationship to node composition" and
   `KNOWN-GAPS.md` "Node composition" are both explicit that Gateway must not become it — "Build
   composition outside the Gateway service; do not turn Gateway into the Node" — but neither
   names what does. Identity, Registry, Record, authority, and service routes need assembling by
   something; nothing in what I read claims that job today.

4. **Who negotiates on this node's behalf with another sovereign node?** `contracts/service.json`
   declares a `federation` port. `KNOWN-GAPS.md` "Capability negotiation" states local
   `list-endpoints` semantics can answer what this node declares, and that "two-sided negotiation"
   is deferred to "the federation boundary" — a boundary, not a named owner.

Each of these routes to a decision record at whichever tier `STATUS.yaml`'s resolution rule
names, the ordinary way; none of them is decided by being listed here.
