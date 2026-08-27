# Identity Service — Requirements

Status: `BUILT` — self-reported by the drafting session under `decisions/0067`;
not witnessed. This document changes no standing of its own: the service it
describes remains `PROPOSED · PLACEMENT PROVISIONAL · CHALLENGE AND RECOVERY
BUILT` (`CHARTER.md`), and `contracts/service.json` remains `PROPOSED`.

This is a scoped copy of `PRD.md`'s shape (`decisions/0067`) with the node,
not a human, as the named user: Identity's caller is whatever in Soveraeign
needs to mint, deliver, present, enroll, redeem, revoke, or report against a
principal's verification state.

## Product outcome

Give every principal a receipted, storage-free way to move an identity claim
toward `VERIFIED` — by presenting a one-time challenge over a channel the
principal's own record declares, or by redeeming a sealed recovery secret
when that channel is lost — without the mechanism itself ever becoming a
source of authority (`CHARTER.md`, "What it does not do"; `decisions/0048`
ID-8).

## Callers

`decisions/0067` names the node as this service's user. Concretely, as read
from `CHARTER.md` and `contracts/service.json`:

- **A controller principal**, minting a challenge for the principal one hop
  below it — the ordinary recovery path (`decisions/0048` ID-14; `CHARTER.md`,
  "Below the root, recovery is not a second mechanism").
- **The declared channel** — `console-session`, `local-file`, or
  `os-account` (`contracts/service.json` `ports`) — that a minted token is
  handed to. The module never touches the channel directly; delivery is
  the caller's act (`CHARTER.md`, "What it does not do").
- **Whatever holds the principal registry.** `mint` and `present` both take
  a principal record as an argument rather than looking one up, and ID-1
  (every actor resolves to a registered principal) is enforced where the
  registry lives, not here (`CHARTER.md`). `STATUS.yaml` names the current
  state of that boundary as `node_identity_status:
  PROPOSED_CONTRACT_BUILT_REGISTRY_READ_NO_ADMISSION_TRANSITION` — a
  registry contract and a read path exist
  (`scripts/sovsession/principals.py`); no governed transition currently
  writes a presentation's or a redemption's result into it. See
  `JOURNEYS.md`.
- **A human enrolling or revoking a recovery set**, and the physical
  custodian of a redeemed secret once it is handed over (`CHARTER.md`,
  "Sealed recovery, and why it is not a challenge").
- **Whoever reads `Recovery.unenrolled`**, the report naming every principal
  with no live recovery, root first (`CHARTER.md`, "The unanswered question
  above it"). No caller of this report exists in this repository outside its
  own tests at drafting time — see `JOURNEYS.md`.
- **The caller that journals every emitted record.** Both `Challenges` and
  `Recovery` hold their attempts only in an in-memory `.records` list "for
  the caller to journal" (`challenges.py`, `recovery.py` module
  docstrings); this service writes nothing to the operational System of
  Record itself.

## Requirement lifecycle

Same ladder as `PRD.md`: `OPEN → BUILT → WITNESSED → RATIFIED`. Nothing in
this document claims past `BUILT` — a build cannot witness itself
(`AGENTS.md`, Evidence and standing).

## Requirements

### SVC-IDENTITY-1 · Mint only to a declared, node-local channel

`mint-challenge` refuses a principal with no declared verification channel
and refuses a channel of kind `external` or any kind outside
`LOCAL_CHANNEL_KINDS` (`console-session`, `local-file`, `os-account`)
(`challenges.py`; `contracts/service.json` `ports`, `forbids:
external-channel-delivery-in-phase-i`).

Defeating case: a challenge mints against an undeclared or an external
channel and is not refused.

Serves: `PROD-I-3` (Cross — a crossing must name its authoritative source and
channel). Standing: `BUILT`
(`test_undeclared_channel_is_refused`, `test_external_channel_is_refused_in_phase_i`).

### SVC-IDENTITY-2 · Refuse a revoked principal at mint and at presentation

