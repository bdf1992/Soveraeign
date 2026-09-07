# Witness record: discovery and reuse vertical slice (P15-X3)

```witness
standing_supported  WITNESSED
subject  discovery-and-reuse
revision  60d5615621340d5a34e85ffa618f794d39ac707f
pass  5
```

Five passes by the same role, different commits. Pass 5 (commit `60d5615`) is current and
owns the declaration above. Pass 4 (commit `57271f7`, RATIFIABLE), pass 3 (commit `ea01dcc`,
RATIFIABLE), pass 2 (commit `b0c013c`, RATIFIABLE-WITH-CONDITIONS) and pass 1 (commit
`26b1887`, NOT-YET) follow it unchanged as history.

## Pass 5: commit 60d5615 (2026-09-07)

### Subject

Repository candidate `60d5615621340d5a34e85ffa618f794d39ac707f` (tree
`cb4e158c1d2167fb2cac3537be3b03d792010014`), frozen on base
`ee6080153c64938f43377617e1c4c1f231ddd00a` (`origin/main` and local `main`), HEAD of
`claude/sovereign-phase-1-5-5uzffu`. `git rev-parse HEAD` read the candidate before and after
every command. The record's twelve `changed_paths` equal `git diff --name-only
ee60801...60d5615`. `git diff-tree -r 57271f7 60d5615 --name-status` is three lines:
`M scripts/run_tooling_tests.py`, `M scripts/tests/test_run_tooling_tests.py`,
`M scripts/tests/test_sov_reuse.py`. The shared working tree holds uncommitted presented-side
files not in the candidate; none was read as evidence.

### Claim

Two hosted CI jobs at `ea01dcc` failed verify's catastrophic ceiling on `repository tooling
tests` (33.985 s pooled, 31.235 s alone; 30.0 s and 36.8 s on a second runner); `57271f7`
passed by timing alone. The builder claims: one shared fixture per test module in
`test_sov_reuse.py` with each variant run once (2.8 s from 3.7 s alone); `MODULE_WEIGHTS`
remeasured at 111 modules with weights of measured seconds times ten for modules at or above
one second (shards 12.1/9.6/11.0/9.8 s from 4.5/10.4/18.6/5.3 s, wall 12.6 s from 18.9 s); and
the partition property asserted for whichever module the table weights heaviest.

### Verdict

**RATIFIABLE.**

The instrument and `sovland` are byte-identical to the revision passes 2 through 4 witnessed;
the candidate record describes its range; the clean-clone gates pass with the tooling check
at half the catastrophic ceiling on this host; the weight table orders the heaviest modules
the way my measurements do; and the partition property fails under three defeats. I support
`BUILT -> WITNESSED` for `scripts/sov_reuse.py` at `60d5615` and confirm this candidate for
landing. What a hosted runner measures is evidence only that runner can produce; I record
this host's numbers as this host's.

### Verified

Linux host, Python 3, clean `git clone --no-hardlinks` of the candidate (HEAD `60d5615`,
porcelain empty). Wall clocks are `time.perf_counter()` around a subprocess; `/usr/bin/time`
is absent on this host. Nothing timed ran concurrently with anything else I started.

| Command | Exit | Bounded excerpt |
| --- | --- | --- |
| `git rev-parse` of ten paths at `57271f7` and `60d5615` | 0 | identical blob ids: `scripts/sov_reuse.py`, `sovreuse/{__init__,discover,fixture,reuse,settle}.py`, `contracts/custodies/phase-1-5.json`, `scripts/sovland/candidates.py`, `scripts/tests/test_repository_candidate_effects.py`, `docs/documentation.html` |
| `git diff --name-only ee60801...60d5615` against the record | 0 | twelve paths, identical lists |
| `python scripts/lint.py` (clone) | 0 | `PASS: repository hygiene (1204 text files, 562 Python modules, 10 named debt)` |
| `python scripts/verify.py` (clone, timed) | 0 | wall 16.1 s; `PASS: repository tooling tests (111 modules, 4 shards)`; `TIME: repository tooling tests: 15.147s wall, 33.336s cpu (2.20x)`; shards `Ran 704 tests in 14.178s`, `520 in 10.647s`, `441 in 12.284s`, `485 in 12.117s`; no suspect re-run (the check never reached the 30 s pooled threshold); `documentation reader` PASS at 282 documents |
| for comparison, pass 1 on this host at `26b1887` (old table) | 0 | `TIME: repository tooling tests: 22.797s wall`; longest shard `Ran 734 tests in 21.814s` |
| `python -m unittest scripts.tests.test_sov_reuse` alone, twice (clone) | 0 / 0 | 2.9 s, 3.0 s (14 tests OK); pass 2 measured the previous module at 5.35 s, pass 1 at 4.4 s |
| the table's eight heaviest modules, each alone (clone, sequential) | 0 x 8 | `test_sov_fresh` 5.38 s (weight 51), `test_sov_strand` 3.19 (36), `test_sov_reuse` 2.79 (30), `test_sov_backlog` 2.39 (25), `test_sov_ci_subject` 2.01 (23), `test_automation_control` 1.68 (17), `test_automation_health` 1.67 (16), `test_repository_candidate_effects` 1.65 (18) |
| `python -m unittest scripts.tests.test_run_tooling_tests` (clone) | 0 | `Ran 7 tests OK` |
| partition probe (scratch script over `run_tooling_tests` and the test's own `peers`/`weights` helpers) | 0 | heaviest `test_sov_fresh.py` 51; 111 modules; `peers` 27 weighted, 30 with the entry dropped: property holds. Test with the heaviest entry dropped: `FAILS: 29 not less than 27`; with the heaviest weight set to 1: `FAILS: 29 not less than 27`; with an empty table: `FAILS: ValueError`. Synthetic loads `[100, 100, 100, 99]`, sizes `[27, 27, 29, 28]`; `test_sov_fresh` in shard 0, `test_sov_reuse` in shard 2 |
| `python scripts/sov_reuse.py selfcheck` and the live reading | - | not re-run this pass: `scripts/sov_reuse.py` and `sovreuse/` are byte-identical to pass 4, where both ran on the clone |

### Reading of the change

- `scripts/tests/test_sov_reuse.py:27-48`: one module-level fixture built on first use and one
  memoised result per variant; cases only read results. The runner executes each shard as
  `python -m unittest <modules>` (`run_tooling_tests.py:107-108`), so the lazily registered
  `addModuleCleanup` runs at that process's module teardown and the temporary directory is
  released either way. The same fourteen cases run; what changed is how many times the
  builder's probe is run.
- `scripts/run_tooling_tests.py:56-76`: sixteen weights, each the measured seconds times ten.
  My measurements order the five heaviest exactly as the table does. Positions six to eight
  (`automation_control` 1.68 s, `automation_health` 1.67 s, `repository_candidate_effects`
  1.65 s) lie within 0.03 s of one another; the table puts `repository_candidate_effects` first
  of the three and my host does not distinguish them. The table's own comment calls the
  weights scheduling hints, never evidence or budget, and the partition is graded by the
  synthetic loads it produces, which are level.
- `scripts/tests/test_run_tooling_tests.py:63-77`: the property is asserted for the heaviest
  entry rather than a named module. Dropping the heaviest entry re-targets the assertion to
  the next entry, and it fails there too on this corpus (29 not less than 27), so the defeat
  the docstring names is real on the current table; whether it stays real as the corpus
  changes is a property of the packing, not of the test.

### Findings

- **F1, F2, F3, F4, F6, F8, F9** remain discharged: identical instrument bytes.
- **F5, F7** remain residuals as recorded in pass 1. **F10** as recorded in pass 4.
- **F11 (LOW, observation).** The repair's effect on the hosted runner is a claim only the
  hosted runner can settle. On this host the pooled tooling check reads 15.1 s against a
  30 s catastrophic ceiling and the longest shard 14.2 s; the builder's Linux numbers are
  lower still. A runner two times slower than this host would sit at the ceiling. The weights
  are hints and the ceiling is graded on the pooled check with a serial re-run before it
  refuses (`scripts/sovverify/budget.py`), so this is performance evidence, not a defect in
  the candidate. No repair is asked.

### Judgement

- **J1** and **J2** unchanged from pass 2.

### Uncovered

I did not run the hosted CI, did not measure on Windows, did not re-run selfcheck, the live
reading or the mutants (identical instrument bytes to pass 4), and did not time modules below
the table's eighth entry. Timings are single or double runs on a shared host, not a
distribution. No clarity review for this record.

### Standing supported

`WITNESSED` for `scripts/sov_reuse.py` at `60d5615621340d5a34e85ffa618f794d39ac707f`. It binds
to the instrument claim: the probe is what it says and grades what it says, on this host and
on a clean clone, and each of nine defeating variants fails on a real state. It says nothing
about P15-X3 holding for this node; both live predicates read unmet, truly. Exact words for
`stage_observed_by`:
`claude-fable-5-1/sov-witness@2026-09-07 pass 5 at 60d5615, clean-clone gates with timings, partition property and instrument identity (witness/discovery-and-reuse.md; witness/observations/2026-09-07-discovery-and-reuse-observation-5.json); first supported at pass 2, b0c013c`.
Receipt: `witness/observations/2026-09-07-discovery-and-reuse-observation-5.json`. The
landing-gate file for this pass reads `CONFIRMED`. Observer
`claude-fable-5-1/sov-witness@2026-09-07`, independent of the builder, contributed nothing to
the build.

## Pass 4: commit 57271f7 (2026-09-07)

### Subject

Repository candidate `57271f727b88032d2c1be908cf7ba819dae066d3` (tree
`fad1d5256c36567ee62f2823cd07d502be93b212`), frozen on base
`ee6080153c64938f43377617e1c4c1f231ddd00a` (`origin/main` and local `main`), HEAD of
`claude/sovereign-phase-1-5-5uzffu`. `git rev-parse HEAD` read the candidate before and after
every command. The landing of `ea01dcc` was refused by `sov_land.py land-candidate` for a
record whose `changed_paths` named `docs/documentation.html`, a path the `base...commit` range
no longer held once the page returned to the base's bytes. `git diff-tree -r ea01dcc 57271f7
--name-status` is two lines: `M scripts/sovland/candidates.py`,
`M scripts/tests/test_repository_candidate_effects.py`.

The shared working tree holds uncommitted files not in the candidate that were not read as
evidence: `STATUS.yaml`, `CLAUDE.md`, `.clarity/coverage.json`,
`contracts/custodies/phase-1-5.json` (carrying the pass-3 words and a pass-7
fresh-participation pointer), `witness/fresh-participation.md` (pass 7), the observation-7
receipt, `reports/2026-09-07-discovery-and-reuse-slice.md`, `acceptance/A24.json`, and my
own earlier records and receipts.

### Claim

The builder claims the freeze now records `changed_paths` from `repo.carried_paths` after the
commit (the graded request keeps the wider pre-commit set), with one new test in which a
staged path reverts to base while a carried path stays; and that nothing else changed.

### Verdict

**RATIFIABLE.**

The candidate record describes its own range; the gate's integrity check accepts it and
refuses a widened copy; the clean-clone gates pass; the instrument is byte-identical to the
revision passes 2 and 3 witnessed. I support `BUILT -> WITNESSED` for `scripts/sov_reuse.py`
at `57271f7` and confirm this candidate for landing.

### Verified

| Command | Exit | Bounded excerpt |
| --- | --- | --- |
| `git diff --name-only ee60801...57271f7` against the record's `changed_paths` | 0 | ten paths, identical lists |
| `git diff --stat ee60801 57271f7 -- docs/documentation.html` | 0 | empty: the page equals the base's bytes, so it is rightly outside the range |
| `git rev-parse` of the nine pass-3 paths at `ea01dcc` and `57271f7` | 0 | nine identical blob ids (eight instrument paths and `docs/documentation.html`) |
| `git clone --no-hardlinks`; `git rev-parse HEAD`; `git status --porcelain` | 0 | `57271f7...`; empty; the candidate record copied into the clone's gitignored `.local/candidates/` |
| `python scripts/lint.py` (clean clone) | 0 | `PASS: repository hygiene (1204 text files, 562 Python modules, 10 named debt)` |
| `python -m unittest scripts.tests.test_repository_candidate_effects scripts.tests.test_repository_candidate scripts.tests.test_sov_land` (clean clone) | 0 | `Ran 41 tests OK` |
| `candidates._candidate_integrity(record)` in the clone; then on a copy widened with `docs/documentation.html` | 0 | `integrity: OK 57271f7`; widened copy `refused: candidate changed_paths do not describe its exact base...commit range` |
| `python scripts/verify.py` (clean clone) | 0 | `== documentation reader ==` / `PASS: documentation page matches 282 documents`; `PASS: repository tooling tests (111 modules, 4 shards)`, shard 3 lists `test_repository_candidate_effects` and `test_sov_reuse`; the `FAIL:` lines in the log are tooling-test fixture output present in every passing run |
| `python scripts/sov_reuse.py selfcheck` (frozen shared tree) | 0 | `PASS ... 9 defeating variants each fail their own predicates for exactly the defects they declare` |
| `python scripts/sov_reuse.py run --principal principal:claude-fable-5-1` (clean clone) | 1 | `revision 571e936c733a`; the same eight trunk-drifted addresses; `landing ee6080153c64`; `inventory []`; Q3.1 `settlement was not against current state`; Q3.2 `fresh participant did not use the accepted result` |
| same command on the shared working tree | 1 | same two predicates, but `revision 26b1887e8435`, `landing 26b1887e8435`, drift on the instrument's own paths: the run read the other sessions' uncommitted `contracts/custodies/phase-1-5.json` and `witness/fresh-participation.md` (pass 7), not the candidate. Recorded as what the shared tree does, not as evidence about the candidate |

### Reading of the repair

`candidates.py:96-100` reads `repo.carried_paths(args.target, branch)` after `git commit`;
`_candidate_integrity` (`candidates.py:136-150`) reads `repo.carried_paths(base_commit,
commit)`; both are `git diff --name-only target...branch` (`repo.py:79-108`), so the record and
the gate now read one range. The graded request still carries the pre-commit union of staged
and carried paths, which is a superset of the recorded range, so no path lands that the
authority grade did not see. The new test stages a path whose bytes revert to base alongside a
carried one and asserts `changed_paths == ["z.py"]` after `_candidate_integrity` accepts it.

### Findings

- **F1, F2, F3, F4, F6, F8, F9** remain discharged: identical bytes to pass 3.
- **F5, F7** remain residuals as recorded in pass 1.
- **F10 (LOW, observation, not on the candidate).** The instrument's live reading on this
  shared working tree now describes other sessions' uncommitted edits rather than the
  candidate, because `discover` reads the custody collection and the witness record from
  the working tree. That is the reader doing what it says (`discover.py:3-5`) on a tree that
  moved (`CLAUDE.md`, trap T6); it is why the attestable live reading in this pass is the
  clone's. No repair is asked; a reader who wants the candidate's reading runs it on the
  candidate's bytes.

### Judgement

- **J1** and **J2** unchanged from pass 2.

### Uncovered

As pass 3. The mutants and the reuse unit suite were not re-run this pass; the instrument
bytes are identical to pass 2. I did not run `sov_land.py` itself. No clarity review for
this record.

### Standing supported

`WITNESSED` for `scripts/sov_reuse.py` at `57271f727b88032d2c1be908cf7ba819dae066d3`. It binds
to the instrument claim: the probe is what it says and grades what it says, on this host and
on a clean clone, and each of nine defeating variants fails on a real state. It says nothing
about P15-X3 holding for this node; both live predicates read unmet, truly. Exact words for
`stage_observed_by`:
`claude-fable-5-1/sov-witness@2026-09-07 pass 4 at 57271f7, clean-clone gates, candidate integrity and instrument commands (witness/discovery-and-reuse.md; witness/observations/2026-09-07-discovery-and-reuse-observation-4.json); first supported at pass 2, b0c013c`.
Receipt: `witness/observations/2026-09-07-discovery-and-reuse-observation-4.json`. The
landing-gate file for this pass reads `CONFIRMED`. Observer
`claude-fable-5-1/sov-witness@2026-09-07`, independent of the builder, contributed nothing to
the build.

## Pass 3: commit ea01dcc (2026-09-07)

### Subject

Repository candidate `ea01dcced56b345c7946b25d9dcd1a4419b4f9a1` (tree
`ada2d664818ea23001edfde8b9bed4e3a9990381`), frozen on base
`ee6080153c64938f43377617e1c4c1f231ddd00a` (`origin/main` and local `main`), HEAD of
`claude/sovereign-phase-1-5-5uzffu`. `git rev-parse HEAD` read the candidate before and after
every command. Nine changed paths against the base, matching
`.local/candidates/ea01dcced56b345c7946b25d9dcd1a4419b4f9a1.json`. `git diff-tree -r b0c013c
ea01dcc --name-status` is one line: `M docs/documentation.html`. The shared working tree holds
files not in the candidate that were not read as evidence: the other session's uncommitted
`witness/fresh-participation.md` (pass 7) and observation-7 receipt, the builder's
`reports/2026-09-07-discovery-and-reuse-slice.md`, `acceptance/A24.json` (appeared during this
pass), and my own earlier records and receipts.

### Claim

The builder claims pass-2 condition C1 discharged: `docs/documentation.html` rebuilt with every
uncommitted file stashed, so the page indexes exactly the committed documents (282), and no
other byte changed from `b0c013c`.

### Verdict

**RATIFIABLE.**

C1 is discharged: a clean clone of `ea01dcc` passes `verify`, `lint` and the documentation
check, and re-rendering the page in that clone changes nothing. The instrument is
byte-identical to the revision pass 2 witnessed. I support `BUILT -> WITNESSED` for
`scripts/sov_reuse.py` at `ea01dcc` and confirm this candidate for landing.

### Verified

| Command | Exit | Bounded excerpt |
| --- | --- | --- |
| `git rev-parse` of the eight instrument paths at `b0c013c` and `ea01dcc` | 0 | eight identical blob ids (`scripts/sov_reuse.py` `b2359e2`, `sovreuse/{__init__,discover,fixture,reuse,settle}.py`, `tests/test_sov_reuse.py`, `contracts/custodies/phase-1-5.json` `442c997`) |
| `git clone --no-hardlinks` of the candidate; `git rev-parse HEAD`; `git status --porcelain` | 0 | `ea01dcc...`; empty |
| `python scripts/sov_docs.py check` (clean clone) | 0 | `PASS: documentation page matches 282 documents` |
| `python scripts/lint.py` (clean clone) | 0 | `PASS: repository hygiene (1204 text files, 562 Python modules, 10 named debt)` |
| `python scripts/sov_docs.py build` (clean clone), then `git status --porcelain` | 0 | empty: the committed page is byte-identical to a fresh render of the committed documents; clone restored |
| `python scripts/verify.py` (clean clone) | 0 | `== documentation reader ==` / `PASS: documentation page matches 282 documents`; `PASS: repository tooling tests (111 modules, 4 shards)`; remaining `FAIL:` lines are tooling-test fixture output (`receipt_0071c026e66eb526`, `9999-A`) present in every passing run; budget overruns attributed as debt |
| `python scripts/sov_reuse.py selfcheck` (frozen shared tree) | 0 | `PASS ... 9 defeating variants each fail their own predicates for exactly the defects they declare` |
| `python scripts/sov_reuse.py run --principal principal:claude-fable-5-1` (frozen shared tree) | 1 | unchanged: Q3.1 `settlement was not against current state` (eight trunk-drifted addresses); Q3.2 `fresh participant did not use the accepted result` (`holds no live open:session grant`) |
| `git show ea01dcc:docs/documentation.html` greps | 0 | `282 documents`; zero occurrences of `discovery-and-reuse`, `pass  7`, `fresh-participation-observation-7`, `2026-09-07-discovery-and-reuse-slice` |

### Findings

- **F9 discharged.** The committed page indexes the committed documents alone; the clean-clone
  gates pass; a rebuild is a no-op.
- **F1, F2, F3, F4, F6, F8** remain discharged: the bytes pass 2 read are the bytes here.
- **F5, F7** remain residuals as recorded in pass 1.

### Judgement

- **J1** and **J2** unchanged from pass 2. They concern the clause and the live node, not the
  instrument, and are not conditions on this candidate.

### Uncovered

As pass 2. The mutants and the unit suite were not re-run this pass; they ran in pass 2
against identical bytes. No clarity review for this record.

### Standing supported

`WITNESSED` for `scripts/sov_reuse.py` at `ea01dcced56b345c7946b25d9dcd1a4419b4f9a1`. It binds
to the instrument claim: the probe is what it says and grades what it says, on this host and
on a clean clone, and each of nine defeating variants fails on a real state. It says nothing
about P15-X3 holding for this node; both live predicates read unmet, truly. Exact words for
`stage_observed_by`:
`claude-fable-5-1/sov-witness@2026-09-07 pass 3 at ea01dcc, clean-clone gates and instrument commands (witness/discovery-and-reuse.md; witness/observations/2026-09-07-discovery-and-reuse-observation-3.json); first supported at pass 2, b0c013c`.
Receipt: `witness/observations/2026-09-07-discovery-and-reuse-observation-3.json`. The
landing-gate file for this pass reads `CONFIRMED`. Observer
`claude-fable-5-1/sov-witness@2026-09-07`, independent of the builder, contributed nothing to
the build.

## Pass 2: commit b0c013c (2026-09-07)

### Subject

Repository candidate `b0c013c4bb0b6232cb646c8f5fa8e48ed2ddf797` (tree
`224d901829f7ba2f42e854da46e0f8738a31d49b`), frozen on base
`ee6080153c64938f43377617e1c4c1f231ddd00a` (`origin/main` and local `main`), HEAD of
`claude/sovereign-phase-1-5-5uzffu`. `git rev-parse HEAD` read the candidate before and after
every command. Nine changed paths against the base, matching
`.local/candidates/b0c013c4bb0b6232cb646c8f5fa8e48ed2ddf797.json` exactly; `git diff
26b1887..b0c013c` is the repair: seven files, `docs/documentation.html` among them. The working
tree also holds files that are not this candidate's and were not read as evidence: the other
session's `witness/fresh-participation.md` (pass 7, uncommitted) and
`witness/observations/2026-09-07-fresh-participation-observation-7.json`, the builder's
`reports/2026-09-07-discovery-and-reuse-slice.md` (appeared during this pass), and my own
pass-1 record and receipt.

### Claim

The builder claims F1, F2, F3, F4, F6 and F8 repaired, F5 and F7 left as residuals, and a
rebuilt `docs/documentation.html`.

### Verdict

**RATIFIABLE-WITH-CONDITIONS.**

The instrument's claim now reproduces, on this host and on a clean clone. Every pass-1
finding the builder took is discharged in the bytes. One new finding, F9, is not in the
instrument but in the candidate: the committed `docs/documentation.html` was rendered over a
working tree holding documents the commit does not carry, so a clean checkout of `b0c013c`
fails `python scripts/verify.py`. I support `BUILT -> WITNESSED` for `scripts/sov_reuse.py` at
this revision and do not confirm this candidate for landing.

### Verified

Environment as pass 1 (`SOV_PRINCIPAL=principal:claude-fable-5-1`). Sandbox: a fresh
`git clone --no-hardlinks` of the candidate under scratch, HEAD `b0c013c`, porcelain empty.

| Command | Exit | Bounded excerpt |
| --- | --- | --- |
| `python scripts/verify.py` (shared working tree) | 0 | 25.4 s; `PASS: documentation page matches 283 documents`; tooling shard 3 lists `test_sov_reuse`; `PASS: 14 witness receipt(s) graded, 0 unusable, 14 stale against their subject` |
| `python scripts/verify.py` (clean clone of `b0c013c`) | 1 | `== documentation reader ==` / `FAIL: docs/documentation.html is stale`; `FAIL: test_the_built_page_is_current (scripts.tests.test_sov_docs.Staleness...)` `AssertionError: 1 != 0`; summary `FAIL: documentation reader, repository tooling tests` |
| `python scripts/sov_docs.py check` (working tree / clean clone) | 0 / 1 | `PASS ... 283 documents` / `FAIL: docs/documentation.html is stale` |
| `python scripts/sov_docs.py build` in the clone, then `git diff` | 0 | page moves from `283 documents` to `282`; the removed content includes `subject  discovery-and-reuse` (my uncommitted pass-1 record) and the pass-7 text of `witness/fresh-participation.md` (uncommitted); clone restored afterwards |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1207 text files, 562 Python modules, 10 named debt)` |
| `python scripts/sov_reuse.py selfcheck` | 0 | `PASS ... 9 defeating variants each fail their own predicates for exactly the defects they declare` |
| `python -m unittest scripts.tests.test_sov_reuse` | 0 | `Ran 14 tests OK` |
| `python scripts/sov_reuse.py run --principal principal:claude-fable-5-1` (text; `--json`) | 1 / 1 | same two predicates as pass 1: Q3.1 `settlement was not against current state` (eight trunk-drifted addresses, `landing ee6080153c64`, `inventory []`); Q3.2 `fresh participant did not use the accepted result` (`holds no live open:session grant`) |
| `python scripts/sov_reuse.py run --principal principal:claude-fable-5 --json` (control) | 1 | `used True grant_6ab7d1d0a99e419e`; `P15-Q3.2: []`; Q3.1 drift only |
| `python scripts/sov_custody.py selfcheck` | 0 | `46 case(s), 27/27 declared refusals reached`; `selfcheck PASS` |
| `python scripts/sov_active_phase_progress.py` | 0 | no output |
| `python scripts/sov_next.py` | 0 | `scripts/sov_fresh.py [LANDED]`; `scripts/sov_reuse.py [PRESENTED]` |
| M0 unmutated clone (scratch script over `sovreuse.reuse`, pass-2 code) | - | `inventory=[]`; grades Q3.1 drift only, Q3.2 `[]` (F1 discharged) |
| M4 tampered journal entry on the clone | - | `reach='BrokenChain: entry 40 digest does not match its contents'`, `used=False`, Q3.2 `missing capability`, `did not use`; no traceback (F2 discharged) |
| M2, M3, M6, M8 on the clone | - | record denying, relation lookalike, extra branch (`branch feat/left-behind`), extra worktree: each still fails naming the changed state |
| fixture variants, facts behind each of the nine (scratch script) | - | reader is `principal:fresh-reader` in every variant but `no-grant` (`principal:bdo`); `journal-tampered` drifts the export digest and reads `BrokenChain: entry 0`; every other variant fails on the same real state as pass 1 |
| `python -c` import of `sovnode.journal` | 0 | `journal.custody.BrokenChain` resolves to `soveraeign_record_service.errors.BrokenChain` |

