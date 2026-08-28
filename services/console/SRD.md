# Console Service Requirements — Founding and Phase I

Status: `BUILT · SELF-REPORTED BY THE DRAFTING SESSION · NOT OWNER-RATIFIED`

Scoped copy of `PRD.md`'s shape for one service, per `decisions/0093-service-srd-spec-ground.md`.
This is a projection at service scope of decisions already made at root scope. It
grants the Console Service no authority over its own account of itself: `BUILT`
is what self-report produces here; `WITNESSED` requires a party that did not
write this document, and none of the entries below claim it, whatever
independent evidence is cited alongside them.

## Product outcome

Give the node's human and model operators one governed, threaded record of
what happened, what needs attention, and what is waiting on a human right —
without becoming a second authority system (`CHARTER.md` Role).

## Callers

The Console Service is not called by end users directly; its callers are the
node's own participants and the Gateway that fronts it:

- the human operator, through the Human Binding (`bindings/console/`,
  declared, not built) and today through the shipped CLI directly;
- the model operator, through the same CLI or the MCP binding
  (`bindings/mcp/`), holding the same kernel operations as the human path
  (`CHARTER.md` Human and model participation);
- `.claude/hooks/console_session.py`, host plumbing that briefs and closes a
  Claude Code session against an operator session through the CLI
  (`README.md`); it holds no standing itself;
- the Gateway Service, chartered but unbuilt, whose manifest depends on the
  Console Service owning authority grants — a default `decisions/0040` took
  rather than a boundary Bdo has settled (`STATUS.yaml`,
  `gateway_service_status`);
- the Asset Service and Proofing Service, read-only: Console reads their event
  envelopes and receipts through a declared crossing and never writes their
  state (`CHARTER.md` Integration with sibling services and the kernel, item 1);
- a later federated node, through the declared and unconfigured federation
  port (`contracts/service.json` ports; `KNOWN-GAPS.md` Federation row).

## Requirements

Same lifecycle as `PRD.md`: `OPEN → BUILT → WITNESSED → RATIFIED`. `BUILT` is
an implementation claim; `WITNESSED` requires independent evidence this
document does not itself supply; `RATIFIED` requires the declared right. Status
below reflects `contracts/service.json` operation standing and `KNOWN-GAPS.md`
as read on 2026-08-27, not an inference from charter intent.

### SVC-CONSOLE-1 · Continuity across a session boundary

Status: `BUILT`

A human operator and a model operator reach the same thread through one
transition; work posted in one session is readable in the next. Serves the
two-binding proof's human/model parity leg and `PRD.md` PROD-I-3 (Cross).

Defeating case: a human post and a model post in the same thread take
different transitions or yield irreconcilable receipts (`CHARTER.md` Defeating
cases).

### SVC-CONSOLE-2 · Addressed notification

Status: `OPEN`

An operator who is mentioned, assigned, asked for judgement, or named on a
receipt outcome receives an addressed input record naming its source address,
digest, kind, and acknowledgement. Serves PROD-I-6 (the pending-right report)
and PROD-I-3 (crossing visibility).

Defeating case: a notification cannot name its source address and digest, or
is treated as the record it points to (`CHARTER.md` Defeating cases). Not
built: `notify`, `acknowledge-notification`, and `list-notifications` are
`PROPOSED` in `contracts/service.json`; only a derived `mentions_you` flag on a
continuity read exists today (`KNOWN-GAPS.md`, Notifications row).

### SVC-CONSOLE-3 · Judgement request never blocks the node

Status: `OPEN`

A judgement request queues without blocking unrelated operation; the
conditioned operation settles `UNRESOLVED` rather than staying open
indefinitely. Serves PROD-I-6 directly.

Defeating case: a run remains open indefinitely awaiting owner judgement, or
the pending right is hidden from the owner's pending list (`CHARTER.md`
Defeating cases; `PRD.md` PROD-I-6). Not built: `request-judgement`,
`list-pending-judgement-requests`, and `show-judgement-request` are `PROPOSED`
(`KNOWN-GAPS.md`, Judgement requests row).

### SVC-CONSOLE-4 · Only a human resolves judgement

Status: `OPEN`

A judgement request is resolved only through a typed, scoped, live human
`JUDGEMENT` grant checked at the transition; a model attempt is `REFUSED`.
Serves PROD-I-5 (Typed authority) directly.

Defeating case: a machine right ratifies judgement-typed truth (`PRD.md`
PROD-I-5); `judgement-resolution.schema.json` fixes `resolver_kind` to the
constant `HUMAN`. Not built: `resolve-judgement` is `PROPOSED`
(`KNOWN-GAPS.md`, Judgement resolutions row).

### SVC-CONSOLE-5 · A setting never widens authority

Status: `OPEN`

An operator or node setting conditions projections and notification routing
only; changing it never grants capability or authority it did not already
carry. Serves PROD-I-5.

Defeating case: a setting, dashboard role, or session state widens an
authority check (`CHARTER.md` Defeating cases). Not built: `set-setting` is
`PROPOSED` (`KNOWN-GAPS.md`, Operator settings row).

### SVC-CONSOLE-6 · Projections are rebuildable and resolve to source

Status: `OPEN`

