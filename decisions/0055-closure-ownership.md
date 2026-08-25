# 0055 · A concern is carried to closure, not to an artifact about closure

Status: `OWNER-DIRECTED · PROPOSED`

## Decision

A participant that accepts a bounded concern carries it to a landed result. The default
loop is `inspect -> implement -> test -> recruit helper -> repair -> verify -> present or
land`.

An issue, a branch, a pull request, a review finding, a TODO, or a question for the owner
records a concern. None of them advances one. Opening one counts as progress only when it
is the shortest remaining path to the result.

`AGENTS.md`, Closure ownership, is the normative statement. `CONTRIBUTING.md` carries the
working path. `contracts/closure-ownership.json` is the declared table both read, and
`scripts/sov_closure.py` grades a claimed handoff against it.

## What the table decides

Five seams are admissible, and every other stopping point is refused as reachable closure:

| Seam | The participant genuinely lacks | Asked of |
| --- | --- | --- |
| `AUTHORITY_SEAM` | a typed grant it cannot mint | the tier that holds it |
| `POLICY_SEAM` | a ruling between two settled constraints | controller or owner |
| `EFFECT_SEAM` | an effect class the phase does not admit | owner |
| `DEPENDENCY_SEAM` | an artifact another participant must produce, an independent observation included | worker, orchestrator, controller |
| `ACCEPTANCE_SEAM` | owner acceptance of a finished evidenced result | owner |

Ten refusal codes fire against everything else. `ROUTINE_DECISION` refuses asking another
tier to settle a reversible engineering choice. `ABSORBABLE_FOLLOW_ON` refuses filing work
that crosses no service, effect class, or authority boundary. `WIP_EXCEEDED` refuses a
second concern opened before the first landed. `HELPER_NOT_RECRUITED` refuses asking
another tier for a reading a recruitable helper could have given. `HELPER_AS_WITNESS`
refuses an editing helper offered as the independent observation. `LOOP_INCOMPLETE`
refuses a handoff that skipped a step whose tool the participant held.
`REACHABLE_ALTERNATIVE`, `SEAM_UNDECLARED`, `PROVISION_UNROUTED`, and
`JUDGEMENT_NOT_OWNER` complete the set. Nineteen declared cases in
`conformance/fixtures/closure/handoff-cases.json` prove eight seams admitted and every
refusal code actually firing.

## The absorption test, which is the whole of the scope-creep line

Follow-on work is absorbed into the concern in hand when `same_service`,
`same_effect_class`, and `same_authority` all hold. Crossing any one of the three mints a
separate concern. Crossing none of them is the concern discovered more fully, and filing
it is the externalizing this decision refuses.

This supersedes the flat reading of "scope creep is a refusal, not a favor" in
`.claude/agents/sov-worker.md`. That sentence was written against a worker that widens its
grant; read flatly it also refused a worker that finished what it started. The three
predicates separate the two cases, and the boundary is unchanged: an operation that
crosses a service, an effect class, or an authority is still refused.

## Helpers, and why recruiting one costs nothing

A participant recruits a helper model or subagent without asking. Arranging ordinary model
assistance is not a request to another tier; it is using the environment. The helper is
pointed at the defect the participant cannot see, the missing test, the scope drift, the
unnecessary abstraction, and the authority assumed rather than held. The participant
repairs what the helper finds; it does not file it.

A helper that read or edited the change is inside the build and can never witness it. That
is why recruiting one is free of standing consequence in both directions: it cannot
manufacture evidence, and refusing to recruit one saves nothing. `.claude/agents/sov-worker.md`
gains the `Agent` tool so a launched worker can actually do this; a worker whose invocation
has no such tool records `recruit_helper` as absent, and the table excuses the step.

## Defaults taken

- **The evaluator holds no copy of the table.** Seams, routine decisions, the absorption
  predicates, the WIP ceiling, the loop's tool map, and the order refusals are reported in
  all live in the contract. Admitting a new seam or raising the ceiling is a contract
  change with a case behind it, not an edit to `scripts/sov_closure.py`.
- **The WIP ceiling is one unlanded concern per participant.** One is a default, not a
  measurement; nothing yet counts live branches or pull requests per participant.
- **`present` is a leased worker's terminal.** Harness roles may not run `git commit`, so
  a launched worker cannot land. Recorded honestly rather than papered over; see
  `OPEN-SEAMS.md` S21.
- **Existing vocabulary is reused rather than duplicated.** Provisions are the
  `grant | judgement | contract | fixture | capability | observation` set from
  `contracts/issue-metadata.schema.json`; tiers are the `worker | orchestrator |
  controller | owner` set from the same schema; refusal codes follow the `SPEC.md` shape.
  Judgement is owner-held here for the same reason it is there.
- **Scoped to non-Sov participants.** Bdo scoped this change to agent types other than Sov
  agents. `SOV.md`, `bindings/sov/`, and `.claude/agents/sov.md` are unchanged.

## Residuals

1. **No landing capability.** No harness role can reach the terminal the contract names.
   `OPEN-SEAMS.md` S21 records the three readings and settles none. Five live sessions
   currently share one working tree, which is a reason the commit boundary is where it is,
   not an argument that it belongs there.
2. **The claim is a self-declaration.** `sov_closure.py judge` grades what a participant
   says about its own handoff — which tools it held, which loop steps it took, whether it
   recruited a helper. A participant that misstates its claim passes. Independent grading
   would need handoffs to reach the Record Service journal as events, which they do not.
   This is the same gap `AGENTS.md` names when it says an executor self-report is not
   authority; the table is a discipline, not an oracle.
3. **The WIP ceiling is not measured.** Nothing reads live branches, pull requests, or
   assignments per participant, so `WIP_EXCEEDED` fires only against a count a participant
   declares. Closing this needs assignment machinery that does not exist.
4. **Sov is unaddressed.** Whether closure ownership binds a Sov-loaded operator is not
   settled here. `SOV.md` and the portable profile do not restate it, and a Sov-loaded
   operator reading `AGENTS.md` will find a section that names the harness roles and not
   the profile. Bdo scoped it that way; the question of whether the profile should carry
   the same loop is open.
5. **The `WITNESSED` step is unreached.** This decision is registered in
   `STATUS.yaml` under `acceptance_policy.unruled_proposals` and the gate is green, which
   establishes `BUILT` and nothing further. No participant other than the one that wrote
   the table has re-derived its refusals, so the closure rules are not witnessed by
   anything except their own corpus.

## Demotion

Demote this decision if participants begin absorbing work across service, effect, or
authority boundaries and calling it closure; if the loop is used to justify a large
unreviewed change presented as one concern; if `recruit helper` becomes a step performed
for the record rather than for a reading; or if a helper's contribution starts appearing as
independent observation in a witness report.

The absorption test is what keeps the first failure visible: three predicates, all of which
must hold, each of which a reader can check against the diff.

## Source

Bdo's 2026-08-24 direction: a worker that accepts a bounded concern should be expected to
carry it toward a landed result rather than treating the creation of issues, branches,
pull requests, reviews, TODOs, or owner questions as progress by themselves; and this must
not wait for identity, budgeting, scheduling, agent-runtime, or assignment machinery that
does not yet exist. Where the machinery is absent, the strongest available approximation is
used and the gap is recorded as a residual.
