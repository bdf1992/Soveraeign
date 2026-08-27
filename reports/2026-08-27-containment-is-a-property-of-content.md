# Containment is a property of content, not of commits

A rescue pass over the working area on 2026-08-27, and one shape the field defeated.
This is a report. It is not policy and it changes no standing.

## What happened

`acceptance/A11.json`, a finished acceptance packet, was destroyed in this shared
working tree with no copy anywhere. It had never been a commit, so no reading in this
repository could see it — before it died or after.

Everything built to notice lost work classifies *commits and branches*.
`scripts/sov_strand.py` grades branches against remotes. `scripts/sov_backlog.py`
measures branches against the trunk. `scripts/sov_branch.py` inventories branches and
worktrees. The loss happened in the one place none of them look.

The check was not silent about the working tree — it printed the uncommitted count
underneath its verdict. It just never read it, so it could print
`PASS: no commit exists only in this directory` over a tree holding 145 files that
nothing protected. Counting is not grading.

## Shape delta

| Field | Reading |
| --- | --- |
| `supplied_shape` | Rescue classified by worktree and branch; at risk means commits reachable from no remote. |
| `observed_pressure` | A11 was destroyed and appeared in no at-risk reading. At the moment of survey, 145 uncommitted files were in the same state, and the check graded that tree PASS. Nine sessions write this tree at once; six files changed between being captured and being verified, inside one minute. |
| `revised_shape` | At risk is a property of *content with no second copy*, not of *commits with no remote*. A third class, `EXPOSED`: uncommitted content whose exact bytes no ref in this repository holds. It fails the check the way a stranded commit does. |
| `preserved_invariants` | Recoverability, attribution, separate settlement. Containment claims nothing about the work: a rescue ref is not a branch, not a landing, and not a witness. |
| `lost_distinctions` | None. `AT_RISK` and `UNLANDED` are untouched. |
| `new_distinctions` | Held versus exposed, inside the uncommitted population. The decision that now depends on it: whether a tree may be cleaned, reset, or left overnight. |
| `migration` | `uncommitted()` returns paths rather than a count; the public surface is otherwise unchanged and re-exported. |
| `defeating_case` | If content that no ref holds is nonetheless routinely recoverable here — an editor history, a backup daemon, a synced directory — the class is measuring the wrong thing and should be retired. Nobody has shown that, and A11 is evidence against it. |
| `closure_effect` | 152 files that existed only in one directory now survive a delete and a garbage collection. |

## Why the predicate is truthful rather than cautious

Contained means the identical blob is reachable from some ref, whoever put it there.
A stricter rule — only a deliberate capture counts — would report files as endangered
that a sibling session had just committed, and a check that cries wolf gets ignored,
which is how the first version of this reading came to be printed and not read.

The cost is one reachable-object listing, 0.2 s in this repository.

## What was done

- **Contained.** Every uncommitted file, captured under `refs/rescue/uncommitted-2026-08-27`
  by explicit path into a throwaway index. The shared `.git/index` is asserted unchanged
  before and after, because eight other sessions were writing this tree throughout.
  Verified by re-reading each blob out of the object database and comparing bytes to the
  live file: 145 of 145 identical.
- **Contained the commits too.** The 37 commits then reachable from no remote were bundled
  and recovered into a repository seeded only from `origin`. 37 of 37 recoverable, 0 not.
  Partway through, a peer session pushed 7 branches, which is why 14 of the 37 became
  reachable mid-measurement. That is trap T6 in `CLAUDE.md` observed live.
- **Repaired the reading.** `scripts/sov_strand.py` now grades exposed content and names it
  at session start. `python scripts/sov_strand.py contain` makes the capture repeatable.
  17 tests, each defeating case included. Commit `3383ea6`.
- **Reduced the inventory.** 28 abandoned clean worktrees retired (91 → 61) and 33 branches
  whose commits `main` already holds (85 → 52). Zero commits became unreachable across
  either operation, measured before and after.

## A defect this found in itself

The first run of `contain` dropped six paths the previous capture held, because it wrote a
tree containing only what was exposed at that moment. A rescue that can un-rescue is not
one. `capture` now merges onto an existing ref, newer bytes winning, previous capture as
parent, with its own defeating test. The six paths were never lost — the earlier capture
was pinned before the merge was written.

## What this did not touch

The custody registry, the work circuit and the phase record under `contracts/` are held by
a live sibling session and were left alone. The pressure worth recording against them from
outside: `custody:trunk-reconciliation` read *target reached, zero stages to go* while 246
commits sat unlanded on 46 branches. Whether that is false containment or a target
deliberately set below the work is the holder's call, not this reading's.

## An open seam in the guard

The hook that refuses `git add -A` in a shared tree is right about commits and blocks the
cheapest route to containing someone else's exposed work — it refuses even into an isolated
index that no branch can reach. The workaround here is per-path capture, which is correct
but slower and easy to get wrong. A rescue path that does not need the workaround would be
worth having.
