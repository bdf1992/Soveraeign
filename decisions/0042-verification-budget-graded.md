# 0042 · The verification budget becomes graded, ceiling fifteen seconds

Status: `PROPOSED · BDO HAS NOT RULED`

Bdo directed both moves: raise the ceiling from three seconds to fifteen, and
grade the wall time inside it rather than reporting one bit. This record exists
because the number is a term of a baseline Bdo already accepted
(`decisions/0012`), and because six surfaces stated the old figure as a rule.

## What the gate now says

`scripts/verify.py` holds bands, and the ceiling is derived from the slowest:

| Grade | Wall time | Exit |
| --- | --- | --- |
| `PLATINUM` | 3.000 s or less | 0 |
| `GOLD` | 6.000 s or less | 0 |
| `SILVER` | 15.000 s or less | 0 |
| none | over 15.000 s | 1 |

Every passing run prints the grade it earned and what the next faster band
costs, for example `GRADE: GOLD at 4.011s; PLATINUM needs 3.000s or less`. Over
the ceiling the run fails and says so as before. Losing a grade is a reportable
observation; it is not a failing gate.

`BUDGET_GRADES` is the single declaration and `BUDGET_SECONDS` is derived from
its last entry, so the two cannot drift apart. A test asserts that.

## What changed

- `scripts/verify.py`: `BUDGET_SECONDS` moves from `3.0` to `15.0` and is now
  derived from `BUDGET_GRADES`. Two functions were added, `grade` and
  `budget_line`. The module is 295 lines against the 300-line limit.
- `scripts/tests/test_verify_observations.py`, `BudgetReporting`: eight cases.
  The positive ones pin the bands, their order, ceiling inclusivity, and the
  next-band phrasing. The defeating one proves that past the slowest ceiling no
  grade is earned and the overrun still enters the failure list, so grading
  cannot quietly turn the budget into advice.
- Root surfaces restating the rule: `AGENTS.md` (Testing and verification),
  `ENGINEERING.md` (stack table and Acceptance), `CONTRIBUTING.md`,
  `README.md`, `.cursorrules`.
- Nine skill files under `.claude/skills/` carry the figure for launched
  agents. All nine now state the bands.
- `.claude/workflows/sov-f2-control.js`: `ORACLE_LAW` now forbids loosening a
  `BUDGET_GRADES` band as well as raising `BUDGET_SECONDS`, and the witness
  prompt looks for both. `BUDGET_LAW` described a standing residual: this tree
  is a git worktree whose filesystem ran the tooling tests about 0.5 s slower
  than the main checkout, so the gate exited 1 at about 3.2 s while every check
  passed. That residual is gone, because a run at that speed now earns `GOLD`
  and passes. The law says so instead of teaching agents to ignore an exit code.
- Three rationale comments cited the old figure while recording a measurement
  taken under it, in `scripts/sov_mutate.py`,
  `scripts/tests/test_sov_mutate.py`, and
  `services/console/tests/test_operator_continuity.py`. The two describing a
  past measurement now state no figure; rewriting the number there would have
  made a true record false.

Deliberately unchanged:

- `.github/workflows/verify.yml` keeps `timeout-minutes: 5`.
- The observation JSON from `--json` still carries one entry per check and no
  budget entry. `sov-f2-control.js` depends on exactly that to tell a host
  residual from a real failure, and the grade is a property of the run rather
  than of any one check.
- `conformance/fixtures/lineage/lesson-cases.json` keeps the three-second
  figure. It is a recorded lesson with a git evidence address, not a live rule.
- `decisions/0012` and `decisions/0039` are not edited. This record amends the
  verification term in the first and answers the defect recorded in the second.

## What was measured

The old budget was already being missed. `decisions/0039` recorded 2.55-2.99 s
across measured runs against the 3.000 s ceiling, and one run at 4.359 s under
load from another process in the same tree. It named raising the budget a policy
change and declined to make it.

The gate was failing on the budget outright before this change: `verification
budget (4.022s > 3.000s)`, then 4.051 s, 4.046 s, and 4.184 s across three runs
timed from outside the process. Those runs carried unrelated failures from other
in-flight work in the same tree, which moves the figures at the margin and not
the conclusion. Four seconds earns `GOLD`.

The cause is unchanged and is not addressed here: twenty checks fan out as
twenty concurrent interpreter startups. `decisions/0039` established that
clearing every `__pycache__` moved wall time by under 50 ms, so the cost is
process startup rather than bytecode compilation.

## What it costs

A single fifteen-second ceiling would have been the wrong trade on its own. It
is roughly 3.7x the current measurement, and between four and fifteen seconds
the gate would have reported nothing, so a check that started reaching the
network or a test that grew an fsync loop would land silently until it was
nearly four times worse than today. The three-second ceiling had been doing that
work by accident.

Grading is what pays for the ceiling. The gate keeps the three-second figure as
a target visible on every run instead of a wall that fails the build, so the
slowdown signal survives the raise. What it costs instead:

- The bands are judgement, not measurement. Three, six, and fifteen were chosen,
  not derived from anything.
- A grade is machine-dependent. The same commit can earn `PLATINUM` on one host
  and `GOLD` on another, so a grade is only comparable against itself on one
  machine. It is absent from the observation JSON for that reason.
- A printed grade needs a person or a prompt to read it. Nothing enforces a
  grade, and nothing should. Enforcing one would recreate the failing ceiling
  this record removed.

Residual: reducing the fan-out is verification-domain work and is still undone.
`PLATINUM` is now the name of that job.

## Owner action

`ACCEPT` leaves `BUDGET_GRADES` at 3/6/15, keeps the six surfaces as edited, and
`engineering_framework_status` carries `BUDGET_GRADED_UNDER_0042` until the
baseline is re-accepted with the new terms.

`REJECT` restores a bare `3.0` ceiling on every surface and returns the gate to
failing on the budget, which then has to be answered by cutting the fan-out
instead.

## Demotion

Defeated by a measurement showing the gate runs well under three seconds on
ordinary hardware, which would make the old ceiling right and this host's timing
the anomaly. Also defeated by a fan-out reduction that brings wall time back
under three seconds on every host, after which the ceiling should come down and
the bands should tighten with it. Defeated in a different direction if grades
prove to be noise: if one unchanged tree swings between two bands run to run,
the grade is measuring load rather than the repository, and it should be dropped
rather than tuned.

## Sources

- `decisions/0012-engineering-baseline.md`, Verification and hygiene.
- `decisions/0039-the-node-surface.md`, the recorded budget defect and the
  4.359 s observation.
- `scripts/verify.py`, `BUDGET_GRADES`, `grade`, `budget_line`, and the budget
  check at the end of `main`.
- `scripts/tests/test_verify_observations.py`, `BudgetReporting`.
- `.claude/workflows/sov-f2-control.js`, `ORACLE_LAW` and `BUDGET_LAW`.
- Measured on this host on 2026-08-23 across four runs.
- Directed by Bdo in an interactive Claude Code session; recorded there.
