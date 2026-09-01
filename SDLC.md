# Domain-Mapped SDLC Loop

Status: `OWNER-DIRECTED · OPERATING LOOP PROPOSED`

This document defines how work on Soveraeign itself is planned, dispatched,
executed, witnessed, and released. It is a stack-neutral process contract: it
names tiers, stances, skills, and workflow templates without binding them to a
named person, model, provider, or harness. `AGENTS.md` remains the normative
operating contract; this loop composes its rules into a repeatable motion and
adds the release gate defined here.

The loop is itself a surface performing named operations. It is therefore
subject to the `AI-NATIVE.md` axes and, eventually, the Soveraeign bar.

## Three tiers

The loop runs on an authority-delegation chain. Grants flow downward and narrow
at every step; reports flow upward and are never self-settling; each tier's
output is settled by the tier above it.

| Tier | Role | May | May not |
| --- | --- | --- | --- |
| **Control** | Strategic planning and monitoring over registered concerns | Read the concern registry, select the next named operation, declare the operation plan, issue scoped grants, launch orchestrations, observe results independently, settle receipts, update standing, escalate to the owner | Ratify judgement, widen its own grant or effect class, keep private state about concerns |
| **Orchestration** | Decomposition and supervision of one launched operation | Lease workers, fence execution, collect reports, run independent observation over durable outputs, settle worker-task outcomes, report settlement evidence upward | Widen the received grant, settle its own operation, ratify anything |
| **Work** | Scoped leased execution in a declared environment | Execute the leased task, emit an attributed report | Settle, witness its own output, write authoritative state, outlive its lease |

Escalation to the owner is a first-class transition, not a failure: judgement
remains a visible pending right at every tier. A controller is an operator
under grant like any other; its sequencing decisions are attributable events.

Tier depth is fixed at three. A deeper chain adds crossings and receipts
without adding a new kind of accountability.

## Two dyads

Two paired stances govern the loop. Both are typed stances that any qualified
operator may hold under grant; neither hardcodes a named person or model
(`OPEN-SEAMS.md` S7). In both dyads, neither hand settles anything alone —
results exist only in combination.

**Left/Right — the authority dyad.**

- `LEFT` — synthesis: inspect, compare, draft, implement, propose.
- `RIGHT` — judgement: product intent, naming, ratification, phase gates.

Left output is always a proposal. Right holds ratification. A left hand may
never present its synthesis as the right hand's judgement.

**Red/Blue — the verification dyad.**

- `BLUE` — construction: build the positive path, its contract, and its
  declared positive and defeating conformance cases.
- `RED` — adversarial witnessing: attempt to defeat the built artifact and
  discover the defeating cases Blue did not declare.

Blue's passing run establishes `BUILT` evidence only. Red's engagement is how
`WITNESSED` is earned. Declared defeating fixtures are Blue work — known
adversarial cases stated in advance. Red work is generative: refusal bypasses,
authority escalation, stale-source use, provenance gaps, retraction that
erases history, and any defeat the builder did not anticipate.

**Combination outcomes.** Each dyad combines into a named outcome; a concern
goes green only when both have combined.

- `PURPLE` — the settled combination of the verification dyad: Blue's built
  proof plus Red's converged adversarial witnessing, recorded as the
  engagement receipt that satisfies the release gate.
- `JOINED` — the settled combination of the authority dyad: a synthesis
  proposal met by explicit judgement, recorded as a ratification receipt.
- `GREEN` — the derived go-state of a concern at its current gate: its
  verification is `PURPLE` and its authority is `JOINED`.

Combination outcomes name receipts and derived state, not stances or
standings. No operator holds `PURPLE` or `JOINED`: an operator holding both
hands of a dyad is the self-witnessing and self-ratifying failure the
contract exists to prevent. `GREEN` is derived from recorded receipts, never
selected directly, and lapses when either combination is countered or
invalidated.

## Concern registry

A **concern** is a registered unit of monitored work. Each concern records:

- a stable name and its owning domain or service;
- the governing contract and document set;
- current artifact standing in the
  `OPEN -> BUILT -> WITNESSED -> RATIFIED` lifecycle;
- the next gate and its blocking open decisions;
- the admitted effect envelope for the current phase.

The registry is a projection derived from `STATUS.yaml`, `decisions/`, and
`OPEN-SEAMS.md`. It introduces no competing System of Record: standing changes
land in the owning documents, and the registry is rebuildable from them. A
controller that keeps private concern state has left the contract.

## Repository carrier lifecycle

Repository history and evidence use different clocks. Construction may move;
qualification may not silently move with it. The executable state machine is
`contracts/repository-candidate-lifecycle.json`; this section composes that
contract into the SDLC and does not define a second vocabulary.

1. **Construct while `MUTABLE`.** FEAT/DEV work may amend, autosquash, or rebase
   onto current `main`. Prefer reconciliation by rebase over merging `main`
   into a topic branch because the carrier is still disposable construction
   history.
2. **Freeze before qualification.** Once Blue presents the exact candidate for
   CI, Red, witness, RC qualification, or acceptance evidence, create a
   `FROZEN` repository candidate naming `base_commit`, `candidate_commit`, and
   `candidate_tree`. Evidence names that subject, not merely its patch.
3. **Rewrite work, never evidence.** A `FROZEN` candidate is not rebased,
   amended, squashed, force-updated, or replaced in place. If its base is stale
   or the candidate needs repair, mark it `SUPERSEDED`, return the work to a
   mutable carrier, and freeze a new subject. Evidence for the old subject
   remains historical evidence for that old subject.
