# Witness record — tooling-test-cost (PR #222)

```witness
standing_supported  none
subject             tooling-test-cost
revision            e08af8930587fdc3586ac517ca7188f98cb8702c
pass                3
```

## Pass 3: commit e08af89 (2026-09-07)

**Verdict: CONFIRMED**, apart from the orientation-snapshot commit count. Pass 2's
F4 is repaired: the partition suite passes, the tooling runner exits 0 twice, and
its wall is back below pass 2's. Pass 1's F1 and F2 repairs hold. Verify on a clean
full-history clone fails on the orientation snapshot and on nothing else.

**Standing supported: none.** No `STATUS.yaml` field names this subject. The landing
record for `e08af89` reads `CONFIRMED`; this observation settles nothing.

Why this is pass 3 and not a rewritten pass 2: the branch moved from `cd006b0` to
`e08af89` while pass 2's deposits were being written. Pass 2 is a frozen Finding on
a pushed commit, so it stays as evidence and this pass observes the new subject.

- **Commit witnessed:** `e08af8930587fdc3586ac517ca7188f98cb8702c`, one commit after
  `cd006b0`, HEAD of `feat/tooling-test-cost`; base unchanged at
  `aeecc605c05c7a6f74e80ee4bd49e0b6f2ea19d9`; candidate tree
  `4850e1793a3c49ad205d7e5017b2af9e12a4673f`.
- **Working tree witnessed against:** the `feat/tooling-test-cost` worktree at
  `e08af89`; its porcelain held only this participant's untracked deposits
  throughout. Measurements ran in a full-history clone of the main checkout at
  `e08af89` (970 commits, empty porcelain).
