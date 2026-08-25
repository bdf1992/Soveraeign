# 0050 · The verification budget becomes graded, ceiling fifteen seconds

Status: `PROPOSED · BDO HAS NOT RULED`

Bdo directed both moves: raise the ceiling from three seconds to fifteen, and
grade the wall time inside it rather than reporting one bit. This record exists
because the number is a term of a baseline Bdo already accepted
(`decisions/0012-engineering-baseline.md`), and because five surfaces stated the
old figure as a rule.

Numbering note: drafted as 0042 on `feat/federation-harness-and-hardening`, where
that number was taken by `0042-the-decision-queue-is-not-a-queue.md` before this
could land. 0043 and 0044 are taken there, 0045 to 0047 by the acceptance
records, and 0048 to 0049 by `docs/principal-identity`. 0050 is the first number
free against all of them.

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
the ceiling the run fails and says so exactly as before. Losing a grade is a
reportable observation; it is not a failing gate.

`BUDGET_GRADES` is the single declaration and `BUDGET_SECONDS` is derived from
its last entry, so the two cannot drift apart. A test asserts that.

## Why now

The gate was not merely tight, it was failing, and it was failing selectively.
Measured on 2026-08-24 across the open pull requests:

- `feat/acceptance-docket`, one commit, two runners: Python 3.11 passed at
  2.674 s and Python 3.12 failed at 3.233 s. Same code, same run, one number
  either side of the ceiling.
- `feat/session-guardrails`: `blue · construction` failed at 3.856 s while
  `repository (3.11)` and `repository (3.12)` passed at 2.354 s and 2.319 s on
  that same commit. It passed on a re-run that drew a faster runner.
- `feat/federation-harness-and-hardening`: `verification budget (3.309s >
  3.000s)`.

A gate whose verdict depends on which runner it drew is not measuring the
repository. Every one of those runs had all its checks pass.

The cause is unchanged and is not addressed here: the checks fan out as
concurrent interpreter startups, and `decisions/0012` records the cost as
process startup rather than bytecode compilation.

## What changed

- `scripts/verify.py`: `BUDGET_SECONDS` moves from `3.0` to being derived from
  `BUDGET_GRADES`, whose slowest band is 15.0. Two functions added, `grade` and
  `budget_line`. The passing path prints the grade.
- `scripts/tests/test_verify_budget.py`: ten cases, new file. The positive ones
  pin the bands, their order, ceiling inclusivity, and the next-band phrasing.
  The defeating ones prove that past the slowest ceiling no grade is earned and
  the overrun still enters the failure list, so grading cannot quietly turn the
  budget into advice.
- Surfaces restating the rule: `AGENTS.md`, `CONTRIBUTING.md`, `ENGINEERING.md`
  (stack table and acceptance paragraph), `README.md`, `.cursorrules`.

Deliberately unchanged:

- `.github/workflows/verify.yml` keeps its job timeout.
- `acceptance/accepted/A1.json` keeps the three-second figure. It is a record of
  what was accepted at the time; editing it would make a true record false.
- `decisions/0060-board-management-role.md` keeps it for the same reason: it
  states a measurement taken under the old rule.
- `decisions/0012` is not edited. This record amends its verification term.

## What would defeat this

A run that earns a grade while exceeding the budget, or a `BUDGET_SECONDS` that
stops tracking the slowest band. Both have a case in
`scripts/tests/test_verify_budget.py`. Separately: if wall time climbs past
fifteen seconds, the answer is not another ceiling but the startup cost the
measurement above names.

## What still waits on Bdo

- Whether fifteen seconds is the right ceiling. Three was a term of an accepted
  baseline, so replacing it is his to accept, not the drafter's to assume.
- Whether a lost grade should ever be more than a reportable observation. As
  written, a run that slips from `PLATINUM` to `SILVER` passes silently apart
  from the printed line, and nothing tracks the slide.
