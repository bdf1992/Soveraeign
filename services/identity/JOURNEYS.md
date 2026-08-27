# Identity Service — Journeys

Status: `BUILT` — self-reported by the drafting session under `decisions/0067`;
not witnessed. The piece the root pattern has no analog for: what a caller's
path through this service actually looks like, stated plainly as completing
or dead-ending, with the exact sentence that makes it so.

A journey below is judged against this service's own boundary — what
`challenges.py` and `recovery.py` do — not against the whole node. Where a
journey's outcome depends on something outside this service (the principal
registry, an authority check, a physical custodian), that is named as the
dead end rather than assumed away.

## Journeys

### J1 · A caller discovers what this service will let it do

**Mostly completes.** `CHARTER.md` and `contracts/service.json` together
name every operation, precondition, and reason-code table without requiring
oral briefing — the general claim `GROUND-006` makes. It does not fully
complete: `SERVICE-SPEC.md`'s Refusal reason codes section names five
places where the contract's declared refusal list for an operation and the
code's actual refusal codes disagree (`present-challenge` refuses
`PRINCIPAL_REVOKED` in code but the contract does not declare it there;
`deliver-challenge` and `enroll-recovery` declare refusals the code does not
implement; `redeem-recovery` and `revoke-recovery` return codes the contract
does not declare for them). A caller reading only `contracts/service.json`
would be wrong about what can happen on four of the seven operations.

### J2 · A controller mints a challenge for a principal over a declared local channel

**Completes**, or refuses legibly. `mint()` returns a token exactly once and
a `COMMITTED` record, or refuses `CHANNEL_UNDECLARED`, `CHANNEL_REFUSED`, or
`PRINCIPAL_REVOKED` with a record naming why (`challenges.py`;
`test_undeclared_channel_is_refused`, `test_external_channel_is_refused_in_phase_i`,
`test_revoked_principal_cannot_mint`). This is the one journey through
Identity that is fully contained inside its own boundary from start to
finish.

### J3 · The token crosses to its declared channel

**Completes as a record, not as a delivery — deliberately.**
`deliver-challenge` records that the crossing was owed, `effect_class:
RECORD_LOCAL`, and stops there: "It performs no delivery" (`CHARTER.md`).
Handing the token to the channel is the caller's act. This is not a gap; it
is the stated boundary of what Phase I's node-local channels need.

### J4 · The principal presents the token within its window

**Completes inside this service; dead-ends immediately outside it.**
`present()` returns `COMMITTED` and a `verification_basis` string once a
live token is presented by the principal it names. Nothing in this
repository then writes that `verification_basis` into any principal's
`claim.verification`. Three independent sources confirm this is not an
oversight but a held-open seam:

- `CHARTER.md`: "It resolves no principals."
- `decisions/0048`, Remaining work item 3: "Bind the challenge runtime to
  the principal registry, so presenting a challenge actually writes
  `verification: VERIFIED` with its basis... Held deliberately: that
  binding is where identity stops being a proposal, and ID-11 ... should be
  answered first."
- `STATUS.yaml`: `node_identity_status:
  PROPOSED_CONTRACT_BUILT_REGISTRY_READ_NO_ADMISSION_TRANSITION`, and
  `scripts/sovsession/principals.py`'s own docstring: "Nothing here upgrades
  a claim: `UNVERIFIED` becomes `VERIFIED` only by presenting a live
  challenge token, which is the Identity Service's lifecycle and not this
  module's," followed by "The instance does not exist in this branch yet.
  Until it does, every session resolves `UNIDENTIFIED`."

A caller can obtain a valid `verification_basis` today. No path in this
repository consumes it.

### J5 · A controller issues a fresh challenge to recover a principal below it (ID-14)

**Completes procedurally through this service's own boundary; inherits J4's
dead end and adds one of its own.** Mechanically this is J2 + J3 + J4 with
a controller as the caller, so it reaches the same registry-write dead end
J4 does. It adds a second gap: nothing in `mint()` or `present()` checks
that the caller invoking them on a principal's behalf is actually that
principal's registered controller. `CHARTER.md` states this plainly — "the
caller passes the principal record" — and `AGENTS.md` Authority places the
check "at the operation boundary," which for this operation is outside the
module entirely, not inside it.

### J6 · A human enrolls a fresh recovery set for a principal

**Completes**, with one declared refusal unreachable. `enroll()` returns ten
secrets exactly once and refuses `ALREADY_ENROLLED` against a live set
(`test_enrollment_never_silently_replaces_a_live_set`). It cannot refuse
`PRINCIPAL_REVOKED`, which `contracts/service.json` declares for this
operation, because `enroll(principal_id: str, ...)` never receives a
principal record to check revocation against — read from the code, not
stated in `CHARTER.md`.

