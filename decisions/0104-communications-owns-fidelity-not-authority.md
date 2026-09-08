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

## Seats participate in several graphs, and only one of them is authority

Ownership is one graph. Concern ownership, work dependency, orchestration, communication
and routing, observation, custody and settlement are others. The same participants appear
in several of them, and the edges mean different things. Most of this repository already
keeps them apart in separate records — `contracts/domain-owners.json`,
`contracts/acceptance-routing.json`, `contracts/work-lease.schema.json`,
`contracts/custodies/`. The seat etiquette did not.

It derived where a statement may travel from `owner_seat`, which is the delegation graph.
Three consequences, each demonstrated against the live checker before this was changed:

- a witness could not witness a controller;
- a witness could not address any seat but the one that owns it;
- a worker could not ask a sibling anything.

Every statement had to travel the ownership tree, so interaction implied hierarchy by
construction. That is the conflation this decision now refuses.

The topology may declare typed edges beside ownership: `witnesses`, `renders-for`, `asks`.
An act names the relation it travels, and a declared edge of that type is an admissible
route. `owner_seat` still derives the delegation graph and is the only graph that carries
authority.

**A typed edge is a route and never a grant** (`RELATION_GRANTS_NOTHING`). A seat that
witnesses a controller is not owned by it and cannot direct it; a seat that renders for
the root does not thereby report to it. An edge is consulted only for the act that names
that relation, so no edge licenses an act which did not ask for one, and `DISPATCH` names
none. Both refusals are pressed from outside their fixtures.

## What Communications is not

**Not a seat type.** `contracts/seat-registry.schema.json` keeps `root`, `control`,
`orchestration`, `work`. A fifth would put representation into the delegation graph, which
is the one graph this decision keeps it out of.

**Not a rung anywhere.** Communications interacts with Controller, Orchestrator, Worker
and Witness, and none of those interactions places it above or below any of them. It may
discover it needs a tool and ask a Controller to define the work; it may render a Worker's
artifact for an audience; it may route between two domains and gain neither domain's
authority. Being connected is not being owned, in either direction.

**A seat instance is admissible and is not yet needed.** A `seat:communications` typed
`work` was constructed against the live checker: it cannot `AGGREGATE`, so it cannot
forward what it renders. That refusal is about the act table, not about hierarchy, and a
`renders-for` edge plus `rendered_by` already carries the case this branch had. Adding the
seat is a change to `seats` and `relations`, not a change to the shape of authority, and
it is left for the first concern that needs a durable custody record rather than taken on
speculation.

**Not a new act.** `RENDER` was drafted and withdrawn. `AGGREGATE` carrying a plain-English
body is admitted; the same message proposing `BUILT -> WITNESSED` is refused; the same
message dropping a carried question is refused.

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
5. Three relation types are declared — `witnesses`, `renders-for`, `asks` — because three
   are what the refused cases needed. Custody, dependency and settlement edges live in
   their own records today and are not folded in here; whether they should share this
   vocabulary is unsettled and is not settled by this decision.
6. `ASK` names the `asks` relation and the topology declares no `asks` edge, so it still
   travels delegation only. The route exists and nothing uses it yet.
