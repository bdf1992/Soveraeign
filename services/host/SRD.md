# Host Service Requirements — Founding and Phase I

Status: `BUILT` (drafted under `decisions/0067-service-srd-spec-ground.md`; self-report by
the drafting session, not independently witnessed or ratified)

This is a service-scope projection of `PRD.md`'s shape, with the node — not a human — named
as the caller. It grants Host no authority over its own account of itself; it is `BUILT`
because a drafting session wrote it, nothing more.

## Product outcome

The Host Service gives the node one governed, single-boundary view of its own execution host,
and — once a declared mutating operation earns its route, adapter, policy, and independent
observation — a governed way to request host-level work, without ever letting an
operating-system credential become Soveraeign authority (`CHARTER.md` Role in Soveraeign;
defeating case "an OS credential is accepted as SOV authority").

## Callers

`CHARTER.md`: "Human, Model, and later System callers still enter through the same Node
Interface and Gateway, and every call requires a live SOV grant for its exact capability and
scope." Two of those three are demonstrated today: `services/host/tests/test_host_service.py`
(`HostGatewayVertical.test_human_and_model_use_same_route_and_service_receipt`) drives an
`actor_kind` of `HUMAN` and an `actor_kind` of `MODEL` through the identical
`sov://host/read-health` Gateway route and gets back the identical Host-owned receipt shape
for both. `System` is named in the charter as a later caller, not a demonstrated one; three
`host.*` capability-office entries (`request-restart`, `request-scan`, `restart`) already list
`SYSTEM` in their `actor_kinds` (`contracts/capability-offices.json`), ahead of any route that
would let a `SYSTEM` actor reach them.

No other chartered service's manifest names Host as a dependency (checked against every
`services/*/contracts/service.json` in this repository). Host's own manifest names five
services it depends on — Record, Console, Observation, Automation, Runtime — but nothing yet
depends on Host in the other direction.

## Requirement lifecycle

Same as `PRD.md`: `OPEN → BUILT → WITNESSED → RATIFIED`, a distinct artifact-standing
lifecycle from the operational record standing `SPEC.md` defines. No requirement below claims
past `BUILT`. `KNOWN-GAPS.md`: "Passing participant tests establishes `BUILT` evidence for
`read-health` only. It does not witness the result, ratify the service, or advance any
deferred operation."

## Phase-I requirements

### SVC-HOST-1 · Read the execution host without an OS credential

Standing: `BUILT` — `sov://host/read-health`, the one operation `services/host/contracts/service.json`
marks `"standing": "BUILT"`.

A Human or Model caller can read one normalized, adapter-sourced snapshot of the process
execution host and receive a durable Host-owned terminal receipt, with no administrator
account, root token, service manager, or package-manager ACL entering as authority anywhere
in the path (`CHARTER.md` Role in Soveraeign). Serves `PROD-I-3` (every declared `read-health`
operation cites it in `contracts/service.json`).

Defeating case: a read requires or accepts an OS-level credential as authority, or the crossing
completes without a durable terminal receipt.

### SVC-HOST-2 · Unsupported fields are declared absent, never fabricated

Standing: `BUILT` — enforced in `soveraeign_host_service/core.py` (`snapshot_defect`) and
proven for the standard-library adapter in
`test_local_adapter_matches_contract_without_disclosing_hostname`.