### Pass-1 findings, re-read against these bytes

- **F1 discharged.** `settle.py:126-128` lists `%(refname:short)|%(symref)` and keeps only lines
  with an empty symref; `fixture.py:95-99` gives the fixture history a bare remote with
  `origin/HEAD` set, and `test_sov_reuse.py:126-127` asserts `origin|refs/remotes/origin/main`
  is listed. The unmutated clone reads `inventory=[]`.
- **F2 discharged.** `reuse.py:41-43` catches `journal.custody.BrokenChain` and returns it as
  the capability's reason; variant `journal-tampered` (`fixture.py:210-216`) and
  `test_tampered_export_is_refused_not_raised` cover it. The clone mutant is a graded refusal.
- **F3, F4 discharged.** The member note reads nine variants and states both live facts:
  the eight trunk-drifted addresses and the missing grant. Both match what I measured.
- **F5 residual, as recorded.** Nothing executes the custody closure `COMMAND` expression.
- **F6 discharged.** `fixture.py:33` names `principal:fresh-reader`; `_registry_with_reader`
  adds it to the fixture registry; `build` opens the fixture root's office for both principals;
  `run_variant` reads as the reader. The facts dump shows the reader in every variant.
- **F7 residual, as recorded.**
- **F8 discharged.** `EXPECTED_FAILURES` carries exact lists; `sov_reuse.py:73-75` and
  `test_sov_reuse.py:64-66` compare equality per predicate.

