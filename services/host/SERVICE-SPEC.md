# Host Service Specification (service scope)

Status: `BUILT` (drafted under `decisions/0093-service-srd-spec-ground.md`; self-report only)

A service-scope projection of `SPEC.md`'s shape. It cites `contracts/kernel-transitions.json`
and `services/host/contracts/service.json` rather than re-deriving the kernel's transition
contract; this document does not compete with `SPEC.md` and is not named `SPEC.md`.

## Owned domain records

From `CHARTER.md` Owned records:

| Record | Standing |
| --- | --- |
| `host-health` | Built — one normalized reading of the adapter's execution boundary |
| `network-state` | Declared only |
| `driver-inventory` | Declared only |
| `utility-inventory` | Declared only |
| `host-operation` | Declared only — a requested or attempted scan, restart, power, driver, or utility operation with its operation plan and lifecycle |
| `host-receipt` | Built for `read-health`; declared for every other operation — the terminal receipt for a Host Service operation |

## Service-local states and standing

`SPEC.md`'s historical-standing ladder (`RECORDED → ADMITTED → RATIFIED → EFFECTIVE`) does not
apply to `host-health` readings at all. `read-health` commits `DERIVED`
(`contracts/service.json`), and `contracts/service-manifest.schema.json` defines that value:
"A READ commits `DERIVED` and writes no authoritative record." Confirmed in
`soveraeign_host_service/core.py`, whose `COMMITTED` receipt detail carries
`"standing_effect": "NONE"` — the read produces an event and a receipt, and no authoritative
domain record besides them.

The declared `host-operation` record, once any mutating operation is reachable, is the one
that will use the standing ladder — through whichever kernel transition its own manifest entry
names (`submit_proposal` for a proposal-shaped operation, `begin_run` for an operation that
attempts an effect directly).

## Legal transitions

Sourced from `services/host/contracts/service.json`; the `kernel_transition` column is what
`SPEC.md`'s Transition contract table (and its compiled form,
`contracts/kernel-transitions.json`, `decisions/0067` O20) names for that step:

| Operation | Standing | CRUD | Kernel transition | Commit | Refusals |
| --- | --- | --- | --- | --- | --- |
| `read-health` | BUILT | READ | — (direct service-owned read) | `DERIVED` | `HOST_UNAVAILABLE`, `HOST_READ_FAILED`, `HOST_BOUNDARY_UNKNOWN`, `MALFORMED_HOST_REQUEST` |
| `read-network` | PROPOSED | READ | — | `DERIVED` | `HOST_UNAVAILABLE`, `HOST_READ_FAILED` |
| `request-scan` | PROPOSED | CREATE | `begin_run` | `RECORDED` | `SCAN_UNAVAILABLE`, `MISSING_PRECONDITION`, `EFFECT_CLASS_REFUSED` |
| `request-restart` | PROPOSED | CREATE | `submit_proposal` | `RECORDED` | `BOOT_ID_UNAVAILABLE`, `INCOMPLETE_PROPOSAL` |
| `restart` | PROPOSED | CREATE | `begin_run` | `COMMITTED` | `AUTHORITY_REFUSED`, `STALE_STATE`, `BOOT_ID_UNAVAILABLE`, `EFFECT_CLASS_REFUSED` |
| `power-off` | PROPOSED | CREATE | `begin_run` | `COMMITTED` | `AUTHORITY_REFUSED`, `POLICY_REFUSED`, `EFFECT_CLASS_REFUSED` |
| `suspend` | PROPOSED | CREATE | `begin_run` | `COMMITTED` | `AUTHORITY_REFUSED`, `POLICY_REFUSED`, `EFFECT_CLASS_REFUSED` |
| `list-drivers` | PROPOSED | READ | — | `DERIVED` | `HOST_UNAVAILABLE`, `DRIVER_INVENTORY_UNAVAILABLE` |
| `propose-driver-update` | PROPOSED | CREATE | `submit_proposal` | `RECORDED` | `DRIVER_UNKNOWN`, `INCOMPLETE_PROPOSAL` |
| `apply-driver-update` | PROPOSED | SUPERSEDE | `begin_run` | `COMMITTED` | `AUTHORITY_REFUSED`, `DRIVER_UPDATE_UNAVAILABLE`, `STALE_STATE`, `EFFECT_CLASS_REFUSED` |
| `list-utilities` | PROPOSED | READ | — | `DERIVED` | `HOST_UNAVAILABLE`, `UTILITY_INVENTORY_UNAVAILABLE` |
| `install-utility` | PROPOSED | CREATE | `begin_run` | `COMMITTED` | `AUTHORITY_REFUSED`, `UTILITY_MANAGER_UNAVAILABLE`, `INCOMPLETE_PROPOSAL`, `EFFECT_CLASS_REFUSED` |
| `update-utility` | PROPOSED | SUPERSEDE | `begin_run` | `COMMITTED` | `AUTHORITY_REFUSED`, `UTILITY_MANAGER_UNAVAILABLE`, `UTILITY_UNKNOWN`, `EFFECT_CLASS_REFUSED` |
| `remove-utility` | PROPOSED | COUNTER | `begin_run` | `COUNTERED` | `AUTHORITY_REFUSED`, `UTILITY_MANAGER_UNAVAILABLE`, `UTILITY_UNKNOWN`, `EFFECT_CLASS_REFUSED` |
| `read-operation` | PROPOSED | READ | — | `DERIVED` | `OPERATION_UNKNOWN` |

