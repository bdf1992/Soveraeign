# Witness record: an address below the file (scripts/sovaddress.py)

```witness
standing_supported  WITNESSED
subject  sovaddress
revision  b8012544a5a4c30e089a02876145840b1f5d213a
pass  5
```

Five passes by the same role. Pass 5 (candidate `b801254`) is current and owns the declaration
above. Passes 4, 3, 2 and 1 follow it unchanged as history; their subjects `f957987`, `a63b09b`,
`e835205` and `a57d736` are superseded, and their bytes are carried into `b801254` unaltered.
No `*_status` field in `STATUS.yaml` names this subject and no custody member carries
`scripts/sovaddress.py`; the work was carried under `custody:phase-1-5/discovery-and-reuse`.

## Pass 5: candidate b801254 (2026-09-07)

Verdict: **RATIFIABLE**. Landing **CONFIRMED**.

The reading is the narrow one this record drew at pass 4: blob identity carries the code reading,
the integration reading is retaken at the new base. Both halves were measured. All 14 blobs are
identical to `f957987`, and so to `a63b09b`, which passes 1 to 3 observed; the declared
`changed_paths` equal `git diff --name-only b1448ee...b801254` and the two-dot range, 14 for 14,
with nothing in the range undeclared, nothing declared outside it, and nothing removed. On a
clean full-history clone `verify.py` exits 0 and `lint.py` exits 0; the eleven suites pass, the
tooling runner passes twice, the four readers grade `b801254` with the same verdict per receipt
and the same summary as `b1448ee`, and 164 of 165 present committed addresses digest identically.
The sixteen mutants were **not** rerun, because no blob moved; that is said here rather than left
to be assumed from a pass that did run them.

One measured detail worth its own line: the three paths this candidate adds relative to its base
are `scripts/sovaddress.py`, `scripts/sovclarity/digests.py` and
`scripts/tests/test_sovaddress.py` - exactly the three the discarded candidate `434c6a5` left
out. The failure mode F17 describes is absent from this candidate, and that is measured rather
than assumed.

**F18 is discharged.** `base_commit` is `b1448ee`, which is both `origin/main` and the local
`main` ref, so `scripts/sov_candidate.py:83` has nothing to refuse.

Subject frozen: candidate `b8012544a5a4c30e089a02876145840b1f5d213a`, tree `f0c7ce1b1c4251bdaf0ef2bb2bcc416dcbfc6368`, base `b1448eeb458afa4a8c60b57c1cb46906246af7f7`, record
`.local/candidates/b8012544a5a4c30e089a02876145840b1f5d213a.json`, one commit past the base. `git rev-parse HEAD` read the commit
before and after every command and `git status --porcelain` was empty until the deposits.

### The two questions put to this witness

**Is F17 a precondition of landing, or a finding to route? A finding to route. Land this
candidate.** The reason is specific and it is not indulgence. My confirmation does not rest on
the candidate record's `checks` field at all. I ran `verify.py` and `lint.py` on a clean
full-history clone of this exact commit - which is precisely the reading F17 says the freeze
fails to take - so the defect in how the record's `PASS` was obtained does not reach the
evidence this landing stands on. That is what an independent witness is for, and here it did the
job the freeze did not.

Two conditions attach to that answer, and they are not decoration. First, **the landing must
cite this receipt rather than the record's `checks` field**; that field is not evidence about its
own tree until F17 is repaired, this candidate's included. Second, **F17 becomes a precondition
the moment a landing rests on that field alone** - an unattended run, a skipped witness, a
`--skip-checks` freeze taken as qualification. This observation does not cover such a landing.
Routing F17 and J5 to Bdo as the next concern is right, and I am not treating the coordinator's
message as consent for anything; this is my own reading, stated because it was asked for.

**Should `.local/candidates/434c6a5….json` be moved to `SUPERSEDED`? Not yet, and never
erased.** Leave it exactly as it is until the F17 concern has read it: it is the only artifact in
the tree that shows a `FROZEN` record whose `checks verify PASS` is false of the tree it names,
and I measured that falsity from the commit itself (`run_tooling_tests.py` exits 1 there). After
that concern has taken it as evidence, moving it to `SUPERSEDED` is right and overdue - with the
`checks` bytes preserved as written, because a retraction adds a counter-record and never
rewrites the original. Not tidying away evidence one produced is the correct instinct and I would
keep it.

### Findings

- **F17 (high) - stands, routed, not held.** Above. Unrepaired in this candidate by decision, not
  by oversight.
- **F18 - discharged.** The base is current.
- **F19 (low) - stands by agreement.** Eight candidate records, all `FROZEN`, including the
  discarded `434c6a5` and four superseded ones. Owed after F17 reads them.
- **F1, F4, F13 discharged; F2, F3, F5-F8, F11, F12 repaired; F15 retracted at pass 3.** All as
  recorded in passes 2 to 4, on bytes identical to these.
- **F21 (info).** This concern has now been frozen five times against four different bases in one
  day, and each move cost a witness pass. Nothing here is wrong - the base moving is other work
  landing - but the pattern is worth naming: what made the re-passes cheap was that the bytes
  were provably unchanged, so only the integration reading had to be retaken. Without blob
  identity each re-freeze would have cost a full re-witness.

### Judgement items

- **J5** (from pass 4) stands and is routed with F17: should
  `contracts/repository-candidate-lifecycle.json` require a candidate's `checks` to be true of
  its `candidate_tree`, and require the record to name the tree they graded?
- J1, J2 discharged; J4 answered at pass 3.

### Verified

Every command ran with `SOV_PRINCIPAL=principal:claude-fable-5-1`.

- `git rev-parse HEAD` -> `b8012544a5a4c30e089a02876145840b1f5d213a` before and after every command; `git status --porcelain` ->
  empty until the deposits; `git rev-parse b801254^{tree}` -> `f0c7ce1b1c4251bdaf0ef2bb2bcc416dcbfc6368`; `git ls-remote origin`
  -> branch at `b801254`, `main` at `b1448ee`; `git rev-list --count b1448ee..b801254` -> 1.
- Blob identity: `git rev-parse f957987:<p>` equals `b801254:<p>` for all 14 declared paths;
  0 differ. The object ids are recorded in the receipt.
- Completeness: declared `changed_paths` (14) equals the three-dot range (14) and the two-dot
  range (14); nothing in the range undeclared; nothing declared outside it; paths added -
  `scripts/sovaddress.py`, `scripts/sovclarity/digests.py`, `scripts/tests/test_sovaddress.py`;
  paths removed - none; every declared path byte-equal to the working tree.
- Clean full-history clone at `b801254`: `python scripts/verify.py` -> **exit 0**, `PASS: 10 of
  10 snapshot claim(s) match the record`; `python scripts/lint.py` -> **exit 0**;
  `python scripts/run_tooling_tests.py` twice -> exit 0, exit 0, 112 modules; tree clean after.
- Eleven suites on a `git archive` copy: `test_sovaddress` 18, `test_sov_witness_layer` 72,
  `test_witness_record` 14, `test_sov_diagrams` 16, `test_sov_clarity` 7, `test_sov_reuse` 15,
  `test_repository_candidate_effects` 10, `test_repository_candidate` 4, `test_sov_land` 31,
  `test_landing_isolation` 16, `test_landing_ledger` 15 - all OK; `test_sovaddress` also runs as
  a script.
- Four readers at `b801254` against `b1448ee`: `records` exit 0 both, identical verdict per
  receipt and identical summary (27 graded, 0 unusable, 27 stale); `sov_diagrams.py` and
  `sov_clarity.py check` exit 0 both, byte-identical; `sov_reuse.py run` exit 1 both, identical
  verdict, predicates and drifted set. 165 committed addresses, 164 identical both ways, 1
  absent (pre-existing), 0 containing `#`.