### New finding

- **F9 (HIGH)** `docs/documentation.html` at `b0c013c`. The committed page indexes 283
  documents and contains text that exists only in uncommitted working-tree files: my pass-1
  record (`subject  discovery-and-reuse`, nine occurrences) and the other session's pass-7
  rewrite of `witness/fresh-participation.md` (`pass  7`, `observation-7`). The commit carries
  neither: its `witness/fresh-participation.md` is pass 6, and `witness/discovery-and-reuse.md`
  is untracked. On a clean clone of the candidate `python scripts/sov_docs.py check` exits 1
  and `python scripts/verify.py` exits 1 (`documentation reader` and
  `test_sov_docs.Staleness.test_the_built_page_is_current`). On the shared working tree both
  pass, because the files are present there. This is the defect class procedure 6a names: the
  check graded a working tree holding what the commit does not. Consequence if landed as-is:
  `main` fails verify on any clean checkout, including CI. Attribution: the render is the
  builder's; the documents it swept in are mine and the other session's, uncommitted in a
  shared tree (`CLAUDE.md`, trap T6). The instrument is untouched by this finding.

### Conditions

- **C1 (discharges F9).** Re-render `docs/documentation.html` from a tree that holds exactly the
  candidate's committed documents (a clean checkout, or `git stash -u` of the shared tree), so
  `python scripts/sov_docs.py check` exits 0 on a clean clone of the successor, and freeze a
  successor candidate. Pass 3 re-runs the clone verify and the instrument commands; the
  instrument digests below should be unchanged.

