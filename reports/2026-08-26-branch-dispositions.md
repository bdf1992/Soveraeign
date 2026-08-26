# Branch dispositions, 2026-08-26

Status: `MEASURED · JUDGED · NOT WITNESSED · NOTHING RATIFIED`

Trunk frozen at `origin/main` = `3360a26` (merge of PR #117). Local `main` was
four commits stale at the time of the survey, so every comparison in this report
is against `origin/main` and not against `main`.

Eighteen branches are dispositioned here. Ten more were deliberately left alone:
`feat/sov-control-mesh`, `feat/sov-hypervisor`, `feat/console-authority-enforced-only`,
`feat/human-collection-substrate`, `wt/pr118`, `chore/status-and-projection-bookkeeping`,
`docs/witness-debt-sweep`, `fix/harness-routing-model`, `feat/surface-collection-transplant`
and `feat/federation-harness-and-hardening` are being worked by live sessions right
now, and a disposition written against a moving branch is a false reading
(`CLAUDE.md`, trap T6).

This report measures and judges. It merges nothing, deletes nothing and lands
nothing. Landing is a separate act under `contracts/standing-grants.json`, and no
harness role may commit (`OPEN-SEAMS.md` S21).

## Every branch here reaches a remote

`git rev-list --count <branch> --not --remotes` returned `0` for all eighteen. No
`RETIRE` or `SUPERSEDED` call below destroys the evidence it rests on: deleting
the local branch leaves the remote copy standing, and every one of them can be
fetched back.

## The dispositions

| Branch | Disposition | Evidence |
| --- | --- | --- |
| `docs/qa-witness-sweep-c296c25` | `LAND` | One file, zero merge conflicts. `reports/2026-08-23-qa-witness-sweep-c296c25.md` is absent from `origin/main`, and it carries the six-witness measurement that produced the graded verify budget. |
| `feat/gate-loop-pattern` | `LAND_AFTER_REPAIR` | Strict superset of both other F2 branches. Eight files absent from main: `.claude/workflows/sov-gate-control.js`, `.claude/schedules/f2-gate-loop.json`, `scripts/sovschedule/patterns.py`, `scripts/sovschedule/preflight.py`, three test modules, and its decision record. Repairs: `decisions/0045-gate-loop-as-a-scheduled-pattern.md` collides with main's `decisions/0045-acceptance-not-approval.md`, and four conflicts — `STATUS.yaml`, `conformance/fixtures/kernel/transition-cases.json`, `conformance/run.py`, `docs/documentation.html`, of which the last is a regenerable projection. One domain, `RECORD_LOCAL`. |
| `fix/landing-gate-host-independence` | `LAND_AFTER_REPAIR` | Nothing of its own is on main: `scripts/sovkernel/scope.py`, `scripts/sovland/{__init__,repo,tree}.py`, `scripts/witness_stages.py`, `scripts/tests/test_sov_land.py` (576 lines) and eleven `reports/observations/2026-08-25-*.json`. Main's `scripts/sovkernel/authority.py` still grades a path by spelling alone, and main's `scripts/lint.py` still names `scripts/witness_infrastructure.py` in `KNOWN_MODULE_DEBT`, which this branch pays. One conflict, `docs/documentation.html`, a generated projection. |
| `feat/tier-model-loop` | `LAND_AFTER_REPAIR` | Zero merge conflicts. Twelve files absent from main, including `scripts/sov_loop.py`, `scripts/sovloop/{artifacts,ollama,rules,run}.py`, `scripts/sov_bench.py`, `contracts/tier-bindings.json` and `conformance/fixtures/loop/`. The repair is not a text conflict: `decisions/0033-tier-model-bindings.md` collides with main's `decisions/0033-close-the-founding-docket.md` and must be renumbered past 0066. |
| `feat/registry-owner-gate` | `LAND_AFTER_REPAIR` | Main's `scripts/verify.py` has no `domain owner register` check, main's `scripts/sov_owners.py` has no `--strict` and no `unowned_services`, main's `contracts/domain-owners.json` has no `defaults` block, and `scripts/tests/test_sov_owners.py` (161 lines) does not exist on main. Two conflicts, `.github/CODEOWNERS` and `scripts/verify.py`, both additive: a CODEOWNERS block to append and one `Check` tuple to insert. |
| `feat/work-coordination-kernel-participant` | `ABSORB` | 71 of its 74 files duplicate PR #118's branch and `fix/landing-gate-host-independence`. Three commits are unique in the whole repository: `46dd4f3`, `24021f8` and `d6a82d4`, adding `reports/2026-08-26-bravo-contract-freeze-v0.md`, `reports/2026-08-26-bravo-kernel-walk.md` and two new gap rows in `services/asset/KNOWN-GAPS.md` (observe/settle split; proposal-to-run path). Absorb those three doc-only commits as their own small records concern; the rest is duplicate. |
| `fix/console-grant-attribution` | `ABSORB` into PR #118 | Main's `services/console/.../core.py` still defaults `granted_by: str = "Bdo"` and main's `authority.py` never mentions an issuer. PR #118's branch removes the default but has no empty-issuer check — `git grep "empty issuer"` on it returns nothing. The `_issuer()` guard that refuses `--granted-by ""` exists only here, and all four of its conflicts are with the #118 surface. Rebase the guard onto #118 rather than landing the branch beside it. |
| `wt/pr43` | `SUPERSEDED` | PR #43 merged at `5e35c62`. Main's `charting/derive.py` is the later version: it scopes the skill walk to `sdlc-*` and carries the `SkillBindingScope` class with its defeating case, both of which this branch lacks. Its `scripts/verify.py` is 180 lines behind. |
| `wt/principal-identity` | `SUPERSEDED` | PR #71 merged at `464072d`. All 22 of its distinctive paths exist on main; the only two whose bytes differ, `services/identity/contracts/service.json` and `services/record/.../custody.py`, are larger on main. |
| `feat/6-shared-kernel-transitions` | `SUPERSEDED` | The weakest call here; see the red section below. PR #61 was closed, which is a decision and not drift, and the replacement landed in three parts: the legality half as `contracts/kernel-transitions.json` and `scripts/sovkernel/transitions.py` (PR #62) plus `contracts/kernel-parity.json` (PR #63), and the journal half as the Record Service (PR #66), whose `core.py` already has `append`, `receipt`, `counter`, `reconstruct` and `rebuild_projections` beside `digest.py` and `tests/test_journal.py`. A second journal under `kernel/` would deepen PROD-I-8, which asks for one journal and not three. Absorb `reports/2026-08-23-kernel-witness.md` before the branch is dropped: it is an independent observation held nowhere else. |
| `feat/verification-channels` | `SUPERSEDED` | PR #64 closed. All eleven of its files are on main, including `scripts/sovmutate/`, `.claude/workflows/sov-review.js` and both schedules. Its `decisions/0020-verification-channels-and-merge-authority.md` landed renumbered as `decisions/0025-verification-channels-and-merge-authority.md`; the branch's copies still cite the three-second budget and decision `0019`. |
| `docs/verification-budget` | `SUPERSEDED` | `decisions/0050-verification-budget-graded.md` is on main and `scripts/verify.py` carries `BUDGET_GRADES = (("PLATINUM", 3.0), ("GOLD", 6.0), ("SILVER", 15.0))`. 0050 names this branch's draft in its own numbering note. Landing it would replace a graded budget with a flat one. |
| `feat/record-witness-surface` | `SUPERSEDED` | PR #99 closed. Every file it adds is on main, and main is a strict superset: the branch's digest computation is exactly main's `LEGACY_DIGEST_PROFILE` branch, beside which main added `soveraeign-record-chain/v2`. |
| `fix/custody-tests-declare-posix` | `SUPERSEDED` | PR #80 closed, PR #84 merged. Main's `scripts/infrastructure.py` already judges custody paths with `PurePosixPath`, and `scripts/custody_posix.py` gives the POSIX skip an honest receipt instead of an inline `skipUnless`. The branch also deletes `test_apply_is_idempotent_and_verifiable`, which main keeps. |
| `wt/pr59-merge-main` | `SUPERSEDED` | A WIP savepoint from 2026-08-24 whose own message says it left one conflict unresolved. The reconciliation it was a savepoint for landed twice since: PR #107 at `8d0ba04` and PR #113 at `4b96ba1`. The ruling it deferred is settled — main now carries `scripts/sov_board.py` and `adapters/github/catalogue.py` and `adapters/github/plan.py` — and its `decisions/0027-board-management-role.md` is on main renumbered as `decisions/0057-board-management-role.md`. |
| `feat/console-authority-enforced` | `RETIRE` | PR #115 closed. Both of its axes are held elsewhere in larger form. Console: PR #118's branch has `services/console/tests/fixtures.py`, `conformance/fixtures/authority/grant-cases.json` and a `permits.py` with node-root issuer logic this branch lacks. Landing gate: `fix/landing-gate-host-independence` carries the identical `sovland`/`scope.py`/`witness_stages.py` stack plus 59 lines this branch does not have. |
| `feat/f2-control-loop` | `RETIRE` | Content subset of `feat/gate-loop-pattern`, which deletes none of its files. The single file where the two differ, `.claude/workflows/sov-f2-control.js`, is byte-identical between this branch and `origin/main`, so nothing is lost by keeping the superset instead. |
| `feat/f2-integration` | `RETIRE` | `git diff --name-status feat/f2-control-loop feat/f2-integration` is empty: the two trees are identical. Its tip is a merge commit whose second parent is already on main. It adds no content to any branch. |

## Five more local branches that need no disposition at all

These carry nothing the trunk lacks. `git rev-list --count --left-right
origin/main...<branch>` puts zero on the branch side for every one of them, so
each is wholly contained in `origin/main` and deleting it cannot lose a commit.
They never appeared in the survey because the survey only lists branches with
outstanding work, which is exactly why they have been sitting here.

| Branch | Behind trunk by |
| --- | --- |
| `probe/rebase` | 4 |
| `chore/reconcile-and-ratify` | 5 (PR #113, merged) |
| `feat/session-principal` | 204 (PR #101, merged) |
| `wt/pr36` | 297 (PR #36, merged) |
| `worktree-agent-aeb007dbe3ae39b96` | 0 — this session's own scratch branch, disposable when its worktree closes |

## Landing order, against the contested surface

124 files are changed by more than one unlanded branch. The five `LAND` and
`LAND_AFTER_REPAIR` calls above should go in this order, smallest contested
surface first, so each landing does not manufacture the next conflict:

1. `docs/qa-witness-sweep-c296c25` — one file, contested by nothing.
2. `feat/tier-model-loop` — sixteen files, zero merge conflicts, no shared file
   with any other landing candidate.
3. `feat/registry-owner-gate` — six files; touches `scripts/verify.py`, which
   `feat/gate-loop-pattern` does not.
4. `fix/landing-gate-host-independence` — 26 files; its only conflict is a
   generated projection, and it must precede the absorption of
   `feat/work-coordination-kernel-participant` and `fix/console-grant-attribution`.
5. `feat/gate-loop-pattern` — 36 files and the widest contested surface, so it
   pays the conflicts rather than creating them.

## The attack on the disposable calls

Eleven branches are judged here as carrying nothing worth keeping. Each was then
attacked directly: for every path the branch changes, does `origin/main` hold it,
or does any branch named as carrying its work hold it? A path held by none of
them defeats the disposition.

Seven survived with no orphan at all, including all three `RETIRE` calls.
`feat/console-authority-enforced` is the one worth stating explicitly: all 72 of
its paths are held by `feat/console-authority-enforced-only` or by
`fix/landing-gate-host-independence`, so retiring it is not a judgement about its
quality but an observation that two other branches already carry every byte.

Four were flagged, and three of those are the probe being wrong rather than the
disposition:

- `feat/verification-channels` · `decisions/0020-verification-channels-and-merge-authority.md`
  is on main as `decisions/0025-`, same title, later status.
- `docs/verification-budget` · `decisions/0043-the-verification-budget-measures-the-wrong-thing.md`
  is answered by `decisions/0050-verification-budget-graded.md`, which names it.
- `wt/pr59-merge-main` · `decisions/0027-board-management-role.md` is on main as
  `decisions/0057-`, same title and same status.

A path-presence probe cannot see a renumbered decision record. That is a real
limitation of the method used throughout this report, and it cuts the other way
too: a row above could be wrong because a file landed under a name this survey
did not think to check.

The fourth flag is not a false positive. `feat/6-shared-kernel-transitions` holds
22 paths nothing else holds — the whole `kernel/` package, `kernel/tests/`,
`reports/2026-08-23-kernel-witness.md`, and two records whose numbers collide with
main. The `SUPERSEDED` call above is a claim about capability, not about bytes,
and it rests on PR #61 having been closed while PR #62, #63 and #66 landed the
alternative. Anyone who thinks a stateful kernel reference is still wanted should
reverse this row; it is the one call in the table that a reasonable reader could
settle the other way.

## What this report could not establish

The `LAND` definition asks for checks passing on the merged result. No merged
result was produced, because producing one means merging, which this role may
not do. Extracting a `git merge-tree` result with `git archive` was tried and
discarded: the same extraction of `origin/main` alone also fails, so the method
measures the missing `.git` directory rather than the merge. Every `LAND` and
`LAND_AFTER_REPAIR` call above therefore rests on the merge-tree conflict set
plus file-level content comparison, and not on a green run of the merged tree.
Whoever lands one runs `python scripts/verify.py` on the merged tree first.

## Worktrees

Thirty are open. A worktree is not a branch: removing one leaves its branch and
the branch's remote copy untouched.

Safe to remove now — the session that opened it is finished, and the branch
either landed or is dispositioned above with a remote copy standing:

| Worktree | Branch |
| --- | --- |
| `.../07be545c-.../scratchpad/report-wt` | `docs/qa-witness-sweep-c296c25` |
| `.../0fde28fd-.../scratchpad/wt-kernel` | `feat/6-shared-kernel-transitions` |
| `.../20229bcd-.../scratchpad/wt-43` | `wt/pr43` |
| `.../20229bcd-.../scratchpad/wt-59` | `wt/pr59-merge-main` |
| `.../2628a168-.../scratchpad/wt-principal` | `feat/session-principal` (PR #101 merged) |
| `.../a0d8dcb2-.../scratchpad/wt-posix` | `fix/custody-tests-declare-posix` |
| `.../ef218c2e-.../scratchpad/wt-loop` | `feat/tier-model-loop` |
| `C:/Users/bdf19/Desktop/sov-budget` | `docs/verification-budget` |
| `C:/Users/bdf19/Desktop/Soveraeign-f2` | `feat/f2-control-loop` |
| `C:/Users/bdf19/Desktop/Soveraeign-merge` | `feat/f2-integration` |

Keep until the work in them lands or is absorbed: `C:/Users/bdf19/Desktop/sov-registry`,
`C:/Users/bdf19/Desktop/sov-fix-attribution`, `C:/Users/bdf19/Desktop/soveraeign-gate-pattern`,
`C:/Users/bdf19/Desktop/soveraeign-landing-gate`, `C:/Users/bdf19/Desktop/soveraeign-fleet-bravo`.

Do not remove — a live session holds it: `C:/Users/bdf19/Desktop/Soveraeign`, the six
worktrees under `.claude/worktrees/`, the three detached trees under this session's own
scratchpad, `.../49ae4a52-.../scratchpad/wt-drain`, `.../a75dfbcc-.../scratchpad/wt-collection`,
`C:/Users/bdf19/Desktop/soveraeign-fleet-alpha`, `C:/Users/bdf19/Desktop/soveraeign-hypervisor`
and `C:/Users/bdf19/Desktop/soveraeign-fleet-echo`.

## What genuinely waits on Bdo

Nothing in this table. Every disposition above was settled on evidence already in
the repository, which is what `decisions/0033-close-the-founding-docket.md`,
Ruling 1 requires. Two items are worth his attention when the landings happen,
and neither blocks one:

- `feat/tier-model-loop` pins each loop tier to a named local model. That is a
  resource-consumption commitment, and `contracts/acceptance-policy.json` names
  resource commitment as an admissible hold. It is an acceptance question over
  the landed result, not permission to land.
- `decisions/0050` still records two open owner questions of its own — whether
  fifteen seconds is the right ceiling, and whether a lost grade should ever be
  more than a reportable observation. Retiring `docs/verification-budget` does
  not close them.

## What would defeat this report

Any branch above whose distinctive file is present on `origin/main` under a name
this survey did not check, or absent from main when this report says it is
present. Each row names the exact path; re-running `git ls-tree -r --name-only
origin/main -- <path>` defeats or confirms the row directly. Separately: several
sessions write this tree at once, so a branch reserved above may have been
finished, and a branch dispositioned above may have moved, since `3360a26`.
