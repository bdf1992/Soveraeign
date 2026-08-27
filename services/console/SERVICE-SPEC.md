# Console Service Logical Specification

Status: `BUILT · SELF-REPORTED BY THE DRAFTING SESSION · NOT OWNER-RATIFIED`

Scoped copy of `SPEC.md`'s shape for one service, per
`decisions/0093-service-srd-spec-ground.md`. This does not re-derive the
kernel: it cites `contracts/kernel-transitions.json` and
`services/console/contracts/service.json` rather than restating their rules,
and it fixes no storage, encoding, language, or transport of its own beyond
what `ENGINEERING.md` and `CHARTER.md` already name (a local CLI over a Python
API, no HTTP, no UI framework).

## Owned domain records

From `contracts/service.json` `owns` (twelve records; `CHARTER.md`'s prose
list of owned records omits `authority-grant`, `console-receipt`, and
`publication` even though the manifest declares them — a coherence gap
recorded here, not repaired by inventing charter text). Each record carries
the shared `standing` enum `RECORDED → ADMITTED → RATIFIED → EFFECTIVE`
(`SPEC.md` Historical standing) unless noted.

| Record | Schema | One line |
| --- | --- | --- |
| `authority-grant` | none checked in under `contracts/` for this record name; see `permits.py` | typed, scoped, revocable capability held by an operator at a node (`CHARTER.md` Role; `KNOWN-GAPS.md` Authority envelope row) |
| `channel` | `channel.schema.json` | named, domain-driven container for threads, scoped to `node_id` |
| `thread` | `thread.schema.json` | bounded conversation in a channel, `lifecycle` `OPEN → ARCHIVED`, optionally pinned to an exact address |
| `post` | `post.schema.json` | one attributed turn by `actor_kind` `HUMAN` or `MODEL`, content-addressed, carrying a `proposal_id` |
| `notification` | `notification.schema.json` | addressed input naming `source_address`/`source_digest`, `kind`, `lifecycle` `ISSUED → ACKNOWLEDGED`, `delivery` fixed to `LOCAL` |
| `judgement-request` | `judgement-request.schema.json` | queued request for a `JUDGEMENT`-typed right; `lifecycle` `QUEUED → RESOLVED \| WITHDRAWN \| EXPIRED`; carries `resolution_id` back-reference |
| `judgement-resolution` | `judgement-resolution.schema.json` | the answer record; `resolver_kind` fixed to `HUMAN`; the only console record expected to reach `RATIFIED`, and only by an appended event |
| `operator-setting` | `operator-setting.schema.json` | typed, scoped preference for `holder_kind` `OPERATOR` or `NODE`; `change_authority_type` `VERIFICATION` or `JUDGEMENT` |
| `projection-view` | `projection-view.schema.json` | declared `DASHBOARD` or `ACTIVITY` projection; `authoritative` is always `false`; carries source addresses, omissions, and rebuild time |
| `publication` | `publication.schema.json` | a thread's `PUBLIC` visibility state, `lifecycle` `PUBLISHED → WITHDRAWN`, scoped to `node_id` |
| `operator-session` | `operator-session.schema.json` | one operator's continuity: `lifecycle` `OPEN → CLOSED`, `active_thread_id`, `unread_cursor` |
| `console-receipt` | none checked in under `contracts/`; every operation emits one per `contracts/service.json` `commit` field | terminal outcome of one attempted transition |

## Service-local states

Proposed lifecycles from `CHARTER.md`, service policy awaiting owner
ratification and not a replacement for the shared record standing above:

```text
operator session:  OPEN → CLOSED
thread:            OPEN → ARCHIVED
judgement request: QUEUED → RESOLVED | WITHDRAWN | EXPIRED
notification:      ISSUED → ACKNOWLEDGED
publication:       PUBLISHED → WITHDRAWN   (schema-declared; CHARTER.md's
                                             lifecycle block does not list it,
                                             the same coherence gap noted above)
```

Judgement loop modes (`CHARTER.md`):