4. **Land the exact subject.** A qualified candidate reaches `LANDED` through a
   merge settlement that preserves the candidate commit as ancestry. Squash
   merge and rebase merge are not landing methods for a qualified candidate
   because both replace the identity that was observed.
5. **Patch equivalence does not transfer standing.** It can prove that bytes or
   work are already carried elsewhere; it cannot move qualification, witness,
   acceptance, or settlement from one repository subject to another.

This carrier lifecycle is orthogonal to artifact standing. `FROZEN` does not
mean `WITNESSED`; `LANDED` does not mean `RATIFIED`. It only makes the subject of
those claims stable and reconstructable.

## Skill axes

Skills are declared competence sets loaded by an operator for a role. They
come in two orthogonal axes; a working operator holds exactly one tier skill
and the domain skills its concern requires.

**Tier skills** state how a participant at that altitude behaves:

- `Control Skill` — planning, dispatch, settlement, escalation, refusals.
- `Orchestration Skill` — decomposition, leasing, observation, reporting.
- `Worker Skill` — bounded execution, reporting, lease discipline.

**Domain skills** state what competence a concern requires:

- `Product Skill` — requirements, PRD alignment, decision drafting.
- `Development Skill` — the implementation order and technical baseline as
  owned by `AGENTS.md` and `ENGINEERING.md`.
- `QA Skill` — both verification stances: the Blue lane (conformance, unit
  tests, repository verification, positive paths) and the Red lane
  (defeat-seeking engagement under a scoped grant).
- `Release Skill` — release notes, documentation, and marketing drafts as
  `RECORD_LOCAL` artifacts, plus the visible refusal of every
  `EXTERNAL_WORLD` publication step while `no_external_effects_in_phase_i`
  and open decision O1 stand.
- `Feedback Skill` — standing review, residual and seam capture, correction
  proposals routed into `OPEN-SEAMS.md`, `decisions/`, and `STATUS.yaml`.

A skill links to the owning governing document for every rule it applies and
may sequence or cite owned rules; a skill that restates one as independent
authority is defective. On any divergence between a skill and an owning
document, the owning document prevails.

## Workflow templates

A workflow template is a declared orchestration shape the Control tier may
dispatch for a concern. Phase-I templates:

| Template | Purpose | Terminal artifact |
| --- | --- | --- |
| **Report** | Bounded state summary of one concern | Handoff note per `AGENTS.md` context hygiene |
| **Standup** | Registry-wide standing sweep | Updated standings and next bounded operations |
| **Review** | Change protocol plus both QA lanes over a change | Settlement receipt and standing evidence |
| **Demo** | Walk a proving operation end to end | Witnessed narrative with reconstructable receipts |
| **Design** | Explore and converge on a consequential choice | A `decisions/` record at proposal standing |

Templates are process declarations. Executable orchestration scripts are not
admitted before the logical specification and defeating fixtures that govern
them, per the protected boundary in `STATUS.yaml`.

## Release gate

Work on a concern may not advance past `BUILT` until its verification dyad
combines to `PURPLE`: a settled Red engagement receipt over Blue-built work.
Repository-backed evidence at this gate must name one `FROZEN` candidate under
the carrier lifecycle above. The gate's rules:

1. A Red engagement runs under a typed grant naming its target surfaces,
   effect class (Phase I: `RECORD_LOCAL` only, isolated environments, no
   authoritative writes), budget, and exit criterion.
2. Red findings are proposals. A claimed defect counts only after it
   reproduces under observation independent of the Red operator.
3. Every confirmed finding becomes a permanent defeating fixture in the
   conformance corpus. A defeat, once found, can never recur silently.
4. Resolution of a confirmed finding is fix-and-repass. A fixture may not be
   weakened to admit a participant; the owner may instead accept a residual
   explicitly as named debt with a decision record.
5. The bounded exit criterion is dry-run convergence: a declared number of
   consecutive engagement rounds with no new confirmed finding. Red may fail
   a release; it may not filibuster one.
6. Red operators receive the contract, the claimed invariants, and the built
   artifact. The builder's tests, plan, and assumptions are part of that
   artifact: Red may read them and attack them, and never uses them as
   evidence or as the oracle. Red derives its own checks from the contract.
   Like the conformance oracle, the Red lane must not import the
   participant's implementation into its oracle.

`RATIFIED` remains the owner's judgement and is not reachable by any
combination of machine evidence.

## Bindings

This loop is defined stack-neutrally. A harness realization — skills, agent
configuration, and workflow tooling for a specific model host — is an
operator binding under `bindings/` rules: it may project the loop differently
but may not introduce private standing, authority, transitions, or storage
writes.

`Sov` is the portable main operating-agent profile and the default candidate to
occupy Control. The candidate designation supplies context and agency, not the
Control grant: the current actor, task, capability, effect envelope, and live
authority still determine whether Sov may occupy that tier. `SOV.md` and
`bindings/sov/` own the portable profile; no host binding owns its semantics.

The `.claude/` directory is the first such binding, admitted as a provisional
target by owner direction. The model-substitutability requirement applies to
the loop itself: a second, materially different binding must be able to run
the same loop against the same governing documents. A loop that only one
provider's harness can operate fails the Soveraeign bar it is meant to
enforce.

## Acceptance

This loop is `BUILT` when the governing documents register it, repository
verification passes, and the binding skeleton exists at proposal standing. It
is `WITNESSED` only after its own release gate is exercised against a real
concern; a bounded, owner-directed provisional exercise is admitted for that
witnessing before ratification. It is `RATIFIED` only when Bdo accepts the
tiers, dyads, registry derivation, and Red-gated release requirement recorded
as open decision O13. O13 therefore gates activation — the loop becoming the
required process — not the provisional exercise that witnesses it.