- **Observed:** 2026-09-07T12:50Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-tooling-test-cost-observation-3.json`.
- **Landing record:** `.local/observations/2026-09-07-tooling-test-cost-landing-3.json`.
- **Principal:** `SOV_PRINCIPAL=principal:claude-fable-5-1` for every command except
  the two mutant runs, which unset it because the case under test is about it.

### Claim

From `git show e08af89`: every module at or above one second carries its measured
seconds times ten (18 entries; `test_sov_branch` measured 0.9 s and left the table),
and the two partition cases that pinned `test_sov_branch` by name now read whichever
module the table weights heaviest. `git diff --stat cd006b0..e08af89`: two files,
`scripts/run_tooling_tests.py` (+11/-6) and `scripts/tests/test_run_tooling_tests.py`
(+8/-2). Across the whole branch, `aeecc60..e08af89` touches those two and
`scripts/tests/test_sov_fresh.py`, nothing else.

### What was reproduced

| # | Claim | Read | Result |
| --- | --- | --- | --- |
| 1 | F4 repaired | `python -m unittest scripts.tests.test_run_tooling_tests` in the clone | 7 tests, OK, exit 0 |
| 2 | Tooling runner | `run_tooling_tests.py` unchanged, `_run` wrapped with `perf_counter`, twice, alone | exit 0 both. Run 1: shards 10.48 / 11.98 (holds fresh, 23 modules) / 12.16 / 14.06 s, wall 14.06 s. Run 2: 12.46 / 12.70 / 14.19 / 14.42 (holds fresh, 23 modules) s, wall 14.44 s. Against 15.44 / 15.09 s at `cd006b0` and 13.25 / 14.67 s at `479ac74` |
| 3 | F1 repair still holds | pass 1 mutant on a scratch copy of `e08af89`, both orders | 1 failure each order, the named case; exit 1 both |
| 4 | F2 repair still holds | `python -W error::ResourceWarning -m unittest scripts.tests.test_sov_fresh`; in-process probe | exit 0, no warnings; shared directory absent after the suite |
| 5 | Same verdicts both orders | custom loader | 24 ok reversed (3.69 s) and forward (3.94 s) |
| 6 | Timing | three sequential runs, alone | 4.31 / 4.14 / 3.87 s, 24 cases, exit 0 |
| 7 | Weights against this host | every one of the 111 modules run alone through `python -m unittest scripts.tests.<stem>`, `perf_counter` around the subprocess, once each, 53.8 s total | See F5. 15 of 18 entries within two units of this host's reading; `test_sov_reuse` 36 against 40, `test_automation_health` 21 against 25; `test_sov_branch` 1.22 s here, absent from the table; `test_sov_node_journal` 0.98 s here, carried at 12 |
| 8 | Lint | `python scripts/lint.py` in the worktree | exit 0, `PASS: repository hygiene (1207 text files, 562 Python modules, 10 named debt)` |
| 9 | Verify on full history | `python scripts/verify.py` in the clean clone at `e08af89` | exit 1. `FAIL: orientation snapshot` only: `page says 942, record holds 970 (tolerance 25)`. `repository tooling tests` PASS at 18.497 s pooled; `fresh participation slice` PASS at 4.793 s; 52 checks in 19.679 s wall |
| 10 | No other file moved | `diff -rq` between the `cd006b0` and `e08af89` clones, `.git`, `__pycache__` and `.local` excluded | Only the two declared files differ |

### Findings

#### F5 · MINOR · the rule's precision exceeds the measurement's, and `test_sov_branch` straddles the threshold

The table's rule quantises at 0.1 s. Run-to-run noise on this host is about ten
percent (the fresh suite read 3.87 to 4.31 s across this pass), so at four seconds
a difference of up to four units is noise, and every entry but one is inside that.
`test_sov_branch` is the exception: the commit records 0.9 s and drops it; this host
reads 1.22 s, a third more, which by the rule is an entry of 12. The module drives
real git subprocesses, so which side of one second it lands on is a property of the
host. The runner's comment already says the weights are scheduling hints and never
evidence or budget, the partition cases pass with the table as written, and the wall
is shorter than at either earlier commit. Recorded, not failed; the next remeasure
should say which host and how many runs the readings come from.

### Residuals

- R1. Orientation snapshot: page 942, record 970, tolerance 25. The same class as
  #221; outside the standing grant's scope for the builder to correct.
- R2. Pre-existing and outside this concern: `scripts/tests/test_sov_clarity.py`
  fails when run alone with `ModuleNotFoundError: No module named 'sovclarity'`,
  identically at `aeecc60`; it imports through a `sys.path` insert another module in
  its shard performs. The branch touches no clarity file. Owed a route by whoever
  holds the tooling concern; not absorbed here.
- R3. Two entries differ from this host's single reading by four units
  (`test_sov_reuse`, `test_automation_health`); inside noise, noted for the next
  remeasure.

### Judgement

- J1 stands as recorded in pass 1.

### Commands and exit codes

| Command | cwd | Exit |
| --- | --- | --- |
| `git status --porcelain`; `git diff --stat cd006b0..HEAD`; `aeecc60..HEAD` | worktree | 0; 2 files; 3 files |
| `python -m unittest scripts.tests.test_run_tooling_tests` | clone `e08af89` | 0 (7 tests) |
| `python scripts/run_tooling_tests.py` (timed wrapper) x2 | clone `e08af89` | 0, 0 |
| mutant suite, loader order / reverse | scratch `e08af89` | 1 / 1 |
| custom loader, reverse / forward | clone `e08af89` | 0 / 0 |
| `python -W error::ResourceWarning -m unittest scripts.tests.test_sov_fresh` | clone `e08af89` | 0, no warnings |
| `python -m unittest scripts.tests.test_sov_fresh` x3 | clone `e08af89` | 0, 0, 0 |
| every module alone, 111 subprocesses | clone `e08af89` | 110 exit 0; `test_sov_clarity` exit 1 (R2) |
| `python scripts/lint.py` | worktree | 0 |
| `python scripts/verify.py` | clone `e08af89` | 1 (orientation snapshot only) |

## Pass 2: commit cd006b0 (2026-09-07)

**Verdict: NOT_CONFIRMED.** Pass 1's F1 and F2 are repaired and reproduced. The
F3 repair introduced a regression: the remeasured weight makes the tooling runner's
own partition test fail, so `python scripts/run_tooling_tests.py` exits 1 and verify
fails on `repository tooling tests` as well as the orientation snapshot. F4 below.

**Standing supported: none.** Supports `BUILT` for the F1 and F2 repairs; withholds
`WITNESSED` on F4. Settles nothing.

- **Commit witnessed:** `cd006b0f244f78f86c74be33180f2a537c4e9a47`, one commit after
  `479ac74`, HEAD of `feat/tooling-test-cost`; base unchanged at
  `aeecc605c05c7a6f74e80ee4bd49e0b6f2ea19d9`; candidate tree
  `0a78389a40e9395d84425411bde3642ef1ef5e3e`.
- **Working tree witnessed against:** the `feat/tooling-test-cost` worktree at
  `cd006b0`, whose porcelain held only this participant's two untracked pass 1
  deposits throughout. Measurements ran in a full-history clone of the main checkout
  at `cd006b0` (969 commits, empty porcelain).
- **Observed:** 2026-09-07T12:35Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-tooling-test-cost-observation-2.json`.
- **Landing record:** `.local/observations/2026-09-07-tooling-test-cost-landing-2.json`.
- **Principal:** `SOV_PRINCIPAL=principal:claude-fable-5-1` for every command except
  the two mutant runs, which unset it because the case under test is about it.

