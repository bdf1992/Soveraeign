# 0056 · The participation substrate: instance principals, work leases, budgets

Status: `PROPOSED · SLICES 1-4 BUILT, SELF-TESTED, NOT WITNESSED`

Commissioned by Bdo on 2026-08-24: make closure ownership attributable, bounded,
measurable and eventually enforceable, without changing the behavioural expectation that
is already in force. One substrate through which system agents, service agents, Sov,
personalised variants, user-authored workflows, imported and forked community agents, and
future services all participate — rather than a different kernel species for each.

The governing invariant, stated by Bdo and adopted unchanged:

> Machinery strengthens closure ownership; it does not create permission to practise it.

## The chain

```text
agent definition -> instance principal -> grant -> work lease -> budget
                 -> execution and helpers -> observations -> receipts
```

Nothing in that chain is new to this repository except the middle. Definitions already
exist as agents, skills, workflows and service manifests. Grants are `SPEC.md`'s
`AuthorityGrant`. Observations and receipts are contracts with fixtures. What was missing
is the join: a record saying *this running participant is holding this concern, under this
grant, inside this envelope, against this closure condition*.

## Sessions were already half of it

The live-session registry (`scripts/sov_session.py`, host plumbing, no standing) was built
on 2026-08-23 to stop concurrent sessions overwriting each other. Reading it against this
commission, it already implements four of the seven things the substrate needs, under
different names:

| Substrate needs | The session registry already does | What was missing |
| --- | --- | --- |
| an attributable running participant | mints a name from the host session id, inherited by every subprocess it launches | no definition, no provenance, no controller, not resolvable as an `actor_id` |
| work possessed by that participant | claims paths and resources with a holder and an intent | claims a *file*, not a *concern*; no grant, no budget, no closure condition |
| the lease running out | expiry by heartbeat silence, plus a liveness probe on the process | advisory only, and with no fence a superseded holder is not visibly superseded |
| helper invocations | nothing — a subagent inherits the parent's session id and disappears into it | no parent edge, so nobody is on the hook for a helper |

So this is not a new execution model. It is the session registry given the nouns it
lacked, sharing its store, its identity source and its liveness rule. That is why the
first four slices are small: the hard part — one append-preserving log visible from every
worktree of the repository, with a liveness rule that does not wedge on a dead process —
was already built and is already carrying six concurrent sessions.

The boundary that must not blur: a session record is host plumbing and holds no standing.
A lease carries a grant reference and a closure claim, so it is a governed record with a
contract under `contracts/`. They share storage. They do not share standing.

## What a lease is

`contracts/work-lease.schema.json` (`soveraeign-work-lease/v1`). A lease is the difference
between a ticket that has an assignee and work somebody is holding right now. It names:

- the **concern** — a referent into whatever surface owns the item, never a second copy of it;
- the **holder** — an instance principal, its relation (`PARENT`, `HELPER`, `WITNESS`), the
  lease that recruited it, the controller one step up, the host session, and the
  **definition** it derives from with that definition's **provenance**;
- the **grant** — or the honest absence of one;
- the **budget** — consumption and emission, multidimensional;
- the **closure condition** — and what evidence would show it was not met;
- a **fence**, `granted_at`, `expires_at`, and a state that distinguishes `RELEASED`,
  `EXPIRED`, `COMPLETED` and `FAILED`.

A lease grants nothing. The grant carries authority; the lease says who is on the hook and
inside what envelope. A lease with a null grant is ordinary and admissible, and reaches no
further than the local record.

## Requirements, each with the case that defeats it

`scripts/sovkernel/work_lease.py` judges these. Every one has a fixture or a test that
trips it, and `test_every_declared_refusal_code_is_reachable` fails if a declared refusal
becomes unreachable — the defect `OPEN-SEAMS.md` S17 already records once.

**WL-1 · No unattributed holder.** A recruited holder names the principal above it.
*Defeat: a helper with no controller participates anyway.* → `UNANCHORED_HOLDER`

**WL-2 · Identity is never authority.** A holder with no grant may declare no effect past
`RECORD_LOCAL`. *Defeat: a grantless lease declaring `EXTERNAL_WORLD` is accepted.*
→ refused by the contract itself

**WL-3 · A helper is subordinate.** A `HELPER` or `WITNESS` lease names a parent, and the
parent must be readable. *Defeat: an orphan helper nobody is responsible for.*
→ `HELPER_WITHOUT_PARENT`

**WL-4 · Recruiting cannot mint authority.** A child's capabilities, effect ceiling and
authority type are bounded by its parent's. *Defeat: a bounded worker manufactures an
unbounded one and calls it delegation.* → `AUTHORITY_WIDENED`

**WL-5 · A child cannot outlive its parent.** *Defeat: a helper still running after the
lease that recruited it expired.* → `LEASE_OUTLIVES_PARENT`

**WL-6 · A build cannot witness itself.** A `WITNESS` lease refuses the principal that
holds the work. *Defeat: a builder recruits itself as its own witness.*
→ `SELF_WITNESS_REFUSED` (the existing code, not a synonym)

**WL-7 · Closure stays with the parent.** A parent may not declare closure while a child
still holds part of the concern. *Defeat: recruiting help becomes a way to hand off
responsibility for closing.* → `CLOSURE_WITH_HELD_CHILD`

**WL-8 · Closure needs evidence.** *Defeat: a lease closes itself on its own say-so.*
→ `CLOSURE_WITHOUT_EVIDENCE`

