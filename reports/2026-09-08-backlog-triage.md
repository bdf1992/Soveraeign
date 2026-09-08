# Backlog triage — 2026-09-08

23 branches carry 236 commits `main` (`1f8c506`) does not hold. `sov_strand.py` reports no commit existing only on local disk: a landing backlog, not a rescue.

## Landability was measured, not inferred

The first version of this report classified branches by merge-conflict count and called thirteen of them mechanical. That was a proxy, and it was wrong. Every branch was then merged into `main` for real and put through `lint.py` and `verify.py`; the merge was aborted and nothing was kept.

**One branch of twenty-three lands with no work.** A clean merge does not mean a landing: these branches were cut weeks ago and the trunk has tightened underneath them.

| | branches | commits |
| --- | --- | --- |
| Lands clean — merges, lints and verifies | 1 | 1 |
| Merges clean, then fails the gate | 4 | 24 |
| Conflicts on a live merge | 17 | 208 |
| Superseded, should not land | 1 | 1 |

`sov_backlog.py`'s merge-tree prediction agreed with the live merge on all 23. The tool is accurate; the earlier reading of it was not. What it cannot tell you is whether the merged result passes, and that is where the backlog actually stops.

## Per branch

`out` = commits not on the trunk. `confl` = paths a merge cannot resolve. `real` = those that are not regenerated files. `state` = what a live merge plus the gate actually did.

| branch | out | confl | real | state | what blocks it |
| --- | --- | --- | --- | --- | --- |
| `gap/derive-bdos-core-digest-check` | 1 | 0 | 0 | CLEAN | SUPERSEDED by `scripts/sov_vendor.py` (#234) — same three assertions, same `ROW` regex, plus the reverse direction |
| `witness/compression-2026-08-31-f1ee8f2` | 1 | 0 | 0 | CLEAN | nothing — landed from this triage |
| `feat/local-sdlc-environment-v0-1-v2` | 1 | 0 | 0 | REWORK | merges clean, verify fails; one of three overlapping takes, none an ancestor of another |
| `archive/prep-phase-1-5-evidence-carrier` | 5 | 0 | 0 | REWORK | `_prep_evidence_envelopes.py` is 374 lines against a 300 limit, `_prep_evidence_fix.py` lacks `from __future__ import annotations`, and its workflow fails two CI-retention tests the trunk added after this branch was cut |
| `feat/local-sdlc-environment-v0-1` | 18 | 0 | 0 | REWORK | merges clean, verify fails |
| `integrate/local-sdlc-environment-v0-1` | 24 | 0 | 0 | REWORK | merges clean, verify fails; the largest of the three |
| `claude/exit-zero-logging-imw5wu` | 2 | 3 | 0 | CONFLICT |  |
| `docs/product-milestone-forecast` | 2 | 2 | 0 | CONFLICT | ASK_BDO: dated milestone scenarios are product intent, which `AGENTS.md` puts at the root seat |
| `claude/access-requirements-zbl1s7` | 4 | 1 | 0 | CONFLICT |  |
| `claude/astra-gtp-scalability-6eus65` | 8 | 1 | 0 | CONFLICT |  |
| `claude/movement-72-hours-2claax` | 9 | 1 | 0 | CONFLICT |  |
| `claude/witness-context-discovery-runas1` | 12 | 3 | 0 | CONFLICT |  |
| `claude/witness-context-handoff-n8lk0h` | 15 | 1 | 0 | CONFLICT |  |
| `claude/sovereign-phase-1-5-exits-fb7ysc` | 17 | 3 | 0 | CONFLICT |  |
| `research/disposition-lab-v0-1` | 41 | 1 | 0 | CONFLICT |  |
| `feat/tooling-test-cost` | 1 | 2 | 2 | CONFLICT |  |
| `claude/skill-loop-closure-identity-iiogql` | 11 | 4 | 2 | CONFLICT |  |
| `claude/agent-independence-definition-z4crlv` | 9 | 5 | 3 | CONFLICT |  |
| `gap/compression-mechanics` | 2 | 4 | 4 | CONFLICT |  |
| `claude/phase-1-5-exit-custody-x7fsi0` | 8 | 6 | 4 | CONFLICT |  |
| `claude/phase-1-5-work-6n59ox` | 5 | 10 | 8 | CONFLICT |  |
| `refactor/the-evaluator-is-three-modules-with-one-verdict` | 16 | 24 | 21 | CONFLICT | shares every commit but one with the spike below, off base `02482a7`; this tip splits `authority.py` |
| `spike/cedar-grades-the-grant-corpus` | 16 | 24 | 21 | CONFLICT | the other tip — Cedar 4.12.0 under `experiments/cedar-authority/`. Landing both lands the shared fifteen twice |

## What this changes

The backlog is not a merge queue. Twenty-two of twenty-three branches need engineering before they can land — conflict resolution, a module split, an import, a test the trunk added since. Planning it as "merge these thirteen" would have produced thirteen red builds.

Order by real contested surface once the rework is done: `feat/tooling-test-cost` (2 real paths) first, the phase-1-5 cluster next, and the refactor/spike fork last, since whichever tip wins rewrites 21 shared paths.

## Evidence

`sov_backlog.py` measures; a live `git merge` of each branch into `main` followed by `lint.py` and `verify.py`, aborted after reading; commit subjects; ancestry checks between the two clusters. Full diffs were not read for every branch.

A survey is a snapshot and several sessions write this tree (`CLAUDE.md`, trap T6). Re-run before acting; the report is dated for that reason.