Minting refuses `PRINCIPAL_REVOKED`; a presentation against a principal
revoked since minting is refused and the challenge is burned rather than
left live (`CHARTER.md` refusal table; `decisions/0048` ID-4).

Defeating case: a revoked principal mints a fresh challenge, or a token
minted before revocation still verifies afterward.

Serves: `PROD-I-3`. Standing: `BUILT`
(`test_revoked_principal_cannot_mint`, `test_revocation_after_mint_refuses_presentation`).

### SVC-IDENTITY-3 · A challenge is presentable exactly once, inside its window, by the principal it names

Presentation compares moments rather than stamp strings (a microsecond past
expiry refuses), is single-use (a second presentation of the same token
refuses `CHALLENGE_SPENT`), and refuses a presenter who is not the principal
the token was minted to — burning the token rather than leaving it live for
its rightful owner (`CHARTER.md`, "The window closes when it says it
closes"; `decisions/0048` ID-12, ID-13).

Defeating case: a token verifies twice, verifies after its window, or
verifies for a principal other than the one it names.

Serves: `PROD-I-3`. Standing: `BUILT`
(`test_a_microsecond_past_expiry_is_refused`, `test_replay_is_refused`,
`test_stolen_token_is_refused`, `test_stolen_token_is_burned_not_left_live`,
`test_unknown_token_is_refused`, `test_presentable_at_the_last_moment`).

### SVC-IDENTITY-4 · No token or recovery secret ever enters a record

Only a digest of a token or a recovery secret is held or emitted; the plain
value exists once, as a return value the caller drops
(`CHARTER.md`, "The token never enters the record"; `AGENTS.md`, Secrets and
local boundaries).

Defeating case: any emitted record or any held challenge or recovery set
carries a plain token or secret.

Serves: `PROD-I-3`; `AGENTS.md` Secrets and local boundaries. Standing:
`BUILT` (`test_no_record_ever_carries_a_token`,
`test_no_record_ever_carries_a_secret`).

### SVC-IDENTITY-5 · Verification never substitutes for authority

A `VERIFIED` claim, however it was reached, grants no capability; every
consequential transition still checks its own live typed grant
(`CHARTER.md`, "It grants nothing"; `decisions/0048` ID-8; `CONTRACT.md` C3).

Defeating case: a caller treats a presented challenge or a redeemed recovery
secret as sufficient, on its own, to proceed with a consequential
transition, with no separate grant check.

Serves: `PROD-I-5` (Typed authority). Standing: `OPEN` — this module holds no
authority-checking code path to exercise a defeating case against; the
property is a boundary this module keeps by never reaching toward authority,
not one its own suite can prove. It is exercised, if at all, in whatever
calls this service.

### SVC-IDENTITY-6 · A recovery secret has no expiry and is bounded by single use, a finite set, and whole-set revocation instead

Deliberately the inverse of a challenge: delivered once at enrollment, never
expiring, spent once, and revocable only as a complete set
(`CHARTER.md`, "Sealed recovery, and why it is not a challenge"; `recovery.py`
module docstring; `decisions/0048` ID-11a).

Defeating case: a secret redeems twice, a secret from a revoked set still
redeems, or an individual secret is revoked alone while the rest of the set
stays live.

Serves: `PROD-I-3`. Standing: `BUILT` (`test_replay_is_refused`,
`test_revoked_set_cannot_be_redeemed`, `test_exhaustion_is_visible_on_the_last_redemption`).

### SVC-IDENTITY-7 · Enrollment never silently replaces a live set

Enrolling over an already-live, unrevoked set refuses `ALREADY_ENROLLED`;
replacing recovery without a deliberate revoke first is how recovery is lost
(`CHARTER.md` refusal table).

Defeating case: a second enrollment silently overwrites a live set's
digests.

Serves: `PROD-I-3`. Standing: `BUILT`
(`test_enrollment_never_silently_replaces_a_live_set`).

### SVC-IDENTITY-8 · Revocation counters a whole set as a receipted, attributed transition

`revoke-recovery` retires every live digest in one transition, is receipted
with `revoked_by` and a reason, and a principal may re-enroll a fresh set
afterward (`recovery.py`; `contracts/service.json` `revoke-recovery`,
`crud: COUNTER`).

Defeating case: a revoke leaves a live digest redeemable, erases the prior
enroll or redeem history rather than countering it, or succeeds with no
declared actor.

Serves: `PROD-I-4` (Gate and retract). Standing: `OPEN` — the whole-set
counter and re-enrollment are `BUILT` (`test_double_revoke_is_refused`,
`test_revoke_then_re_enroll`), but `contracts/service.json` declares a
`declared_actor` precondition and an `AUTHORITY_REFUSED` refusal for this
operation that `recovery.py`'s `revoke()` does not implement — any caller
supplying any `revoked_by` string succeeds. Detailed in `SERVICE-SPEC.md`.
Inferred, not charter-stated.

### SVC-IDENTITY-9 · Every principal with no live recovery is named, root first, with the consequence stated

`report-unenrolled` lists every principal whose set is missing, exhausted, or
revoked, sorted root-first, and states plainly that a root with none is
unrecoverable because nothing sits above it to re-enroll one
(`recovery.py` `unenrolled()`; `CHARTER.md`, "What this component does owe
regardless of the ruling").

Defeating case: an unenrolled, exhausted, or revoked-set principal is absent
from the report, or the root's entry does not state that the gap is
terminal.

Serves: `PROD-I-3`. Standing: `BUILT`
(`test_unenrolled_names_the_root_first_and_says_it_is_terminal`,
`test_enrolled_principals_leave_the_gap_report`,
`test_exhausted_set_returns_to_the_gap_report`,
`test_revoked_set_returns_to_the_gap_report`).

### SVC-IDENTITY-10 · Delivery is recorded as owed, never performed

`deliver-challenge` records that a crossing to a channel was owed, with
`effect_class: RECORD_LOCAL`; it performs no external effect, and Phase I
offers no channel kind that would require one
(`challenges.py` `deliver()`; `CHARTER.md`, "It performs no delivery").

Defeating case: `deliver` mutates anything outside its own record, or is
called against a channel kind this service does not itself validate.

Serves: `PROD-I-3`. Standing: `BUILT` for the record-only crossing
(`test_deliver_of_unknown_challenge_is_refused`, `test_mint_deliver_present`);
`deliver()` itself performs no channel-kind check, so the `CHANNEL_REFUSED`
refusal `contracts/service.json` declares for this operation has no
implementing path — detailed in `SERVICE-SPEC.md`. Inferred, not
charter-stated.

## Non-goals

- Deciding where recovery secrets are custodied, or whether they are the
  root's answer to recovery at all. `decisions/0048` ID-11 states this is
  Bdo's; this document does not resolve it (see `JOURNEYS.md`).
- Performing delivery over any channel, local or external
  (`CHARTER.md`, "It performs no delivery").
- Resolving, registering, or admitting principals — ID-1 and ID-2 belong to
  wherever the principal registry lives (`CHARTER.md`, "It resolves no
  principals").
- Cryptographic verification of any claim. `decisions/0048` ID-7: added only
  when a conformance case demonstrates a forged claim, not before.
- Judging whether a caller minting or presenting on a principal's behalf
  actually holds authority to do so for that principal — the module accepts
  the principal record it is handed (`CHARTER.md`, "the caller passes the
  principal record"); `AGENTS.md` Authority puts that check at "the
  operation boundary," which for a mint or a controller-issued recovery
  challenge is outside this module.
- Storing anything durably. The in-memory maps in `Challenges` and
  `Recovery` are projections of the records each emits; durable custody is
  undecided pending `decisions/0048` judgement 3 (`CHARTER.md`).