- Mutants: not rerun; no blob moved from `f957987`, where all sixteen were caught.
- After the deposits: `python scripts/sov_witness_layer.py records` -> exit 0, this pass's
  receipt `CURRENT`; `python scripts/sov_clarity.py check` -> exit 0; `python scripts/lint.py`
  -> exit 0; `python scripts/sov_standing.py` -> PASS; `git -C <root> status --porcelain` ->
  ` M witness/sovaddress.md` and two untracked receipts.

### Uncovered

`sov_land.py land` was not executed. The pass-4 probes and the sixteen mutants were not rerun.
Nothing under `conformance/` or `services/` changed. The pass-4 record and receipt were
re-deposited from byte-identical scratch copies after checking the tracked record's passes 3 to 1
matched them exactly; this witness did not re-observe `f957987` to do so.

### Standing supported

`WITNESSED` for `scripts/sovaddress.py`, its four adoptions, and the freeze ordering in
`scripts/sovland/candidates.py`, as carried by candidate `b8012544a5a4c30e089a02876145840b1f5d213a`. `stage_observed_by`, if a
custody member is ever minted: `claude-fable-5-1/sov-witness@2026-09-07-sovaddress, pass 5 at
b8012544a5a4c30e089a02876145840b1f5d213a`. Not supported: any reading of a candidate record's `checks` field as evidence about its
own tree, until F17 is repaired. Receipt:
`witness/observations/2026-09-07-sovaddress-observation-5.json`. Landing observation:
`.local/observations/2026-09-07-sovaddress-landing-5.json`, `CONFIRMED`. This record is an
observation; it ratifies nothing and settles nothing.

## Pass 4: candidate f957987 (2026-09-07)

Verdict: **RATIFIABLE**. **REPRODUCED**: all 14 declared paths are carried by the commit and
equal the working tree, the declared `changed_paths` equal the `6498fc7..f957987` range exactly,
and all 14 blobs are identical to `a63b09b`. On a clean full-history clone `verify.py` exits 0
and `lint.py` exits 0, so **F1 is discharged - by the base moving, not by any code change**.
Eleven suites pass, tooling passes twice, all sixteen mutants are caught with the control green,
the four readers grade `f957987` with the same verdict per receipt and the same summary as
`6498fc7`. Landing is **CONFIRMED** on the evidence. Two things that confirmation does not
cover: **F17**, the freeze runs its checks against the working directory rather than the
committed tree, which I reproduced and which the discarded candidate `434c6a5` demonstrates on
disk today; and **F18**, `origin/main` has moved to `b1448ee`, so the lander's own gate will
refuse this base until the work is reconciled and re-frozen.

Two questions were put to this witness beyond re-confirming the earlier dispositions. Both are
answered below: F17 for the untracked-file gap, and the "Does WITNESSED bind to f957987"
paragraph for the second.

Subject frozen: candidate `f957987b45e02d86341c0c348a5c8f3f90af0777`, tree `d89cedaacd75eae4ff420f89937bfa6761eb9158`, base `6498fc7b3172476df54882d7b65c47f52366c8c8`, record
`.local/candidates/f957987b45e02d86341c0c348a5c8f3f90af0777.json`. `git rev-parse HEAD` read the commit before and after every
command and `git status --porcelain` was empty until the deposits. Every mutating command ran in
a scratch clone at `f957987`, a worktree at `6498fc7`, a `git archive` copy of `f957987` or of
`434c6a5`, or a throwaway repository.

### Does WITNESSED bind to f957987?

Yes, and not by inheritance. A standing claim binds to bytes read in a context, so blob identity
alone would carry only half of it. Both halves were taken here. The code reading transfers by
measurement: `git rev-parse a63b09b:<p>` equals `f957987:<p>` for all 14 paths, and the blob ids
are recorded in the receipt so a later reader can check that claim without repeating this pass.
The integration reading does not transfer, because the base changed from `aeecc60` to `6498fc7`
and the readers run against the whole tree, so it was retaken: verify, lint, the eleven suites,
tooling twice, the sixteen mutants and the four readers' equivalence were all rerun at this base.
The `a63b09b` SHA being gone costs nothing that was not re-measured.

### F17: the freeze's checks read the working directory, not the committed tree

The repair landed at `a63b09b` moved the checks *after* the commit, and that much holds: in my
reproduction the check ran with `HEAD` equal to the candidate commit. But `tree.gather_checks`
runs `verify.py` as a subprocess with `cwd=repo.ROOT`, which is the working directory. So the
checks are late in time and wrong in space: they read a tree that is the commit *plus whatever
is untracked or dirty*, and `freeze` stages only `--path`, which the operator computed with
`git diff --name-only main` - a command that by construction cannot name an untracked file.

Reproduced through the real `candidates.freeze` in a throwaway repository: one tracked file
staged, one untracked file the change needs, check present at check time, commit tree without it,
record written `checks {"verify": "PASS"}` and `changed_paths ["x.py"]`, `git status` after the
freeze still showing the file untracked.

Confirmed on the artifact rather than from the report. `.local/candidates/434c6a5...json` is
still on disk, `state FROZEN`, `checks verify PASS`, 11 `changed_paths`. `git cat-file` on its
tree shows `scripts/sovaddress.py`, `scripts/sovclarity/digests.py` and
`scripts/tests/test_sovaddress.py` all absent. A `git archive` copy of that exact commit runs
`python scripts/run_tooling_tests.py` and exits **1**, `FAILED (failures=1, errors=1)`. So this
is not "a check that might have read the wrong tree": a candidate record exists whose recorded
`PASS` is provably false of the tree it names, and it is the record of a candidate about a module
its own tree does not contain.

**Refuse or isolate: isolate.** Refusing on the presence of untracked files is the wrong rule and
would be wrong most days in this tree - `CLAUDE.md` trap T6 says several sessions write it at
once, witness deposits are routinely untracked, and the three deposits of my own passes 1 to 3 sat
untracked here for hours while other freezes ran. A rule that refuses on dirt refuses honest work
and teaches operators to clean the tree before freezing, which loses the evidence.

Three readings, in the order I would take them:

1. **Run the checks against the committed tree.** `git worktree add --detach` or `git archive` at
   `candidate_commit`, run `verify` and `lint` there, and the record's `checks` become true of
   `candidate_tree` by construction - immune both to an untracked file the candidate lacks and to
   another session's dirt that this landing did not cause. Cost is one extra verify run, 21 to 35
   seconds on this host. This is the one that settles it; the module named
   `scripts/sovland/isolation.py` is where the repository already keeps this concern.
2. **Report the dirty paths the freeze was not asked to carry.** `repo.dirty_paths()` already
   exists and `sov_land.py`'s gate path already uses it; `git status --porcelain` includes
   untracked files where `git diff --name-only` does not. I measured it against the three files
   actually omitted at `434c6a5`: it names all three. One reading, no refusal, and the operator
   sees by name what the freeze is about to leave out.
3. **Intersect what each check declares it read with what the tree holds foreign.**
   `isolation.foreign_paths` and `isolation._touches` already do exactly this for *failing*
   checks; extending it to passing ones would name the defect precisely. I measured its reach and
   it is a lower bound: of the three omitted files, only `scripts/tests/test_sovaddress.py` is
   covered, by two checks that declare the directory `scripts/tests`; nothing declares an address
   covering `scripts/sovaddress.py` or `scripts/sovclarity/digests.py`. It reads a declaration
   where reading 1 measures, which is the defect class this repository keeps rediscovering.

Whatever is chosen, the record should say which tree the checks graded. Today `checks: {"verify":
"PASS"}` carries no tree identity at all, so a reader cannot tell a true PASS from `434c6a5`'s.
The mechanism is the builder's to choose; only J5 below is anyone else's.

