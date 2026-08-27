# Branch dispositions, 2026-08-26

Status: `MEASURED · JUDGED · OBSERVED INDEPENDENTLY · NOTHING RATIFIED`

An independent witness read this report at `4108185` and dissented: no
disposition was wrong, but six rows misstated their own evidence and five counts
did not reproduce. All eleven findings are repaired below, each verified again by
hand before the edit. The witness's residuals, which are about the method rather
than any row, are listed at the end under their own heading and are not repaired,
because naming them is the repair.

Trunk frozen at `origin/main` = `3360a26` (merge of PR #117). Local `main` was
four commits stale at the time of the survey, so every comparison in this report
is against `origin/main` and not against `main`.

Eighteen branches are dispositioned here, out of the local branches ahead of
the trunk. Fifteen remote-tracking branches were missed entirely; that is
repaired under `Coverage` at the end, and the scope claim in this report's
title is withdrawn there. Ten more were deliberately left alone:
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
| `feat/gate-loop-pattern` | `LAND_AFTER_REPAIR` | Strict superset of both other F2 branches. Fourteen of its paths are absent from main, among them `.claude/workflows/sov-gate-control.js`, `.claude/schedules/f2-gate-loop.json`, `scripts/sovschedule/patterns.py`, `scripts/sovschedule/preflight.py`, three test modules, and its decision record. Repairs: `decisions/0045-gate-loop-as-a-scheduled-pattern.md` collides with main's `decisions/0045-acceptance-not-approval.md`, and four conflicts — `STATUS.yaml`, `conformance/fixtures/kernel/transition-cases.json`, `conformance/run.py`, `docs/documentation.html`, of which the last is a regenerable projection. One domain, `RECORD_LOCAL`. |
| `fix/landing-gate-host-independence` | `LAND_AFTER_REPAIR` | Seventeen of its paths are absent from main, including `scripts/sovkernel/scope.py`, `scripts/sovland/{__init__,repo,tree}.py`, `scripts/witness_stages.py`, `scripts/tests/test_sov_land.py` (617 lines) and eleven `reports/observations/2026-08-25-*.json`. Main's `scripts/sovkernel/authority.py` still grades a path by spelling alone, and main's `scripts/lint.py` still names `scripts/witness_infrastructure.py` in `KNOWN_MODULE_DEBT`, which this branch pays. One conflict, `docs/documentation.html`, a generated projection. |
| `feat/tier-model-loop` | `LAND_AFTER_REPAIR` | Zero merge conflicts. Fourteen of its paths are absent from main, including `scripts/sov_loop.py`, `scripts/sovloop/{artifacts,ollama,rules,run}.py`, `scripts/sov_bench.py`, `contracts/tier-bindings.json` and `conformance/fixtures/loop/`. The repair is not a text conflict: `decisions/0033-tier-model-bindings.md` collides with main's `decisions/0033-close-the-founding-docket.md` and must be renumbered past 0066. |
| `feat/registry-owner-gate` | `LAND_AFTER_REPAIR` | Main's `scripts/verify.py` has no `domain owner register` check, main's `scripts/sov_owners.py` has no `--strict` and no `unowned_services`, main's `contracts/domain-owners.json` has no `defaults` block, and `scripts/tests/test_sov_owners.py` (161 lines) does not exist on main. Two conflicts, `.github/CODEOWNERS` and `scripts/verify.py`, both additive: a CODEOWNERS block to append and one `Check` tuple to insert. |
| `feat/work-coordination-kernel-participant` | `ABSORB` | Every path it changes is held by main, by `feat/console-authority-enforced-only` or by `fix/landing-gate-host-independence`; 38 of the 74 differ from both carriers at byte level, so this row is a claim about which concern owns the work and not a claim that the bytes are duplicated. Three commits are unique in the whole repository: `46dd4f3`, `24021f8` and `d6a82d4`, adding `reports/2026-08-26-bravo-contract-freeze-v0.md`, `reports/2026-08-26-bravo-kernel-walk.md` and two new gap rows in `services/asset/KNOWN-GAPS.md` (observe/settle split; proposal-to-run path). Absorb those three doc-only commits as their own small records concern; the rest is duplicate. |
| `fix/console-grant-attribution` | `ABSORB` into PR #118 | Main's `services/console/.../core.py` still defaults `granted_by: str = "Bdo"` and main's `authority.py` never mentions an issuer. PR #118's branch removes the default but has no empty-issuer check — `git grep "empty issuer"` on it returns nothing. The `_issuer()` guard that refuses `--granted-by ""` exists only here, and all four of its conflicts are with the #118 surface. Rebase the guard onto #118 rather than landing the branch beside it. |
| `wt/pr43` | `SUPERSEDED` | PR #43 merged at `5e35c62`, and none of the branch's eight paths is absent from main. Main's `charting/derive.py` is the later version: it skips a non-`sdlc-` skill directory outright, where the branch walks every directory and raises `ChartingError` on the first `sov-<domain>` skill it meets. Main's `charting/tests/test_model.py` also carries the `SkillBindingScope` class and its defeating case, which the branch lacks. Its `scripts/verify.py` is 98 lines behind, 65 against 163. |
| `wt/principal-identity` | `SUPERSEDED` | PR #71 merged at `464072d`. All 22 of its distinctive paths exist on main. Nine of them differ in bytes, and main's version is the larger in all nine, so nothing on the branch is content main has not already taken further. |
| `feat/6-shared-kernel-transitions` | `SUPERSEDED` | The weakest call here; see the red section below. PR #61 was closed, which is a decision and not drift, and the replacement landed in three parts: the legality half as `contracts/kernel-transitions.json` and `scripts/sovkernel/transitions.py` (PR #62) plus `contracts/kernel-parity.json` (PR #63), and the journal half as the Record Service (PR #66), whose `core.py` already has `append`, `receipt`, `counter`, `reconstruct` and `rebuild_projections` beside `digest.py` and `tests/test_journal.py`. A second journal under `kernel/` would deepen PROD-I-8, which asks for one journal and not three. Absorb `reports/2026-08-23-kernel-witness.md` before the branch is dropped: it is an independent observation held nowhere else. |
| `feat/verification-channels` | `SUPERSEDED` | PR #64 closed. All eleven of its files are on main, including `scripts/sovmutate/`, `.claude/workflows/sov-review.js` and both schedules. Its `decisions/0020-verification-channels-and-merge-authority.md` landed renumbered as `decisions/0025-verification-channels-and-merge-authority.md`; the branch's copies still cite the three-second budget and decision `0019`. |
| `docs/verification-budget` | `SUPERSEDED` | `decisions/0050-verification-budget-graded.md` is on main and `scripts/verify.py` carries `BUDGET_GRADES = (("PLATINUM", 3.0), ("GOLD", 6.0), ("SILVER", 15.0))`. 0050 names this branch's draft in its own numbering note. Landing it would replace a graded budget with a flat one. |
| `feat/record-witness-surface` | `SUPERSEDED` | PR #99 closed. Every file it adds is on main, and main is a strict superset: the branch's digest computation is exactly main's `LEGACY_DIGEST_PROFILE` branch, beside which main added `soveraeign-record-chain/v2`. |
| `fix/custody-tests-declare-posix` | `SUPERSEDED` | PR #80 closed, PR #84 merged. Main's `scripts/infrastructure.py` already judges custody paths with `PurePosixPath`, and `scripts/custody_posix.py` gives the POSIX skip an honest receipt instead of an inline `skipUnless`. None of the branch's three paths is absent from main. |
| `wt/pr59-merge-main` | `SUPERSEDED` | A WIP savepoint from 2026-08-24 whose own message says it left one conflict unresolved. The reconciliation it was a savepoint for landed twice since: PR #107 at `8d0ba04` and PR #113 at `4b96ba1`. The ruling it deferred is settled — main now carries `scripts/sov_board.py` and `adapters/github/catalogue.py` and `adapters/github/plan.py` — and its `decisions/0027-board-management-role.md` is on main renumbered as `decisions/0057-board-management-role.md`. |
| `feat/console-authority-enforced` | `RETIRE` | PR #115 closed. Both of its axes are held elsewhere in larger form. Console: PR #118's branch has `services/console/tests/fixtures.py`, `conformance/fixtures/authority/grant-cases.json` and a `permits.py` with node-root issuer logic this branch lacks. Landing gate: `fix/landing-gate-host-independence` carries `scripts/sovland/*` and `scripts/witness_stages.py` byte-identical, and carries `scripts/sovkernel/scope.py` at 160 lines against this branch's 146 — the host-dependent-path refusal this branch predates. The decisive check is the defeating corpus rather than the code: all 34 `case_id`s in this branch's `conformance/fixtures/authority/grant-cases.json` are among the 36 on `fix/landing-gate-host-independence`, so retiring it loses no defeating case. |
| `feat/f2-control-loop` | `RETIRE` | Content subset of `feat/gate-loop-pattern`, which deletes none of its files. The single file where the two differ, `.claude/workflows/sov-f2-control.js`, is byte-identical between this branch and `origin/main`, so nothing is lost by keeping the superset instead. |
| `feat/f2-integration` | `RETIRE` | `git diff --name-status feat/f2-control-loop feat/f2-integration` is empty: the two trees are identical, both `979b559`. Its tip `13dc03c` is a merge commit whose first parent `a8a173e` is already on main and whose second parent `ae069ba` is `feat/f2-control-loop`'s tip, so the branch is that branch plus a merge and nothing else. |

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

100 files are changed by more than one of the eighteen branches here, and 139
counting the ten reserved ones too. The five `LAND` and
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

Thirty-one are open. A worktree is not a branch: removing one leaves its branch
and the branch's remote copy untouched.

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

## What the independent witness found, and what is left standing

A witness that neither wrote nor read this report while it was being built read it
at `4108185` and dissented. It reproduced the safety claim for all eighteen
branches, all five merge-conflict sets, every pull-request state, the whole attack
section including the count of 22 orphans, and the internal tally of one
disposition per branch. It found no disposition wrong. It found six rows and five
counts misstating their own evidence; every one is corrected above, and every
correction was re-derived by hand before the edit rather than taken on the
witness's word.

Four residuals it raised are not corrections to any row, and they stand:

- **The probe was path presence; three conclusions were written as byte claims.**
  This report already named one direction of that gap, that a renumbered decision
  record produces a false orphan. The other direction matters more: a carrier that
  holds a path with the branch's content stripped out produces a false clearance.
  The two `RETIRE` rows that depend on a carrier are now backed by something
  stronger than path presence — an identical tree for `feat/f2-integration`, and a
  `case_id` comparison of the defeating corpus for `feat/console-authority-enforced`.
- **Three destructive calls rest on carriers that are themselves unlanded.**
  `feat/f2-control-loop` and `feat/f2-integration` are carried only by
  `feat/gate-loop-pattern`, and `feat/console-authority-enforced` only by
  `fix/landing-gate-host-independence` and by the reserved
  `feat/console-authority-enforced-only`. Retire none of the three before its
  carrier lands. The remote copies mitigate this and do not remove it.
- **A reserved branch was used as evidence.** `feat/console-authority-enforced-only`
  is named above as a live branch too unstable to disposition, and then relied on
  as the carrier for two rows. That is the same false reading this report declines
  to make elsewhere, and it is the reason the `fix/console-grant-attribution` row
  says to rebase onto PR #118 rather than to delete anything.
- **The disposition vocabulary is this report's own.** `LAND` and
  `LAND_AFTER_REPAIR` are minted here. `SUPERSEDED`, `RETIRE` and `ABSORB` are
  words `contracts/decision-standing.json`, `scripts/sov_canon.py` and
  `contracts/closure-ownership.json` already use for other things. Nothing here
  changes what those contracts mean, and a future version of this survey should
  either define its terms in `.claude/skills/sov-backlog/SKILL.md`, which already
  names five of them, or use the contracts' words.

The nineteenth branch ahead of the trunk is this report's own,
`docs/branch-dispositions`. It carries the report and nothing else.

## What would defeat this report

Any branch above whose distinctive file is present on `origin/main` under a name
this survey did not check, or absent from main when this report says it is
present. Each row names the exact path; re-running `git ls-tree -r --name-only
origin/main -- <path>` defeats or confirms the row directly. Separately: several
sessions write this tree at once, so a branch reserved above may have been
finished, and a branch dispositioned above may have moved, since `3360a26`.

## Coverage: this survey read local branches only

A second independent reading found the survey incomplete, and it is. Every
comparison above uses `git for-each-ref refs/heads/` and
`git rev-list --count <branch> --not --remotes`, so it never looked at a
remote-tracking ref. Thirty-three branch names appear above and every local
branch that carried unlanded commits against `3360a26` when this was written is
among them — that part holds and was re-checked. But fifteen branches under
`refs/remotes/origin/` were already in this clone before the first report commit,
carried seventy-one commits against the frozen trunk, and are named nowhere.

The claim "every outstanding branch" was false for that reason and is withdrawn.
What follows repairs it with the same method the rows above use: per-file
presence against `origin/main`, then a blob comparison for files present in both.

One correction to the finding as it reached me, because it matters for anyone
re-running this. The first count I made said seven *local* branches were
uncovered. That was wrong: I had typed the named set out of the pull request
summary rather than reading it out of this file, and all seven are named here.
Counted against the file, the local gap is zero and the whole gap is remote.

### Nine that carry nothing main does not already have

For each of these, no file it touches is absent from `origin/main`, and every
file whose bytes differ has a newer commit date on main. Nothing is lost by
retiring them, and each reaches a remote.

| Branch | Evidence |
| --- | --- |
| `feat/gateway-end-to-end-slice` | no file absent, no file differing |
| `feat/kernel-binding-closure` | no file absent, no file differing |
| `feat/node-interface-projection` | no file absent, no file differing |
| `feat/phase-i-runtime-image-proof` | no file absent, no file differing, 2 identical |
| `feat/phase-i-runtime-image-contract` | 2 files differ, both newer on main, 7 identical |
| `fix/verification-budget-five-tooling-shards` | 1 file differs, newer on main |
| `fix/verification-budget-tooling-shards` | 4 files differ, all newer on main |
| `queue-agent-controller` | 1 file differs, newer on main |
| `merge/main-into-federation` | 113 files differ, all newer on main, 388 identical |

### Six that carry files present nowhere on main

These are measured, not judged. Each carries at least one file that
`git rev-parse origin/main:<path>` cannot resolve, so the work is unlanded and a
`RETIRE` or `SUPERSEDED` call would destroy evidence. Whether any of them should
land is a judgement about product intent that measurement does not settle, and
two of them are branch names this repository did not mint.

| Branch | Files absent from main | Differ | One that proves it |
| --- | --- | --- | --- |
| `claude/console-terminal-interfaces-5d0lzg` | 39 | 10 | `bindings/desk/scripts/demo.py` |
| `feat/composable-human-surface` | 7 | 0 | `scripts/sov_composed_surface.py` |
| `feat/surface-session-presence` | 7 | 0 | `scripts/sov_composed_surface.py` |
| `claude/ui-primitives-service-nav-rfqg7t` | 5 | 4 | `contracts/fixtures/surface-primitives.fixtures.json` |
| `feat/human-binding-affordances` | 5 | 0 | `scripts/sov_composed_surface.py` |
| `feat/phase-i-local-infrastructure` | 2 | 18 | `decisions/0014-phase-i-local-infrastructure.md` |

Three of the six name the same absent file, `scripts/sov_composed_surface.py`.
They are one body of surface work split across three branches, not three
independent claims on the trunk, and dispositioning any of them alone would
misread the other two.

### What would defeat this section

The presence test is `git rev-parse -q --verify origin/main:<path>` per file, and
the ordering test compares `git log -1 --format=%ci` on each side. The ordering
test is the weaker of the two: a newer commit date on main proves main's copy was
written later, not that it contains everything the branch's copy holds. A row in
the nine above is defeated by finding one hunk on the branch that is absent from
main's newer version of the same file. The six are defeated by finding their
"absent" path on main under a name this survey did not check.

The count of fifteen is itself dated. It is every remote-tracking ref whose
earliest reflog entry precedes this report's first commit at
`2026-08-26 12:49:04 -0500`; a ref fetched after that is drift and is excluded
deliberately, which is why the number here is smaller than a plain count of
unmentioned remote branches today.