### Judgement

- **J1** unchanged from pass 1: which reading of "settlement follows current state" P15-Q3.1
  owns. Under the instrument's reading Q3.1 on this node stays unmet until a new
  fresh-participation witness pass, and every landing of this custody keeps it so.
- **J2** unchanged: whether a grant to `principal:claude-fable-5-1` on the live node is Bdo's
  to issue and the intended route for P15-Q3.2, or the control reading as
  `principal:claude-fable-5` is the reuse the clause asks for. J3 from pass 1 is discharged for
  the fixture by F6; on the live node it is the same question as J2.

### Uncovered

As pass 1, plus: I did not run `sov_docs.py build` on the shared working tree (it would write
a repository file); the page comparison came from the clone. I did not read
`reports/2026-09-07-discovery-and-reuse-slice.md`. No clarity review for this record.

### Standing supported

`WITNESSED` for `scripts/sov_reuse.py` at `b0c013c4bb0b6232cb646c8f5fa8e48ed2ddf797`. The
block above declares it once, for the gate. It binds to the instrument claim at this
revision: the probe is what it says and grades what it says, on this host and on a clean
clone, and each of nine defeating variants fails on a real state. It says nothing about
P15-X3 holding for this node (both live predicates read unmet, truly), and it does not confirm
the candidate for landing while F9 stands; the landing-gate file for this pass reads
`NOT_CONFIRMED`. Exact words for `stage_observed_by`:
`claude-fable-5-1/sov-witness@2026-09-07 pass 2 at b0c013c, instrument, selfcheck, unit suite, live reading, clean-clone and tampered-export mutants (witness/discovery-and-reuse.md; witness/observations/2026-09-07-discovery-and-reuse-observation-2.json)`.
Receipt: `witness/observations/2026-09-07-discovery-and-reuse-observation-2.json`. Observer
`claude-fable-5-1/sov-witness@2026-09-07`, independent of the builder, contributed nothing to
the build.

