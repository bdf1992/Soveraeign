# 0071 · Key the verification budget on compute, not wall time

Status: `PROPOSED · BDO HAS NOT RULED`

`decisions/0050` owns the verification budget and is not amended here. This
record proposes replacing what that budget keys on, and nothing about it is in
force. The bands stay `PLATINUM` 3.000 s, `GOLD` 6.000 s, `SILVER` 15.000 s of
wall time until Bdo rules.

The measurement this record argues from is built and landed on the same branch:
`scripts/sovverify/clocks.py` times every check on two clocks. That part changed
nothing about the gate.

## What is proposed

Grade a verification run on the CPU its checks consumed rather than on the wall
time the operator waited, and keep wall time as a reported number that fails
nothing.

The drafter does not recommend adopting this as it stands. An adversarial pass
measured the premise and found it holds in one regime and fails in another: at
the moderate load that actually trips this gate the two clocks separate cleanly,
and at deliberate saturation they move together, worst of all on the CPU-bound
checks a compute band would have to key on. That measurement is under **What
would defeat this** and should be read before the argument for the change.

What the drafter does recommend is that the question is now answerable, which it
was not before, and that answering it needs a measurement taken on
`ubuntu-latest` rather than on a 32-core development host.

## Why

A gate that keys on wall time reports "the repository is too slow" when the
truth is "another process was busy". Measured on clean `origin/main` at
`5951bc4`, in an untouched worktree, three consecutive runs:

| Run | Wall | Verdict |
| --- | --- | --- |
| 1 | 13.967 s | PASS |
| 2 | 18.447 s | FAIL |
| 3 | 18.354 s | FAIL |

All 39 checks passed every time. Only the ceiling tripped, and it tripped
because the host was busy. `decisions/0050` records the same failure across CI
runners a day earlier and raised the ceiling rather than changing what was
measured; the ceiling has been reached again.

Until this branch there was no compute figure anywhere in the harness to argue
from. The run printed `44.372s of work`, which was a sum of `time.perf_counter`
readings — a second wall figure, carrying the same contention as the first.

## What the two clocks now read

Three consecutive runs of this branch, same worktree, host otherwise idle:

| Run | Aggregate wall | Summed check wall | Summed check CPU |
| --- | --- | --- | --- |
| 1 | 13.397 s | 42.464 s | 19.812 s |
| 2 | 12.863 s | 40.200 s | 19.719 s |
| 3 | 13.398 s | 42.641 s | 22.719 s |

Two readings the per-check numbers make visible for the first time:

- `repository tooling tests` reads a CPU-to-wall ratio above 1, because its four
  shards run at once. A per-process measurement would have reported nearly zero
  for the most expensive check in the suite.
- `Asset Service reference tests` reads 12.982 s wall against 1.625 s CPU on this
  Windows host, a ratio of 0.13. The largest single consumer of the wall budget
  spends seven-eighths of it not computing. Why is a separate concern; it is
  named here because it is what a wall-keyed ceiling is actually measuring.

The same suite on `ubuntu-latest`, the runner that gates merges, read 7.600 s
aggregate wall against 26.281 s of summed check CPU. Wall and compute are not
translatable between the two hosts, which is the practical reason a compute band
would have to be measured on CI rather than derived from the numbers above.

## What a compute-keyed budget would have said

One run of this branch failed the gate while a second agent was working the same
host:

```
FAIL: verification budget (17.259s > 15.000s)
COST: 39 checks in 17.259s wall; 44.636s of check wall, 21.703s of check cpu
```

All 39 checks passed. The compute figure, 21.703 s, sits inside the idle band of
19.719 s to 22.719 s above. Wall crossed the ceiling and compute did not move.
That is the whole case in one run, and it is the first time the harness could
state it rather than guess it.

Three consecutive runs later, on the same tree, with the host at 8-10 % busy from
other sessions rather than deliberately loaded — which is the condition that
actually trips this gate:

| Run | Wall | Summed check CPU | Verdict |
| --- | --- | --- | --- |
| 1 | 13.981 s | 23.375 s | PASS |
| 2 | 18.188 s | 23.047 s | FAIL |
| 3 | 16.344 s | 24.797 s | FAIL |