**WL-9 · `WITNESSED` needs a witness.** Closure evidence claiming `WITNESSED` needs a
witness lease held by a different principal; the holder's own report reaches `BUILT`.
*Defeat: a standing claim with nothing independent behind it.*
→ `UNWITNESSED_STANDING_CLAIM`

**WL-10 · Fences supersede.** Same rule and same refusal as the kernel transition
evaluator. *Defeat: a holder that lost the lease writes behind the one that took it.*
→ `STALE_LEASE`

**WL-11 · Phase binds a lease.** *Defeat: an effect ceiling above what the phase admits.*
→ `EFFECT_CLASS_REFUSED`

## Budgets are envelopes, not throttles

The purpose Bdo stated is to give autonomy a visible operating envelope and make
pathological behaviour observable — a participant consuming heavily while producing
coordination objects and never approaching closure. So a budget bounds, and
`scripts/sovkernel/lease_budget.py` reports; it refuses nothing.

Two measurements are kept apart, because collapsing them is the error `CANON.md` was
written to prevent:

- **consumption** — `wallclock_seconds`, `tokens`, `tool_calls`, `usd`, `turns`,
  `skill_invocations`. What was spent.
- **emission** — `helper_leases`, `witness_leases`, `branches`, `pull_requests`, `issues`,
  `external_effects`. What was produced. A pull request costs nothing to hold and still
  crowds the world.

No arithmetic crosses a dimension. `pressure()` selects the worst single fraction rather
than combining them: a lease at 90% of its tokens and 5% of its wall clock is at 90%, and
adding the two would describe nothing that happened.

Four readings, none of which refuse anything:

| Reading | Means |
| --- | --- |
| `BUDGET_EXCEEDED` | a declared limit was passed |
| `UNBOUNDED_DIMENSION` | something is being drawn that no limit covers, so nothing here would notice it growing |
| `UNRECEIPTABLE_USAGE` | `turns` and `skill_invocations` can be bounded but no receipt field carries them yet |
| `COORDINATION_WITHOUT_CLOSURE` | well into the envelope, coordination objects produced, no closure evidence, lease still open |

The last one is what this was commissioned for. It is a reading and not a refusal because
some honest work genuinely looks like that; the point is that it becomes visible instead
of being discovered afterwards.

## Extensibility: one contract, not one species per participant

`holder.definition` carries `definition_kind` (`agent`, `workflow`, `skill`, `service`,
`schedule`, `human`) and `provenance` (`SYSTEM_AUTHORED`, `USER_AUTHORED`, `PERSONALIZED`,
`IMPORTED`, `FORKED`, with `derives_from` for the last three). Both are descriptive. The
admission question is:

> Can this participant satisfy the identity, grant, budget, closure and evidence contracts?

never *should this be merged into the canonical agent*. Provenance changes how a reader
weighs a participant; it changes nothing about what it may do. A large customisation
extends around these contracts and needs no permission. A change to the lease contract
itself — to authority, identity, receipt or closure semantics — is a protocol change, and
gets a decision record, which is where a fork becomes visible instead of quiet.

## What landed, and what did not

Built, self-tested, not witnessed:

1. **Instance principal**, derived from the host session name so every subprocess agrees
   on who it is without a handshake. Two runs of one definition are two principals.
2. **Work lease** over a concern, held by that principal, with grant, budget and closure.
3. **Helper and witness child leases**, bounded by the parent in authority and lifetime.
4. **Multidimensional budgets** with a draw ledger and the four readings.

Named and not built:

5. **Receipts for resource use.** `contracts/receipt.schema.json` already carries
   `consumed`, but its enum admits four dimensions and a budget bounds six. Extending it
   is its own change with its own fixtures, and until it happens `UNRECEIPTABLE_USAGE`
   reports the gap rather than hiding it.
6. **Independent witness invocation identity** beyond the lease relation. WL-6 and WL-9
   check the relation; nothing yet proves the witness read anything.
7. **A durable definition registry.** Definitions are declared on the lease today. A
   registry is where `IMPORTED` and `FORKED` provenance stops being self-reported.

## Defaults taken

- Lease storage sits in the session store under the common git directory, not in SQLite
  and not committed. Reversible, and it is where the readers already look.
- An undeclared budget dimension is unbounded and reported, not refused. Requiring every
  lease to enumerate every possible limit would make budgets ceremony.
- `PRESSURE_NOTICE` is 0.5. A constant at the top of the module, adjustable on evidence.
- A helper's principal defaults to the session name plus the part handed over, so a
  session does not silently witness its own work.
- The phase effect ceiling defaults to `RESOURCE_CONSUMPTION`, matching the standing
  refusal of external effects in Phase I.

## What would defeat this record

A participant that satisfies every check here and still leaves a concern with no readable
owner. If that case exists, the substrate is measuring the wrong thing, and the fix is a
new requirement rather than a tighter threshold.

## Seams this leaves open

- `docs/principal-identity` carries `decisions/0021-principal-identity` and its
  `contracts/principal.schema.json`, unmerged, with `durability: INSTANCE` and a
  delegation record — the durable half of what this decision references. This record cites
  `0021` by its content, not by a number that survives a rebase (`OPEN-SEAMS.md` S16).
  When that branch lands, `holder.principal_id` should resolve into that registry rather
  than being self-declared on the lease.
- `STATUS.yaml`, `OPEN-SEAMS.md` and `scripts/verify.py` were held by other live sessions
  while this was written, so the standing entry, the seam entry, and registering
  `python scripts/sov_lease.py selfcheck` as a verification check are not in this landing.
  The unit tests run under the existing `scripts/tests` discovery check either way.
