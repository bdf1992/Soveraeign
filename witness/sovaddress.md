# Witness record: an address below the file (scripts/sovaddress.py)

```witness
standing_supported  WITNESSED
subject  sovaddress
revision  a63b09be32d9d34824f694e26e133de4ffd3dec2
pass  3
```

Three passes by the same role, different commits. Pass 3 (commit `a63b09b`) is current and owns
the declaration above. Pass 2 (commit `e835205`) and pass 1 (commit `a57d736`) follow it
unchanged as history. No `*_status` field in `STATUS.yaml` names this subject and no custody
member carries `scripts/sovaddress.py`; the work was carried under
`custody:phase-1-5/discovery-and-reuse`. The declaration binds to the module's claim, its four
adoptions, and the freeze ordering in `scripts/sovland/candidates.py`. It does not bind to the
branch as a landable unit; see the verdict.

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