```text
IN_LOOP  the conditioned operation stays UNRESOLVED until a human right resolves it
ON_LOOP  the operation proceeds; the human watches and may counter through retraction
```

## Legal transitions

Twenty-one declared operations (`contracts/service.json`). Standing below is
the manifest's own per-operation `standing` field, read 2026-08-27; it is not
inferred from `CHARTER.md` prose. `kernel_transition` is named only where the
manifest declares it explicitly.

| Operation | Standing | Subject | CRUD | Kernel transition | Commit |
| --- | --- | --- | --- | --- | --- |
| `open-session` | `BUILT` | operator-session | CREATE | — | `COMMITTED` |
| `close-session` | `BUILT` | operator-session | SUPERSEDE | — | `COMMITTED` |
| `session-context` | `BUILT` | operator-session | READ | — | `DERIVED` |
| `open-channel` | `BUILT` | channel | CREATE | — | `COMMITTED` |
| `list-channels` | `PROPOSED` | channel | READ | — | `DERIVED` |
| `open-thread` | `BUILT` | thread | CREATE | — | `COMMITTED` |
| `archive-thread` | `BUILT` | thread | SUPERSEDE | — | `COMMITTED` |
| `read-thread` | `BUILT` | thread | READ | — | `DERIVED` |
| `post` | `BUILT` | post | CREATE | — | `COMMITTED` |
| `publish-thread` | `BUILT` | publication | CREATE | — | `COMMITTED` |
| `withdraw-publication` | `BUILT` | publication | SUPERSEDE | — | `COMMITTED` |
| `list-publications` | `BUILT` | publication | READ | — | `DERIVED` |
| `grant` | `BUILT` | authority-grant | CREATE | — | `COMMITTED` |
| `revoke` | `BUILT` | authority-grant | COUNTER | — | `COUNTERED` |
| `list-grants` | `BUILT` | authority-grant | READ | — | `DERIVED` |
| `discover-operations` | `BUILT` | operator-session | READ | — | `DERIVED` |
| `notify` | `PROPOSED` | notification | CREATE | — | `COMMITTED` |
| `acknowledge-notification` | `PROPOSED` | notification | SUPERSEDE | — | `COMMITTED` |
| `list-notifications` | `PROPOSED` | notification | READ | — | `DERIVED` |
| `request-judgement` | `PROPOSED` | judgement-request | CREATE | `submit_proposal` | `RECORDED` |
| `list-pending-judgement-requests` | `PROPOSED` | judgement-request | READ | — | `DERIVED` |
| `show-judgement-request` | `PROPOSED` | judgement-request | READ | — | `DERIVED` |
| `resolve-judgement` | `PROPOSED` | judgement-resolution | CREATE | `ratify` | `EFFECTIVE` |
| `set-setting` | `PROPOSED` | operator-setting | SUPERSEDE | — | `COMMITTED` |
| `rebuild-projection` | `PROPOSED` | projection-view | REBUILD | — | `REBUILT` |
| `show-receipt` | `PROPOSED` | console-receipt | READ | — | `DERIVED` |

`request-judgement` realizes `SPEC.md`'s `submit_proposal` row: the request's
question enters as the kernel `Proposal`, and it must be `ADMITTED` before
`ratify` runs; whether admission happens inside `request-judgement` or through
a separate `admit` transition is open, tracked by fixture `CONS-009`
(`judgement-request.schema.json` description). `resolve-judgement` realizes
`ratify`: preconditions are `judgement_request_recorded`, `human_actor`,
`live_matching_grant`; refusals are `AUTHORITY_REFUSED` or `STALE_STATE`,
matching the kernel row exactly (`SPEC.md` Transition contract).

