# Identity Service — Ground

Status: `BUILT` — self-reported by the drafting session under `decisions/0067`;
not witnessed. A short list of claims this service commits to always being
true for its caller, not forced to sixteen. Named `SERVICE-GROUND.md`, not
`GROUND.md`: the root document owns that name.

### `SVC-IDENTITY-GROUND-1` — a token or secret exists in exactly one place

> A minted token or an enrolled recovery secret is returned to the caller
> exactly once, as a plain value. Every record this service holds or emits
> afterward carries only its digest.

*What would defeat it.* Any record in `Challenges.records`,
`Recovery.records`, a held `Challenge`, or a held `RecoverySet` is found to
carry a plain token or secret rather than a digest. Pinned by
`test_no_record_ever_carries_a_token` and `test_no_record_ever_carries_a_secret`,
which read every emitted and every held record back and fail on a match.

No root `GROUND-<nnn>` claim specializes this directly; the nearest governing
text is `AGENTS.md` Secrets and local boundaries ("Never print secrets or raw
credentials in logs, receipts, exceptions, prompts, fixtures, or test
snapshots").

### `SVC-IDENTITY-GROUND-2` — verification is never authority

> Reaching `VERIFIED` — by presenting a live challenge or redeeming a
> recovery secret — never itself permits a consequential transition. It only
> ever changes what an identity claim says about itself.

*What would defeat it.* Any code path inside this service, or any caller
observed relying on this service, treats a presentation or a redemption
result as sufficient on its own to proceed with a consequential transition,
without a separate live grant check.

Specializes `GROUND-003` — authority is granted, never acquired. Grounded
also in `decisions/0048` ID-8 and `CONTRACT.md` C3.

### `SVC-IDENTITY-GROUND-3` — a challenge keeps exactly the window it declared

> A challenge verifies at most once, and only strictly inside the interval
> between its `minted_at` and its `expires_at`, compared as moments rather
> than as rendered strings.

*What would defeat it.* A token verifies a second time, or verifies at or
after its declared expiry — including the case a whole-second expiry stamp
sorts lexically after a moment a fraction past it. Pinned by
`test_a_microsecond_past_expiry_is_refused` and `test_replay_is_refused`.

Specializes `GROUND-005` — a consequential act binds to exact state.

### `SVC-IDENTITY-GROUND-4` — what may be asked is readable from the artifact, with a named exception

> A caller arriving with no briefing can find every operation, precondition,
> and declared refusal code this service names from `CHARTER.md` and
> `contracts/service.json` alone.

*What would defeat it.* An operation, a precondition, or a refusal a caller
actually encounters is absent from those two documents. `SERVICE-SPEC.md`'s
Refusal reason codes section already names five places where this currently
does not hold — a refusal the code returns and the contract does not declare
for that operation, or a refusal the contract declares and the code does not
implement — so this claim is stated with that gap named rather than
papered over.

Specializes `GROUND-006` — the node is discoverable from the artifact alone.

### `SVC-IDENTITY-GROUND-5` — every attempt is journalable, none is durable here

> Every mint, deliver, present, enroll, redeem, revoke, and unenrolled-report
> attempt — refused or committed — produces one record the caller can
> journal. This service keeps none of them beyond the life of its own
> process.

*What would defeat it.* An attempt, including a refused one, completes with
no entry appended to `.records`; or this service is found to persist a
record anywhere outside that in-memory list.

Specializes `GROUND-007` — every crossing leaves a record — with the caveat
`CHARTER.md` states plainly: "It stores nothing durably." Durable custody of
the record this service emits is undecided (`decisions/0048` judgement 3).

### `SVC-IDENTITY-GROUND-6` — revocation counters a set without erasing what happened to it

> Revoking a recovery set stops its live digests from redeeming and lets a
> fresh set be enrolled afterward. It never removes the record of what was
> already enrolled or already redeemed from that set.

*What would defeat it.* A revoked set's `spent_digests` history or its
`enrolled_at` disappears from the record, rather than the set simply
becoming unredeemable and reportable as revoked.
`test_revoked_set_returns_to_the_gap_report` and
`test_revoke_then_re_enroll` exercise this together: the set reports as
revoked, and a fresh enrollment is still possible afterward.

Specializes `GROUND-009` — correction never erases occurrence.

### `SVC-IDENTITY-GROUND-7` — a root with no live recovery is reported as terminal, not merely absent

> `report-unenrolled` does not just list a root principal with no recovery;
> it states, in the record it returns, that the gap cannot be closed by
> anyone but the root itself, because nothing sits above the root to
> re-enroll one.

*What would defeat it.* A root principal with zero remaining, unrevoked
recovery digests is missing from the report, or its entry carries the same
"recoverable by its controller" consequence text a non-root principal's
entry gets. Pinned by
`test_unenrolled_names_the_root_first_and_says_it_is_terminal`.

No root `GROUND-<nnn>` claim specializes this precisely; nearest is
`GROUND-008` (refusal is an outcome, told legibly) read alongside
`CHARTER.md`'s own framing: "the only honest handling is to say so
continuously rather than discover it at the worst possible moment." This
service says it whenever asked; it does not itself say it continuously —
see `JOURNEYS.md`'s open question on who consumes the report.