### Claim

From `git show cd006b0`: the inherited-variable case runs its own `probe.run` under
the variable and the docstring says the key carries no environment (F1); the shared
`TemporaryDirectory` is released by `unittest.addModuleCleanup` (F2); the module
weight in the shard table goes from 51 to 39 by the table's own rule at 3.9 s (F3).
`git diff --stat 479ac74..cd006b0`: two files, `scripts/run_tooling_tests.py`
(1 line) and `scripts/tests/test_sov_fresh.py` (+9/-4).

### What was reproduced

| # | Claim | Read | Result |
| --- | --- | --- | --- |
| 1 | F1 repaired | diff lines 138-145; the pass 1 mutant (`layers.py:63`, inherited variable wins) in scratch copy of `cd006b0`, `SOV_PRINCIPAL` unset, loader order and reverse | Reproduced: 1 failure in each order, the named case, exit 1 both. Docstring lines 37-39 now true of every case: the two other environment cases were already direct |
| 2 | F2 repaired | `python -W error::ResourceWarning -m unittest scripts.tests.test_sov_fresh`; in-process probe reading `_SHARED["temp"].name` after the suite | Reproduced: exit 0, zero warning lines; the directory is registered and does not exist after the suite |
| 3 | Same verdicts in both orders | custom loader | 24 ok reversed (3.80 s) and forward (4.07 s), exit 0 both |
| 4 | Timing | `perf_counter` around `python -m unittest scripts.tests.test_sov_fresh`, three sequential runs, alone | 4.00 / 4.18 / 4.20 s, 24 cases, exit 0. Within noise of pass 1's 3.88 / 3.88 / 3.99 s; the extra probe costs about 0.2 s |
| 5 | No other file moved | `diff -rq` between the `479ac74` and `cd006b0` clones, `.git` and `__pycache__` excluded | Only the two declared files differ |
| 6 | Lint | `python scripts/lint.py` in the worktree | exit 0, `PASS: repository hygiene (1206 text files, 562 Python modules, 10 named debt)` |
| 7 | Tooling runner | `run_tooling_tests.py` unchanged, `_run` wrapped with `perf_counter`, twice, alone | **exit 1 both runs.** Run 1: shards 12.21 / 12.47 / 13.82 / 15.43 (holds fresh, 31 modules) s, wall 15.44 s. Run 2: 11.59 / 12.29 / 13.35 / 15.09 (holds fresh, 31 modules) s, wall 15.09 s. One failure: see F4 |
| 8 | Verify on full history | `python scripts/verify.py` in the clean clone at `cd006b0` | exit 1. `FAIL: orientation snapshot, repository tooling tests`. Snapshot: `page says 942, record holds 969 (tolerance 25)`. `fresh participation slice` PASS at 4.255 s. 52 checks, 19.643 s wall, tooling check 18.502 s pooled |

### Findings

#### F4 · MATERIAL · the remeasured weight defeats the runner's own partition test and lengthens the tooling wall

`scripts/tests/test_run_tooling_tests.py:65-80`,
`test_the_declared_weight_buys_the_heaviest_module_fewer_peers`, asserts that the
module the table weights heaviest has fewer shard peers with its weight than with the
entry dropped. At `cd006b0` the heaviest entry is `test_sov_fresh.py: 39`; with it the
module has 31 peers, without it 30: `AssertionError: 31 not less than 30`. The runner
exits 1 on both runs, and verify's `repository tooling tests` check fails with it.

