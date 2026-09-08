# 0104 · Communications owns fidelity, never authority

Status: `OWNER-DIRECTED · PROPOSED`

Bdo asked whether Communications is a real domain and what it may hold. It is, and the
answer needed no new authority: the seat machinery already carried the semantics, and
what was missing was attribution.

## Decision

**Communications owns fidelity of representation across participant boundaries.** It may
transform wording, compression, vocabulary and audience context. It may not alter speaker
identity, authority, standing, provenance, carriage, dissent or settlement.

**A rendered statement remains the speaker's statement. The renderer is separately
attributable.** `rendered_by` on a seat message names the participant that chose the
words. The speaker keeps the claim, its standing, and the answering for it.

Four consequences follow, and each is checked rather than asserted:

| Property | Where it lives |
| --- | --- |
| A rendering forwards; it does not speak for itself | `AGGREGATE`, relation `FORWARDED` |
| Wording cannot improve standing | that act's `standing_ceiling` is `null` |
| Questions, dissents, residuals and stalls survive | `CARRY_EVERYTHING_RECEIVED`, `NO_EDIT_IN_TRANSIT` |
| The renderer is not the speaker | `SPEAKER_IS_THE_OCCUPANT` |
| The renderer is a real participant | `RENDERER_IS_A_REGISTERED_PRINCIPAL` |

`python scripts/witness_seats.py` runs in `scripts/verify.py` and presses all of them
from outside their own fixtures.

## What Communications is, in the terms this repository already has

- **A concern.** `AGENTS.md` One session, one concern: the list is open and a new concern
  needs no kernel enum. This one is `concern:communications`.
- **A participant.** A principal in `contracts/principals.json`, resolved the same way
  every other actor is. `decisions/0048` ID-1 admits no orphan actors, and a renderer is
  an actor on a consequential record.
- **A competence.** `.claude/skills/`, `.claude/agents/sov-comms.md`, and the graders in
  `scripts/sov_comms.py` and `scripts/witness_seats.py`.
- **A history.** `LESSONS.md`, which is where this repository already accumulates the
  failures it does not want to repeat. Communication failures go there, not into a
  ledger of their own.

## What Communications is not

**Not a seat type.** `contracts/seat-registry.schema.json` keeps `root`, `control`,
`orchestration`, `work`. A fifth would put representation into the authority hierarchy,
which is the one thing this decision is against.

**Not a seat instance either, and that was tested rather than assumed.** A
`seat:communications` typed `work` was constructed against the live checker. It is
refused twice: a work seat may not `AGGREGATE`, so it cannot forward what it renders, and
`AGGREGATE` travels to its owner, so it cannot reach the root. Making it work would take
either `AGGREGATE` in every work seat's `may` list, which lets any worker forward, or a
`control` seat, which grants dispatch. The same conversation with no comms seat and
`rendered_by` set is admitted as written.

That is the finding, and it is the reason the shape is what it is: **a seat is an
authority position, and Communications holds no authority.** None of the properties Bdo
asked for — its own concern, its own skills, an attributable participant, graders, a
history of communication failures, somewhere to accumulate competence — needs one.

**Not a new act.** `RENDER` was drafted and withdrawn. The control seat's `AGGREGATE`
carrying a plain-English body is admitted; the same message proposing `BUILT ->
WITNESSED` is refused; the same message dropping a carried question is refused. Every
property was already there, and the `body` is unconstrained on purpose.

## What would defeat this

A communication failure that none of the five checks above can express. If meaning is
lost across a boundary while speaker, standing, carriage, occupancy and renderer all
check out, then fidelity is not fully reducible to them and this decision is incomplete
rather than wrong.

## Residuals

1. `decisions/0048` ID-1 is wired here and nowhere else. Seat occupants are still
   `sov-controller@1` and siblings, which resolve to no principal, so the corpus this
   decision sits in does not itself meet the rule it applies to renderers. Wiring ID-1
   across the kernel receipt path is that decision's own open item and remains Bdo's.
2. `concern:communications` is named here and registered nowhere. Sessions still carry
   `concern:session/<id>` fallbacks.
3. Whether a Communications principal should exist distinctly from the model principal a
   session runs on is owner identity, which `contracts/acceptance-policy.json` reserves.
   The fixtures use an already-registered principal rather than minting one.
4. The etiquette this builds on is `PROPOSED` (`decisions/0035`). This decision does not
   promote it.
