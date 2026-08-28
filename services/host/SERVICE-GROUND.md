# Host Service Ground

Status: `BUILT` (drafted under `decisions/0093-service-srd-spec-ground.md`; self-report only)

A short list of claims this service commits to always being true for its caller — not forced
to sixteen, per `decisions/0067`. Each names what would defeat it, and cites the root
`GROUND-<nnn>` claim it specializes where one applies. Naming a claim here does not make it
true today; several are aspirational for the fourteen `PROPOSED` operations and say so.

### SVC-HOST-GROUND-1 — An OS credential never becomes Soveraeign authority through Host

However a caller reaches the Host boundary, no administrator account, root token, service
manager, or package-manager ACL is ever accepted as a live grant. Specializes `GROUND-003`
(authority is granted, never acquired).

What would defeat it: an admin account, root token, or OS-level ACL treated as a live grant
anywhere in the `read-health` path today, or in any future host-operation path
(`CHARTER.md` Defeating cases, verbatim: "an OS credential is accepted as SOV authority").

### SVC-HOST-GROUND-2 — The declared boundary is the process execution host, never silently claimed as the physical machine

`boundary` is an exact declared value (`PROCESS_EXECUTION_HOST`), checked against the
adapter's own output rather than assumed. Specializes `GROUND-005` (a consequential act binds
to exact state; coincidence of value is never treated as identity).

What would defeat it: "the adapter reports a container or process boundary as the physical
host" (`CHARTER.md` Defeating cases, verbatim), or a spoofed `boundary` field being accepted
instead of refused `HOST_BOUNDARY_UNKNOWN`.

### SVC-HOST-GROUND-3 — An unsupported reading is declared missing, never fabricated

A field the adapter cannot read is `null` and named in `limitations`. No root `GROUND` claim
maps cleanly to this one; it is a service-local elaboration of the general discipline in
`GROUND-005` that what is recorded is exact observed state, not invented state.

What would defeat it: a `null` field silently replaced by a guessed or default value instead
of appearing in `limitations`.

### SVC-HOST-GROUND-4 — Every crossing leaves a durable, actor-attributed receipt, success or refusal alike

`read-health` never returns without a corresponding entry recoverable from the Record
Service's journal, whether the outcome is `COMMITTED`, `REFUSED`, or `FAILED`. Specializes
`GROUND-007` (every crossing leaves a record) and `GROUND-008` (refusal is an outcome).

What would defeat it: a `read-health` call — of any outcome — completing without a receipt
recoverable through `self.record.entry(receipt["entry_id"])`.

### SVC-HOST-GROUND-5 — Actor kind alone never substitutes for a live grant

A Human or Model caller reaches the adapter only because a live `read:host-health` grant
covering the exact requested scope was checked on that dispatch — never because of who or
what kind of actor it is. Specializes `GROUND-002` (one governed world, same authority checks
for people and models) and `GROUND-003`.

What would defeat it: "a caller reaches the adapter around the Gateway or live grant check"
(`CHARTER.md` Defeating cases, verbatim).

### SVC-HOST-GROUND-6 — A raw adapter diagnostic never reaches a receipt, log, or caller

An adapter's exception text — which could carry a path, token, or credential fragment — never
appears in a `REFUSED` or `FAILED` receipt; only a typed reason code and, for a fault, the
exception's type name do. No root `GROUND` claim names this directly; it is drawn from
`AGENTS.md` Secrets and local boundaries rather than a numbered claim.

What would defeat it: a raw adapter exception message surfacing in a receipt, a log, or an
exception visible to the caller (directly tested in `test_host_service.py` against a marker
credential-shaped string).

### SVC-HOST-GROUND-7 — A mutating host effect never settles on the executor's own report

Aspirational: no mutating operation is reachable yet. Once one is, its terminal `COMMITTED`
outcome must depend on an independent post-effect observation — for restart, a changed boot
id — never on the executor's return alone. Specializes `GROUND-010` (a report is not an
observation).

What would defeat it: "a restart executor report settles the restart without a changed boot-id
observation" (`CHARTER.md` Defeating cases, verbatim).