`scripts/run_tooling_tests.py:45-47` states the hazard in the builder's own table:
"peers are not monotonic in the weight across the whole range ... so a weight has
to be measured rather than reasoned about." The 39 was reasoned from the
seconds-times-ten rule, not measured against the packing. The measured effect on the
concern's own objective is a longer wall: 15.44 / 15.09 s against 13.25 / 14.67 s at
`479ac74`, because the shard holding this module grew from 27 modules to 31.

Attribution: pass 1's F3 named 39 as what the table's rule gives; this participant
owns that the number was stated without a packing measurement. The check that
catches it, `python scripts/run_tooling_tests.py`, is the builder's to run before
pushing, and the commit message reports it as remeasured, which it was not.

Repair, inside the concern: measure a weight that buys fewer peers than the dropped
entry, as the comment prescribes, or restore 51, which passed and packed the module
into the shorter shard at pass 1. Either is a routine decision for whoever holds the
branch.

### Residuals

- R1. Orientation snapshot count now 969 against 942, tolerance 25; unchanged class.
- R2. Verify fails on two checks at `cd006b0`; only the snapshot is outside the
  builder's reach.

### Judgement

- J1 stands as recorded in pass 1.

### Commands and exit codes

| Command | cwd | Exit |
| --- | --- | --- |
| `git status --porcelain` | worktree | 0; two `??` pass 1 deposits only |
| `git diff --stat 479ac74..cd006b0` | worktree | 0; 2 files |
| mutant suite, loader order / reverse | scratch `cd006b0` | 1 / 1 |
| custom loader, reverse / forward | clone `cd006b0` | 0 / 0 |
| `python -W error::ResourceWarning -m unittest scripts.tests.test_sov_fresh` | clone `cd006b0` | 0, no warnings |
| `python -m unittest scripts.tests.test_sov_fresh` x3 | clone `cd006b0` | 0, 0, 0 |
| `python scripts/lint.py` | worktree | 0 |
| `python scripts/run_tooling_tests.py` (timed wrapper) x2 | clone `cd006b0` | 1, 1 |
| `python scripts/verify.py` | clone `cd006b0` | 1 (orientation snapshot, repository tooling tests) |

## Pass 1: commit 479ac74 (2026-09-07)

**Verdict: NOT_CONFIRMED.** One material finding (F1) withholds the landing; the
speed claim, the case count, the carried selfcheck evidence and the order
independence of the verdicts are reproduced. The repair is one line inside the
concern and keeps the speed gain.

**Standing supported: none.** The subject is a test module; no `STATUS.yaml`
field names it. This observation supports `BUILT` for the commit's claim as
stated and withholds `WITNESSED` on F1. It settles nothing.

- **Commit witnessed:** `479ac74becae9fbb05b22ed4079379f116f5fcf8`, HEAD of
  `feat/tooling-test-cost`; base `aeecc605c05c7a6f74e80ee4bd49e0b6f2ea19d9`
  (`origin/main`); candidate tree `632eec12a481419cedb063a101ea728a1b68bf04`.
- **Working tree witnessed against:** the `feat/tooling-test-cost` worktree, `git status --porcelain`
  empty before every command and after every command until the three deposits
  below were written. Timings, the tooling runner and verify ran in full-history
  clones of the main checkout, checked out at each commit, both with an empty
  porcelain.
- **Observed:** 2026-09-07T12:19Z (UTC).
- **Receipt:** `witness/observations/2026-09-07-tooling-test-cost-observation.json`,
  conforming to `contracts/participant-observation.schema.json`.
- **Landing record:** `.local/observations/2026-09-07-tooling-test-cost-landing.json`.
- **Principal:** every command ran with `SOV_PRINCIPAL=principal:claude-fable-5-1`,
  except the four mutant runs under F1, which ran with the variable unset because
  the case under test is about that variable.

## Claim

From `git show 479ac74`, the builder's words: probe runs shared per
`(variant, principal, issuer)` across the module; the selfcheck subprocess case
removed because verify runs `sov_fresh.py selfcheck` as the "fresh participation
slice" check; the `unittest.main` guard moved from mid-file to the end; 25 cases to
24; 10.1 s to 4.0 s on the builder's host. One file changed:
`scripts/tests/test_sov_fresh.py` (38 insertions, 14 deletions).

