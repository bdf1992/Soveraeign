# 0100 · Launch your own witness: the loop gains the step it always implied

Status: `OWNER-DIRECTED · ACCEPTED POLICY`

Accepted by Bdo (seat:root) 2026-08-28 through acceptance packet A19
(`acceptance/accepted/A19.json`), recorded at 2026-08-28T18:04:42Z in the
acceptance ledger. The acceptance was given verbally in-session and recorded
by the building session as scribe; the judgement is the owner's.

## Decision

The default closure loop gains an explicit required step between `verify` and
`present or land`: launch an independent witness. It is now
`inspect -> implement -> test -> recruit helper -> repair -> verify ->
launch witness -> present or land`.

The rule "a build cannot witness itself" names a dependency, not a stopping
point. A builder that can launch a witness — a participant that did not build
or read the change — is expected to launch one and receive its observation as
its own step, without asking. Presenting an uncommitted working tree with
"I cannot witness my own build, and landing belongs to the standing loop" as
the terminal is the failure this decision refuses. The landing gate
(`scripts/sov_land.py`) is invoked by whoever holds the branch; the standing
loop is one caller of that gate, not its owner.

Bdo directed this correction on 2026-08-28 after a session reported exactly
that terminal: everything uncommitted in the shared tree, on the stated ground
that it could not witness its own build.

## What changed

- `contracts/closure-ownership.json`: a `witness` step (tool
  `launch_witness`, required) between `verify` and `present_or_land`, and
  `launch_witness` in the declared tool vocabulary. The existing excusal rule
  is unchanged: a required step is excused only when the invocation genuinely
  lacks its tool, so a leased worker or restricted session that cannot launch
  agents is not refused.
- `conformance/fixtures/closure/handoff-cases.json`: C-001 takes the step;
  C-114 is the defeating case — a builder with `launch_witness` available
  hands back an unwitnessed uncommitted tree and is refused
  `LOOP_INCOMPLETE`.
- `AGENTS.md` Closure ownership, `CONTRIBUTING.md` Carrying a concern to
  closure, and `CLAUDE.md`: the loop sentence names the step, and each states
  the corrected reading of the self-witness rule.

`LOOP_INCOMPLETE` already existed and its evaluator is unchanged; the step is
data, which is the point of the table.

One carried hunk is claimed here rather than landed silently: AGENTS.md's
Testing and verification section still stated the superseded `decisions/0050`
rule (past fifteen seconds the run fails). An earlier session had already
rewritten it in the working tree to the `decisions/0081` language — debt, not
failure; per-check ceilings in `contracts/verification-budget.json`; the
landing gate as the semantic rule — and left it uncommitted. The independent
witness for this concern surfaced the hunk as undeclared. It aligns the
document with already-committed policy and changes no rule, so it is committed
with this concern and named here.

## What would defeat this

- A measured pattern of witness launches that add cost without ever defeating
  a claim: the step would then be ceremony, and it should become conditional.
- A host posture where the witness-capable tool is routinely present but
  witness runs are too expensive for routine concerns: the ceiling belongs in
  `helper_policy`-style budget terms, not in a required step.
- Evidence that the step pushes builders to launch cosmetic witnesses that
  rubber-stamp: the defect would be witness quality, owned by
  `contracts/standing-grants.json`'s independence requirement, and this step
  would need a quality predicate rather than a presence predicate.

## Residuals

- `decisions/0055-closure-ownership.md` states the older seven-step loop in
  its Decision section. It is a historical record and is not edited; this
  decision supersedes its loop sentence only.
- Whether the step binds a Sov-loaded operator follows the same open residual
  as the rest of closure ownership (`decisions/0055`, residuals).