### Findings

- **F1 - discharged.** `verify.py` exits 0 at `f957987`; `CLAUDE.md` at the base reads 970
  commits against a record of 977. Discharged by the base moving, not by a code change; nothing
  in this concern repaired it, and the earlier passes' reading of it stands as it was written.
- **F2, F3, F5, F6, F7, F8, F11, F12 - repaired and re-measured** at these bytes: all sixteen
  mutants caught, control green.
- **F4 - discharged.** The sibling branch's scratch-view change landed in the base through
  PR #220; `f957987`'s diagram diff is the `sovaddress` adoption alone. The duplication resolved
  by one branch landing first.
- **F13 - partly discharged.** A record exists for `f957987`. See F19.
- **F15 - retracted at pass 3**, unchanged.
- **F17 (high, new) - the freeze's checks read the working directory.** Above.
- **F18 (medium, new) - the base has moved.** `git ls-remote` reads `origin/main` at
  `b1448ee` (PR #224) while this candidate declares base `6498fc7` and the local `main` ref still
  reads `6498fc7`. `scripts/sov_candidate.py:83` refuses `LAND` when `base_commit` differs from
  the target head, so this candidate is landable only against a `main` that has since moved. The
  reconciliation is ordinary work; if it leaves the 14 blobs identical, this observation carries
  to the new SHA and the receipt records the blob ids so that can be checked rather than assumed.
- **F19 (low, new) - superseded and discarded candidates still read FROZEN.**
  `.local/candidates/` holds eight records, all `state FROZEN`, including `434c6a5` (discarded)
  and `a57d736` (superseded). `contracts/repository-candidate-lifecycle.json` has a `SUPERSEDED`
  state and nothing moved them into it. A discarded record that still declares itself frozen and
  passing is the artifact F17 is read from, which is how I found it.
- **F20 (info).** The pass 1 to 3 records and receipts are now tracked in the base, committed
  byte-identically at `25e1f7b` and `64aba4b`; I verified the committed bytes equal what I wrote.

### Conditions

None on this candidate. F17 and F19 are repairs owed inside the concern that owns the freeze;
F18 is ordinary reconciliation before landing.

### Judgement items

- **J5 (new).** Should `contracts/repository-candidate-lifecycle.json` require a candidate's
  `checks` to be true of its `candidate_tree`, and require the record to name the tree they
  graded? That binds every future candidate and every reader of a frozen record, so it is a
  contract question rather than an implementation choice. Which of the three readings above is
  used to satisfy it is the builder's, not the owner's.
- J1, J2 discharged by F1 and F4. J4 answered at pass 3.

### Verified

Every command ran with `SOV_PRINCIPAL=principal:claude-fable-5-1`.

- `git rev-parse HEAD` -> `f957987b45e02d86341c0c348a5c8f3f90af0777` before and after every command; `git status --porcelain` ->
  empty until the deposits; `git rev-parse f957987^{tree}` -> `d89cedaacd75eae4ff420f89937bfa6761eb9158`;
  `git diff --stat 6498fc7..f957987` -> 14 files, +735/-36.
- Completeness: record `changed_paths` (14) equals `git diff --name-only 6498fc7 f957987` (14);
  every declared path present in `git ls-tree -r f957987` and byte-equal to the working tree;
  none absent.
- Blob identity: `git rev-parse a63b09b:<p>` equals `f957987:<p>` for all 14 paths.
- Clean full-history clone at `f957987`: `python scripts/verify.py` -> **exit 0**, `PASS: 10 of
  10 snapshot claim(s) match the record`; `python scripts/lint.py` -> **exit 0**;
  `python scripts/run_tooling_tests.py` twice -> exit 0, exit 0, 112 modules.
- Eleven suites on a `git archive` copy: `test_sovaddress` 18, `test_sov_witness_layer` 72,
  `test_witness_record` 14, `test_sov_diagrams` 16, `test_sov_clarity` 7, `test_sov_reuse` 15,
  `test_repository_candidate_effects` 10, `test_repository_candidate` 4, `test_sov_land` 31,
  `test_landing_isolation` 16, `test_landing_ledger` 15 - all OK.
- Sixteen mutants, eleven suites each: M1, M2, M3, M4, M10, M11, M12 caught by `test_sovaddress`
  (M1 also by `test_sov_diagrams`); M5, M6, M7 by `test_sov_witness_layer`; M8 by
  `test_sov_reuse`; M9 by `test_sov_clarity`; M13, M14, M15, M16 by
  `test_repository_candidate_effects`; unmutated control green on all eleven.
- Four readers at `f957987` against `6498fc7`: `records` exit 0 both, identical verdict per
  receipt and identical summary (27 graded, 0 unusable, 27 stale); `sov_diagrams.py` and
  `sov_clarity.py check` exit 0 both, byte-identical; `sov_reuse.py run` exit 1 both, identical
  verdict, predicates and drifted set. 165 committed addresses, 164 identical both ways, 1
  absent (pre-existing), 0 containing `#`.
- F17 reproduction and the `434c6a5` measurement: as described above, including
  `run_tooling_tests.py` -> exit 1 on that commit's own tree.
- After the deposits: `python scripts/sov_witness_layer.py records` -> exit 0, 28 receipts
  graded, 0 unusable, this pass's receipt `CURRENT`; `python scripts/sov_clarity.py check` ->
  exit 0; `python scripts/lint.py` -> exit 0; `python scripts/sov_standing.py` -> PASS;
  `git -C <root> status --porcelain` -> ` M witness/sovaddress.md` and
  `?? witness/observations/2026-09-07-sovaddress-observation-4.json`.
  The first draft of this receipt digested `witness/sovaddress.md`, the record it sits
  beside, and the grader read it `STALE_PROBE` the moment that record was rewritten. That
  is the check working on its author: a receipt that digests its own record declares probe
  drift. The address was removed before the deposit stood, and no receipt of mine names an
  address under `witness/`.

### Uncovered

`sov_land.py land` was not executed; F18 is read from `sov_candidate.py` and the lifecycle
contract. The repair for F17 is described, not written - this witness edits nothing. Nothing
under `conformance/` or `services/` changed.

### Standing supported

`WITNESSED` for `scripts/sovaddress.py`, its four adoptions, and the freeze ordering in
`scripts/sovland/candidates.py`, as carried by candidate `f957987b45e02d86341c0c348a5c8f3f90af0777`. `stage_observed_by`, if a
custody member is ever minted: `claude-fable-5-1/sov-witness@2026-09-07-sovaddress, pass 4 at
f957987b45e02d86341c0c348a5c8f3f90af0777`. Not supported: any reading of a candidate record's `checks` field as evidence about its
own tree, until F17 is repaired. Receipt:
`witness/observations/2026-09-07-sovaddress-observation-4.json`. Landing observation:
`.local/observations/2026-09-07-sovaddress-landing-4.json`, `CONFIRMED`, with F18 named as the
precondition the lander's own gate tests. This record is an observation; it ratifies nothing and
settles nothing.

## Pass 3: commit a63b09b (2026-09-07)

Verdict: **RATIFIABLE-WITH-CONDITIONS**. **REPRODUCED**: the diff `e835205..a63b09b` touches
only `scripts/sovland/candidates.py` (+8) and `scripts/tests/test_repository_candidate_effects.py`
(+45); every instrument and adoption path is blob-identical to `e835205`. The pre-commit
evaluation and the post-commit drift refusal are both present and each has a fixture that fails
when it is removed. Because the two new cases mock `authority.evaluate` entirely, this witness
also ran the kernel evaluator unmocked against the live grant: scope comes back
`AUTHORITY_REFUSED` with no checks offered, so the freeze stops before committing; only absent
checks come back `MISSING_PRECONDITION`. F11 and F12 are repaired. **F1 is confirmed
unrepaired** and withholds landing on its own. **Retraction:** pass-2 F15 was wrong; see F15
below. Landing is **NOT_CONFIRMED, for F1 alone**; apart from F1 this witness would land
`a63b09b`.

Claim under observation, as the coordinator stated it and as the commit message states it: the
`repository.commit` grant is evaluated before the commit with no checks offered, and a refusal
for anything but `MISSING_PRECONDITION` (scope, type, budget, time, revocation) stops the freeze
with nothing committed; after the commit the grant is evaluated again on the committed tree with
the checks; checks that rewrite a checked path refuse after the commit, naming it; two cases
added. The list was read as the claim; nothing below is taken from it.

Subject frozen: commit `a63b09be32d9d34824f694e26e133de4ffd3dec2`, tree `341a36969c7b9aa38b0e9aced1c60866afc755a3`, two commits past the frozen candidate `a57d736`
on `feat/address-below-the-file`, at the same commit on `origin`; base `aeecc60` is still
`origin/main`. `git rev-parse HEAD` read the commit before and after every command and
`git status --porcelain` was empty until the deposits. No candidate record exists for `e835205`
or `a63b09b`.

### Findings

- **F1 (high, landing) - unrepaired, confirmed.** `verify.py` exit 1 at `a63b09b`: `FAIL
  commits: page says 942, record holds 970 (tolerance 25)`. Withholds landing by itself.
- **F11 - repaired.** `candidates.py:67-73` evaluates the grant with `{}` checks before the
  commit and stops on any code but `MISSING_PRECONDITION`. M14 (drop it) and M15 (let
  `AUTHORITY_REFUSED` through) are caught. The unmocked evaluator confirms the predicate the
  cases assume: `evaluate()` judges actor, branch, scope, budget, time and revocation
  (`_grant_unavailable`) before the observation and precondition tests
  (`sovkernel/authority.py:175-209`).
- **F12 - repaired.** `test_checks_that_modify_the_checked_paths_refuse_after_the_commit`;
  M13 is caught. M16 (drop the post-commit evaluation) is caught too.
- **F13 (medium, record) - unchanged.** No candidate record for `e835205` or `a63b09b`;
  `a57d736`'s still reads `FROZEN`. Follows from F1.
- **F4, J1, J2 - unchanged.**
- **F15 - retracted.** Pass 2 said the pass-1 deposits had been removed from the working tree by
  something other than git. They had not: this witness's `cp` commands in passes 1 and 2 ran
  after `cd` into its scratch clone with relative targets, so every deposit landed in the clone
  (`ls` there shows all five; `ls` in the witnessed tree shows none). The `git status
  --porcelain` readings those passes reported were the clone's. No other process removed
  anything, and the T6 attribution is withdrawn. This pass writes with absolute paths into the
  witnessed tree and reports `git -C <root> status --porcelain`.
- **F16 (info).** A grant that required an observation for `repository.commit` would read
  `OBSERVATION_MISSING` pre-commit and the freeze would never commit; the live grant requires none
  for this capability, so no effect today.

### Conditions

- C1 (F1) and C7 (F13): unchanged from pass 2; C6 (F12) discharged.

### Judgement items

- J1, J2 unchanged. J4 is answered by the change as this witness framed it; nothing new is asked.

### Verified

Every command ran with `SOV_PRINCIPAL=principal:claude-fable-5-1`.

- `git rev-parse HEAD` -> `a63b09be32d9d34824f694e26e133de4ffd3dec2` before and after every command; `git status --porcelain` ->
  empty until the deposits; `git diff --stat e835205..a63b09b` -> 2 files, +53; `git ls-remote
  origin` -> branch at `a63b09b`; `git rev-list --count a63b09b` -> 970.
- Blob identity: `git rev-parse e835205:<p>` equals `a63b09b:<p>` for `scripts/sovaddress.py`,
  `scripts/sovwitness/records.py`, `scripts/sovwitness/shape.py`, `scripts/sov_diagrams.py`,
  `scripts/sov_clarity.py`, `scripts/sovclarity/digests.py`, `scripts/sovreuse/settle.py` and the
  five adoption test modules: all twelve identical.
- `python scripts/verify.py` (clone, `a63b09b`) -> **exit 1**, orientation snapshot only;
  `COST: 52 checks in 21.514s wall`. `python scripts/lint.py` -> **exit 0**.
- `PYTHONPATH=scripts python -m unittest scripts.tests.<m>` (clone): `test_landing_isolation` 16
  OK; `test_landing_ledger` 15 OK; `test_repository_candidate` 4 OK;
  `test_repository_candidate_effects` 10 OK; `test_sov_land` 31 OK.
- Mutants (four archive copies, five sovland suites each): M13 drop the drift refusal -> caught;
  M14 drop the pre-commit evaluation -> caught; M15 wave `AUTHORITY_REFUSED` through -> caught;
  M16 drop the post-commit evaluation -> caught; control -> all pass.
- Unmocked evaluator (`sovkernel.authority.evaluate`, `sov_grant.load_grants()` ->
  `grant:standing-landing-loop`, `candidates._request(actor sov, target main,
  repository.commit)`): `decisions/x.md` with no checks -> `AUTHORITY_REFUSED` "inside the
  excluded prefix decisions/"; `CLAUDE.md` -> `AUTHORITY_REFUSED`; `scripts/sovaddress.py` with
  no checks -> `MISSING_PRECONDITION` "required check 'verify' is not present"; with PASS checks
  -> `PERMITTED`; with verify FAIL -> `MISSING_PRECONDITION`; actor `nobody` ->
  `AUTHORITY_REFUSED`. Through the freeze's own predicate: `decisions/x.md` stops before the
  commit; `scripts/sovaddress.py` proceeds to it.
- After the deposits, in the witnessed tree by absolute path: `python
  scripts/sov_witness_layer.py records` -> exit 0, 15 receipts graded, 0 unusable, this pass's
  receipt `CURRENT`, passes 1 and 2 `STALE_SUBJECT` as receipts of earlier commits should;
  `python scripts/sov_clarity.py check` -> exit 0; `python scripts/lint.py` -> exit 0; `python
  scripts/sov_standing.py` -> PASS; `git -C <root> status --porcelain` -> exactly
  `?? witness/observations/2026-09-07-sovaddress-observation-2.json`,
  `?? witness/observations/2026-09-07-sovaddress-observation-3.json`,
  `?? witness/observations/2026-09-07-sovaddress-observation.json`, `?? witness/sovaddress.md`.

### Uncovered

`sov_land.py freeze` was not executed end to end; the ordering is read from the code, its
cases, the mutants and the unmocked evaluator. Nothing under `conformance/` or `services/`
changed.

### Standing supported

`WITNESSED` for `scripts/sovaddress.py` and its four adoptions (bytes unchanged since
`e835205`) and for the freeze ordering in `scripts/sovland/candidates.py` at `a63b09be32d9d34824f694e26e133de4ffd3dec2`.
`stage_observed_by`, if a custody member is ever minted:
`claude-fable-5-1/sov-witness@2026-09-07-sovaddress, pass 3 at a63b09be32d9d34824f694e26e133de4ffd3dec2`. No standing for the
branch as a landable unit (F1). Receipt:
`witness/observations/2026-09-07-sovaddress-observation-3.json`. Landing observation:
`.local/observations/2026-09-07-sovaddress-landing-3.json`, `NOT_CONFIRMED` for F1 alone. This
record is an observation; it ratifies nothing and settles nothing.

## Pass 2: commit e835205 (2026-09-07)

Verdict: **RATIFIABLE-WITH-CONDITIONS**. **REPRODUCED**: every repair the coordinator listed is
in `git diff a57d736..e835205` and each has a fixture that fails when the repair is reverted.
The five mutants that survived at `a57d736` (M3-M7) are caught at `e835205`, and reverting each
new repair (M10-M12) is caught too. The module's pass-1 claims still hold, the four readers grade
the tree at `e835205` exactly as at `aeecc60`, lint passes, tooling passes twice. **F1 is
confirmed unrepaired** and withholds landing on its own. Three new findings: the grant for
`repository.commit` is now evaluated after the commit is made (F11, J4); the post-commit drift
refusal has no fixture (F12); `e835205` has no candidate record while `a57d736`'s still reads
`FROZEN` (F13). Landing is **NOT_CONFIRMED, for F1 alone**; apart from F1 this witness would
land `e835205`.

Claim under observation, as the coordinator stated it and as the commit message states it:
F2 repaired by six cases in `test_sov_witness_layer.AddressesBelowTheFile`; F3 repaired (no
report path in the docstring); F5 (class above `unittest.main`); F6 (`UnicodeDecodeError`
refuses `FRAGMENT_MALFORMED` for every kind); F7 (selector requires the key present; duplicate
YAML key, trailing-mark heading and fenced-block cases); F8 (selfcheck output captured); J1
acted on (`sovland/candidates.freeze` commits first, reads the range, runs the checks on the
committed tree, then evaluates authority; a refusal after the commit names the commit and writes
no record; two cases). F1 not repaired and not repairable inside the grant; #221 held on #220;
F4 unchanged. The list was read as the claim; nothing below is taken from it.

Subject frozen: commit `e835205a4d0c2f99e289019cdba81d2c1af59852`, tree
`0b05987fe4b23a004ad29766029b301aed4372e2`, one commit past `a57d736` on
`feat/address-below-the-file`, at the same commit on `origin`; base `aeecc60` is still
`origin/main`. `git rev-parse HEAD` read the commit before and after every command and
`git status --porcelain` was empty until the deposits. The commit changes 7 files (+192/-31);
the whole range `aeecc60..e835205` is 14 files (+702/-44), all under `scripts/`. No candidate
record exists for `e835205`. The pass-1 deposits (`witness/sovaddress.md`,
`witness/observations/2026-09-07-sovaddress-observation.json`,
`.local/observations/2026-09-07-sovaddress-landing.json`) were absent from the working tree at
the start of this pass; no commit or stash holds them; byte-identical copies from the witness's
scratch directory (sha256 `8a2bbf97...`, `39967806...`, `5b12fd84...`) were re-deposited
unchanged. Every mutating command ran in the scratch clone at `e835205`, its worktree at
`aeecc60`, or a `git archive` copy of `e835205`.

### Findings

- **F1 (high, landing) - unrepaired, confirmed.** `python scripts/verify.py` exits 1 on the
  clean clone at `e835205`: `FAIL commits: page says 942, record holds 969 (tolerance 25)`
  (`CLAUDE.md:197`). The correction is to a root governing document outside
  `grant:standing-landing-loop`. This finding alone withholds landing.
- **F2 - repaired.** `scripts/tests/test_sov_witness_layer.py:210-265` adds six cases; M5, M6
  and M7 are each caught by that suite.
- **F3 - repaired.** `scripts/sovaddress.py:5-6` names the four gates instead of a report path;
  `git grep` at `e835205` finds no reference to the absent report under `scripts/`.
- **F4 (medium, coordination) - unchanged.** `6be70fb` on the sibling branch still carries the
  same scratch-view change and the `CLAUDE.md` correction to 970/32.
- **F5 - repaired.** `BasisAddresses` sits above `unittest.main()`; script mode runs it.
- **F6 - repaired.** `scripts/sovaddress.py:185-189` decodes once and refuses undecodable bytes
  as `FRAGMENT_MALFORMED` for every kind; M12 is caught; `basis_digest` reads `None`,
  `current_state` reads drifted, `records.grade` reads `INVALID`, `source_digest` refuses.
- **F7 - repaired, one documented residual.** `_select` requires the key present (M11 caught);
  a duplicate YAML top-level key has a case (M3 caught); trailing marks have a case (M4 caught);
  `_headings` skips fenced blocks (M10 caught). Closing marks are still stripped, so `## A ##`
  and `## A` collide and a heading whose text ends in `#` is unreachable by its text; the
  docstring now says so ("before any closing marks"), which makes it a documented shape rather
  than a defect.
- **F8 - repaired.** The selfcheck test redirects stdout; the `e835205` verify log carries no
  selfcheck lines.
- **F11 (medium, authority).** `scripts/sovland/candidates.py:87-107`: `git commit` now runs
  before `authority.evaluate(grants, request)` for `repository.commit`. A refusal for scope or a
  missing precondition now lands after the effect. The carrier is `MUTABLE`, no record is
  written, and the refusal names the commit, so the effect is reversible and attributed; but the
  grant that governs the capability is read after the capability is exercised. Whether that is
  admissible under "a typed, scoped, live grant at the operation boundary" is J4.
- **F12 (low, fixtures).** The post-commit refusal "the checks modified the paths they checked"
  (`candidates.py:97-101`) has no fixture: M13 (`if by_checks and False`) survives all seven
  suites. `preflight.refusal` now always receives `[]` for `by_checks` from `freeze`, so its own
  branch at `preflight.py:63-68` is dead on that path.
- **F13 (medium, record).** `.local/candidates/` holds no record for `e835205`, and
  `a57d736`'s record still reads `FROZEN` although the branch has moved past it. `AGENTS.md`
  reads a stale frozen candidate as `SUPERSEDED` with a new subject frozen; the new freeze cannot
  write that record while F1 makes verify fail, so F13 follows from F1.
- **F14 (info).** `scripts/tests/test_sov_witness_layer.py` is 682 lines (624 at base); lint
  passes, so tests are outside the 300-line ceiling or named debt.
- **F15 (info, T6).** Three untracked files this witness deposited in pass 1 were removed from
  the working tree by something other than git between passes.

### Conditions

- C1 (F1): unchanged from pass 1; the repair is outside the grant (J1).
- C6 (F12): one case that fails when the post-commit drift refusal is removed.
- C7 (F13): freeze `e835205` (or its successor) once verify passes, so a record names the
  subject; mark `a57d736` `SUPERSEDED`.

### Judgement items

- J1 (unchanged): which seat corrects `CLAUDE.md:197`, given the grant's scope?
- J2 (unchanged): which branch carries the duplicated scratch-view change (F4)?
- J4 (new): is evaluating the `repository.commit` grant after the commit, on a `MUTABLE` carrier
  with no record written and the commit named in the refusal, within "a typed, scoped, live grant
  at the operation boundary", or must scope be evaluated before the commit and only the
  check-dependent preconditions after it?

### Verified

Every command ran with `SOV_PRINCIPAL=principal:claude-fable-5-1`.

- `git rev-parse HEAD` -> `e835205a4d0c2f99e289019cdba81d2c1af59852` before and after every
  command; `git status --porcelain` -> empty until the deposits; `git log a57d736..HEAD` -> one
  commit; `git ls-remote origin` -> branch at `e835205`, `main` at `aeecc60`; `git show --stat
  e835205` -> 7 files; `git diff --stat aeecc60..e835205` -> 14 files, all under `scripts/`;
  `.local/candidates/` -> six records, none for `e835205`, `a57d736` `FROZEN`.
- Scratch clone: `git fetch` of the branch, `git checkout e835205`, `git status --porcelain`
  empty; worktree at `aeecc60` kept from pass 1; `git archive e835205 | tar -x`.
- `python scripts/verify.py` (clone, `e835205`) -> **exit 1**; `FAIL commits: page says 942,
  record holds 969 (tolerance 25)`; `FAIL: orientation snapshot`; every other check `PASS`;
  `COST: 52 checks in 21.085s wall`. Check-name diff against the `aeecc60` log: that verdict and
  the counts 111 -> 112 modules, 1204 -> 1207 text files; the F8 selfcheck lines are gone.
- `python scripts/lint.py` (clone) -> **exit 0**.
- `PYTHONPATH=scripts python -m unittest scripts.tests.<m>` (archive): `test_sovaddress` 18 OK;
  `test_sov_witness_layer` 72 OK, six `AddressesBelowTheFile` cases listed; `test_witness_record`
  14 OK; `test_sov_diagrams` 16 OK; `test_sov_clarity` 7 OK; `test_sov_reuse` 15 OK;
  `test_repository_candidate_effects` 8 OK; `test_landing_isolation`, `test_landing_ledger`,
  `test_repository_candidate`, `test_sov_land` -> exit 0; `python scripts/tests/test_sovaddress.py`
  -> OK.
- `python scripts/run_tooling_tests.py` twice (clone) -> exit 0, exit 0; tree clean after.
- Four readers at `e835205`, diffed against the pass-1 `aeecc60` readings with timings
  stripped: `sov_witness_layer.py records` exit 0 identical; `sov_diagrams.py` exit 0 identical;
  `sov_clarity.py check` exit 0 identical; `sov_reuse.py run --principal
  principal:claude-fable-5-1` exit 1 both, same predicates `P15-Q3.1`, `P15-Q3.2`, same drifted
  set. Digest equivalence: 114 committed addresses, 113 identical both ways, 1 absent
  (pre-existing), 0 with `#`.
- Mutants (nine archive copies, seven suites each): M3 -> caught (`test_sovaddress`); M4 ->
  caught (`test_sovaddress`); M5, M6, M7 -> caught (`test_sov_witness_layer`); M10 no fenced-block
  skip -> caught; M11 selector matches a missing key -> caught; M12 decode error escapes ->
  caught; M13 freeze ignores checks that modified the checked paths -> **survives**; control ->
  all pass.
- Adversarial probe (archive): sibling edit `CURRENT`; member edit `STALE_SUBJECT`; fragment
  gone `STALE_SUBJECT` "gone from the tree"; malformed `INVALID`; `p.py#x` `INVALID`; `../`
  before `#` `INVALID`; `[key=None]` -> `FRAGMENT_NOT_FOUND`; YAML key twice ->
  `SELECTOR_AMBIGUOUS`; a `# ...` line inside a fence no longer ends a section; non-UTF-8
  `.md#S` -> `FRAGMENT_MALFORMED`; `## A ##` still collides with `## A`; CRLF bytes verbatim.
- Sizes at `e835205`: every touched file <= 100 characters per line, no CRLF; production
  modules <= 219 lines.
- After the deposits (record, both receipts, both landing records): `python
  scripts/sov_witness_layer.py records` -> exit 0, 14 receipts graded, 0 unusable, this pass's
  receipt `CURRENT`, the pass-1 receipt `STALE_SUBJECT` against `e835205` as a receipt of
  `a57d736` should; `python scripts/sov_clarity.py check` -> exit 0; `python scripts/lint.py`
  -> exit 0; `python scripts/sov_standing.py` -> PASS; `git status --porcelain` -> exactly the
  three untracked files under `witness/`; `git rev-parse HEAD` -> `e835205`.

### Uncovered

`sov_land.py freeze` and `land` were not executed; F11 and F12 are read from the code and its
two cases. The conformance oracle and service suites were not run (nothing under `conformance/`
or `services/` changed). The sibling branch was not re-read beyond confirming F4 unchanged.

### Standing supported

`WITNESSED` for `scripts/sovaddress.py` and its four adoptions at
`e835205a4d0c2f99e289019cdba81d2c1af59852`. `stage_observed_by`, if a custody member is ever
minted: `claude-fable-5-1/sov-witness@2026-09-07-sovaddress, pass 2 at
e835205a4d0c2f99e289019cdba81d2c1af59852`. No standing for the branch as a landable unit (F1)
and none for the freeze reordering beyond its two cases (F11, F12). Receipt:
`witness/observations/2026-09-07-sovaddress-observation-2.json`. Landing observation:
`.local/observations/2026-09-07-sovaddress-landing-2.json`, `NOT_CONFIRMED` for F1 alone. This
record is an observation; it ratifies nothing and settles nothing.

## Pass 1: commit a57d736 (2026-09-07)

Verdict: **RATIFIABLE-WITH-CONDITIONS** for the module. **REPRODUCED**: every fragment kind
resolves to the bytes the docstring names, all four refusals fire under their own name, a sibling
edit leaves a fragment digest alone while the member's own edit moves it, every committed
whole-file address digests identically (113 of 113 present), and the four readers grade the tree
at `a57d736` exactly as they grade it at `aeecc60`. **DISSENT** from two claims: the sovwitness
adoption has no test of its own, and the frozen candidate does not pass `verify.py` on a clean
clone. Landing is **NOT_CONFIRMED** (F1, F2).

Claim under observation, as the commit message and the candidate record state it:
`scripts/sovaddress.py` resolves `path#fragment` to bytes (JSON pointer with `[key=value]`
selectors whose values may hold slashes, canonical JSON bytes; a top-level YAML block by line
shape; a Markdown section to the next heading at its level or above; bare path = exact bytes;
refusals `FRAGMENT_UNSUPPORTED`, `FRAGMENT_MALFORMED`, `FRAGMENT_NOT_FOUND`,
`SELECTOR_AMBIGUOUS`). Four readers adopt it: `scripts/sovwitness/{shape,records}.py`,
`scripts/sov_diagrams.py`, `scripts/sov_clarity.py` with `scripts/sovclarity/digests.py`, and
`scripts/sovreuse/settle.py`. Diagram scratch views move to temp directories with a pinning test.
Every existing whole-file address digests identically; a sibling change leaves a fragment digest
unchanged; the four adoptions each have a test. The candidate record
`.local/candidates/a57d736c2a3df67d07ba38d0f2992e3dbee5d5c2.json` reads `verify: PASS`,
`lint: PASS`. The commit message was read as the claim; no builder report was read as evidence.

Subject frozen: commit `a57d736c2a3df67d07ba38d0f2992e3dbee5d5c2`, tree
`fff48b3ffcf575905d93c6ccddbe464cf38ded03`, base `aeecc605c05c7a6f74e80ee4bd49e0b6f2ea19d9`
(= `origin/main`, confirmed by `git ls-remote`), branch `feat/address-below-the-file` at the
same commit on `origin`. `git rev-parse HEAD` read the commit before and after every command and
`git status --porcelain` was empty until this record and its receipt were written. The commit
changes 11 files (+530/-33), all under `scripts/`, and the candidate record's `changed_paths`
names exactly those 11. `conformance/` and `services/` are untouched, so no service suite or
oracle run was owed. Every mutating command ran in a full clone (968 commits, not shallow) checked
out at `a57d736` under the witness's scratch directory, in a worktree of that clone at `aeecc60`,
or in a `git archive` copy of `a57d736`.

### Findings

- **F1 (high, landing).** `python scripts/verify.py` exits 1 on the clean clone at `a57d736`.
  The one failing check is the orientation snapshot: `FAIL commits: page says 942, record holds
  968 (tolerance 25)` (`CLAUDE.md:197`; rule `scripts/sovsnapshot/claims.py:205`,
  `scripts/sovsnapshot/grading.py:76`). At `aeecc60` the record holds 967 and the check passes.
  The candidate's own commit is what crosses the tolerance. The record's `verify: PASS` is true of
  the tree it measured: `scripts/sovland/candidates.py` gathers checks, then runs `git commit`,
  then writes `frozen_at`, so the check graded a tree one commit behind the subject it names.
  `scripts/sovland/isolation.py` `attribute()` sends every failing check to `CHANGE` when no
  foreign path is dirty, so the landing gate refuses this candidate. Consequence if ratified as-is:
  a frozen candidate whose recorded PASS cannot be reproduced at its own commit.
- **F2 (high, evidence).** The sovwitness adoption (`scripts/sovwitness/records.py:104-125`,
  `scripts/sovwitness/shape.py:153`) has no test. No case in `scripts/tests/test_witness_record.py`
  or `scripts/tests/test_sov_witness_layer.py` names a fragment, and three mutants survive all six
  suites: M5 reads `FRAGMENT_NOT_FOUND` as `INVALID` instead of moved; M6 drops the split before
  containment (a `:` or `..` in a fragment would then be refused as a path); M7 digests the whole
  file and ignores the fragment. The claim "the four adoptions each have a test" holds for
  diagrams (M1 caught), clarity (M9 caught) and reuse (M8 caught) and fails for the reader that
  gates landings. This witness observed the claimed behaviour by its own probe; the tree carries
  nothing that would notice its loss.
- **F3 (medium, record).** `scripts/sovaddress.py:5` cites
  `reports/2026-09-07-discovery-and-reuse-slice.md`, findings 2 and 8, as the record of the four
  gates going stale. That file is not in the tree at `a57d736` and not on `main`; it exists only
  on `origin/claude/sovereign-phase-1-5-5uzffu` (`d71f153`, `77421de`, `6be70fb`). The module's
  stated motivation rests on a record this revision does not hold.
- **F4 (medium, coordination).** The sibling branch's `6be70fb` ("diagram scratch views live
  outside diagrams/") makes the same change to `scripts/sov_diagrams.py` and
  `scripts/tests/test_sov_diagrams.py` that this candidate carries, and the same branch rewrites
  `CLAUDE.md:197` to `970 commits ... 32 reports`. `git merge-tree --write-tree a57d736
  origin/claude/sovereign-phase-1-5-5uzffu` is clean (`d870be9`), so the two do not conflict
  textually, but the work is done twice on two unlanded branches. The `CLAUDE.md` the host
  presented to this witness at launch carried the sibling's 970/32 wording while the tree it was
  told to witness reads 942/31 (`CLAUDE.md`, trap T6); the tree itself did not move.
- **F5 (low, test shape).** `scripts/tests/test_sov_clarity.py:107` places `BasisAddresses`
  after `if __name__ == "__main__": unittest.main()`. It runs under `-m unittest` (7 tests, was
  6) and would not run if the file were executed as a script. Executing that file as a script
  already fails on import at `aeecc60`, so there is no live loss today.
- **F6 (low, refusal).** `scripts/sovaddress.py:176-178` decodes `.yaml` and `.md` as UTF-8
  without catching `UnicodeDecodeError`. `records.py` catches it as `ValueError` and reads
  `INVALID`; `sovclarity/digests.py`, `sovreuse/settle.py` and `sov_diagrams.py` catch only
  `AddressError`, so a fragment address on a non-UTF-8 file crashes those readers instead of
  refusing by name. `lint.py` pins UTF-8, so no committed address reaches this.
- **F7 (low, fixtures).** Module behaviours with no defeating fixture: a YAML top-level key that
  appears twice refuses `SELECTOR_AMBIGUOUS` (M3 survives; live `STATUS.yaml` declares
  `ticket_kind_vocabulary_status` twice, and `STATUS.yaml#ticket_kind_vocabulary_status` does
  refuse); the heading regex strips trailing `#` marks (M4 survives), so `## A ##` and `## A`
  collide as `A` and a heading whose text ends in `#` (`## C#`) is unreachable by its text and
  reachable as `C`; a `# ...` line inside a fenced code block ends the enclosing section; a
  selector `[key=None]` matches elements that lack the key (`str(None)`); YAML keys outside
  `[A-Za-z_][A-Za-z0-9_-]*` (quoted, numeric, dotted) are neither addressable nor block
  terminators, so a preceding block would run over them. None of these touch a committed address.
- **F8 (low, noise).** `test_the_selfcheck_leaves_diagrams_as_it_found_it` calls
  `sov_diagrams.selfcheck()`, whose seven `PASS:` lines now print inside the tooling shard and so
  into every `verify.py` log (the base/candidate log diff shows exactly those lines).
- **F9 (info).** `scripts/sov_diagrams.py:27-30` inserts `ROOT/scripts` into `sys.path` in a
  non-test module. `AGENTS.md` forbids that in production code; 166 files under `scripts/` do it
  at `aeecc60`, so this follows the directory's convention rather than breaking a rule that was
  being kept.
- **F10 (info, residual).** `sovaddress.resolve(root, address)` does no containment
  (`root / "/etc/hostname"` reads outside the root). `records.py` contains the path half before
  digesting; diagrams, clarity and settle do not, exactly as they did not for bare paths at
  `aeecc60`. Not a regression.

### Conditions

- C1 (F1): a candidate whose `verify.py` passes at its own commit. Either `CLAUDE.md:197` is
  corrected before the freeze (a root governing document, outside `grant:standing-landing-loop`'s
  scope; J1) or the freeze reruns verify on the committed tree. `a57d736` is frozen and becomes
  `SUPERSEDED`; the repair is a new candidate.
- C2 (F2): one positive and one defeating case for the sovwitness adoption, killing M5, M6 and
  M7: a receipt with a fragment address that reads `CURRENT`, `STALE_SUBJECT` when the fragment
  is gone, `INVALID` when it is malformed, and a `:` inside a fragment that is admitted.
- C3 (F3): cite a record the tree holds, or land the report first.
- C4 (F5): move `BasisAddresses` above `unittest.main()`.
- C5 (F7, optional): fixtures for YAML `SELECTOR_AMBIGUOUS` and trailing-`#` headings.

### Judgement items

- J1. When a candidate's own commit tips the orientation snapshot past its tolerance, which seat
  edits `CLAUDE.md:197`? The standing grant excludes root governing documents, and the freeze
  measures verify before the commit exists. Is a freeze that grades the pre-commit tree an
  acceptable check for `checks.verify`, or must `sov_land.py freeze` measure the committed tree?
- J2. The same scratch-view change and the same `CLAUDE.md` correction sit on
  `origin/claude/sovereign-phase-1-5-5uzffu`, unlanded. Which branch carries them, and does the
  repaired candidate rebase onto that branch's landing?
- J3. May `WITNESSED` for `scripts/sovaddress.py` stand with C2 open, given that the module's own
  claim is reproduced and the untested part is the adopter?

### Verified

Every command ran with `SOV_PRINCIPAL=principal:claude-fable-5-1`. Paths are the witness's
scratch clone (`a57d736`), its worktree (`aeecc60`) or its archive copy (`a57d736`).

- `git rev-parse HEAD` -> `a57d736c2a3df67d07ba38d0f2992e3dbee5d5c2` before and after every
  command; `git status --porcelain` -> empty until the deposits; `git show --stat a57d736` -> 11
  files, +530/-33; `git ls-remote origin` -> `feat/address-below-the-file` at `a57d736`, `main`
  at `aeecc60`.
- `git clone <repository root> clone`; `git rev-parse --is-shallow-repository` -> `false`;
  `git checkout a57d736`; `git worktree add base aeecc60`; `git archive a57d736 | tar -x`;
  `sha256sum` of `arch/scripts/sovaddress.py` equals the tree's.
- `python scripts/verify.py` (clone, `a57d736`) -> **exit 1**. `FAIL commits: page says 942,
  record holds 968 (tolerance 25)`; `FAIL: orientation snapshot`; every other check `PASS`;
  `COST: 52 checks in 23.760s wall`; 13 checks over ceiling, attributed as debt.
- `python scripts/verify.py` (worktree, `aeecc60`) -> **exit 0**; `PASS: 10 of 10 snapshot
  claim(s) match the record`. `git rev-list --count` -> 967 at `aeecc60`, 968 at `a57d736`.
  The check-name diff between the two logs is the snapshot verdict, the module counts
  (111 -> 112 tooling modules, 1204 -> 1207 text files) and the selfcheck lines of F8.
- `python scripts/lint.py` (clone) -> **exit 0**; `PASS: repository hygiene (1207 text files,
  565 Python modules, 10 named debt)`; pre-existing `WARN` on the duplicate `STATUS.yaml` key.
- `python -m unittest scripts.tests.<m>` (clone): `test_sovaddress` 14 OK, exit 0;
  `test_sov_witness_layer` 66 OK, exit 0; `test_witness_record` 14 OK, exit 0;
  `test_sov_diagrams` 16 OK, exit 0; `test_sov_reuse` 15 OK, exit 0; `test_sov_clarity` ->
  exit 1, `ModuleNotFoundError: No module named 'sovclarity'`, identical at `aeecc60`; with
  `PYTHONPATH=scripts` -> 7 OK, exit 0 (6 at `aeecc60`), `BasisAddresses` listed and passing.
- `python scripts/run_tooling_tests.py` twice (clone) -> exit 0, exit 0; `PASS: repository
  tooling tests (112 modules, 4 shards)`; 16.99s and 16.97s; `git status --porcelain` empty and
  `diagrams/` holds only its `.md` files afterwards.
- Four readers at both trees, outputs diffed with timings stripped:
  `sov_witness_layer.py records` -> exit 0 both, identical (12 receipts graded, 0 unusable,
  12 `STALE_SUBJECT`, same recomputed counts); `sov_diagrams.py` -> exit 0 both, identical
  (8 `CURRENT`); `sov_clarity.py check` -> exit 0 both, identical (`PASS: clarity scope and
  receipts are well-formed and current`); `sov_reuse.py run --principal
  principal:claude-fable-5-1` -> exit 1 both, the same two failing predicates `P15-Q3.1` and
  `P15-Q3.2`, the same eight drifted addresses; only the session id, lease id, projection urn
  and the inventory's branch name differ.
- Digest equivalence (archive): the 114 unique addresses named by `witness/observations/*.json`,
  `.clarity/coverage.json` bases and `diagrams/*.md` `source` lines -> `sovaddress.digest`
  equals `sha256(read_bytes)` for 113; 1 is absent from the tree at both revisions; 0 differ;
  0 committed addresses and 0 tracked file names contain `#`.
- Adversarial probe (archive, temp root, `records.grade`, `settle.current_state`,
  `basis_digest`, `sov_diagrams.grade`, `sovaddress.resolve`): sibling member edited plus a
  custody appended -> `CURRENT`; the member edited -> `STALE_SUBJECT`; fragment gone ->
  `STALE_SUBJECT` "gone from the tree (FRAGMENT_NOT_FOUND ...)"; `c.json#custodies` ->
  `INVALID FRAGMENT_MALFORMED`; `p.py#x` -> `INVALID FRAGMENT_UNSUPPORTED`;
  `../c.json#/custodies` -> `INVALID` not canonical; `/etc/hostname#/x` -> `INVALID` not
  repository-relative; `c.json#/../../etc/passwd` -> `STALE_SUBJECT` (`..` is a pointer key,
  no file is opened); `:` in a fragment admitted, in the path half refused; selector value with
  `/` resolves, with `]` -> `FRAGMENT_MALFORMED`; YAML key twice -> `SELECTOR_AMBIGUOUS`;
  `## A ##` -> `A`; `C#` -> `FRAGMENT_NOT_FOUND`, `C` -> the `C#` section; CRLF YAML block
  `b` -> `b'b:\r\n  - x\r'`, CRLF Markdown section -> `b'## S\r\n\r\nbody\r\n\r'` (bytes
  verbatim; LF and CRLF digest differently); non-UTF-8 `.md#S` -> `UnicodeDecodeError` out of
  `sovaddress`, `basis_digest`, `current_state` and `source_digest`, `INVALID` from
  `records.grade`; diagram view on `STATUS.yaml#owner_holds` -> `CURRENT`, on `#no_such` ->
  `INVALID` "does not resolve".
- Mutants (nine archive copies, six suites each): M1 `_steps` without bracket depth -> caught
  by `test_sovaddress` and `test_sov_diagrams`; M2 no trailing blank/comment trim -> caught by
  `test_sovaddress`; M3 YAML duplicate key silent -> survives; M4 no trailing-`#` strip ->
  survives; M5 grader reads `FRAGMENT_NOT_FOUND` as `INVALID` -> survives; M6 `resolve_address`
  without the split -> survives; M7 grader digests the whole file -> survives; M8 settle puts
  `NOT_FOUND` in drifted -> caught by `test_sov_reuse`; M9 `basis_digest` digests the whole
  file -> caught by `test_sov_clarity`; unmutated control -> all six pass.
- Sizes at `a57d736`: every touched file <= 295 lines (`sov_clarity.py` is 295) and <= 100
  characters per line (`sovclarity/digests.py` reaches 100); no CRLF.
- Record lookups: `git ls-tree a57d736 reports/` -> no `2026-09-07` file; `git log --all --
  reports/2026-09-07-discovery-and-reuse-slice.md` -> `6be70fb`, `77421de`, `d71f153`, all on
  the sibling branch; `git diff --stat aeecc60...origin/claude/sovereign-phase-1-5-5uzffu` over
  the candidate's files -> `CLAUDE.md`, `scripts/sov_diagrams.py`,
  `scripts/tests/test_sov_diagrams.py`; `git merge-tree --write-tree` -> clean.
- After writing this record and its receipt: see the closing line of this section, filled from
  the reruns over the tree with the deposits present.

### Uncovered

The conformance oracle and the service suites were not run: the diff touches nothing under
`conformance/` or `services/`. Windows path handling of fragments was not exercised. PR #221's
discussion was not read. `sov_land.py` was not run; the refusal in F1 is derived from reading
`scripts/sovland/isolation.py`, not from observing the gate. The sibling branch was read only
for the overlap in F3 and F4.

### Standing supported

`WITNESSED` for `scripts/sovaddress.py` at `a57d736c2a3df67d07ba38d0f2992e3dbee5d5c2`: the
module's resolution semantics and its four refusals, with the sibling-invariance of a fragment
digest. `stage_observed_by`, if a custody member is ever minted for it:
`claude-fable-5-1/sov-witness@2026-09-07-sovaddress, pass 1 at
a57d736c2a3df67d07ba38d0f2992e3dbee5d5c2`. No standing is supported for the candidate as a
landable unit (F1) or for the sovwitness adoption (F2). Receipt:
`witness/observations/2026-09-07-sovaddress-observation.json`. Landing observation:
`.local/observations/2026-09-07-sovaddress-landing.json`, `NOT_CONFIRMED`. This record is an
observation; it ratifies nothing and settles nothing.

After the deposits: `python scripts/sov_witness_layer.py records` -> exit 0, 13 receipts graded,
this one `CURRENT`; `python scripts/sov_clarity.py check` -> exit 0; `python scripts/lint.py` ->
exit 0; `git status --porcelain` -> exactly `?? witness/observations/2026-09-07-sovaddress-observation.json`
and `?? witness/sovaddress.md`; `git rev-parse HEAD` -> `a57d736c2a3df67d07ba38d0f2992e3dbee5d5c2`.
