# Host Service Journeys

Status: `BUILT` (drafted under `decisions/0067-service-srd-spec-ground.md`; self-report only)

This document has no analog in the root pattern (`decisions/0067`). It enumerates the abstract
journeys a caller takes through the Host Service — `discover → authority-check → invoke →
receipt → provenance`, the shape `services/host/README.md` already draws as
`Human or Model Binding -> Node Interface -> Gateway -> Host Service -> Host Port` — and states
plainly, per journey, whether it completes or dead-ends, citing the charter or `KNOWN-GAPS.md`
standing that makes it so.

Naming an open question in this document does not assign, resolve, or make it Host's to
decide (`decisions/0067`, What this is not). It routes to a decision record the ordinary way.

## Journey: read the execution host — `sov://host/read-health`

**COMPLETES.** `host_service_status` in `STATUS.yaml`:
`BUILT_READ_HEALTH_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED`.

1. **Discover.** `services/host/README.md` gives the discovery command:
   `python scripts/sov_interface.py show host.read-health --binding MODEL`. (Whether this
   operation also surfaces through `console.discover-operations`, the capability projection
   `STATUS.yaml`'s `discovery_surface_status` describes, is not checked here — named as
   unverified rather than assumed.)
2. **Authority-check.** The Gateway requires a live `read:host-health` grant scoped to
   `host:local`. `test_missing_grant_refuses_before_the_adapter` proves an ungranted actor is
   refused `AUTHORITY_REFUSED` with the adapter never called (`adapter.calls == 0`). A grant is
   issued through `ConsoleService.grant(actor, "read:host-health", "host:local", "Bdo")` and
   rechecked on every dispatch, not cached — proven for both an `actor_kind` of `HUMAN` and one
   of `MODEL` in `test_human_and_model_use_same_route_and_service_receipt`.
3. **Invoke.** The Gateway resolves the logical endpoint, confirms a bound service-owned route
   exists (`HostRoutes.OPERATIONS = ("read-health",)`), and calls `HostRoutes.call`, which
   refuses `MALFORMED_HOST_REQUEST` if the caller supplied any domain argument at all — the
   contract for this operation declares zero required and zero optional arguments
   (`routes.py`). `HostService.read_health` then calls the injected adapter.
4. **Adapter.** The standard-library adapter (`adapters/host/local_host_adapter.py`) reads
   `platform`, `os.cpu_count()`, `os.getloadavg()`, `/proc/meminfo`, `/proc/uptime`, and
   `/proc/sys/kernel/random/boot_id` — no shell execution, no privilege elevation, no
   credential of any kind.
5. **Receipt.** `HostService` validates the returned snapshot's shape defensively
   (`snapshot_defect`) rather than trusting the adapter's self-report, then emits one terminal
   receipt through `RecordService`: outcome `COMMITTED`, `host_id` the configured
   `"host:local"` identity (never the OS hostname), `observation_status`
   `"UNATTESTED_ADAPTER_READING"` (an explicit admission this reading is not independent
   observation).
6. **Provenance.** The Gateway returns that exact receipt unchanged, attributed to the checked
   actor — `test_human_and_model_use_same_route_and_service_receipt` asserts the returned
   object equals `self.record.entry(returned["entry_id"])` and carries the checked actor's
   name, not a client-supplied one (a separate test, `test_client_attribution_override_refuses_before_the_adapter`,
   proves a client-supplied `actor` argument is refused `MALFORMED_REQUEST` before the adapter
   runs at all).

