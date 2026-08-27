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

Deliberate load says the same thing less sharply. Three interleaved pairs, each
an idle run followed immediately by a run under 32 CPU burners on 32 cores:

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
- CPU rising for reasons that are not the repository growing. This is measured,
  not hypothetical: saturating the host added 31 % to summed CPU, because
  competing for cache and memory buys real cycles. A compute band wide enough to
  absorb that may be no more discriminating than the wall band it replaced, and
  the strongest argument against this record is that nobody has yet shown the
  compute band would be narrower.
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
  reportable observation; this record narrows that to a concrete question.
- If it does key on compute, the band values. They are not the wall bands, and
  they must be measured on the runner that gates merges rather than on a
  32-core development host.