## What independence rests on

This participant built nothing here and edited no file outside the three deposits.
The builder's commit message located the subject; nothing in it was taken as
evidence. Every number below was re-derived by running the artifact.

## What was reproduced

| # | Claim | Read | Result |
| --- | --- | --- | --- |
| 1 | 25 cases to 24 | `python -m unittest -v` at both commits, names diffed | Reproduced: 25 at aeecc60, 24 at 479ac74; the one removed name is `test_selfcheck_passes` |
| 2 | 10.1 s to 4.0 s | `perf_counter` around `python -m unittest scripts.tests.test_sov_fresh`, three runs each, sequential, alone | Direction reproduced, magnitude host-bound: head 3.88 / 3.88 / 3.99 s; base 6.87 / 7.11 / 6.94 s. A 43 % reduction here against the builder's 60 % |
| 3 | Every case reads a result the probe produced for the key it asked for | Read `shared_run` (lines 52-59): lookup by `(variant, principal, issuer)`, one `mkdtemp` per key, one shared registry copy; every call site listed | Reproduced for variant, principal, issuer, registry and node state. Not reproduced for the environment: see F1 |
| 4 | No case mutates a shared result | grep for assignments, `del`, `.update/.pop/.append/...` into result dicts | Reproduced: the only writes are `os.environ.pop` in the three environment cases |
| 5 | Same verdicts in reverse order | custom loader, 24 cases reversed | Reproduced: 24 ok in both orders, exit 0, 3.51 s reversed / 3.58 s forward |
| 6 | Removed case's evidence carried by verify | `scripts/sovverify/commissioning.py:17` defines "fresh participation slice" as `sov_fresh.py selfcheck`; `scripts/verify.py:97` grades `exit_code == 0` | Reproduced. `python scripts/sov_fresh.py selfcheck` exit 0 in the worktree; verify on the clean clone reports `PASS: fresh participation slice` at 4.757 s. The removed case also asserted `"PASS"` in stdout; verify reads the exit verdict instead, which is the right byte |
| 7 | Guard moved to the end | diff hunks at lines 209-218 and 316-319 | Reproduced |
| 8 | Nothing else changed | `git diff --stat aeecc60 479ac74`; clones diffed | Reproduced: one file. No assertion weakened other than the deleted case |
| 9 | Tooling runner | `scripts/run_tooling_tests.py` unchanged, `_run` wrapped with `perf_counter`, run alone | exit 0 all three runs. Head run 1: shards 11.70 / 11.75 / 12.96 (holds fresh) / 13.25 s, wall 13.25 s. Head run 2: 11.99 / 12.10 / 13.59 (holds fresh) / 14.67 s, wall 14.67 s. Base: 12.29 / 12.72 / 14.53 / 16.71 (holds fresh) s, wall 16.72 s |
| 10 | Lint | `python scripts/lint.py` in the worktree | exit 0, `PASS: repository hygiene (1204 text files, 562 Python modules, 10 named debt)` |
| 11 | Verify on full history | `python scripts/verify.py` in the clean clone at 479ac74 (968 commits) | exit 1. Exactly one check fails: `orientation snapshot`, `FAIL commits: page says 942, record holds 968 (tolerance 25)`. 52 checks, 20.536 s wall, `repository tooling tests` PASS at 19.479 s pooled with no catastrophic rerun. The `CONF-*-DEF FAIL` lines are the oracle's declared defeating controls |

## Findings

### F1 · MATERIAL · one environment case now reads a shared run, so its defeating power depends on loader order

`test_an_inherited_principal_variable_does_not_reach_the_resolver` (lines 135-146)
sets `SOV_PRINCIPAL=principal:bdo` and then calls `self.run_variant()`, which is
`shared_run("positive", FIXTURE, ISSUER)`. The key omits the environment. The case
runs its own probe only if nothing has requested that key before it. In the
loader's alphabetical order it happens to be the first requester, so the check
currently sees what it grades; any earlier requester makes it read a cached result
and pass whatever the resolver does.

