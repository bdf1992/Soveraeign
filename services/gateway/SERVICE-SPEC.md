# Gateway Service Logical Specification

Status: `BUILT (self-report by the drafting session) · NOT WITNESSED · NOT RATIFIED`

A service-scoped projection of `SPEC.md` under `decisions/0093-service-srd-spec-ground.md`. This
file cites `contracts/kernel-transitions.json` and `services/gateway/contracts/service.json`
rather than re-deriving their contents. Where this document and either contract disagree, the
contract governs and this document is stale.

## Owned domain records

`contracts/service.json` `owns` names six record kinds. None has a standalone JSON Schema yet
(`KNOWN-GAPS.md` "Request contract", "Receipt contract"); the fields below are the ones the
reference implementation actually writes, in
`services/gateway/src/soveraeign_gateway_service/evidence.py`.

- **`gateway-request`** — the received envelope, recorded before any refusal can occur
  (`evidence.record_request`): `request_id`, `actor_kind`, `transport`, `scope`,
  `argument_names`, `envelope_fields`.
- **`capability-resolution`** — the resolved logical endpoint against the authored manifest and
  capability projection (`evidence.record_resolution`): `request_id`, `capability_id`,
  `service_id`, `operation`, `effect_class`, `transport`, `route_address`,
  `capability_map_digest`.
- **`authority-check`** — the authority decision (`evidence.record_authority`): `request_id`,
  `resolution_entry_id`, `actor_kind`, `required_authority`, `scope`, `decision`, and
  (when present) `authority_grant_id` or `diagnostic_code`.
- **`routing-record`** — the record of invoking the bound service-owned route
  (`evidence.record_routing`): `request_id`, `request_entry_id`, `resolution_entry_id`,
  `authority_entry_id`, `capability_id`, `service_id`, `operation`, `transport`,
  `route_address`, `authority_grant_id`, `effect_class`, `scope`.