### J7 · A human redeems a recovery secret because their normal channel is lost

**Completes inside this service; dead-ends at the same registry boundary as
J4.** `redeem()` matches a digest, single-use, receipted, with exhaustion
visible on the last redemption (`test_exhaustion_is_visible_on_the_last_redemption`).
As with a presented challenge, nothing in this repository writes a
successful redemption back into any principal's verification claim — the
same three citations under J4 apply here, since `decisions/0048` frames
recovery as "the same door" as a challenge for this purpose.

### J8 · A controller revokes a whole recovery set

**Completes the receipt and the counter; the authority clause it declares
does not.** `revoke()` retires every live digest in one transition and
permits a fresh enrollment afterward (`test_double_revoke_is_refused`,
`test_revoke_then_re_enroll`). `contracts/service.json` declares this
operation's precondition as `declared_actor` and its refusal set as
including `AUTHORITY_REFUSED`; `revoke()` accepts any `revoked_by` string
with no check behind it. Read from the code against the contract, not
stated in `CHARTER.md` or `decisions/0048`.

### J9 · Someone asks which principals currently have no live recovery

**Completes as a mechanism; dead-ends as an ongoing practice.**
`Recovery.unenrolled()` correctly names every principal with a missing,
exhausted, or revoked set, root first, with the root's consequence stated as
terminal (`test_unenrolled_names_the_root_first_and_says_it_is_terminal`).
Searching this repository for a caller of `unenrolled(` outside
`tests/test_recovery.py` finds none: no script, workflow, or scheduled
check currently invokes it. `CHARTER.md` asks that this gap be said "loudly
and continuously" — the mechanism to say it exists; nothing yet says it.

### J10 · The root itself needs to recover

**Dead-ends by design, not by omission.** `CHARTER.md` states the boundary
directly: "The root has no controller, so root recovery cannot be a support
path," and the mechanism this service provides — sealed recovery secrets —
is offered with **no answer** attached: "whether recovery secrets are how
the root recovers, and where the paper physically lives, is ID-11 and
belongs to Bdo." This is the journey the task of drafting these four
documents was told explicitly not to resolve, and it is not resolved here.

## Open custody / ownership questions

None of the following is assigned, resolved, or made this service's to
decide by being named here (`decisions/0067`, "What this is not"). Each
routes to a decision record the ordinary way, at whichever tier
`STATUS.yaml`'s resolution rule names.

1. **Whether sealed recovery secrets are the root's recovery mechanism at
   all, and where the paper physically lives.** `decisions/0048` ID-11:
   "the one requirement whose content only Bdo can supply; it is queued,
   not defaulted." `CHARTER.md`, "The unanswered question above it." Not
   resolved by this document (see J10).

2. **Whether principal identity is a service boundary
   (`services/identity/`) or a kernel-level registry.** `decisions/0048`
   judgement queue item 3, still open. `CHARTER.md` states its own
   placement is "provisional" on this ruling and is written so the ruling
   "moves one file and changes no semantics."

3. **Who writes a presented challenge's or a redeemed recovery secret's
   result into a principal's verification claim.** `decisions/0048`
   Remaining item 3 names the binding and holds it deliberately pending
   ID-11, but does not name which participant executes it once ID-11
   clears — this service, the registry, or a third boundary. See J4 and J7.

4. **Who is meant to enforce the authority check
   `contracts/service.json` declares for `revoke-recovery`** (the
   `declared_actor` precondition and `AUTHORITY_REFUSED` refusal) but
   `recovery.py` does not implement. Inferred from reading the code against
   the contract, not stated in `CHARTER.md`. See J8 and `SERVICE-SPEC.md`.

5. **Node lost or destroyed (`decisions/0048` ID-11b).** "Not an identity
   problem, and the stack does not answer it either" — no backup, restore,
   or off-node custody provision exists anywhere in the repository, so "a
   recovery secret redeems against a journal that must still exist."
   `CHARTER.md` points to `OPEN-SEAMS.md` "S11" for this; that citation is
   itself stale — `OPEN-SEAMS.md`'s own renumbering note records the seam
   as having moved to **S24, "Durability and custody"** after a collision
   with an unrelated S11 on `main`. Named here as a citation to correct,
   not a question this document settles.

6. **Root occupant unavailable — succession (`decisions/0048` ID-11c).**
   "No technology answers this: it needs a named successor principal and a
   declared condition under which succession fires. Pure judgement, and
   only Bdo can supply it."

7. **Who consumes `Recovery.unenrolled`'s report.** No caller of it exists
   in this repository outside its own tests today (see J9). Not named as
   any participant's job in `CHARTER.md` or `decisions/0048`.
