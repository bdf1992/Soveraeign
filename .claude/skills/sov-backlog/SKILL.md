---
name: sov-backlog
description: Domain know-how for draining unlanded work - branches that were built and then left, the commits stranded on them, and the disposition each one needs. Load when a task names "sov-backlog", "the backlog", "unlanded work", "stranded branches", "branch cleanup", "what never merged", "drain the branches", or asks which of the open branches are still wanted. Covers surveying every branch against the trunk, judging a disposition with evidence, and naming the small set of choices that genuinely need Bdo. Not for landing a single concern's own branch (that is the concern's own closure), not for GitHub pull-request administration (adapters/github/), and not for the epic issue tree (sov-epic).
---

## Purpose

Work in this repository is built faster than it is landed. On 2026-08-25 eighteen
branches carried unlanded commits, several of them finished and tested, and the
only detector was Bdo noticing. This domain turns that pile into a disposition
per branch, with the evidence under it, so the pile shrinks by decision rather
than by attrition.

The domain measures and judges. It does not merge. Landing is a separate act
under `contracts/standing-grants.json`, and no harness role may commit
(`.claude/agents/*`, and `OPEN-SEAMS.md` S21).

## Owns / Must not

Owns: `scripts/sov_backlog.py` (the survey), `scripts/sov_strand.py` (the
loss-risk check and its session-start reading), and the disposition report this
domain produces.

Must not: merge, commit, push, delete a branch, or rewrite history. Must not
recommend deleting a branch whose commits reach no remote - push first, decide
after, because a decision that destroys the evidence it rests on cannot be
revisited. Must not treat a green `verify.py` on the trunk as evidence about a
branch that has never been merged into it.

## Key files

- `scripts/sov_backlog.py` - the survey. `--json` for machine use, bare for a
  table. Reads git only, writes nothing, and trials merges with
  `git merge-tree`, which resolves in memory and touches no index or worktree.
  Safe in a tree other sessions are working in, which this tree always is.
- `scripts/sov_strand.py` - grades whether a branch's commits reach any remote.
  Run it first: a branch that exists only on this disk is a loss risk before it
  is a backlog item.
- `scripts/tests/test_sov_backlog.py`, `scripts/tests/test_sov_strand.py` - the
  defeating cases, including work already landed under another hash.

Both tools read local heads **and** remote-tracking refs with no local head, and
skip a remote copy of a branch already counted locally. Until 2026-08-27 they
read `refs/heads/` alone, so a branch pushed once and never checked out here
again was reported as nothing at all: eighteen branches carrying 88 commits,
one of them with an open pull request, invisible in the two tools whose whole
purpose is seeing them. `git fetch --prune` before a survey, or the reading is
of a stale copy of the remote rather than of the remote.

## The three measures, and what each one settles

| Column | Question it answers | Why it is not obvious |
| --- | --- | --- |
| `out` | commits the trunk does not carry | raw commit count double-counts work that already landed by rebase or cherry-pick |
| `done` | commits the trunk already carries under another hash | a branch that is entirely this is finished, and deleting it loses nothing |
| `confl` | paths a merge cannot resolve alone | zero means mechanical; a number means somebody must choose |

`shared_files` names every file two or more branches change. That is where
landing order stops being free.

## Dispositions

Every branch gets exactly one, and each names its evidence:

- `LAND` - outstanding work, no conflicts, checks pass on the merged result.
  Mechanical. Needs nobody's judgement.
- `LAND_AFTER_RESOLUTION` - outstanding work, conflicts named, and the
  resolution is inside one service and one effect class. Ordinary engineering.
- `ALREADY_HOME` - `out` is zero. The work landed by another route. Deleting
  the branch loses nothing, and the survey proves it rather than asserting it.
- `SUPERSEDED` - the outstanding commits are answered by later work on the
  trunk. This one needs the diff read, not just counted; say what supersedes it.
- `ASK_BDO` - the branch is a product-intent, naming, or external-commitment
  question, or two settled constraints conflict in it. Nothing else qualifies
  (`contracts/acceptance-policy.json` names the admissible reasons and states
  the list is exhaustive).

Wanting a second opinion is not `ASK_BDO`. A branch nobody remembers is not
`ASK_BDO` either; read it.

## How to work this domain

1. `python scripts/sov_strand.py`. Anything at risk gets pushed before any
   disposition is written.
2. `python scripts/sov_backlog.py --json`. This is the evidence base; do not
   re-derive it per branch.
3. Per branch: read the commit subjects and the diff against the trunk, decide
   the disposition, and state what would defeat it.
4. Order the `LAND` set against `shared_files`, smallest contested surface
   first, so each landing does not manufacture the next conflict.
5. Report as a delta, not an inventory: what the count was, what it is, and
   which branches remain and why.

## Verification

`python scripts/verify.py` from the repository root. The survey's own tests run
inside it. A disposition is a claim about a branch and is never witnessed by the
participant that wrote it.

## Blockers

- No harness role may merge or commit, so this domain's terminal is a disposition
  report, not a drained backlog. Ordinary BUILT landing is done by the
  interactive participant or under the standing grant after the required Blue
  checks. Independent witness is queued separately when a named milestone or
  later transition consumes it (`decisions/0098-milestone-witnessing.md`).
- Several sessions write this tree at once (`CLAUDE.md`, trap T6). The survey is
  a snapshot; re-run it before acting on it.