All 39 checks passed all three times. Wall moved 30 %; CPU moved 7 %. That is the
same shape as the three runs on `main` at the top of this record, and it is the
regime the proposal is actually about.

CI says it too, on one commit and two runners: `repository (3.12)` passed while
`repository (3.11)` failed at 17.068 s of wall for 14.226 s of summed CPU — a
runner that did *less* compute and took *more* wall, which is starvation rather
than a repository that grew.

Deliberate saturation says something different, and it is the qualification this
record turns on; it is set out under **What would defeat this**. Three
interleaved pairs, each an idle run followed immediately by a run under 32 CPU
burners on 32 cores:

| Pair | Idle wall | Loaded wall | Idle CPU | Loaded CPU |
| --- | --- | --- | --- | --- |
| 1 | 13.619 s PASS | 44.374 s FAIL | 21.938 s | 33.984 s |
| 2 | 22.311 s FAIL | 31.392 s FAIL | 26.641 s | 36.047 s |
| 3 | 24.625 s FAIL | 48.913 s FAIL | 29.812 s | 34.844 s |

Median inflation: wall x1.99, CPU x1.31. Wall inflated more than CPU in every
pair, which is the claim; CPU inflated by a third, which is the qualification and
is taken up below.

## What would defeat this

- Summed CPU proving as unstable as wall across runs and hosts. Run 3 above
  reads 22.719 s of CPU against run 2's 19.719 s, a 15 % spread on an idle host,
  with no corresponding wall movement. If that spread is the normal case rather
  than an artifact, a CPU-keyed band is no more honest than the wall band and
  this record is wrong.
- **The suite-level figure above is diluted, and the undiluted one nearly settles
  this against the proposal.** An adversarial pass measured a fixed-work child on
  the same host: at exactly saturating load its wall inflated x2.19 and its CPU
  x2.12, and the child's own `time.process_time` moved with them, so the extra
  cycles are real rather than a measurement artifact. Competing for cores, cache
  and turbo headroom costs CPU. The suite reads a gentler x1.31 only because most
  of its wall is spent waiting: `Asset Service reference tests` reads 0.09x and
  `Console Service reference tests` 0.17x, and averaging mostly-idle checks hides
  the inflation of the busy ones.

  The sharpest number is the one check that is genuinely CPU-bound. Across five
  runs of byte-identical bytes, `repository tooling tests` reported 10.531,
  11.641, 16.312, 14.141 and 11.703 seconds of CPU: a spread of x1.55 on the
  largest compute consumer in the suite. A compute-keyed budget would be least
  trustworthy exactly where it would have to be trusted.

  What survives is narrower than the proposal but is not nothing. The two regimes
  differ: at the moderate load that actually trips this gate, wall moved 30 % and
  CPU 7 % across three runs of one tree; at deliberate saturation the two move
  together. A compute-keyed budget would therefore be sound exactly where the
  gate misfires today and unsound where a machine is being abused. Whether that
  is a budget worth having is a judgement, not a measurement, and it is Bdo's.
  Nobody has yet shown that the compute band would be narrower than the wall band
  it replaces, and until someone has, the case for swapping them is not made.
- A compute gate does not bound what the operator waits. A suite that took
  sixty seconds of wall for twenty of CPU would pass it and be unusable. If the
  wait is what Bdo wants bounded, the answer is two graded numbers, not a
  swapped one.
- CPU summed across parallel checks is not comparable to wall on a small runner:
  `ubuntu-latest` gives two to four cores, so a band expressed in CPU seconds is
  a different number from the wall band and has to be measured there, not
  translated from here.

## What still waits on Bdo

- Whether the gate keys on compute at all, or on both numbers, or stays as it
  is. `decisions/0050` left open whether a lost grade should ever be more than a
  reportable observation; this record narrows that to a concrete question and,
  on its own evidence, answers it "not yet".
- If it does key on compute, the band values. They are not the wall bands, and
  they must be measured on the runner that gates merges rather than on a
  32-core development host.
- Whether the reading that actually deserves work is the one this record turned
  up sideways: the two largest wall consumers in the suite spend nine-tenths of
  that wall not computing. Reducing a wait is a different repair from raising a
  ceiling, and it is the one that would make either budget comfortable.
