# 0081 · The verification budget stops blocking, and the pressure moves to per-check ceilings

Status: `OWNER-DIRECTED · CONTRACT WORDING PROPOSED`

Supersedes `decisions/0050-verification-budget-graded.md`, which is
`PROPOSED · BDO HAS NOT RULED` and never was ruled. 0050 raised the ceiling from
three seconds to fifteen and graded the wall time inside it. This record keeps
the grades and takes the ceiling out of the exit code.

Bdo directed it on 2026-08-27, having named the mechanism rather than the number:
"enforcing it as a single global wall-clock hard gate on your primary landing
check is an anti-pattern. It creates artificial friction, misallocates pressure,
and causes false rejections."

## The three findings this rests on

They are Bdo's, restated so a later reader is not sent back to a conversation.

1. **Misattributed blame.** A global ceiling blocks whoever touches the
   repository next, not the owner of the slow check. Measured on 2026-08-27: the
   Automation Service check costs 0.08 s and was refused by a run whose cost was
   Asset Service tests at 11.7 s and repository tooling tests at 10.1 s.
2. **Environmental noise.** Wall-clock time is nondeterministic. `decisions/0050`
   already recorded the proof: one commit, one run, `feat/acceptance-docket`
   passed at 2.674 s on Python 3.11 and failed at 3.233 s on 3.12. This session
   measured the same suite at 11.7 s and at 24.7 s within an hour, unchanged, as
   the count of live sessions sharing the tree moved.
3. **Inversion of purpose.** Pre-landing verification asks whether invariants
   broke. Turning the gate red for clock jitter files a performance reading as a
   correctness failure.

## Decision

### 1. A wall-clock reading grades and records debt. It never refuses

`PLATINUM` at 3 s, `GOLD` at 6 s, `SILVER` at 15 s are unchanged. Past the
slowest band the run earns no grade and prints
`DEBT: no wall-clock grade at 24.700s; SILVER needs 15.000s or less`. Exit code
is unaffected.

The reading is still taken and still recorded, because a budget nobody computes
and a budget always inside its ceiling print the same silence.

### 2. Pressure moves to per-check ceilings, which attribute rather than refuse

`contracts/verification-budget.json` declares a default ceiling of 0.5 s and
thirteen named ceilings. A check over its own ceiling is reported by name with
its number and its ceiling. It does not refuse the run, and it does not refuse
any other check's run.

The default is 0.5 s because twenty-nine of forty-three checks finish under
0.2 s; it is set to make ordinary growth visible, not to trip on a routine
reading. A check added without a named ceiling answers to the default rather
than being exempt, and a named ceiling on a check that does not exist fails the
test suite, because a ceiling on nothing is pressure on nothing.

Two named ceilings are aspirations Bdo set and the repository presently exceeds:
Asset Service reference tests at 4.0 s against a measured 11.7 s, and repository
tooling tests at 3.0 s against 10.1 s. They are set where he set them so the debt
is attributed, rather than drawn around the current cost so it disappears.

### 3. One timing condition still refuses: a single check past thirty seconds

`catastrophic_check_seconds` is 30.0. One check past it fails the run and joins
the semantic failures.

This is the whole of the hard pressure, and it is deliberately unreachable by
load: the slowest check measured under eleven concurrent sessions was 11.701 s.
A check that reaches 30 s has changed, not been crowded.

A catastrophic check is not also reported as debt. One regression is reported
once.

### 4. Semantic failure is what blocks a landing

`scripts/verify.py` returns 1 for a failing check or a catastrophic timing, and
0 otherwise. `scripts/sov_land.py` runs verify and lint before its gate, so this
is the rule that decides whether the landing loop can run at all.

## Observed state at drafting

- 43 checks, 37.3 s of work, wall time observed between 11.7 s and 24.7 s on the
  same tree within one hour, on Windows with eleven live sessions sharing it.
- Two checks are 21.8 s of the 37.3 s. Twenty-nine are under 0.2 s.
- Before this change the run failed with every check passing.
- `.github/workflows/verify.yml` runs `python scripts/verify.py` and takes its
  exit code, so the wall-clock ceiling was a CI gate as much as a local one. Five
  pull requests were green at the time, meaning the hosted runner came in under
  15 s — a margin `scripts/verify.py` already carried a comment about, recording
  that a hosted runner had once spent its budget context-switching between 20+
  Python processes.

## Constraints

- `AGENTS.md`, Testing and verification: the required command is
  `python scripts/verify.py`, and its wall time is graded rather than pass/fail.
  This decision is what makes the second half of that sentence true; it was not.
- `AGENTS.md`, Implementation order: never weaken an oracle merely to make a
  participant pass. This weakens a gate on the owner's direction and on stated
  evidence, and it moves the pressure it removes rather than deleting it. The
  test file that asserted the old rule was rewritten to assert the new one and
  its class `Pressure` exists to make that trade checkable.

## Consequences

- A change that meets its own cost lands while another check's debt stays
  visible against that check.
- The debt is now a number with an owner: 2 checks, 14.354 s above budget on
  2026-08-27.
- Nothing gates on that debt yet. A phase gate or a nightly run could; this
  record does not create one.

## Defaults taken

Reversible choices; Bdo may overturn any without defeating the ruling.

- **The budget moved into a contract rather than staying in code.**
  `scripts/verify.py` restates no number; it derives its bands from the table.
- **Named ceilings for the slow checks were set from measurement plus modest
  headroom, except the two Bdo named**, which are set at his aspiration so they
  read as debt.
- **Per-check overruns do not block.** He wrote "reserve hard failures for
  catastrophic regressions." An alternative reading — that a check blocks on its
  own ceiling — would restore misattribution the moment two checks share a PR.
- **The catastrophic ceiling is per check, not per run.** A per-run version would
  be the old global gate with a larger number.
- **Deterministic proxies are not implemented.** Bdo proposed file-scan counts,
  journal-write counts, and subprocess counts as load-independent pressure. That
  is a better instrument than any timer and it is a separate concern; the
  `worktrees` exclusion another session added to `scripts/lint.py` on 2026-08-26
  is the worked example, and it cut that check by roughly 27 s.
- **No tiering into fast-inner-loop and deep-verification.** He proposed it;
  splitting the suite is a larger change than this one and would move which
  checks run before a landing, which is a different question from what a timing
  reading may do.

## What would defeat this ruling

- A suite that grows steadily under attributed-but-unenforced debt. That would
  show attribution alone is not pressure, and the per-check ceiling would have to
  block after all.
- A check that legitimately takes more than 30 s, which would make the one hard
  condition unusable and leave nothing blocking.
- Evidence that the wall-clock variance was never environmental — that the 11.7 s
  and 24.7 s readings differ for a reason inside the repository. Then the old
  gate was measuring something real and this record removed a working signal.
- A landing that should have been refused and was not, whose defect a timing
  reading would have caught.

## What still waits on Bdo

1. Whether the two aspirational ceilings are the right numbers, or whether 4.0 s
   and 3.0 s should be the cost after a repair rather than the ceiling before it.
2. Whether attributed debt should gate anything — a phase gate, a nightly, a
   release — or stay a readout.
3. The deterministic-proxy instrument and the two-tier split, both of which he
   proposed and neither of which is built here.

## Residuals

- No independent witness. This session wrote it and this session tested it.
- The Asset Service test suite at 11.7 s and the repository tooling suite at
  10.1 s are unrepaired and are now recorded debt rather than a blocked gate.
  `services/asset/KNOWN-GAPS.md` carries the first as a named concern.
- `decisions/0050` is superseded but not withdrawn; it holds the runner-variance
  evidence this record cites and should stay readable.