This journey completes with self-tested, not independently witnessed, evidence
(`KNOWN-GAPS.md`: "Passing participant tests establishes `BUILT` evidence for `read-health`
only. It does not witness the result, ratify the service, or advance any deferred
operation.").

## Journey: request an OS restart — `sov://host/restart`

**DEAD-ENDS**, directly tested. `test_declared_restart_is_not_policy_active_or_routed` drives
the identical request shape used for `read-health` — same actor, same live grant path, only
`logical_endpoint` changed to `sov://host/restart` — and gets back `REFUSED`
`TRANSPORT_NOT_ACTIVATED`, with the adapter never called (`adapter.calls == 0`).

Where it stops: the Gateway's own route step (`services/gateway/CHARTER.md`: "route request —
require an activated transport, an admitted Phase-I effect class, and a bound service-owned
route"). `HostRoutes.OPERATIONS` names only `("read-health",)`; no route exists to bind for
`restart`. Even reaching that far assumes preconditions `contracts/service.json` also declares
and nothing satisfies: `restart_request_admitted`, `current_boot_id_matches_request`, and
`power_adapter_configured`. `KNOWN-GAPS.md` Power row: "Declared only | Explicit confirmation
policy, privilege port, effect authorization, and post-effect observation." `restart` also
carries `"effect_class": "EXTERNAL_WORLD"` in `contracts/capability-offices.json` — a wider
class than the `RECORD_LOCAL` class `read-health` is scoped to.

## Journey: request a scan — `sov://host/request-scan`

**DEAD-ENDS**, inferred rather than directly tested. No test in `services/host/tests/` drives
`sov://host/request-scan` specifically. The inference rests on the same structural fact that
produced the directly-tested `restart` result: `HostRoutes.OPERATIONS` binds only
`read-health`, and the Gateway's route step refuses `TRANSPORT_NOT_ACTIVATED` uniformly for any
logical endpoint with no bound service-owned route, regardless of which operation it names —
that refusal happens before any operation-specific code runs. `contracts/service.json`
declares preconditions nothing satisfies (`complete_operation_plan`, `scanner_adapter_configured`,
`resource_budget_available`); `KNOWN-GAPS.md` Scanning row: "Declared only | Scanner adapter,
definitions provenance, resource budget, result record, and observer."

## Journey: install a utility — `sov://host/install-utility`

**DEAD-ENDS**, inferred the same way as `request-scan` — same unbound-route structural fact,
not a dedicated test. `contracts/service.json` preconditions: `complete_operation_plan`,
`live_matching_grant`, `utility_manager_adapter_configured`, `source_provenance_declared` — none
satisfied. `KNOWN-GAPS.md` Utilities row: "Inventory and mutation operations declared only |
Package-manager adapters, source policy, dependency plan, rollback limits, and observation."
This is also the journey closest to the open custody question below: `install-utility` is one
of the operations that would need the privilege mechanism `KNOWN-GAPS.md`'s Privilege row
describes as not existing at all.

## Open custody and ownership questions

Questions this service's own boundary cannot answer — named rather than silently absorbed or
silently answered by inventing an owner (`decisions/0067`).

1. **Who custodies the credential a future privilege broker would need?** `KNOWN-GAPS.md`'s
   Privilege row calls for "a typed, least-privilege mechanism that consumes SOV authorization
   without becoming authority" — but every mutating operation Host declares (`restart`,
   `power-off`, `suspend`, `apply-driver-update`, `install-utility`, `update-utility`,
   `remove-utility`) would still need *some* credential or token to actually reach the OS
   mechanism underneath: a service-manager token, a package-manager auth, a sudo-equivalent.
   `CHARTER.md` and `KNOWN-GAPS.md` refuse letting that credential *become authority* — the
   defeating case is explicit — but neither says who *holds* it operationally once it exists,
   nor where. Today the question does not arise because the built adapter
   (`adapters/host/local_host_adapter.py`) touches no credential of any kind; it is read-only
   standard library. `AGENTS.md` Secrets and local boundaries states general rules for whoever
   ends up holding such a credential (never commit it, never log it, never expose it in a
   receipt) but does not name Host, an adapter, or any other participant as that holder. This
   is stated as open rather than assumed either way.
2. **Who owns the trigger-time and leased-execution dependencies Host's own manifest names?**
   `contracts/service.json` lists `automation:trigger-time` and `runtime:leased-execution`
   under `depends_on`. Neither `automation` nor `runtime` exists as a directory or a chartered
   service anywhere in this repository (`ls services/` lists `asset`, `console`, `gateway`,
   `host`, `identity`, `observation`, `projection`, `proofing`, `record`, `registry` only).
   `CHARTER.md` is confident about the division of labor in prose — "Automation owns *when* a
   restart or scan is requested; the Host Service owns whether the requested effect is
   admissible and how it is attempted" — but nothing in this repository currently holds either
   role, chartered or built. Until one does, the second half of SVC-HOST-GROUND-7's claim
   (independent post-effect observation, not the executor's report) also has no service
   positioned to supply the observation.
3. **Who verifies source provenance for a driver or utility update?** `propose-driver-update`
   requires `source_provenance_declared`; `apply-driver-update` requires
   `source_digest_verified`; `install-utility` and `update-utility` require
   `source_provenance_declared`. `KNOWN-GAPS.md`'s Drivers row names "signed-source policy" as
   part of the remaining boundary. No document read for this exercise names which participant
   holds the trust root a signed-source policy would verify against — the same shape of
   question as (1), one layer removed from credential custody into provenance custody.
