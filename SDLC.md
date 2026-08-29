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

The two lanes run at different cadences. Blue is continuous and belongs to every
consequential unit of work. Red is a separately queued operation over a named,
immutable milestone target. A concern may therefore continue moving in circuit
stage, scope, and implementation state while its standing remains `BUILT`.
Outstanding witness work is not itself a block; it gates only a transition whose
contract consumes independent observation. `decisions/0098-milestone-witnessing.md`
records the cadence change.

**Combination outcomes.** Each dyad combines into a named outcome; a concern
goes green only when both have combined at the named gate being evaluated.

- `PURPLE` — the settled combination of the verification dyad over one named
  milestone target: Blue's built proof plus Red's converged adversarial
  witnessing, recorded as the engagement receipt that satisfies that milestone's
  witness gate.
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

A concern at `BUILT` may still have reachable engineering work. When independent
witness is due, the obligation is represented as a named
`verification-engagement` over the milestone rather than by freezing every
BUILT concern in place.

The registry is a projection derived from `STATUS.yaml`, `decisions/`, and
`OPEN-SEAMS.md`. It introduces no competing System of Record: standing changes
land in the owning documents, and the registry is rebuildable from them. A
controller that keeps private concern state has left the contract.

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
- `QA Skill` — both verification stances: the continuous Blue lane
  (conformance, unit tests, repository verification, positive paths) and the
  milestone Red lane (defeat-seeking engagement under a scoped grant).
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
| **Review** | Blue verification over an increment, or a separately queued Red engagement over a named milestone | Build evidence or settlement receipt at the gate actually exercised |
| **Demo** | Walk a proving operation end to end | Witnessed narrative with reconstructable receipts |
| **Design** | Explore and converge on a consequential choice | A `decisions/` record at proposal standing |

Templates are process declarations. Executable orchestration scripts are not
admitted before the logical specification and defeating fixtures that govern
them, per the protected boundary in `STATUS.yaml`.

## Release gate

Verification gates claims and named milestones, not ordinary reachable work.
A concern may continue to advance in circuit stage, scope, and implementation
state while its artifact standing remains `BUILT`. It may not claim
`WITNESSED`, cross a release or acceptance transition that explicitly requires
witnessed evidence, or claim a work-circuit stage such as `CAPABLE_NODE` whose
admission explicitly requires outside observation, until the required
independent evidence exists.

A witness target is named before Red runs. It identifies an immutable revision
and the claim or surface being attacked. In the current coordination contract a
`verification-engagement` still pins `target_pr` and `target_head`; an
integration PR may therefore carry a milestone without making the PR itself the
semantic identity of the milestone. Generalising the target carrier is separate
work.

The gate's rules:

1. Blue remains part of each consequential increment: positive cases, declared
   defeating cases, local tests, semantic conformance, and repository
   verification are not deferred with witness.
2. A Red engagement is queued when a meaningful milestone requires independent
   verification. It runs under a typed grant naming its immutable target
   surfaces, effect class (Phase I: `RECORD_LOCAL` only, isolated environments,
   no authoritative writes), budget, and exit criterion.
3. Red findings are proposals. A claimed defect counts only after it reproduces
   under observation independent of the Red operator.
4. Every confirmed finding becomes a permanent defeating fixture in the
   conformance corpus. A defeat, once found, can never recur silently.
5. Resolution of a confirmed finding is fix-and-repass. A fixture may not be
   weakened to admit a participant; the owner may instead accept a residual
   explicitly as named debt with a decision record.
6. The bounded exit criterion is dry-run convergence: a declared number of
   consecutive engagement rounds with no new confirmed finding. Red may fail a
   milestone; it may not filibuster one.
7. Red operators receive the contract, the claimed invariants, and the built
   artifact. The builder's tests, plan, and assumptions are part of that
   artifact: Red may read them and attack them, and never uses them as evidence
   or as the oracle. Red derives its own checks from the contract. Like the
   conformance oracle, the Red lane must not import the participant's
   implementation into its oracle.
8. A failed witness holds or demotes the named milestone and dependent claims
   that consume its defeated predicate. It does not implicitly freeze unrelated
   reachable work. This is the verification form of “blocked edge is not
   blocked frontier.”
9. Deferred witness must remain addressed. A milestone that owes independent
   verification has a queued `verification-engagement`; “we will witness it
   later” with no address is not a verification plan.

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
is `WITNESSED` only after its milestone witness gate is exercised against a real
concern; a bounded, owner-directed provisional exercise is admitted for that
witnessing before ratification. It is `RATIFIED` only when Bdo accepts the
tiers, dyads, registry derivation, and Red-gated release requirement recorded
as open decision O13. O13 therefore gates activation — the loop becoming the
required process — not the provisional exercise that witnesses it.
