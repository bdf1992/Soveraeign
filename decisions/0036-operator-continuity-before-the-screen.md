# 0036 · Build operator continuity before the operator screen

Status: `PROPOSED · BUILT AND SELF-TESTED · RATIFICATION PENDING`

Numbering note: `0035-seat-message-etiquette.md` was minted in this same working
tree while this record was being drafted. `OPEN-SEAMS.md` S16 carries the
allocation seam; this record renumbers rather than contests.

Built by Claude at Bdo's direction (2026-08-23 conversation). Bdo asked for a
cross-session and cross-session-message capability with automatic session-start
metadata, for an interface for operators, measured against the repository's own
definition of AI-native.

## Decision

The Console Service now has an implementation: the **operator continuity record
path**, in `services/console/src/soveraeign_console_service/`, reached through a
CLI and no other way.

Channels, threads, posts, operator sessions and authority grants are appended to
the Record Service journal. The console owns no store of its own beyond immutable
post payloads, and its read path is a projection rebuilt from that journal on
every call.

## Why this slice rather than the declared one

`services/console/README.md` named the first slice as the owner's judgement
surface. This is a different slice, and that deviation is Bdo's to accept or
reject.

The reason to take it first is the AI-native gate. `AI-NATIVE.md` makes
reachability the gate: a fresh model instance must discover state, operations,
required inputs and results through a stable declared path, or nothing else about
the surface can score above `DECORATION`. A judgement surface built first would
have had to invent that path along the way and would have been judged on it. The
continuity path is the thinnest slice that establishes the path itself, and the
judgement surface can then be a set of operations on a mechanism that already
exists rather than a mechanism smuggled in beside a feature.

The gates in that README were also read before proceeding. Gate 2, executable
console fixtures, is satisfied by `services/console/tests/`. Gate 3 is not
engaged: the continuity path projects over its own journal and reads no sibling
service. Gate 4 concerns a Human Binding, and none was built - `CHARTER.md`
forbids a binding implementation, not a service implementation, and the operator
screen is deliberately the last thing, not the first.

## What was built

| Piece | Where |
| --- | --- |
| Transitions and refusals | `core.py`, `refusals.py` |
| Grants as journal records | `authority.py` |
| Read path, rebuilt per call | `continuity.py` |
| Declared record shapes | `contract.py` |
| Machine interface | `cli.py` |
| Host binding to Claude Code | `.claude/hooks/console_session.py` |
| Operating skill | `.claude/skills/sov-continuity/` |

Thirty-one tests in `services/console/tests/`, plus two correspondences in
`contracts/kernel-parity.json` that drive the real service from outside it. Every
declared behaviour has a positive case and a case proving its refusal.

## Rulings

**1. A grant is a record, not a process variable.** The first implementation held
grants in memory. It passed its tests and was useless: a CLI is a new process per
command, so every grant vanished before the next one. Grants are now journal
records, revocation appends rather than deletes, and a revocation refuses the
next operation without reaching back to unmake one already committed.

What would defeat this: a grant that must be checked faster than a journal replay
allows. The check would then need a rebuilt projection, and that projection would
still not be the authority.

**2. A model post that claims needs a proposal.** A `MODEL` post carrying a claim
with no `proposal_id` is refused with `CLAIM_WITHOUT_PROPOSAL` and the refusal is
recorded. A `HUMAN` post that claims is not refused. This is the one place the two
actor kinds are treated differently, and it is treated differently on purpose: a
model's assertion is a proposal until something outside the model settles it.

Everything else is identical. A human post and a model post take one operation,
check one capability, and differ only in `actor_kind` and the receipt's
`interface_id`. `contracts/kernel-parity.json` now drives the real service and
grades that refusal against the kernel's.

What would defeat this: a demonstration that some class of model post makes no
claim and yet is refused, or that a human post can settle something by being
posted. Neither would repair itself; both would mean the claim boundary is drawn
in the wrong place.

**3. Standing stops at `RECORDED`.** Every console record enters at `RECORDED` and
the service has no transition that lifts it. Admission, ratification and
effectiveness are kernel transitions the console does not own, and a payload
asking for anything higher is refused with `STANDING_NOT_OWNED`.

**4. The projection says it is a projection.** Every view returns
`authoritative: false` and names its omissions. The session-start briefing carries
the same two facts in prose. A rewritten journal fails the digest chain and the
projection raises rather than rendering a plausible history.

## Effect class and rollback

`RECORD_LOCAL` throughout. No external effects, no network, no resource
consumption beyond local disk. The store is `.local/console/`, already ignored.

Rollback is deleting `.claude/settings.json` and the four new directories; nothing
outside them changed except the parity contract, the seam register, and the
verification harness registration.

## Defaults taken

- Operator id defaults to `sov`, overridable by `SOVERAEIGN_OPERATOR`. Reversible.
- The session-start hook opens a `MODEL` session automatically. A session record
  per Claude Code start is a real operator session, so recording it is honest;
  if the journal noise is unwanted, the hook is one file.
- `INCOMPLETE_PROPOSAL` was unusable for the parity correspondence because the
  kernel evaluator never emits it. Declared against `MISSING_PRECONDITION`, which
  is what the kernel actually returns, and recorded as `OPEN-SEAMS.md` S17 rather
  than worked around silently.

## What still waits on Bdo

- Whether this slice stands as the console's first, given the README named another.
- Whether every Claude Code session in this repository should open and close a
  console session automatically.
- Ratification. Thirty-one passing self-tests establish `BUILT` and nothing more.
  No independent witness has run, and `AGENTS.md` reserves `RATIFIED` for Bdo.
