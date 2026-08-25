# Identity Charter

Status: `PROPOSED · PLACEMENT PROVISIONAL · CHALLENGE AND RECOVERY BUILT`

## An assumption stated rather than buried

`decisions/0048` judgement 3 asks whether principal identity is a service
boundary or a kernel-level registry. That question is Bdo's and is open. This
directory exists because the challenge lifecycle needed a home to be written
and run, not because the question was answered.

The assumption is made cheap on purpose. The challenge lifecycle is
storage-free: its clock, token source, and identifier source are injected, it
holds no database and reads no file, and it returns records for a caller to
journal rather than journaling anything itself. If Bdo rules "kernel
registry", the ruling moves one file and changes no semantics. Read
`ENGINEERING.md`'s service construction rule as the test this directory has
not yet passed: create a service only when a domain owns a distinct
lifecycle, contract, and authority boundary — otherwise it is a component
inside an existing one.

## What it owns

The challenge: the passwordless verification mechanism from `decisions/0048`
(ID-12, ID-13, ID-14), which is the magic-link pattern built from primitives
the system already has. A challenge is a lease — minted against one principal
and one declared channel, fenced by a token, expiring on a clock, presentable
exactly once. Presenting a live token inside its window is what upgrades an
identity claim from `UNVERIFIED` to `VERIFIED`; the presentation is that
claim's `verification_basis`.

**Below the root, recovery is not a second mechanism.** A lost credential is a
fresh challenge to the declared channel, issued by the controller (ID-14) — no
back door, because there is no front door to distinguish it from.

**At the root it has to be**, and that asymmetry is the whole difficulty. The
root has no controller to issue it a fresh challenge, and the channel a
challenge would travel over is inside the very node that may be what was lost.
Sealed recovery secrets below are the one mechanism this stack can carry for
that case; whether they are the root's answer is Bdo's.

## Two properties that are structural, not promised

**The token never enters the record.** Only its digest is held and only its
digest is emitted, so a journal, a receipt, or a leaked log cannot replay a
challenge. The token exists once: the return value of `mint`, which the caller
hands to the channel and drops. `test_no_record_ever_carries_a_token` reads
every emitted record and every held challenge back and fails if a token
appears in either.

**The window closes when it says it closes.** Expiry compares moments rather
than the strings they render as. This was a real defect in the first draft:
a whole-second expiry renders `...12:10:00Z`, a moment just past it renders
`...12:10:00.000001Z`, and lexically `.` sorts below `Z`, so an expired token
compared as still live. `test_a_microsecond_past_expiry_is_refused` pins it.

## What it refuses

| Refusal | Reason code | Why |
| --- | --- | --- |
| Minting for a principal with no declared channel | `CHANNEL_UNDECLARED` | ID-13: verification travels only over a channel the record declares |
| Minting to an external channel | `CHANNEL_REFUSED` | `no_external_effects_in_phase_i` (O7). Admitting external delivery later changes one tuple and nothing else |
| Minting for a revoked principal | `PRINCIPAL_REVOKED` | ID-4 |
| Presenting a token that was never minted | `TOKEN_UNKNOWN` | — |
| Presenting a token twice | `CHALLENGE_SPENT` | ID-12: one-time |
| Presenting after the window | `CHALLENGE_EXPIRED` | ID-12: leased |
| Presenting someone else's token | `PRINCIPAL_MISMATCH` | A token names who it verifies; the thief is refused and the token is burned rather than left live for its owner |
| Presenting for a principal revoked since minting | `PRINCIPAL_REVOKED` | Revocation beats a live token |

These reason codes are proposed alongside `decisions/0048`; whether `SPEC.md`
adopts them is O10's.

## What it does not do

- **It grants nothing.** A `VERIFIED` claim is identity, not authority; every
  consequential transition still checks a live typed grant (ID-8, C3).
- **It performs no delivery.** Phase I channels are node-local, so `deliver`
  records that a crossing was owed and to which channel; handing the token
  over is the caller's act.
- **It stores nothing durably.** The in-memory map is a projection of the
  records it emits. Durable custody belongs to whichever home Bdo picks.
- **It resolves no principals.** The caller passes the principal record; ID-1
  (every actor resolves to a registered principal) is enforced where the
  registry lives, not here.

## Sealed recovery, and why it is not a challenge

A challenge is short-lived and delivered on demand. Recovery cannot be: at the
moment it is needed, the channel one would deliver over is the thing that was
lost. So a recovery secret is the inverse — delivered once at enrollment, held
outside the node by the human, redeemable whenever, with **no expiry**. That is
ID-12's rule deliberately inverted rather than overlooked: an expiring recovery
secret expires exactly when nobody is watching. Single use, a finite set, and
revocation of the whole set at once are what bound it instead.

| Refusal | Reason code |
| --- | --- |
| Redeeming with nothing enrolled | `NOT_ENROLLED` |
| Redeeming a secret that was never issued | `SECRET_UNKNOWN` |
| Redeeming one twice | `SECRET_SPENT` |
| Redeeming against a revoked set | `SET_REVOKED` |
| Enrolling over a live set | `ALREADY_ENROLLED` — replacing recovery silently is how recovery is lost; revoke deliberately first |

## The unanswered question above it

The root has no controller, so root recovery cannot be a support path. This
component implements the mechanism and **no answer**: whether recovery secrets
are how the root recovers, and where the paper physically lives, is ID-11 and
belongs to Bdo. Examining it split the question three ways — credential lost
with the node intact (answered here), node destroyed (not identity at all; see
`OPEN-SEAMS.md` S11), and the occupant unavailable (succession, pure judgement).

What this component does owe regardless of the ruling is the report:
`Recovery.unenrolled` names every principal with no live recovery, root first,
and states the consequence plainly. For the root that consequence is terminal —
nobody is above it to enroll one afterwards — so the honest handling is to say
so continuously rather than discover it at the worst possible moment.

## Standing

`BUILT` for both components: thirty-two positive and defeating cases run under
`python scripts/verify.py`. Not witnessed — a build cannot witness itself. The
placement, the reason codes, ID-11, and seam S11 remain queued for Bdo.
