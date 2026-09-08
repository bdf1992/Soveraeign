# Backlog triage — 2026-09-08

Trunk `main` at `ddb1a69`. 23 branches carry 236 commits the trunk does not hold. `sov_strand.py` reports no commit existing only on this disk, so nothing here is a loss risk; this is a landing backlog, not a rescue.

## The measure that reorganises the pile

Seventeen branches show merge conflicts. **Ten of them conflict only in generated files** — `docs/documentation.html`, `.clarity/coverage.json`, `docs/surface.html`. Those are rebuilt by `sov_docs.py build`, `sov_surface.py render` and a clarity re-record, so they are not disagreement and no one has to choose. Counting them as conflicts made the backlog look twice as contested as it is.

## Mechanical — 13 branches, 157 commits

No conflict, or conflicts only in regenerated files. The resolution is a command, not a judgement.

| branch | out | conflicts | note |
| --- | --- | --- | --- |
| `feat/local-sdlc-environment-v0-1-v2` | 1 | — generated | sibling of the above; 1 commit |
| `witness/compression-2026-08-31-f1ee8f2` | 1 | — generated |  |
| `claude/exit-zero-logging-imw5wu` | 2 | 3 generated |  |
| `claude/access-requirements-zbl1s7` | 4 | 1 generated |  |
| `archive/prep-phase-1-5-evidence-carrier` | 5 | — generated |  |
| `claude/astra-gtp-scalability-6eus65` | 8 | 1 generated |  |
| `claude/movement-72-hours-2claax` | 9 | 1 generated |  |
| `claude/witness-context-discovery-runas1` | 12 | 3 generated |  |
| `claude/witness-context-handoff-n8lk0h` | 15 | 1 generated |  |
| `claude/sovereign-phase-1-5-exits-fb7ysc` | 17 | 3 generated |  |
| `feat/local-sdlc-environment-v0-1` | 18 | — generated | sibling of the above |
| `integrate/local-sdlc-environment-v0-1` | 24 | — generated | one of three overlapping local-sdlc branches; none is an ancestor of another |
| `research/disposition-lab-v0-1` | 41 | 1 generated | largest single body at 41 commits; a research lab, so whether it is *meant* to land is its owner's call, not a merge question |

## Needs a judgement — 8 branches, 68 commits

| branch | out | real conflicts | what has to be decided |
| --- | --- | --- | --- |
| `claude/skill-loop-closure-identity-iiogql` | 11 | 2 | CLAUDE.md and the phase-1-5 custody — both moved on the trunk since |
| `feat/tooling-test-cost` | 1 | 2 | one module and its test; smallest contested surface in the set, so land it first |
| `claude/agent-independence-definition-z4crlv` | 9 | 3 | three diagrams, which sov_diagrams grades against their sources rather than generating |
| `claude/phase-1-5-exit-custody-x7fsi0` | 8 | 4 | CLAUDE.md, the verification budget, and the active-phase reader |
| `gap/compression-mechanics` | 2 | 4 | three sov-* skill files; 3 of its 5 commits already reached the trunk by another route, so read the diff before assuming the rest is wanted |
| `claude/phase-1-5-work-6n59ox` | 5 | 8 | eight real paths including CLAUDE.md and three diagrams |
| `refactor/the-evaluator-is-three-modules-with-one-verdict` | 16 | 21 | FORK: shares every commit but one with the spike below, off base 02482a7. This tip splits authority.py into three modules |
| `spike/cedar-grades-the-grant-corpus` | 16 | 21 | FORK: the other tip — Cedar 4.12.0 grading the grant corpus, confined to experiments/cedar-authority/. Landing both lands the shared 15 twice |

## Settled here

**`gap/derive-bdos-core-digest-check` — SUPERSEDED.** Its 39-line test asserts three things: the table parses, each recorded file exists, each digest matches. All three are in scripts/sov_vendor.py, landed in #234 (main ddb1a69), with the ROW regex carried over character for character and the reverse direction added. Landing it now would give the rows->tree check twice. Defeated by: a claim in its test that sov_vendor does not make.

**`docs/product-milestone-forecast` — ASK_BDO.** Dated product milestone scenarios and integration dependencies. AGENTS.md puts product intent with the root seat; a forecast is a product claim, not an engineering one. Its two conflicts are both generated. Defeated by: the diff turning out to record only observed history rather than forecast intent.

## Landing order

`shared_files` names 116 files two or more branches touch, but the top two are generated. Ordering by real contested surface: `feat/tooling-test-cost` (2 paths) first, then the mechanical set in any order, then the phase-1-5 cluster, and the refactor/spike fork last because whichever tip is chosen rewrites 21 shared paths.

## What backs each disposition

Measures from `sov_backlog.py` (merge trials via `git merge-tree`, nothing written), commit subjects, and ancestry checks between the two clusters. **Full diffs were not read for every branch.** The two dispositions I settled rest on more: the SUPERSEDED one on reading both implementations, the ASK_BDO one on its subjects. Everything in the two tables is a routing claim, not a merge decision.

## Terminal

A disposition report. This domain does not merge, commit, or delete a branch, and no branch was touched. Nothing here is witnessed; a disposition is never witnessed by the participant that wrote it.