Measured with a mutant of `scripts/sovfresh/layers.py:63` in scratch copies of both
commits, where the inherited variable wins over the declared principal
(`os.environ.get(ENV_PRINCIPAL) or principal_id`), `SOV_PRINCIPAL` unset:

| Tree | Loader order | Reverse order |
| --- | --- | --- |
| aeecc60 | FAIL, 1 failure (the case) | FAIL, 1 failure (the case) |
| 479ac74 | FAIL, 2 failures (the case, and `test_identities_come_from_node_records`, which read the run the case's `principal:bdo` polluted) | **exit 0, 24 ok** |

The module docstring at line 38, "A case that changes the environment or the
registry still runs its own probe", is false for this case; the two other
environment cases (`test_oral_history_is_earned_not_asserted`, lines 120-122, and
`test_the_issuer_gate_reads_the_registry_the_resolver_reads`, line 156) do call
`probe.run` directly and are unaffected. The second row also shows that in the
order the repository runs, six positive readings are of a run performed under this
case's altered environment.

Repair, inside the concern: call `probe.run(ROOT, self.temp / "inherited", FIXTURE,
registry=self.registry, issuer=ISSUER)` in that case, as its siblings do, and drop
the docstring exception or make it true. Cost about 0.35 s.

### F2 · MINOR · the module-level temporary directory is never released

`_SHARED["temp"]` (line 44) is a `TemporaryDirectory` nothing cleans up.
`python -W always -m unittest scripts.tests.test_sov_fresh` at 479ac74 prints
`ResourceWarning: Implicitly cleaning up <TemporaryDirectory ...>` twice; aeecc60
prints none. `unittest.addModuleCleanup` or a `tearDownModule` closes it.

### F3 · MINOR · the runner's weight for this module is now stale by the table's own rule

`scripts/run_tooling_tests.py:70` keeps `test_sov_fresh.py: 51`, set from 5.1 s.
The module measures 3.9 s here, which the table's rule (seconds times ten) puts at
39. A scheduling hint and no evidence, and the shard holding this module was not
the longest at head, so this is recorded, not failed.

## Residuals

- R1. Verify at 479ac74 fails on the orientation snapshot commit count, the same
  class as #221; the root governing document that would correct it is outside the
  standing grant's scope. Nothing else in verify fails.
- R2. The builder's 10.1 s base reading was not reproduced on this host (6.9 s); the
  head reading (3.9 s) matches the builder's 4.0 s.
- R3. The scratchpad directory this session was given already held a `base/` tree
  with a 107-byte `.git` worktree pointer and a `.local/` written at 11:38-11:40 by
  another session. This participant removed it to rebuild `base` as a clean clone.
  `git worktree list` in the main checkout shows no entry for it before or after.

## Judgement

- J1. Does the orientation-snapshot commit count, which the standing grant's scope
  keeps the builder from correcting, wait on Bdo for every branch off aeecc60 as
  #221 recorded, or is it a repair Bdo would accept as a packet?

## Commands and exit codes

| Command | cwd | Exit |
| --- | --- | --- |
| `git status --porcelain` | worktree | 0, empty |
| `python -m unittest scripts.tests.test_sov_fresh` x3 | clone 479ac74 | 0, 0, 0 (24 cases) |
| `python -m unittest scripts.tests.test_sov_fresh` x3 | clone aeecc60 | 0, 0, 0 (25 cases) |
| custom loader, reverse and forward | worktree | 0, 0 |
| `python scripts/sov_fresh.py selfcheck` | worktree | 0 |
| `python scripts/lint.py` | worktree | 0 |
| `python scripts/run_tooling_tests.py` (via timed wrapper) x2 | clone 479ac74 | 0, 0 |
| `python scripts/run_tooling_tests.py` (via timed wrapper) x1 | clone aeecc60 | 0 |
| `python scripts/verify.py` | clone 479ac74 | 1 (orientation snapshot only) |
| mutant suite, loader order / reverse | scratch 479ac74 | 1 / 0 |
| mutant suite, loader order / reverse | scratch aeecc60 | 1 / 1 |
| `python -W always -m unittest scripts.tests.test_sov_fresh` | clone 479ac74 / aeecc60 | 0 (2 ResourceWarning) / 0 (none) |

This record is an observation. It grants no authority and settles nothing.
