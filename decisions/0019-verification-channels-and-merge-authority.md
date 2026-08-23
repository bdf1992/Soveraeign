# 0019 · Verification channels and delegated merge authority

Status: `PROPOSED · OWNER DIRECTED · OWNER RATIFICATION PENDING`

Bdo directed this design in session on 2026-08-23. Direction is not
ratification: under `AGENTS.md` only Bdo ratifies, and ratification reaches the
repository through code owner review on `STATUS.yaml` and `decisions/`. This
record is the proposal that review would rule on.

## Decision

### 1. Verification channels are a projection, never a rename

`SDLC.md` owns the verification vocabulary and keeps it. This record adds a
*readout* over the receipts that vocabulary already produces:

| Channel | Lit when | Sourced from |
| --- | --- | --- |
| `blue` | built, tested, positive and defeating cases declared | `scripts/verify.py`, conformance controls |
| `red` | adversarially probed | mutation score, Red engagement receipts |
| `green` | met the world: demoed, deployed, feedback closed | release and feedback evidence |

Channels are orthogonal and carry intensity, not a boolean, so a concern reads
as a graded colour rather than a rung. Each two-channel combination owes exactly
its missing channel, which is the automation rule — the colour names its own
next operation:

- `blue + green` owes `red` — shipped without ever being attacked
- `blue + red` owes `green` — proven but never shipped
- `red + green` owes `blue` — exercised but not built to contract

The projection is derived from recorded receipts and never selected directly,
which is the rule `SDLC.md` already states for `GREEN`.

### 2. The green channel is not self-generable

`blue` and `red` are established by the repository acting on itself. `green`
cannot be: it requires the world, or it requires Bdo. The oracle is the meter
that computes channel values from evidence; it is not a stance, not a team, and
holds no authority. This preserves the `SDLC.md` rule that no operator holds
both hands of a dyad.

### 3. Model work never runs in CI

CI carries no subscription, so a check that needs a model needs metered API
spend. Under Bdo's 2026-08-23 sourcing direction that spend must be earned
against measured value, which a per-pull-request check cannot demonstrate.
Therefore:

- **CI runs token-free work only, and CI work may block.** Repository
  verification, contract checks, ticket transition evaluation, and mutation
  scoring.
- **Model work runs on the local scheduler, and reports only.** Pull request
  review, code review, and generative Red engagement, under `.claude/schedules/`
  on the operator subscription.

A blocking gate that depends on a purchased key is a gate that fails open when
the key is absent, which is the defect recorded in section 5.

### 4. Merge authority is delegated by state, not by item

Bdo does not review pull requests. Bdo reviews changes to the state that governs
pull requests. Given all required checks green:

- a pull request proposing **no standing change** merges without owner action
- a pull request touching `STATUS.yaml`, `decisions/`, or any governed document
  **waits for code owner review**, which is Bdo
- a pull request proposing a **standing advance** waits for the same review
- any required check red blocks the merge for everyone

The owner-facing surface is therefore the state, not the queue. Activating the
branch protection that makes this binding is `STATUS.yaml` O16, which remains
unruled; this record proposes the rule that protection would enforce.

## Consequences

- Nothing in `SDLC.md` is renamed. `BLUE`, `RED`, `PURPLE`, `JOINED`, and
  `GREEN` keep their meanings as stances and settled outcomes. The channels are
  a lowercase readout over the same receipts.
- **One collision is not resolved here and is queued as O19.** `SDLC.md` `GREEN`
  is the derived go-state combining `PURPLE` and `JOINED`. The `green` channel
  in section 1 is contact with the world. In Phase I these diverge: the former
  is reachable, the latter is not, because `no_external_effects_in_phase_i`
  forbids the demo, deploy, and feedback evidence that would light it. Bdo rules
  whether the channel is renamed or the readout adopts the existing term.
- Under this projection every service in `STATUS.yaml` currently reads `blue`.
  `BUILT_SELF_TESTED_NOT_WITNESSED` is `red = 0` stated in prose, and it is on
  every line. Nothing in the repository has been adversarially engaged.
- The best grade reachable in Phase I is `blue + red`. `green` is pinned at zero
  by protected boundary `no_external_effects_in_phase_i` and lifts only at the
  phase gate, which is Bdo's.
- Mutation scoring gives `red` a measured value rather than an asserted one, and
  costs no tokens at runtime. Its creation, maintenance, and interpretation are
  agent work on the subscription; only the per-run cost is zero, and only while
  per-run output stays mechanical.

## Evidence

Two merged pull requests carried CRLF onto `main` under a passing CI: #58 (two
files) and #44 (twenty files). Neither was defective work; both were
insufficiently gated. The enforcement that detects them —
`.gitattributes`, the `scripts/lint.py` line-ending rule, and the independent
byte scan in `scripts/tests/test_lint.py` — existed only on an unpushed branch.
Under section 1 both pull requests were `blue + green` with `red = 0`, which the
`SDLC.md` ladder had no way to express.

`main` carried no branch protection at the time of writing: every gate reported
and none blocked.

## Known defect this record names

`.github/workflows/qa-lanes.yml` job `red · adversarial screening` reports
**pass** when the lane is unconfigured. It requires the `ANTHROPIC_API_KEY`
secret and the `SOV_RED_LANE_ENABLED` variable; neither is set. The job writes
`RED_LANE_UNCONFIGURED` to the step summary and exits zero, so at the check-list
level a refusal and a real screening are indistinguishable.

Section 1 implies the rule this violates: a disabled lane must not render as a
pass, because a pass on an unlit channel is `blue + green` wearing `blue + red +
green`. Section 3 resolves it by replacing the blocking red gate with mutation
scoring, which needs no key and cannot fail open.

## Source and authority

- `SDLC.md` two dyads, combination outcomes, and release gate — the vocabulary
  this record projects over and does not alter
- `AGENTS.md` authority, evidence, and standing: a build report never witnesses
  itself, and only Bdo ratifies
- `STATUS.yaml` O16 (coordination activation, unruled), protected boundary
  `no_external_effects_in_phase_i`, and the service standing fields read in
  Consequences
- `decisions/0016-github-coordination-registrar.md` for the coordination
  surface this record's section 4 gates
- Bdo's 2026-08-23 direction: verification channels, green as outside
  validation, open-weight-first model sourcing, and the merge authority rule in
  section 4
