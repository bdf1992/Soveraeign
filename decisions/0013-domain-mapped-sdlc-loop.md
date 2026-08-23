# 0013 · Domain-mapped SDLC operating loop

Status: `OWNER-DIRECTED · LOOP PROPOSED`

## Decision

Define the repository's own software development lifecycle as a governed
operating loop in `SDLC.md`: a three-tier authority-delegation chain
(Control, Orchestration, Work) running workflow templates over a registry of
domain-mapped concerns.

Grants flow down and narrow; reports flow up and never self-settle; each
tier's output is settled by the tier above it; escalation to the owner is a
first-class transition. Tier depth is fixed at three.

Name two paired stances as typed dyads rather than named people or models,
resolving the direction of seam S7 for this surface:

- `LEFT`/`RIGHT` — the authority dyad: synthesis proposes, judgement
  ratifies;
- `RED`/`BLUE` — the verification dyad: construction builds and proves the
  declared cases, adversarial witnessing seeks the undeclared defeats.

Neither hand of either dyad settles anything alone; results exist only in
combination. Name the combinations as outcomes, not stances: `PURPLE` is the
settled verification engagement (`RED` + `BLUE`), `JOINED` is the
ratification receipt over a synthesis proposal (`LEFT` + `RIGHT`), and
`GREEN` is the derived go-state of a concern whose current gate holds both.
No operator holds a combination outcome, and `GREEN` is never selected
directly.

Require a settled Red engagement receipt before any concern advances past
`BUILT`. Confirmed Red findings are reproduced independently, then become
permanent defeating fixtures in the conformance corpus. Exit is dry-run
convergence; fixtures are never weakened to admit a participant.

Organize declared competence on two orthogonal skill axes — tier skills
(Control, Orchestration, Worker) and domain skills (Product, Development,
QA, Release, Feedback) — with five Phase-I workflow templates: Report,
Standup, Review, Demo, Design.

Admit the `.claude/` directory as the first, provisional harness binding of
the loop. The loop definition stays stack-neutral, and model
substitutability applies to the loop itself.

## Consequences

- `WITNESSED` standing acquires an operational meaning: survival of a
  scoped, bounded, independent adversarial engagement.
- The concern registry is a projection over `STATUS.yaml`, `decisions/`, and
  `OPEN-SEAMS.md`; no new System of Record is created.
- The Release domain skill is largely a refusal boundary while
  `no_external_effects_in_phase_i` and open decision O1 stand.
- Executable orchestration scripts remain inadmissible until their logical
  specification and defeating fixtures exist.
- Exact tiers, dyads, registry derivation, and the Red-gated release
  requirement remain proposed until Bdo ratifies open decision O13.

## Source and authority

- `AGENTS.md` implementation order, standing lifecycle, and change protocol
- `ENGINEERING.md` kernel primitives, composition, and growth rules
- `CLASSIFICATION.md` participation roles and naming rules
- `AI-NATIVE.md` surface evaluation and the Soveraeign bar
- `BYOM.md` binding, adapter, and substitutability boundaries
- `OPEN-SEAMS.md` S5 (cold-start witnessing) and S7 (operator bindings)
- Bdo's 2026-08-22 direction to define the domain-mapped SDLC loop as
  controller, orchestration, and worker tiers with combined Red/Blue
  stances gating release
