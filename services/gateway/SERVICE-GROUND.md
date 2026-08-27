# Gateway Service Ground

Status: `BUILT (self-report by the drafting session) · NOT WITNESSED · NOT RATIFIED`

A service-scoped projection of `GROUND.md` under `decisions/0067-service-srd-spec-ground.md`.
Each claim below is one this service commits to always being true for whoever depends on it,
with what would defeat it and, where one applies, the root `GROUND-<nnn>` claim it specializes.
This list is short by design; it is not forced to a fixed count.

### G-GW-1 — a caller acts by crossing a declared address, not by having access

A caller acts on this service by presenting a declared `sov://<service>/<operation>` address, not
by calling code directly. Gateway resolves that address against the authored manifest and the
capability projection, verifying the projection's input digest and rederiving the selected row
before trusting it; it never invents an address or infers a missing route
(`CHARTER.md` "What a logical endpoint is"). Specializes `GROUND-004`.

Defeated by: Gateway routing a request to an endpoint it did not resolve from authored inputs, or
trusting a stale or tampered capability-projection row. `test_stale_capability_map_refuses_before_authority_or_service`
and `test_capability_projection_tamper_fails_closed_even_with_fresh_input_digest` are the current
guards.

### G-GW-2 — refusal is legible and distinct from failure

A missing grant, an inactive transport, or an unreachable declared route comes back as a governed
refusal with a reason. A corrupt capability row, an authority-reader exception, or a service
exception comes back as `FAILED` evidence instead — Gateway never turns an infrastructure defect
into a claim that the actor lacked authority (`CHARTER.md` "The route", step 3). Specializes
`GROUND-008`.

Defeated by: an authority-reader exception recorded as `AUTHORITY_REFUSED` rather than `FAILED`.
`test_authority_reader_failure_is_not_counterfeited_as_denial` is the current guard.

### G-GW-3 — every crossing leaves a record, including a refused or failed one

Every request Gateway accepts is recorded before any refusal can occur; every resolution,
authority decision, routing attempt, and refusal or failure leaves its own durable, attributable
entry, distinct from the routed service's own receipt
(`services/gateway/src/soveraeign_gateway_service/evidence.py`). Specializes `GROUND-007`.

Defeated by: a malformed request or a refusal leaving no request record.
`test_malformed_request_has_request_record_before_refusal` is the current guard.

### G-GW-4 — what comes back is the owning service's receipt, unchanged and attributed

The receipt a caller receives is the routed service's own terminal receipt, unchanged and
attributed to the checked actor — never a second, Gateway-manufactured settlement, and never a
promotion of a service-level refusal into a success (`CHARTER.md` "Authoritative versus derived").
Specializes `GROUND-005`.

Defeated by: a returned receipt whose actor does not match the checked actor, or a service
refusal returned as if it had succeeded. `test_terminal_receipt_actor_must_match_checked_actor`
and `test_service_terminal_refusal_is_returned_unchanged_not_promoted_to_success` are the current
guards.

### G-GW-5 — neither a human nor a model gets a private door

A human-attributed request and a model-attributed request for the same operation take the same
resolution, authority, and routing path, and differ only in the attributed actor
(`test_human_and_model_take_same_kernel_path_and_get_service_receipts_unchanged`). Specializes
`GROUND-002`.

Defeated by: actor kind silently changing which resolution, authority, or routing logic applies
beyond the declared, symmetric check. Not yet exercised beyond one participant and one binding
shape; the full two-binding proof `KNOWN-GAPS.md` names as open would extend this claim's
coverage, not replace it.

### G-GW-6 — a network transport does not open itself

HTTP stays inactive and refused while Phase I stands, regardless of what runtime health checks or
listeners exist underneath it (`CHARTER.md` "What it does not do";
`contracts/capability-offices.json` `transport_policy.HTTP`, `external_transports_refused_in_phase`).
No root `GROUND-<nnn>` claim names transport activation directly; this claim is this service's own
reading of the Phase-I boundary rather than a specialization.

Defeated by: an HTTP-addressed request reaching routing. `test_http_stays_refused_in_phase_one`
is the current guard. Who would custody a credential if this ever changes is not answered here —
see `JOURNEYS.md`, "Open custody and ownership questions".
