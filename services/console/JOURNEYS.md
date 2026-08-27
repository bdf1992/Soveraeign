# Console Service Journeys

Status: `BUILT · SELF-REPORTED BY THE DRAFTING SESSION · NOT OWNER-RATIFIED`

Per `decisions/0093-service-srd-spec-ground.md`, this document has no root-level
analog: it enumerates the abstract journeys a caller takes through the Console
Service and states, per journey, whether it completes or dead-ends, citing the
charter and `KNOWN-GAPS.md` standing that makes it so. Naming an open custody
question below does not assign, resolve, or answer it; it routes to a decision
record at whichever tier `STATUS.yaml`'s `resolution_rule` names.

Five operator surfaces are named in `CHARTER.md`; `README.md` and
`KNOWN-GAPS.md` treat continuity itself as the one of the five that is built
("Five of the `CHARTER.md` operator surfaces are named there; one of them
exists"), with `KNOWN-GAPS.md`'s gap table folding the charter's separate
"dashboards" and "activity reporting" items into one row. This document
follows that same five-way grouping rather than the charter Role section's raw
count of five *un-built* items, so the two documents describe the same
service the same way.

## Journey 1 — Continuity: carry work across a session boundary

**Path.** `open-session` → `open-channel` → `open-thread` (optionally pinned to
an exact operation, record, or asset version address) → `post` (human and
model actors in the same thread) → close the session → open a new session
later → `read-thread` reads the same posts; `session-context` reports the
`active_thread_id` and `unread_cursor` carried across the boundary.

**Verdict: COMPLETES.** All seven operations in this path are `BUILT`
(`contracts/service.json`); the built slice is self-tested (thirty-one cases,
`README.md`) and `services/console/tests/test_operator_continuity.py` and
`test_cli_walk.py` drive it end to end. `.claude/hooks/console_session.py`
runs exactly this path as host plumbing to brief and close a Claude Code
session.

**Qualifications, not dead ends.** Completion here means the transitions
commit and the read is stable across a restart, not that every actor claim
about the transition is sound:

- `channel and thread reads` only replay the whole journal per call; there is
  no bounded channel-listing operation (`KNOWN-GAPS.md`, "Channel and thread
  reads" row; `list-channels` is `PROPOSED`).
- The actor posting is an unauthenticated string. `ACTOR_ATTRIBUTION_MISMATCH`
  compares two strings the same caller typed, and a caller can grant itself
  read or post access to a private thread it does not own with declared
  operations alone (`KNOWN-GAPS.md`, Identity row; walked and reproduced in
  `services/console/observations/pr-118-console-authority.json`, claim `4`).
- Two concurrent writers against the same store can break the journal's digest
  chain or let a `COMMITTED` receipt cite a grant a concurrent writer revoked
  moments earlier (`KNOWN-GAPS.md`, "Two writers on one store" row).

**Adjunct: publish a thread publicly.** `publish-thread` → `withdraw-publication`
→ `list-publications` are also `BUILT` and exercise the same continuity
substrate for the `publication` record (`PUBLIC` visibility only). Folded into
this journey because `CHARTER.md`'s prose list of owned records and its five
named surfaces do not mention `publication` at all, even though
`contracts/service.json` owns it and `STATUS.yaml`'s `public_projection_status`
tracks it as a distinct, seat-seam-open concern. Where this adjunct belongs is
named as an open question below.

## Journey 2 — Notifications: find out you were mentioned

**Path.** A model posts in a thread mentioning a human operator → the console
emits a `SYSTEM`-actor `notification` event naming `MENTION` and the post's
source address and digest → the operator's `list-notifications` shows it →
`acknowledge-notification` marks it read.

**Verdict: DEAD-ENDS-AT-NOTIFICATIONS.** `notify`, `acknowledge-notification`,
and `list-notifications` are all `PROPOSED`, not built (`contracts/service.json`;
`KNOWN-GAPS.md`, Notifications row). The only thing reachable today is a
derived `mentions_you` flag surfaced when reading continuity — not an
addressed input record with a source address, digest, kind, or acknowledgement.
Fixture `CONS-004` (`004-notification-resolves-to-source.yaml`) states the
target shape; nothing in `services/console/src` implements it.

## Journey 3 — Judgement: the owner's judgement surface

**Path (reach).** A model attempts an operation whose required authority is
`JUDGEMENT` and no live grant covers it → `request-judgement` records the
question as a kernel `Proposal` and the conditioned operation receives an
`UNRESOLVED` receipt, while unrelated operation keeps running → a
`JUDGEMENT_REQUESTED` notification addressed to the owner is issued →
`list-pending-judgement-requests` shows it on the owner's pending list.
**Path (answer).** The owner invokes `resolve-judgement` under a live
`JUDGEMENT` grant, realized as the kernel `ratify` transition. **Path (land).**
A `judgement-resolution` record carries the resolver, the grant checked, the
decision, and the receipt; its standing reaches `RATIFIED` only by an appended
event; the conditioned operation's successor receipt names the answered
`UNRESOLVED` receipt via `prior_receipt_id`.

**Verdict: DEAD-ENDS-AT-JUDGEMENT.** `request-judgement`,
`list-pending-judgement-requests`, `show-judgement-request`, and
`resolve-judgement` are all `PROPOSED` (`contracts/service.json`;
`KNOWN-GAPS.md`, Judgement requests and Judgement resolutions rows). This is
the slice `CHARTER.md` names first ("First slice: the owner's judgement
surface") and `README.md` explains was *not* built first — the continuity path
came first instead — and gates it behind four preconditions: the logical
specification frozen or provisionally authorized, executable console-specific
fixtures, a stable sibling read path, and Bdo authorizing a provisional Human
Binding target (`README.md`, "Judgement surface (proposed, not built)").
Fixtures `CONS-001`, `CONS-002`, `CONS-008`, and `CONS-009` state the target
shape; none is satisfied by a running implementation.

## Journey 4 — Operator settings: change a preference without changing a right

**Path.** An operator invokes `set-setting` with a scoped key and value →
the setting conditions future notification routing or projection defaults →
an unrelated authority check is unaffected by the change.

**Verdict: DEAD-ENDS-AT-SETTINGS.** `set-setting` is `PROPOSED`
(`contracts/service.json`; `KNOWN-GAPS.md`, Operator settings row). Fixture
`CONS-003` (`003-setting-cannot-widen-authority.yaml`) states the target
invariant; nothing built exercises it.

## Journey 5 — Dashboards and activity: read and counter what happened

**Path (dashboard).** An operator holding a scoped administrative grant
invokes `rebuild-projection` for a `DASHBOARD` view → the view reports
receipts, events, standing, and judgement spend, every value traced to a
source address, `authoritative: false` declared on the view itself.
**Path (activity).** The same operation for an `ACTIVITY` view sources
sibling-service event envelopes and receipts and names its omissions → an
operator on the loop spots an effective record they disagree with and counters
it through kernel `retract`.

**Verdict: DEAD-ENDS-AT-DASHBOARDS-AND-ACTIVITY.** `rebuild-projection` is
`PROPOSED` for both view kinds (`contracts/service.json`; `KNOWN-GAPS.md`,
"Dashboards and activity views" row). The activity leg dead-ends twice over:
even where a view existed, the console exposes no `retract` operation for an
operator to act on it (`KNOWN-GAPS.md`, Retraction row), and cross-node
activity is unconditionally `UNCONFIGURED` (`KNOWN-GAPS.md`, Federation row).
Fixtures `CONS-005` and `CONS-007` state the target shape for both legs.

## Open custody and ownership questions

Named because no existing document currently owns them — not resolved,
assigned, or invented here.

1. **Does the console own who may grant or revoke authority, or does it only
   enforce grants issued elsewhere?** `CHARTER.md`'s Role section says
   "Authority stays where the kernel puts it: the Console Service surfaces
   pending rights and spent judgement; it does not hold, infer, or delegate a
   right." But `grant` and `revoke` are console operations, `authority-grant`
   is a console-owned record, and `permits.py` is the only place in the
   repository that mints or withdraws a live grant on a running node today.
   Whether the console's permits office is meant to be the node's real
   issuing authority for Phase I, or a service-local convenience that a future
   Identity or Authority-issuing mechanism should supersede, is unresolved.

2. **Who owns authenticating the caller?** Every operator is a string the
   caller types; nothing checks that the caller is the name it types, so
   `--granted-by Bdo` succeeds for anyone who types it and posting *as* Bdo
   needs nothing more than naming Bdo (`KNOWN-GAPS.md`, Identity row, walked
   and reproduced in `pr-118-console-authority.json`). `KNOWN-GAPS.md` states
   plainly that there is no Identity service (epic issue #11, unrouted and
   unbuilt) and that "any fix written here would read as closed and would not
   be." This document does not answer whether identity is the console's
   concern, the node layer's, or a service that does not yet exist; it
   restates that the row is "routed to Bdo as an authority seam rather than
   repaired."

3. **Do in-process reads that bypass every declared operation belong to this
   service's authority boundary at all?** `Projection(console).thread_posts`,
   `ConsoleService.body`, and `authority.held` return the same bytes the
   guarded CLI operations refuse, to any caller holding the service object in
   process (`KNOWN-GAPS.md`, "Guarded entry points, unguarded data" row).
   `contracts/capability-offices.json` declares no authority for them, and
   `KNOWN-GAPS.md` itself states the reason this is not answered here:
   inventing a capability for them "would either make that capability's
   authority unanswerable... or mint policy the owner seat has not ruled on."
   Named again here as the same open question, not a new one.

4. **Does the console's node-scoping rest on anything besides a one-time
   bootstrap default?** `node_id` is asserted by whichever process opens the
   service; no Identity service or crossing attests it. The bootstrap default
   — the first caller to name a node's permits office takes it — is what
   currently stands between this and a bypass, and it is a default the Asset
   Service also takes, not a console-specific decision (`KNOWN-GAPS.md`,
   "Node identity is asserted, not attested" row).

5. **Does a declared `precondition` in `contracts/service.json` mean "this
   operation enforces this" or "this is this operation's logical shape"?**
   An independent observation found the console's own manifest is internally
   read both ways by different parts of the repository and asked Bdo to rule,
   because the answer changes whether ten service manifests across the
   repository — not only the console's — currently misdescribe what they
   check (`services/console/observations/pr-118-final.json`, `judgement_items`).
   This bears directly on how much trust Journey 1's "COMPLETES" verdict above
   can carry: completion there is graded against what the manifest declares,
   and this question is about whether that declaration is a promise or a
   description.

6. **Who owns closing the two-writer race the console cannot close from
   inside itself?** `KNOWN-GAPS.md`'s "Two writers on one store" row states
   the repair — a read-and-append the Record Service performs as one
   transaction, or compare-and-append against the head a check read — is
   "owed to the Record Service, not to this one." Every journey above that
   depends on a `COMMITTED` receipt naming the grant that admitted it assumes
   single-writer custody of the store, which `CLAUDE.md` trap T6 already
   warns does not hold in this repository.
