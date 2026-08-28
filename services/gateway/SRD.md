# Gateway Service Requirements Document

Status: `BUILT (self-report by the drafting session) · NOT WITNESSED · NOT RATIFIED`

This is a service-scoped projection of `PRD.md` under `decisions/0093-service-srd-spec-ground.md`.
It states what the Gateway Service owes the callers that depend on it. It is not a new
requirement ladder: every `SVC-GATEWAY-<n>` below either serves a named `PROD-I-<n>` or narrows
`CHARTER.md`'s route contract to a checkable claim. `CHARTER.md` remains this service's
authoritative role statement; this document does not compete with it.

## Product outcome

Give every declared service operation in the node one transport-neutral crossing point that
resolves the logical endpoint, checks the caller's authority, routes to the owning service, and
returns that service's terminal receipt unchanged — refusing legibly, with a durable record,
whenever any step cannot proceed (`CHARTER.md` "Role in Soveraeign", "The route").

## Callers

The Gateway's caller is not a human end user; per `SYSTEM.md`/`AGENTS.md` framing and
`decisions/0067`, its caller is the node itself, expressed through:

- a human operator, acting through a binding that composes a `sov://` request (`contracts/service.json`
  `ports: human-binding`). No dedicated human-facing Gateway binding exists yet; today this shape is
  exercised only by `services/gateway/tests/test_gateway_slice.py` constructing envelopes directly.
- a model operator, acting the same way (`ports: model-binding`), exercised by the same test file
  under `actor_kind: "MODEL"`.
- the owning service whose route Gateway invokes and whose terminal receipt it carries back
  unchanged — the Asset Service today, for `sov://asset/ingest-asset` (`CHARTER.md` "The route").
  This party is the target of a crossing Gateway performs, not an inbound caller of Gateway.
- the older MCP ingress (`bindings/mcp/gateway.py`), which presently has its own resolution,
  authority, and journal behavior and does not yet call this service
  (`KNOWN-GAPS.md` "The MCP binding").
- a federated node (`ports: federation`), a declared port with no negotiation behavior defined
  (`KNOWN-GAPS.md` "Capability negotiation").

## Requirements

Each requirement below carries its own `OPEN → BUILT → WITNESSED → RATIFIED` standing per
`PRD.md`. `BUILT` here is this drafting session's self-report against the evidence cited; it is
not independent witness.

### SVC-GATEWAY-1 · Resolve a declared address

A caller presents one transport-neutral `sov://<service>/<operation>` address. Gateway resolves
it against the authored service manifest and the capability projection, verifies the projection's
input-state digest, and rederives the selected row from authored inputs before trusting it. It
does not invent an address or infer a missing route (`CHARTER.md` "What a logical endpoint is",
route step 2). Serves `PROD-I-3`.

Defeating case: an unknown or undeclared endpoint is answered as if it existed rather than
refused — guarded by `test_unknown_sov_operation_is_not_invented`.

Standing: `BUILT`.

### SVC-GATEWAY-2 · Check exact authority before routing

Gateway requires the declared actor kind and an exact live grant covering the operation's
authority and request scope before it routes. Absence of a covering grant is a durable refusal;
the routed service is never reached (`CHARTER.md` route step 3). Serves `PROD-I-5`.

Defeating case: a request without a covering grant still reaches the Asset Service — guarded by
`test_authority_refusal_is_durable_and_asset_never_sees_the_call`.

Standing: `BUILT`.

### SVC-GATEWAY-3 · Distinguish refusal from operational failure