`SPEC.md`: "No interface, adapter, worker, projection, or graph store may bypass these
transitions to change authoritative state." No Host route or adapter does today; `read-health`
touches only `RecordService.receipt`, never a kernel transition, because it changes nothing
authoritative to begin with.

## Refusal reason codes

Host-owned refusals map to the shared kernel refusal families through
`contracts/service.json`'s `local_refusals` table:

| Host-owned code | Kernel family |
| --- | --- |
| `BOOT_ID_UNAVAILABLE` | `MISSING_PRECONDITION` |
| `DRIVER_INVENTORY_UNAVAILABLE` | `UNREADABLE` |
| `DRIVER_UNKNOWN` | `MISSING_PRECONDITION` |
| `DRIVER_UPDATE_UNAVAILABLE` | `POLICY_REFUSED` |
| `HOST_BOUNDARY_UNKNOWN` | `DATA_BOUNDARY_REFUSED` |
| `HOST_READ_FAILED` | `UNREADABLE` |
| `MALFORMED_HOST_REQUEST` | `INCOMPLETE_PROPOSAL` |
| `OPERATION_UNKNOWN` | `MISSING_PRECONDITION` |
| `SCAN_UNAVAILABLE` | `POLICY_REFUSED` |
| `UTILITY_INVENTORY_UNAVAILABLE` | `UNREADABLE` |
| `UTILITY_MANAGER_UNAVAILABLE` | `POLICY_REFUSED` |
| `UTILITY_UNKNOWN` | `MISSING_PRECONDITION` |

`HOST_UNAVAILABLE` has no `local_refusals` entry of its own; `core.py` treats an adapter that
raises `HostAdapterUnavailable` as `REFUSED` directly. An adapter that raises anything else is
`FAILED` with `HOST_READ_FAILED` and the exception's type name — a fault, not a governed
refusal (`core.py: read_health`).

These are distinct from refusals the Gateway can return before Host is ever reached, evidenced
in `test_host_service.py: HostGatewayVertical`: `AUTHORITY_REFUSED` (no live grant),
`MALFORMED_REQUEST` (client supplied `actor` inside domain arguments — a Gateway-owned shape
check, not `MALFORMED_HOST_REQUEST`), and `TRANSPORT_NOT_ACTIVATED` (a declared logical
endpoint with no bound service-owned route). `services/gateway/CHARTER.md`: "Governed refusal
is distinct from operational failure. A missing grant, inactive transport, or unreachable
declared route is a refusal."

## Persistence and authority

- **Effect class.** `read-health` is `RECORD_LOCAL` (`core.py: EFFECT_CLASS`). Every declared
  mutating operation carries a wider class in `contracts/capability-offices.json`:
  `RESOURCE_CONSUMPTION` for `request-scan`, `EXTERNAL_WORLD` for `restart`, `power-off`,
  `suspend`, `apply-driver-update`, `install-utility`, `update-utility`, and `remove-utility`.
  None of the `EXTERNAL_WORLD` operations is reachable.
- **Persistence.** Every `read-health` outcome (`COMMITTED`, `REFUSED`, `FAILED`) is appended
  as one receipt through `RecordService`, Host's declared dependency on
  `record:append-preserving-journal`. `test_health_read_is_a_durable_service_owned_terminal_receipt`
  proves the returned receipt is byte-identical to `self.record.entry(receipt["entry_id"])`.
- **Authority.** The capability `read:host-health`, scoped to `host:local`, is granted through
  `ConsoleService.grant` and rechecked by the Gateway's authority callback on every dispatch —
  not cached, not inferred from actor kind (`test_host_service.py: HostGatewayVertical`).
- **Identity.** `host_id` is a configured string, `"host:local"` by default
  (`HostService.__init__`), never the OS hostname. The health schema's `additionalProperties:
  false` (`contracts/host-health.schema.json`) and the adapter's own output both carry no
  `hostname` field at all — one is tested directly
  (`test_local_adapter_matches_contract_without_disclosing_hostname`).
- **Observation.** Every `COMMITTED` `read-health` receipt carries
  `"observation_status": "UNATTESTED_ADAPTER_READING"` (`core.py`) — an explicit, self-declared
  admission that this reading is not independent observation. Host's manifest depends on
  `observation:independent-observation`; that service has a self-tested thin slice and no
  witness (`observation_service_status:
  BUILT_THIN_SLICE_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED`, `STATUS.yaml`).
- **Ports.** `contracts/service.json` declares four: `host-port`, `human-binding`,
  `model-binding`, `service-activity`. Only `host-port` has a concrete implementation
  (`adapters/host/local_host_adapter.py`, standard library only, no shell, no elevation); the
  other three are the same Gateway/Console path already proven for sibling services, not a
  Host-specific mechanism.