A dashboard or activity view is a declared projection over receipts, events,
standing, and judgement spend, naming its source addresses and its omissions;
rebuilding it twice from the same records yields the same result. Serves
`SPEC.md`'s Projection rule and, for the activity view, PROD-I-4 (Gate and
retract: the surface from which an operator on the loop counters an effective
record).

Defeating case: a dashboard or activity value does not resolve to an
authoritative record, two rebuilds differ, or an activity entry appears for an
unconfigured node or service without a declared omission (`CHARTER.md`
Defeating cases). Not built: `rebuild-projection` is `PROPOSED`
(`KNOWN-GAPS.md`, Dashboards and activity views row); the console exposes no
`retract` operation at all (`KNOWN-GAPS.md`, Retraction row).

### SVC-CONSOLE-7 · Unconfigured effects refuse visibly

Status: `OPEN`

External delivery of a notification and cross-node activity refuse as
`UNCONFIGURED` with a receipt until a separate decision admits the effect;
neither is ever reported as silent success or a silent drop. Grounded in
`SPEC.md` Local operation and `contracts/service.json` forbids
(`silent-notification-drop`).

Defeating case: external delivery is reported as success instead of
`UNCONFIGURED` (`CHARTER.md` Defeating cases). Not built: the `delivery` and
`federation` ports are declared and unconfigured; no code path has exercised
the refusal (`KNOWN-GAPS.md`, Federation row).

### SVC-CONSOLE-8 · A declared authority requirement is an enforced one

Status: `OPEN`, narrowly

Every `BUILT` operation checks the authority `contracts/capability-offices.json`
declares for it, not merely declares it. Serves PROD-I-5 and `GROUND-003`
(authority is granted, never acquired).

Defeating case, historically true: nine `BUILT` console operations — `grant`
and `revoke` among them — declared a required authority and checked nothing,
so any caller reaching the service could write itself a grant
(`STATUS.yaml`, `console_built_operations_enforcing_no_authority: 9`, dated
2026-08-24). Guarded on Bdo's 2026-08-25 ruling
(`services/console/contracts/service.json` note; commit `6dfe27c`). An
independent observation not authored by the builder re-drove all 15 `BUILT`
operations ungranted and granted on fresh stores and reproduced that every one
now refuses `NO_LIVE_GRANT` ungranted and admits on the exact declared grant
(`services/console/observations/pr-118-final.json`, claim
`2-four-operations-gained-live-matching-grant`, verdict `REPRODUCED`). That
same independent observation dissents from the broader claim that every
*declared precondition* is enforced: `session_live` is declared on eleven
operations and checked on the CLI path by exactly one (`post`); seven
`declared_*` preconditions across five operations are satisfied by an empty
string; several declared refusal codes are never produced by the
implementation (`pr-118-final.json`, findings `NOTE-COUNT-SESSION-LIVE`,
`DECLARED-SATISFIED-BY-EMPTY-STRING`, `DECLARED-REFUSALS-NEVER-PRODUCED`).
Status here is therefore scoped to the required-authority/`live_matching_grant`
class specifically — `WITNESSED`-supporting evidence exists for that class
alone, this document does not itself claim `WITNESSED` standing for it, and
whether the manifest's `preconditions` field is a claim about enforcement or
only about logical shape is an open judgement item routed to Bdo by that same
observation, unresolved as of this drafting.

### SVC-CONSOLE-9 · Records stay scoped to the node that opened them

Status: `BUILT`, bounded

A grant minted under one node satisfies no authority check under another;
`open-thread`, `post`, and `publish-thread` answer a foreign node's record with
`FOREIGN_NODE_RECORD` once a grant has been shown, and every operation naming a
record by id checks `local_node_record`.

Defeating case: a grant minted under one node admits an operation checking a
different node's record. What keeps this from being a bypass is the
once-ever, recorded bootstrap of a node's permits office, not an attested node
identity — no Identity Service exists, and `node_id` is asserted by whichever
process opens the service, not verified (`KNOWN-GAPS.md`, "Node identity is
asserted, not attested" row). Bounded because node names are unbounded and the
two declared refusal codes for "record absent" and "record present under a
foreign node" differ, which is a working existence oracle across nodes on the
same row.

## Non-goals for Phase I

Carried forward from `PRD.md` where they name this service directly, plus
service-scoped additions from `CHARTER.md`:

- a graphical production interface — the Phase-I Console is a local operator
  console proving parity and judgement accounting, not a production GUI claim
  (`CHARTER.md` Relationship to Phase-I requirements; `PRD.md` Non-goals);
- automated external-world effects — external delivery and cross-node
  activity stay refused until separately admitted (`CHARTER.md` item 7);
- distributed consensus or federation — the federation port is declared and
  unconfigured, not implemented (`PRD.md` Non-goals; `CHARTER.md` Deferred);
- real-time presence and cursors, reactions, voice or video, external
  chat-platform bridges, email and push delivery, public share links beyond
  the built `publication` record, role hierarchies beyond typed scoped grants
  (`CHARTER.md` Deferred);
- holding, inferring, or delegating authority: the console surfaces pending
  rights and spent judgement; the kernel keeps authority (`CHARTER.md` Role;
  `CHARTER.md` Integration, closing sentence). Whether the console's own
  `grant`/`revoke` operations already make it the de facto issuing point for
  authority in the running system, in tension with that sentence, is named as
  an open custody question in `JOURNEYS.md` rather than settled here.