## Pass 1: commit 26b1887 (2026-09-07)


Pass 1. The block above advances nothing at the standing gate: only the whole word
`WITNESSED` does, and this observation does not support it. It records that the member
stands at `BUILT` and says why it goes no further yet.

## Subject

Repository candidate `26b1887e84357124c8e99f42382d064ffbeccf8c` (tree
`511389dd9183a24f3fed37835b379e8a032fff5e`), frozen on base
`ee6080153c64938f43377617e1c4c1f231ddd00a`, which is `origin/main` and local `main`. HEAD of
`claude/sovereign-phase-1-5-5uzffu`. `git rev-parse HEAD` read the candidate before and after
every command below, and `git status --porcelain` was empty throughout until this record and
its receipt were written. The change is `git diff ee60801..26b1887`: eight paths, matching
`.local/candidates/26b1887e84357124c8e99f42382d064ffbeccf8c.json` `changed_paths` exactly.

The member is `scripts/sov_reuse.py`, the one `ITEM` under
`custody:phase-1-5/discovery-and-reuse` in `contracts/custodies/phase-1-5.json`, stage
`VERTICAL_SLICE`, standing `BUILT`, work_state `PRESENTED`, `stage_observed_by` null.

## Claim

By the builder (commit message of `26b1887` and the member note): `scripts/sov_reuse.py` is a
vertical slice for exit clause P15-X3. A fresh participant reads the artifact alone for the
result `custody:phase-1-5/fresh-participation` carries at `WITNESSED`, reconstructs why it
stands (witness record, receipt, bytes now at every observed address, the merge that carried
the witnessed revision onto the trunk, inventory left behind), restores the node journal under
`nodes/` to the head the receipt holds outside the export, enters the node as the principal it
declares, and grades P15-Q3.1 and P15-Q3.2 through `conformance/commissioning.py`. `selfcheck`
builds the result under a fixture root and claims eight defeating variants each fail their own
predicates for the reason they declare. The live reading as `principal:claude-fable-5-1` is
claimed to fail on exactly two facts, both true readings of the record.