A typed authority denial is recorded as `AUTHORITY_REFUSED`. An authority-reader exception, a
service exception, or a receipt-attribution mismatch is recorded as `FAILED` evidence, never
counterfeited as a denial (`CHARTER.md` "The route", step 3; "Governed refusal is distinct from
operational failure"). Serves `PROD-I-5`, `GROUND-008`.

Defeating case: a reader exception is recorded as though the actor lacked authority — guarded by
`test_authority_reader_failure_is_not_counterfeited_as_denial`.

Standing: `BUILT`.

### SVC-GATEWAY-4 · Return the owning service's receipt unchanged

Gateway invokes a bound service-owned route and returns that service's terminal receipt
unchanged and attributed to the checked actor. It manufactures no second success receipt and
does not promote a service refusal to a success (`CHARTER.md` "Authoritative versus derived").
Serves `PROD-I-3`, `PROD-I-4`.

Defeating case: the returned receipt's actor does not match the checked actor, or a service-level
refusal is returned as a success — guarded by `test_terminal_receipt_actor_must_match_checked_actor`
and `test_service_terminal_refusal_is_returned_unchanged_not_promoted_to_success`.

Standing: `BUILT`.

### SVC-GATEWAY-5 · One door for a human actor and a model actor

A human-attributed and a model-attributed request for the same operation take the identical
kernel path and receive service receipts that differ only by actor. Serves `PROD-I-3`, and is
groundwork toward the two-binding proof (`AI-NATIVE.md` check 7 as cited in `KNOWN-GAPS.md`
"Two-binding proof").

Defeating case: actor kind changes which path or authority logic applies beyond the declared
check — guarded by `test_human_and_model_take_same_kernel_path_and_get_service_receipts_unchanged`.

Standing: `BUILT` for same-participant human/model parity. The full two-binding proof — a
distinct human binding and two materially different model bindings driving this same door — is
`OPEN` (`KNOWN-GAPS.md` "Two-binding proof").

### SVC-GATEWAY-6 · Refuse smuggled attribution and stale state

Gateway rejects a client-attributed actor override, a stale or tampered capability-projection
row, and a receipt whose actor does not match the checked actor, before authority or service
execution proceeds. Serves `PROD-I-5`, `GROUND-005`.

Defeating case: a spoofed actor or a tampered projection row still reaches routing — guarded by
`test_gateway_rejects_client_attribution_override_before_authority_or_service` and
`test_capability_projection_tamper_fails_closed_even_with_fresh_input_digest`.

Standing: `BUILT`.

### SVC-GATEWAY-7 · Every crossing leaves a record

Every accepted request, resolution, authority decision, and routing/refusal/failure outcome
leaves durable, attributable Gateway evidence — distinct from the routed service's own receipt
(`CHARTER.md` "Authoritative versus derived"; `evidence.py`). Serves `PROD-I-4`, `GROUND-007`.

Defeating case: a malformed request or a refusal leaves no request record — guarded by
`test_malformed_request_has_request_record_before_refusal`.

Standing: `BUILT`.

### SVC-GATEWAY-8 · External transport stays refused in Phase I

HTTP stays inactive and refused regardless of whether underlying node-runtime health checks or
listeners exist; only `IN_PROCESS` and `CLI` are admitted (`CHARTER.md` "What it does not do";
`contracts/capability-offices.json` `transport_policy.HTTP`, `external_transports_refused_in_phase`).
Serves the Phase-I non-goal "Automated external-world effects" (`PRD.md`) and the standing rule
`no_external_effects_in_phase_i`.

Defeating case: an HTTP-addressed request reaches routing — guarded by
`test_http_stays_refused_in_phase_one`.

Standing: `BUILT`.

### SVC-GATEWAY-9 · A second same-class route without service-specific logic

A second service-owned route of the same effect/transport class can be bound behind Gateway
without adding domain-specific logic to Gateway itself (`CHARTER.md` "Relationship to node
composition"; `KNOWN-GAPS.md` "Route coverage", "Replication test before abstraction").

Defeating case: not yet exercisable — only one route (`sov://asset/ingest-asset`) exists. The
replication test is the named next step, not evidence that already passed.

Standing: `OPEN`.

### SVC-GATEWAY-10 · Independent witness of a routed crossing

A party that did not build or route the call can independently verify what crossed the door.
Serves `PROD-I-7`.

Defeating case: not yet stateable — `KNOWN-GAPS.md` "Independent observation" records that
"the Gateway cannot witness itself and there is no fresh independent Gateway witness receipt."

Standing: `OPEN`.

## Non-goals for this service

Carried from `CHARTER.md` "What it does not do" and stated here as requirement boundaries, not
gaps to close:

- Settling a sibling service's operation, or manufacturing a second success receipt for one.
- Witnessing an operation it routed.
- Issuing or widening authority.
- Owning capability definitions or repairing the capability projection in place.
- Falling back to an undeclared transport or route.
- Opening an external transport while Phase I stands.
- Becoming the Node's composition root. Gateway is one service inside the locally sovereign Node
  (`CHARTER.md` "Relationship to node composition"; see `JOURNEYS.md` open questions).