When the adapter cannot read a health field, the field is `null` and named in `limitations`
rather than invented (`CHARTER.md`: "Unsupported fields are `null` and named in `limitations`;
they are never silently invented."). Serves `PROD-I-3`'s requirement that a crossing can name
its omissions.

Defeating case: "unsupported health fields are fabricated instead of declared unavailable"
(`CHARTER.md` Defeating cases, verbatim).

### SVC-HOST-3 · Actor-kind admission is rechecked, never assumed

Standing: `BUILT` — proven by
`test_missing_grant_refuses_before_the_adapter` (`AUTHORITY_REFUSED`, adapter never called).

Human and Model bindings discover and invoke the same `read-health` operation record; the
Gateway rechecks `read:host-health` against the requested scope on every dispatch rather than
trusting actor-kind or a prior admission (`CHARTER.md`). Serves `PROD-I-3` (one record crossed
by both) and `CONTRACT.md` C1 (same world).

Defeating case: "a caller reaches the adapter around the Gateway or live grant check"
(`CHARTER.md` Defeating cases, verbatim).

### SVC-HOST-4 · No shell or arbitrary command execution enters the host boundary

Standing: `BUILT` for the reachable surface — `HostRoutes.ARGUMENTS["read-health"]` declares
zero required and zero optional arguments (`routes.py`); any argument at all refuses
`MALFORMED_HOST_REQUEST` before the adapter is called
(`test_route_has_no_domain_arguments_and_returns_terminal_refusal`). The standard-library
adapter (`adapters/host/local_host_adapter.py`) never shells out; it reads `platform`,
`os.cpu_count`, `os.getloadavg`, and two `/proc` files as text.

Defeating case: "a shell command or arbitrary command string becomes a host operation"
(`CHARTER.md` Defeating cases, verbatim).

### SVC-HOST-5 · A raw adapter diagnostic never reaches a receipt

Standing: `BUILT` — proven in `test_adapter_unavailable_is_a_refusal_not_fabricated_health`
and `test_unexpected_adapter_fault_is_a_failed_host_receipt`, both of which raise an exception
carrying a marker credential-shaped string and then assert the serialized receipt contains
neither a `diagnostic` field nor that string.

When the adapter refuses or faults, the terminal receipt records a typed `reason_code` and, for
an unexpected fault, the exception's type name only — never the adapter's raw exception text,
which could carry a path, token, or credential fragment. Grounded in `AGENTS.md` Secrets and
local boundaries ("Never print secrets or raw credentials in logs, receipts, exceptions,
prompts, fixtures, or test snapshots").

Defeating case: an adapter's raw diagnostic text appears in a `REFUSED` or `FAILED` receipt.

### SVC-HOST-6 · A requested mutating host effect settles only from independent observation

Standing: `OPEN` — no mutating operation is reachable; `restart`'s own precondition
(`current_boot_id_matches_request`) and `KNOWN-GAPS.md`'s Restart schedule row both describe
this as unbuilt ("Observation confirms a changed boot id").

Once a restart, power, driver, or utility operation becomes reachable, its terminal settlement
must come from an independent post-effect observation — for restart, a changed boot id — never
from the executor's own return. Serves `PROD-I-3`'s receipt discipline and specializes
`GROUND-010` (a report is not an observation).

Defeating case: "a restart executor report settles the restart without a changed boot-id
observation" (`CHARTER.md` Defeating cases, verbatim).

### SVC-HOST-7 · Scheduling authority stays outside Host

Standing: `OPEN` — the Automation Service Host's own manifest depends on
(`automation:trigger-time`) has no charter or directory anywhere in this repository
(`ls services/` lists no `automation`).

Host owns whether a requested effect is admissible and how it is attempted; a separate service
owns *when* a restart or scan is requested (`CHARTER.md` Declared surface).

Defeating case: "a scheduled restart makes Automation the owner of the host effect"
(`CHARTER.md` Defeating cases, verbatim) — read as Host silently absorbing timing authority
that a dependency it names, and does not itself implement, is meant to hold.

### SVC-HOST-8 · The declared mutating surface stays unreachable until each precondition is proven

Standing: `OPEN` — 14 of the 15 declared operations in `contracts/service.json` carry
`"standing": "PROPOSED"`.

Network reading, scanning, restart, power-off, suspend, driver inventory/update, and utility
inventory/change stay topology only until contract, positive and defeating fixtures, adapter
capability, policy activation, exact route, and independent observation each individually
advance them (`CHARTER.md` Deferred; `KNOWN-GAPS.md`).

Defeating case: "a mutating declared operation becomes reachable because an adapter implements
it" (`CHARTER.md` Defeating cases, verbatim).

## Non-goals for Phase I

- A privilege-brokerage mechanism, or any path by which an OS credential becomes Soveraeign
  authority (`CHARTER.md` Deferred; `KNOWN-GAPS.md` Privilege row: "No broker exists").
- Arbitrary shell or command execution as a host operation.
- Any remote host transport (`KNOWN-GAPS.md` Transport row: "In-process `read-health` only").
- Treating a process or container execution boundary as a physical machine.
- Automated external-world host effects — restart, power-off, suspend, driver changes, utility
  changes all carry `"effect_class": "EXTERNAL_WORLD"` in `contracts/capability-offices.json`
  and none is reachable in Phase I.
- Owning scheduling/trigger timing for a requested effect — named as Automation's job, not
  Host's, and Automation is not yet a chartered service in this repository.

## Phase-I exit for this service

This service's own Phase-I slice exits when every operation beyond `read-health` has a
positive and defeating fixture, a bound service-owned route, and — for every mutating
operation — an independent post-effect observation that does not depend on the executor's
report; and when the credential-custody question this document's sibling `JOURNEYS.md` names
has an assigned owner, because none of the fourteen `PROPOSED` operations can honestly advance
past declaration while that question stays open.