## Verdict

**NOT-YET.**

The instrument does what the claim says on this host, and every fixture variant fails on a real
state. It is not yet a reading a fresh participant can trust from any host: on a plain
`git clone` of the candidate, which is the canonical fresh participant, the unmutated artifact
reads P15-Q3.1 unmet for a branch named `origin` that does not exist (F1). A tampered journal
export crashes the reader instead of being refused (F2). Both go back to the builder inside
this concern.

## Verified

Environment: `SOV_PRINCIPAL=principal:claude-fable-5-1` for every command. Linux host,
Python 3, git 2.x. Sandbox for mutation: `git clone --no-hardlinks` of the frozen candidate
under the scratch directory; nothing below wrote to the working tree.

| Command | Exit | Bounded excerpt |
| --- | --- | --- |
| `git rev-parse HEAD`; `git rev-parse HEAD^{tree}`; `git status --porcelain` | 0 | `26b1887e...`; `511389dd...`; empty |
| `python scripts/verify.py` | 0 | 23.7 s wall; `PASS: repository tooling tests (111 modules, 4 shards)`; shard 3 lists `test_sov_reuse`; `PASS: 12 witness receipt(s) graded, 0 unusable, 12 stale against their subject`; conformance `SUITE PASS cases=33 coverage_gaps=0` |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1204 text files, 562 Python modules, 10 named debt)` |
| `python scripts/sov_reuse.py selfcheck` | 0 | `PASS: ... positive variant and 8 defeating variants each fail their own predicates for the reason they declare` (2.2 s) |
| `python -m unittest scripts.tests.test_sov_reuse` | 0 | `Ran 13 tests in 4.400s OK` |
| `python scripts/sov_reuse.py run --principal principal:claude-fable-5-1` | 1 | `P15-Q3.1: settlement was not against current state`; `P15-Q3.2: fresh participant did not use the accepted result`; trace: `drifted [8 addresses]; landing ee6080153c64; inventory []`; `use as principal:claude-fable-5-1: REFUSED ... holds no live open:session grant` |
| same with `--json` (twice) | 1 | identical grades both runs |
| `python scripts/sov_reuse.py run --principal principal:claude-fable-5 --json` (control) | 1 | `used: COMMITTED grant_6ab7d1d0a99e419e`; `P15-Q3.2: []`; `P15-Q3.1: [settlement was not against current state]` |
| `python scripts/sov_custody.py selfcheck` | 0 | `46 case(s), 27/27 declared refusals reached`; `selfcheck PASS` |
| `python scripts/sov_active_phase_progress.py` | 0 | no output (0 bytes) |
| `python scripts/sov_next.py` | 0 | `scripts/sov_fresh.py [LANDED] drawn`; `scripts/sov_reuse.py [PRESENTED] drawn` under `custody:phase-1-5/discovery-and-reuse` |
| sha256 of `.git/sov-sessions/*` before and after a live run | 0 | `shared session store unchanged by live run` |
| git: for each of the eight drifted addresses, sha256 of the blob at `571e936`, `ee60801`, `HEAD` against receipt 6 | 0 | all eight: receipt digest equals the blob at `571e936`; blob differs at `ee60801` already (drifted on the trunk, not in this candidate) |
| `git rev-list --merges --ancestry-path 571e936..HEAD` intersected with `git rev-list --first-parent HEAD` | 0 | one commit: `ee60801 Merge PR #218` |
| `git branch -a --contains 571e936`; `git worktree list --porcelain`; `git symbolic-ref refs/remotes/origin/HEAD` | 0 / 0 / 128 | current branch, `main`, their origin twins; one worktree; `origin/HEAD is not a symbolic ref` on this host |
| journal export read: grant-bearing entries in `nodes/node-local/journal/23d3b48086be.json` | 0 | `open:session`, `close:session`, `read:registry` granted to `principal:claude-fable-5` by `principal:bdo`; nothing names `principal:claude-fable-5-1` |
| fixture variants: facts behind each of the eight defeats (scratch script over `sovreuse.fixture`) | 0 | see F8 and the receipt; every failure comes from a real state |
| fourteen mutants of the real artifact in the clone (scratch script over `sovreuse.reuse`) | mixed | see F1, F2 and the receipt |

## Reproduced

- `verify` and `lint` pass on the frozen tree; the candidate record's `checks` agree with what
  I ran, but I did not take the record as evidence.
- `selfcheck` passes and reports eight variants. Each defeating variant fails on a state that
  exists in the fixture: `bytes-moved` drifts `scripts/sov_fresh.py`; `revision-unknown` finds
  no landing on the line; `lease-left-behind` reads an orphaned lease on the custody from the
  unreleased store; `branch-left-behind` reads `feat/left-behind`; `head-private` never
  restores; `no-grant` reaches the node and is refused by it for `principal:bdo`;
  `oral-history` reads `SOV_PRINCIPAL_REGISTRY` from the environment; `no-witness` reads an
  absent record. None is a probe artefact.
- The live reading fails on exactly two predicates and both are true readings: the eight
  drifted addresses all drifted on the trunk between `571e936` and the merge `ee60801` (I
  recomputed each digest from git), and the node's journal holds no grant for
  `principal:claude-fable-5-1`. The control run as `principal:claude-fable-5` commits a
  crossing under `grant_6ab7d1d0a99e419e` and clears P15-Q3.2, so the refusal is the grant,
  not the probe.
- The fresh-participation member's `work_state` change `PRESENTED -> LANDED` is corroborated
  by git: `ee60801` is on the first-parent line of HEAD and its ancestry holds `571e936`.
  `origin/main` and local `main` both equal `ee60801`.
- The custody edits grant, ratify and settle nothing: the new member declares `BUILT`,
  `stage_observed_by` null (schema permits null, meaning a build claim); `judgement_seat`
  stays `seat:root`; `contracts/custody.schema.json` is unchanged; `sov_custody.py selfcheck`
  and `sov_active_phase_progress.py` both pass. `conformance/commissioning.py` is untouched by
  the diff, so the oracle was not weakened; `check_q31` and `check_q32` receive the booleans and
  fields `reuse.py:99-111` assembles.
- What the instrument measures versus reads as declared (procedure 6a): digests against bytes,
  landing and inventory from git, orphaned leases from the store, journal restore through the
  Record Service chain verifier, the crossing through the real node: measured. The witness
  record's block, the receipt's `standing_supported` and `observer_relation`: declarations,
  and `settle.py:36-43` says so. `oral_history_used` measures one environment variable,
  `SOV_PRINCIPAL_REGISTRY`; `--principal` overrides `SOV_PRINCIPAL`, so that variable cannot
  reach the reading undeclared.
- Every new module is under 300 lines (largest `fixture.py`, 210). No secrets, no absolute
  paths, no vocabulary outside `CLASSIFICATION.md`/`SPEC.md` (`LANDED`, `PRESENTED`,
  `WITNESSED`, `BUILT`, `INDEPENDENT`). No unrelated file changed. No helper is declared in
  the commit or the note.

## Findings

- **F1 (HIGH)** `scripts/sovreuse/settle.py:122-126`. `keep` holds `origin/HEAD`, but
  `git branch -a --format=%(refname:short)` renders `refs/remotes/origin/HEAD` as `origin`.
  On the unmutated clone the instrument reports `inventory=['branch origin']` and P15-Q3.1
  fails `closure left temporary coordination inventory` (mutant M0). The live repository has
  no `origin/HEAD` (`git symbolic-ref` exits 128), so the live reading hides this. The fixture
  history (`fixture.py:64-83`) has no remote, so no positive or defeating case covers a clone.
  Consequence if witnessed as-is: the instrument's Q3.1 verdict depends on the reader's
  remote configuration, not on the artifact, and fails for the canonical fresh participant.
- **F2 (MEDIUM)** `scripts/sovreuse/reuse.py:39-42` catches only `RestoreRefused`. A journal
  export with one altered entry (mutant M4) raises
  `soveraeign_record_service.errors.BrokenChain: entry 40 digest does not match its contents`
  out of `reuse.run`, so `sov_reuse.py run` ends in a traceback rather than a graded
  `capability` refusal; `discover.py:7-8` promises a defect, never a traceback.
  `fixture.EXPECTED_FAILURES` (`fixture.py:34-44`) has no tampered-export variant.
  Consequence: the defeating case that matters most for reaching a capability, a journal that
  is not what it says, has no graded answer.
- **F3 (LOW)** `contracts/custodies/phase-1-5.json:157` (member note) says "six defeating
  variants"; `fixture.py:34-44` declares eight and `selfcheck` prints eight. The note
  misdescribes the artifact it points at in the same commit.
- **F4 (LOW)** Same note describes the live reading as refused on the grant only. The live
  reading also fails P15-Q3.1 on eight addresses that drifted on the trunk after the
  witnessed revision. A reader of the custody learns one of the two live facts.
- **F5 (LOW)** `contracts/custodies/phase-1-5.json:136` changes the closure `check` from
  `python scripts/sov_next.py` to `python scripts/sov_reuse.py selfcheck`. Nothing under
  `scripts/` executes a closure `COMMAND` expression (`sovcustody/board.py:167` prints it;
  `sovcustody/model.py:158-160` checks it is present). The unit suite under verify is what
  measures. No consequence today; the check named as closure is a declaration nobody runs.
- **F6 (LOW)** `fixture.py:139-148` and `176-182`: the fixture's builder and its "fresh
  participant" are the same principal, `principal:fresh-probe`, re-entering the node it opened
  under `principal:fixture-root`. The positive variant shows the reader's mechanics, not
  another participant. See J3.
- **F7 (LOW, observation)** `settle.py:122-123` excludes the branch HEAD sits on and its origin
  twin from inventory, so a leftover branch the reader happens to have checked out is never
  reported. The docstring declares this; it is a reading that depends on where the reader
  stands.
- **F8 (LOW)** `scripts/sov_reuse.py:64-72` asserts inclusion, not the exact reason set:
  `no-witness` also fails `settlement was not against current state` and `fresh reuse missing
  basis`; `revision-unknown` also fails `settlement was not against current state`. "Each
  fail their own predicates for the reason they declare" holds as inclusion; "exactly the
  predicates it declares" holds. A precision note on the wording of the claim.

Mutants that behaved as the reader should (recorded so a reader can calibrate F1 and F2):
absent receipt, record denying (`NOT_WITNESSED`), record lookalike (`WITNESSED*`), receipt
denying, relation lookalike (`INDEPENDENTLY_UNCHECKED` is not read as independent), head
mismatch, extra branch, extra worktree, orphan HEAD (landing `NONE`, `declares LANDED; no merge
on the current line carries it`), truncated digest list (`observed no addresses this reader
can measure`), member demoted to `BUILT` (`carries no member at WITNESSED`), unknown revision.
Every one failed a predicate for a reason that names the state I changed.

## Conditions

None declared: the verdict is NOT-YET. What would discharge F1 and F2 is the builder's
ordinary work inside the concern: resolve `origin/HEAD` by symref rather than by name (or
filter remote symrefs) in `temporary_inventory`, add a fixture history with a remote so the
clone case has both polarities, catch the Record Service's chain error in `reach` and return
it as the capability's reason, and add a tampered-export variant to `EXPECTED_FAILURES`. F3
and F4 are note repairs. I name these as what I would re-run, not as instructions the builder
must take.

## Judgement

- **J1** Is P15-Q3.1 "settlement follows current state" rightly operationalised as "no byte at
  any of the 26 addresses receipt 6 observed has changed since `571e936`"? Under that reading
  Q3.1 on this node cannot hold again without a new fresh-participation witness pass, and this
  candidate itself edits an observed address. The alternative reading is that settlement is
  the merge that carried the exact witnessed revision (it did) and drift since is
  `STALE_SUBJECT` debt as `witness/observations/README.md` grades it. Which reading does the
  clause own?
- **J2** P15-Q3.2 on the live node reads unmet because the journal grants only
  `principal:claude-fable-5`, issued under the name `principal:bdo`, which fresh-participation
  pass 5 found unauthenticated. Is a grant to `principal:claude-fable-5-1` (registry entry
  `UNVERIFIED`) Bdo's to issue on the live node, and is that the intended route, or is the
  control reading as `principal:claude-fable-5` the reuse the clause asks for?
- **J3** Does a positive case in which the builder's own principal re-enters its own node
  evidence "another fresh participant", or must the slice's positive case use a second
  fixture principal granted by the fixture root?

## Uncovered

I did not run the conformance oracle outside `verify`; did not read `sovfresh/probe.py`
below its surface; did not try a clone whose default branch is `main` rather than the
candidate branch; did not test on Windows; did not review the Record Service's restore path
beyond what M4 exercised; did not read any `reports/` file from this session; and did not
obtain a `clarity` review for this record, which `contracts/clarity.json` covers. The
`origin` false positive was found by mutation on a clone, not by reasoning from the code
first, so other host-dependent readings of the same shape may remain.

## Standing supported

`BUILT`. This observation supports no transition. It supports `BUILT` standing for
`scripts/sov_reuse.py` at `26b1887` and does not support `BUILT -> WITNESSED` until F1 and F2
are repaired and a later pass reproduces the claim on a clone. Exact words for
`stage_observed_by` when a later pass supports it: none yet; for this pass the field stays
`null`. Receipt: `witness/observations/2026-09-07-discovery-and-reuse-observation.json`.
Observer `claude-fable-5-1/sov-witness@2026-09-07`, independent of the builder, contributed
nothing to the build, and reads the artifact through its declared surface and git only.

## Tree movement after the Finding froze

At 04:59:20 UTC, after every command above had completed (last at 04:54:34) and after this
record was first written (04:58:39), another session rewrote `witness/fresh-participation.md`
in the working tree (uncommitted; `git status` reads `M`; 258 insertions): a pass 7 at
`26b1887` whose block still declares `WITNESSED`. HEAD did not move. That file is not in the
candidate and is not one of the two files this witness writes. The instrument reads it, so I
re-ran `python scripts/sov_reuse.py run --principal principal:claude-fable-5-1 --json` at
05:00:35 UTC: exit 1, grades and other defects identical to the 04:50:22 run, record standing
`WITNESSED`, receipt list unchanged (the custody member's `stage_observed_by` still names
observation 6). Every reading in this record was taken over the frozen candidate; the
mutation sandbox is a clone of the commit and never saw the working tree. Attribution of
the working-tree change is the other session's, not the builder's and not mine.