- **`gateway-receipt`** — Gateway's own crossing-evidence record plus the owning service's
  terminal receipt carried unchanged (`evidence.record_return`, `evidence.refuse`,
  `evidence.fail`): `request_id`, `routing_entry_id`, `terminal_receipt_id`, `terminal_outcome`
  on success; `reason_code`, `failure_class` (`GOVERNED_REFUSAL` or `OPERATIONAL_FAULT`), `stage`
  on refusal or fault. Whether `gateway-receipt` is a distinct owned record, a kernel receipt
  form, or unnecessary beyond this crossing evidence is unsettled (`KNOWN-GAPS.md` "Receipt
  contract").
- **`transport-binding`** — which transport (`IN_PROCESS`, `CLI`, `MCP`, `HTTP`) is activated for
  an operation, governed by `contracts/capability-offices.json` `transport_policy`.

## Service-local states

Gateway does not hold sibling-service domain state (`CHARTER.md` "Authoritative versus derived").
Its own crossing records are the authoritative account of what crossed the door; everything it
says about a routed operation's standing, effect class, or transport activation is derived from
authored service/capability inputs. Its own crossing carries these observed outcomes, a
restriction of `SPEC.md`'s `Receipt` outcome enum to what the reference implementation and its
tests actually exercise:

`ATTEMPTED | COMMITTED | REFUSED | FAILED`

`COUNTERED` and `UNRESOLVED` are declared at the kernel level (`SPEC.md` `Receipt`) but no
Gateway crossing evidence, fixture, or test in `services/gateway/tests/test_gateway_slice.py`
exercises either yet; do not read their absence here as a claim that Gateway refuses them.

## Legal transitions

`contracts/service.json` declares nine operations against subjects `gateway-request`,
`capability-resolution`, `authority-check`, `routing-record`, and `gateway-receipt`:
`accept-request`, `resolve-capability`, `check-authority`, `route-request`, `return-receipt`,
`refuse-request`, `bind-transport`, `list-endpoints`, `read-receipt`. Each operation's
preconditions, commit value, and refusals are declared there and are not restated here.

`route-request` is the one operation the manifest ties to a named kernel transition
(`kernel_transition: "cross"`). `contracts/kernel-transitions.json` `cross` requires
`source_address`, `reader_declaration`, `omissions`, `authority_grant_id`, `destination_address`,
commits to `COMMITTED`, and refuses `READER_UNDECLARED` or `AUTHORITY_REFUSED`. Gateway's
`route-request` narrows this to: the resolved capability address is the source, the checked
actor and live grant are the authority evidence, and the bound service-owned route is the
destination.

Only one of the nine declared operations is realized by the reference implementation's caller
path today. `Gateway.dispatch()` in
`services/gateway/src/soveraeign_gateway_service/core.py` performs
`_accept → _resolve → _check_authority → _admit_route → (owning service call) → return/refuse`
as one call for one presented `sov://` address; it does not expose `list-endpoints` or
`read-receipt` as separately invocable operations (see `JOURNEYS.md` for the caller-facing
consequence of this gap).

## Refusal reason codes

`contracts/service.json` `local_refusals` maps Gateway-local refusal names to the kernel
vocabulary in `contracts/kernel-transitions.json`:

| Gateway-local | Kernel refusal |
| --- | --- |
| `ENDPOINT_UNKNOWN` | `MISSING_PRECONDITION` |
| `GRANT_NOT_COVERED` | `AUTHORITY_REFUSED` |
| `MALFORMED_REQUEST` | `INCOMPLETE_PROPOSAL` |
| `RECEIPT_MISSING` | `OBSERVATION_MISSING` |
| `SERVICE_UNREACHABLE` | `UNREADABLE` |
| `TRANSPORT_NOT_ACTIVATED` | `POLICY_REFUSED` |
| `TRANSPORT_REFUSED_IN_PHASE` | `POLICY_REFUSED` |

The reference implementation (`core.py`) also emits diagnostic codes not present in this table —
`ACTOR_KIND_NOT_ADMITTED`, `AUTHORITY_CHECK_FAILED`, `INVALID_GRANT_REFERENCE`,
`SERVICE_EXECUTION_FAILED` — attached to a `GatewayRefusal` or `GatewayFault` object
(`services/gateway/src/soveraeign_gateway_service/contract.py`) and carried in the `diagnostic_code`
field of the recorded evidence. These are implementation-level detail under the two governing
`failure_class` values, `GOVERNED_REFUSAL` and `OPERATIONAL_FAULT` — not yet reconciled into
`contracts/service.json`'s declared `local_refusals` table. Treat that reconciliation as an open
contract gap, not a silent extension of the contract.

## Persistence and authority notes

Gateway's own crossing records persist through the Record Service's append-preserving journal
(`depends_on: record:append-preserving-journal`, `contracts/service.json`;
`services/gateway/src/soveraeign_gateway_service/evidence.py` calls `RecordService.append` /
`RecordService.receipt`). Gateway holds no SQLite tables or payload store of its own.

Authority is read, never held or issued. Gateway checks Console-owned grant records
(`depends_on: console:authority-grant`; `KNOWN-GAPS.md` "Authority source"). If an Authority
Service later supersedes Console's current grant surface, `KNOWN-GAPS.md` records that "Gateway
must remain a reader either way" — long-term ownership of the grant store itself is unsettled and
is not this service's decision (see `JOURNEYS.md` open questions).

`contracts/service.json` `forbids` names what Gateway may never do regardless of implementation
detail: settling a routed operation, observing what it routed, holding authoritative service
state, issuing authority, silent transport fallback, external transport in Phase I, and reaching
a service except through its logical endpoint.

## Contract standing

`contracts/service.json` `standing: "PROPOSED"` applies to the manifest and to every one of its
nine operations. A self-tested reference implementation exists for the `route-request` /
`return-receipt` path against one operation (`sov://asset/ingest-asset`); implementation and
passing tests are evidence, not a change to the manifest's declared standing
(`decisions/0040-the-declared-service-surface.md`, Ruling 5, as cited in `KNOWN-GAPS.md`).
