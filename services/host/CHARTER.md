# Host Service Charter

Standing: `BUILT` participant with one bounded `read-health` operation. Every
mutating host operation remains `PROPOSED` and unreachable.

## Role in Soveraeign

The Host Service owns the node's governed view of operating-system state and the
lifecycle of requested host work. It is the only service allowed to turn an admitted
Soveraeign host operation into a call through a Host Port.

The service does not acquire authority from an administrator account, root token,
service manager, package manager, or operating-system ACL. Those are mechanisms on the
far side of the port. Human, Model, and later System callers still enter through the
same Node Interface and Gateway, and every call requires a live SOV grant for its exact
capability and scope.

## First slice

`sov://host/read-health` reads the execution host through an injected adapter and
returns a Host-owned terminal receipt. The current standard-library adapter reports
the process execution boundary, not an assumed physical machine. It does not execute a
shell command, elevate privilege, change host state, or expose the host name.

The receipt carries a normalized snapshot with platform, processor, memory, uptime,
and boot identity fields. Unsupported fields are `null` and named in `limitations`;
they are never silently invented. Adapter absence and malformed boundary identity are
service-owned refusals. An unexpected adapter fault is a service-owned failure. The
Gateway returns each terminal receipt unchanged.

Human and Model bindings discover and invoke the same operation record. Actor-kind
admission is not a grant: the Gateway rechecks `read:host-health` against the requested
scope on every dispatch.

## Declared surface

The manifest also declares network reading, scanning, restart requests, restart,
power-off, suspend, driver inventory and updates, and utility inventory and changes.
They are topology only. No adapter method, route, transport, or policy-active endpoint
exists for them yet.

Scheduling is not Host Service state. The Automation Service owns *when* a restart or
scan is requested; the Host Service owns whether the requested effect is admissible and
how it is attempted. A future restart is two-phase: record the pre-restart boot id and
request, then settle only after an independent post-boot observation sees a different
boot id. An executor return cannot establish that a restart occurred.

## Owned records

- `host-health` — one normalized reading of the adapter's execution boundary;
- `network-state` — a future normalized network reading;
- `driver-inventory` — a future inventory of driver identity and version;
- `utility-inventory` — a future inventory of managed utilities;
- `host-operation` — a requested or attempted scan, restart, power, driver, or utility
  operation with its operation plan and lifecycle;
- `host-receipt` — the terminal receipt for a Host Service operation.

## Defeating cases

- an OS credential is accepted as SOV authority;
- a caller reaches the adapter around the Gateway or live grant check;
- a client supplies actor attribution inside domain arguments;
- the adapter reports a container or process boundary as the physical host;
- unsupported health fields are fabricated instead of declared unavailable;
- a shell command or arbitrary command string becomes a host operation;
- a mutating declared operation becomes reachable because an adapter implements it;
- a restart executor report settles the restart without a changed boot-id observation;
- a scheduled restart makes Automation the owner of the host effect;
- adapter loss removes the Node's record, authority, or non-host operation.

## Deferred

Network monitoring, malware and integrity scanning, restart execution, power
management, driver changes, utility management, privilege brokerage, and every remote
host transport remain deferred. Each advances through contract, positive and defeating
fixtures, adapter capability, policy activation, exact route, and independent
observation; registration alone opens none of them.
