# 0023 · Self-direction and transition-local gates

Status: `OWNER-DIRECTED · WORDING PROPOSED`

## Decision

Two rules enter `AGENTS.md` Authority, on Bdo's 2026-08-23 direction:

1. **Self-direction is not delegation.** A participant exercises judgement
   over its own actions within its granted authority: it chooses among
   reachable paths, takes reversible defaults, sequences effort, and decides
   what evidence it needs to continue. It may not settle another
   participant's judgement, widen another's authority, or make a provisional
   choice binding on others. It can construct what it cannot ratify, test
   what it cannot adopt, propose what it cannot settle, and explore what it
   cannot make policy.
2. **Blocked edge is not blocked frontier.** An unresolved owner decision
   gates only the transitions that need that judgement. `STATUS.yaml` records
   those as `gates:` (exact transition names) in place of the former
   `blocks:` (work-global labels). `BLOCKED` is a claim that must be proven
   with `reachable_alternative: NONE`; otherwise the transition is gated and
   the work continues.

Decision drafts end with `Defaults taken`, not `Open authority`. A new open
decision is minted only for a genuinely unresolved governing choice, above all
a conflict between settled constraints.

No new standing-grant decision was created: `AGENTS.md` already lets agents
"inspect, compare, draft, implement, test, and machine-ratify". The defect was
that `CLAUDE.md` ("queue them; never decide them"), `STATUS.yaml` (`blocks:
<x>_implementation`), the decision template, and nine workflow scope prompts
read an unresolved owner judgement as a global work stop.

## Change protocol record

1. **Requested outcome and current state.** Bdo: an owner makes ten decisions
   that open ten thousand clear paths, not a hundred; work should act, record,
   expose, and be validated in batch review. Before: 21 open decisions in two
   days, most minted at the end of Claude-authored records, each with a
   `blocks:` line that gated implementation on a ruling.
2. **Affected.** `AGENTS.md` (two subsections under Authority), `CLAUDE.md`
   (lines 86-87 and the "where to look" row), `STATUS.yaml` (20 `blocks:` →
   `gates:`; O21 narrowed), `decisions/0021` (`Defaults taken`),
   `services/projection/README.md`, `services/console/README.md`,
   `.claude/README.md`, `.claude/agents/sov-controller.md`,
   `.claude/agents/sov-orchestrator.md`, nine `.claude/workflows/sov-*.js`
   scope prompts, five `.claude/skills/sov-*/SKILL.md` gate lists,
   `scripts/sov_next.py` docstring. No fixture, contract, or source changed.
3. **Preconditions and expected result.** Before: `verify.py` green. After:
   `verify.py` green; `grep blocks: STATUS.yaml` returns nothing; every open
   decision names at least one transition; a scope agent reading any domain
   workflow plans reachable precursors instead of returning blocked.
4. **Effect class.** `RECORD_LOCAL`.
5. **Rollback.** Revert the files above. No standing, grant, or protected
   boundary changed; `no_runtime_code_before_logical_spec_and_defeating_fixtures`
   stands as a fixture gate, which it always was.

## Evidence

- `AGENTS.md` Authority (pre-change): agents "may inspect, compare, draft,
  implement, test, and machine-ratify"
- `STATUS.yaml` `open_decisions` (pre-change): nineteen `blocks:` lines, of
  which `proofing_implementation`, `console_implementation`,
  `projection_implementation`, and `production_implementation` read as build
  permits
- `.claude/agents/sov-controller.md`: "a blocker must be proven" already
  existed; this decision generalises it to every participant
- `decisions/0014`, `0021` (pre-change): "remains Bdo's judgement (O-n)" as
  the template's closing move
- Bdo's 2026-08-23 direction, verbatim in the session: "A participant may
  exercise judgement over its own actions within its granted authority. It
  may not exercise judgement on behalf of another participant or convert its
  own judgement into authority for others." and "Blocked edge ≠ blocked
  frontier."

## Gate names

Each former `blocks:` label became one or two transitions:

| Decision | Gates |
| --- | --- |
| O1 | `repository.publish_public` |
| O2 | `engineering.ratify_baseline` |
| O3 | `attestation.bootstrap_first_attestor` |
| O4 | `attestation.ratify_schema` |
| O5 | `gauge.ratify_specification` |
| O6 | `kernel.make_effective_unattestable` |
| O7 | `kernel.commit_external_world_effect` |
| O8 | `qualification.settle_cold_start` |
| O9 | `classification.ratify` |
| O10 | `spec.ratify`, `roadmap.close_f1` |
| O11 | `proofing.ratify_boundary` |
| O12 | `model_binding.ratify_contract` |
| O13 | `sdlc.activate_loop` |
| O16 | `coordination.activate_external_effects` |
| O17 | `sov.activate_live` |
| O18 | `console.ratify_boundary`, `console.authorize_provisional_human_binding` |
| O19 | `ticket_kind.ratify_verification_engagement` |
| O20 | `channels.activate_projection` |
| O21 | `projection.ratify_boundary` |
| O22 | `ticket_kind.ratify_story`, `classification.ratify` |

These names are not yet in the `SPEC.md` transition table; they are
governance transitions over documents and activations, not kernel record
transitions. Whether they belong in `contracts/kernel-transitions.json` or a
sibling governance-transitions projection is a later bounded operation.

## Defaults taken

- Used dotted `<owner>.<verb>_<object>` gate names; renaming is mechanical.
- Mapped O2 (`production_implementation`) to ratification of the baseline
  only: building on the proposed baseline is reachable, as the Asset Service
  already does.
- Mapped the three `<service>_implementation` labels to
  `<service>.ratify_boundary`; implementation stays behind the fixture
  boundary, not behind the ruling.
- Left historical decision records' `Open authority` sections as written; the
  template changes from 0021 onward.
- Left `scripts/sov_epic.py` `HELD ... blocked by` untouched: a ticket held
  by another ticket is a dependency edge, which is the correct use of the
  word.
- Recorded O22's gate as both `ticket_kind.ratify_story` and
  `classification.ratify`, since its question bundles a vocabulary entry.

These defaults remain proposals. Work continues unless a governing constraint
is violated; Bdo may counter any of them in review.
