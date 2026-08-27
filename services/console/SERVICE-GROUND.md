# Console Service Ground

Status: `BUILT · SELF-REPORTED BY THE DRAFTING SESSION · NOT OWNER-RATIFIED`

Scoped copy of `GROUND.md`'s shape for one service, per
`decisions/0067-service-srd-spec-ground.md`. Not forced to sixteen claims.
Each claim is what this service commits to always being true for its caller;
each names what would defeat it and, where the underlying operation is not
yet built, says so instead of implying the commitment is already kept.

### `SVC-GROUND-1` — a judgement request never blocks the node

> An operation whose required authority is `JUDGEMENT` and has no live grant
> settles `UNRESOLVED` and queues a request; unrelated operation keeps running.

Specializes `GROUND-012` (human judgement is reserved and scarce).

*Defeated by.* A run left open indefinitely awaiting owner judgement, or a
pending right absent from the owner's pending list (`CHARTER.md` Defeating
cases; fixture `CONS-001`). *Current reality:* `request-judgement` is
`PROPOSED`, not built (`contracts/service.json`); this is a declared
commitment the running system does not yet keep.

### `SVC-GROUND-2` — only a human resolves judgement

> A model may draft a recommendation into a thread; only a human holding a
> live `JUDGEMENT` grant may resolve a judgement request.

Specializes `GROUND-003` (authority is granted, never acquired) and `PRD.md`
PROD-I-5.

*Defeated by.* A model resolution attempt that is not `REFUSED`
(`judgement-resolution.schema.json` fixes `resolver_kind` to `HUMAN`; fixture
`CONS-002`). *Current reality:* `resolve-judgement` is `PROPOSED`, not built;
the constraint exists in schema and fixture, not yet in a running check.

### `SVC-GROUND-3` — a declared authority requirement is checked, for the class it names

> A `BUILT` operation that declares a required authority type refuses a
> caller with no matching live grant and admits one who holds it.

Specializes `GROUND-003`.

*Defeated by.* A `BUILT` operation that declares an authority and checks none
— true of nine console operations, `grant` and `revoke` among them, until
Bdo's 2026-08-25 ruling (`STATUS.yaml`,
`console_built_operations_enforcing_no_authority: 9`). Repaired for all
fifteen `BUILT` operations and independently reproduced
(`services/console/observations/pr-118-final.json`, claim
`2-four-operations-gained-live-matching-grant`, `REPRODUCED`). *Scope of the
claim, stated deliberately narrow:* it covers `required_authority` and
`live_matching_grant` only. It does not extend to every declared
`precondition` — the same observation dissents that `session_live` is
declared on eleven operations and enforced on the CLI path by one, and that
several `declared_*` preconditions are satisfied by an empty string
(`pr-118-final.json`, findings `NOTE-COUNT-SESSION-LIVE`,
`DECLARED-SATISFIED-BY-EMPTY-STRING`). Whether `preconditions` means
"enforced" or "logical shape" is an open judgement item that observation
routes to Bdo, unresolved as of this drafting.

### `SVC-GROUND-4` — an operator setting never widens authority

> Changing a setting changes projections and notification routing; it never
> grants a capability or scope the holder did not already carry.

Specializes `GROUND-003`.

*Defeated by.* A setting, dashboard role, or session state that widens an
authority check (`CHARTER.md` Defeating cases; fixture `CONS-003`). *Current
reality:* `set-setting` is `PROPOSED`, not built.

### `SVC-GROUND-5` — correction is a new record, not an erasure

> A post, notification, or judgement request is never rewritten or deleted;
> a correction lands as a new record or a counter-record, and the original
> stays visible.

Specializes `GROUND-009` (correction never erases occurrence) and `PRD.md`
PROD-I-4.

*Defeated by.* A post, notification, or request rewritten or erased instead of
countered (`CHARTER.md` Defeating cases). *Current reality:* the Record
Service journal this rests on is append-preserving and self-tested; the
console itself exposes no `retract` operation yet, so the counter-record half
of this claim has no built path through the console today
(`KNOWN-GAPS.md`, Retraction row).

### `SVC-GROUND-6` — a projection resolves to the record it names, twice

> Rebuilding the same dashboard or activity view from the same authoritative
> records twice yields the same result, and every value on it traces to a
> source address.

Specializes `SPEC.md`'s Projection rule and, loosely, `GROUND-011` (standing
does not collapse).

*Defeated by.* Two rebuilds of the same projection differing, or a value that
does not resolve to a source record (`CHARTER.md` Defeating cases; fixture
`CONS-005`). *Current reality:* `rebuild-projection` is `PROPOSED`, not built.

### `SVC-GROUND-7` — refusal is legible, not silent

> A caller told no is told the reason as a receipted refusal; an effect this
> service cannot yet honor — external delivery, cross-node activity — answers
> `UNCONFIGURED` rather than pretending success or dropping silently.

Specializes `GROUND-008` (refusal is an outcome).

*Defeated by.* External delivery reported as success instead of
`UNCONFIGURED` (`CHARTER.md` Defeating cases; `contracts/service.json`
forbids `silent-notification-drop`). *Current reality:* the `delivery` and
`federation` ports are declared and unconfigured; the refusal path is
asserted, not yet exercised by a built operation (`KNOWN-GAPS.md`, Federation
row).

### `SVC-GROUND-8` — a record stays scoped to the node that opened it

> A grant minted under one node admits nothing against another node's record;
> every operation that names a record checks it belongs to this node.

Specializes `GROUND-002` (one governed world) at node granularity.

*Defeated by.* `FOREIGN_NODE_RECORD` failing to fire on a peer's record once a
grant has been shown. *Bound, not unconditional:* this rests on the once-ever
recorded bootstrap of a node's permits office, not on an attested node
identity — `node_id` is asserted by whichever process opens the service, and
no Identity service verifies it (`KNOWN-GAPS.md`, "Node identity is asserted,
not attested" row, which also names a working cross-node existence oracle:
`UNKNOWN_RECORD` and `FOREIGN_NODE_RECORD` differ, and node names are
unbounded).

### `SVC-GROUND-9` — an observation of this service is not this service's own report

> Whatever verifies a claim about console behavior does so by driving the
> shipped CLI or reading the journal directly, not by taking the builder's
> commit message, test output, or manifest prose as evidence.

Specializes `GROUND-010` (a report is not an observation).

*Defeated by.* A standing claim resting only on the participant's own test
suite or its manifest `note` field. *Current reality, both directions
present:* `services/console/tests/` is the builder's own suite and settles
nothing beyond `BUILT`; the two independent observations under
`services/console/observations/` (`pr-118-console-authority.json`,
`pr-118-final.json`) are evidence of the kind this claim asks for, and one of
them dissents from three factual statements in the manifest `note` that the
builder wrote about its own file (`pr-118-final.json`, findings
`NOTE-COUNT-SESSION-LIVE`, `NOTE-STATES-NO-COUNTS`,
`NOTE-BUILT-OPERATIONS-LIST`) — a live instance of a build's self-report
being wrong about itself, caught by exactly the mechanism this claim commits
to.
