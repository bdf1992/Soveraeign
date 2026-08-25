# Host Service Reference Gaps

The service has one built, read-only vertical. These rows are residuals, not implied
capabilities.

| Area | Built now | Remaining boundary |
| --- | --- | --- |
| Health | Normalized local execution-host reading through an injected Host Port | Independent observation and platform-specific adapters beyond the standard-library baseline |
| Host identity | Stable configured `host:local` service identity; optional OS boot id | Registration and reconciliation of multiple physical, virtual, and container hosts |
| Network | Declared only | Interface inventory, counters, change observation, and privacy policy |
| Scanning | Declared only | Scanner adapter, definitions provenance, resource budget, result record, and observer |
| Restart schedule | Host request/effect boundary declared only | Automation owns timing; Runtime/Worker owns leased execution; Observation confirms a changed boot id |
| Power | Declared only | Explicit confirmation policy, privilege port, effect authorization, and post-effect observation |
| Drivers | Inventory and update operations declared only | Platform adapters, signed-source policy, compatibility plan, rollback limits, and observation |
| Utilities | Inventory and mutation operations declared only | Package-manager adapters, source policy, dependency plan, rollback limits, and observation |
| Privilege | No broker exists | A typed, least-privilege mechanism that consumes SOV authorization without becoming authority |
| Transport | In-process `read-health` only | No HTTP, remote agent, or arbitrary-shell transport is admitted |

Passing participant tests establishes `BUILT` evidence for `read-health` only. It does
not witness the result, ratify the service, or advance any deferred operation.
