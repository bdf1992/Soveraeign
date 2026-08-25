# Console judgement slice, 2026-08-23

Status: `BUILT · WITNESSED IN PART BY SEPARATE AGENTS · NOTHING RATIFIED`

Bdo directed, 2026-08-23: "We should create and deliver appropriate interfaces
for user interaction with the system's integration and implementations," and
separately that a GitHub code-owner review click cannot be the owner's
ratification surface because Bdo will rarely be on GitHub (`OPEN-SEAMS.md`
S12). The Console Service is the chartered home for that interface. A
`sov-orchestrator` planned the first slice, the owner's judgement surface;
six `sov-worker` operations built it; a `sov-witness` found eleven defects; a
seventh worker closed them; a second witness reproduced the closures. The
interactive session then made three one-line edits the second witness asked
for. Those three lines are `BUILT` only.

## The slice

One path, three legs, all records:

- reach: `request-judgement` records a judgement request, the conditioned
  operation gets an `UNRESOLVED` receipt, a `JUDGEMENT_REQUESTED` notification
  with delivery `LOCAL` is addressed to the owner; the owner pulls the pending
  list through the Human Binding (Phase I has no push);
- answer: the owner invokes `resolve-judgement` through the binding; the
  console realizes it as the `SPEC.md` `ratify` transition; the request's
  question is the Proposal ratified;
- land: a new owned record, `judgement-resolution`, carries resolver, the
  grant checked, the decision, a rationale address, and its receipt; its
  standing reaches `RATIFIED` by an appended event, never by overwrite; the
  request carries only a `resolution_id` back-reference.

No runtime code. O18 gates `console_implementation`; every file here is
charter, contract, fixture, declaration, or draft. Everything is a proposal.

## Files

| Group | Files | Second witness |
| --- | --- | --- |
| Charter | `services/console/CHARTER.md` | one line open, since fixed by the session (`BUILT`) |
| Contracts | `services/console/contracts/service.json`, `judgement-request.schema.json`, `judgement-resolution.schema.json`, `contracts/fixtures/judgement-request.fixtures.json`, `judgement-resolution.fixtures.json` | `WITNESSED` supported, machine-checked |
| Seed fixtures | `services/console/conformance/002-*.yaml` (updated), `008-judgement-request-reaches-owner.yaml`, `009-owner-resolution-lands-ratified.yaml` | `WITNESSED` supported as SEED text; two defeating lines added after, by the session (`BUILT`) |
| Doc coherence | `services/console/README.md` | `WITNESSED` supported, one residual |
| Binding declaration | `bindings/console/README.md`, `bindings/console/interface.json`, `bindings/README.md` (Console section, append-only) | `WITNESSED` supported |
| Owner packet | `.claude/drafts/o18-console-ratification-packet.md` | supported as a proposal document |

## What the witnesses checked

Both passes ran `python scripts/lint.py` and `python scripts/verify.py` (exit
0) and wrote their own validator against `scripts/sovticket/jsonschema.py`:
seven fixture records match their declared validity; each defeating record
fails for exactly its declared reason; `service.json` validates against the
manifest schema; both schemas use only supported keywords; all seven binding
operations map to declared manifest operations; the O18 fixture's question
bytes hash to the recorded digest and equal `STATUS.yaml` O18 at HEAD. Zero
CR bytes in every file. No `.py` anywhere in the slice. Note: `verify.py`
does not execute console fixtures; their validity rests on the witnesses'
scratch validators, not on the repository gate.

First-pass defects, all closed: one operation under two names; an interface
id spelled two ways; grant capability named three ways; a committed fixture
(CONS-002) still naming fields the slice moved; a charter line and a schema
description contradicting the design; gate keys cited from the other
session's uncommitted `STATUS.yaml` (now cited by O18 id only, so the slice
stands against HEAD); a receipt field name reused on a non-receipt record
(renamed `unresolved_receipt_id`); notifications addressed to sessions
instead of recipients; packet citation errors.

## Residuals

- `services/console/contracts/notification.schema.json` (outside the slice)
  describes `source_address` as post, receipt, request, or counter-record; a
  resolution is now also a source. Description drift.
- `services/console/README.md` gate-4 sentence "ratifying the boundary itself
  gates only the standing word" was written by the other session; a README
  stating what a ratification gates reads as a decision. Queued.
- The other session's uncommitted `STATUS.yaml` splits O18 into two named
  gates (`decisions/0023`). The slice cites O18 as one id; if 0023 lands, the
  charter's "O18 gates `console_implementation`" wording goes stale.
- Where the request's question is admitted (inside `request-judgement` or by
  a separate `admit`) before `ratify` can fire is open; CONS-009 says so.

## Judgement items for Bdo

The packet at `.claude/drafts/o18-console-ratification-packet.md` holds six
yes/no questions: O18's three halves (boundary, provisional local-CLI binding,
name) and three new ones (self-issued founding grant; this record as the
ratification surface replacing the 0016 click; `ACCEPTED | STRUCK | DEFERRED`
as the answer vocabulary). The witnesses added: does `JUDGEMENT_RESOLVED`
point at the resolution or the request; may a service README say what a
ratification gates; is the two-gate O18 split the form Bdo wants.

## Left unread

Both witnesses left `SYSTEM.md`, `CONTRACT.md`, `SDLC.md`, most of `PRD.md`
and `ENGINEERING.md`, decisions 0016 and 0021-0023 beyond grep, and console
fixtures 001/003-007 beyond field greps. The session did not inspect the
other session's concurrent work.
