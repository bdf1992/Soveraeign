# Local Host Adapter

This adapter translates the current process execution environment into the Host
Service's normalized health snapshot. It uses Python's standard library and read-only
operating-system files. It never invokes a shell, elevates privilege, mutates the host,
or grants SOV authority.

`PROCESS_EXECUTION_HOST` is an explicit boundary claim: the adapter may be running on a
physical machine, virtual machine, or inside a container, and it does not pretend to
know which physical chassis ultimately carries the process. Hostname is omitted because
it is neither required for health nor a declared Soveraeign host identity.

Fields that cannot be read portably are returned as `null` and named in
`limitations`. The Host Service decides whether a snapshot satisfies its contract and
owns every terminal receipt.