No operation here bypasses those kernel transitions to change authoritative
state (`SPEC.md`, "No interface, adapter, worker, projection, or graph store
may bypass these transitions"); `contracts/service.json` `forbids` repeats the
same rule at service scope for ratifying on behalf of the owner and presenting
a projection as authoritative.

## Refusal reason codes

Fifteen distinct codes across the manifest's `refusals` arrays, folded to
kernel vocabulary by `local_refusals` (`contracts/service.json`):

| Service-local code | Kernel equivalent |
| --- | --- |
| `ACTOR_ATTRIBUTION_MISMATCH` | `AUTHORITY_REFUSED` |
| `CLAIM_WITHOUT_PROPOSAL` | `INCOMPLETE_PROPOSAL` |
| `FOREIGN_NODE_RECORD` | `AUTHORITY_REFUSED` |
| `MALFORMED_IDENTITY` | `MISSING_PRECONDITION` |
| `NO_LIVE_GRANT` | `AUTHORITY_REFUSED` |
| `PIN_INCOMPLETE` | `INCOMPLETE_PROPOSAL` |
| `SESSION_CLOSED` | `AUTHORITY_REFUSED` |
| `SESSION_NOT_LIVE` | `AUTHORITY_REFUSED` |
| `THREAD_ARCHIVED` | `STALE_STATE` |
| `UNKNOWN_RECORD` | `MISSING_PRECONDITION` |

`AUTHORITY_REFUSED`, `STALE_STATE`, `INCOMPLETE_PROPOSAL`, `UNREADABLE`, and
`MISSING_PRECONDITION` pass through unmapped where an operation declares them
directly (for example `discover-operations` declares `UNREADABLE`, borrowed
from the kernel's own code for an unreadable source rather than a service
synonym, per the manifest note).

An independent observation found that this table is not the whole truth of
what the shipped module *produces*: `STALE_STATE` is declared on four
operations and appears nowhere in `services/console/src`; `INCOMPLETE_PROPOSAL`
is declared on four and appears nowhere; `SESSION_NOT_LIVE` is declared on
thirteen of fifteen and produced only on the routed read, not the CLI path
(`services/console/observations/pr-118-final.json`, finding
`DECLARED-REFUSALS-NEVER-PRODUCED`). Nothing in the repository checks a
declared refusal against the implementation's ability to produce it; that gap
is reported there as belonging to the contracts domain, not repaired here.

## Persistence and authority notes

- Every record is appended to the Record Service's journal
  (`depends_on: record:append-preserving-journal`); the console keeps no
  authoritative table of its own and rebuilds reads from that journal
  (`README.md`; `CHARTER.md` Role).
- Every `BUILT` operation is required to check the authority
  `contracts/capability-offices.json` declares for it. As of commit
  `d604455`, an independent observation reproduced that all fifteen `BUILT`
  operations refuse `NO_LIVE_GRANT` ungranted and admit on the exact declared
  grant (`pr-118-final.json`, claim
  `2-four-operations-gained-live-matching-grant`). `STATUS.yaml`'s
  `console_built_operations_enforcing_no_authority: 9` field is stale against
  that repair and has not been updated; it describes the state before
  2026-08-25, not the current one — flagged here rather than silently
  corrected in a document this task does not own.
- `local_node_record` is checked on every operation that names a record by id
  (eight) plus `list-publications` and `session-context`, which name no
  record and answer from a fold already narrowed to this node
  (`contracts/service.json` note).
- Authority enforcement does not currently extend to caller identity: every
  principal is a string the caller supplies on the command line, and nothing
  checks that the caller is the name it typed (`KNOWN-GAPS.md`, Identity row).
  A grant issued to any typed name is a live grant this specification's
  `live_matching_grant` precondition will honor.
- Two writers against the same store are not serialized by this service: each
  operation reads the journal head and appends in a separate transaction from
  the Record Service, so a concurrent revocation can land between a check and
  its citing receipt, and two concurrent writers can each append against the
  same head and break the journal's digest chain (`KNOWN-GAPS.md`, "Two
  writers on one store" row). The fix is a read-and-append the Record Service
  would need to perform as one transaction, or compare-and-append against the
  head a check read; neither exists, and the gap is recorded there as owed to
  the Record Service, not closed here.
