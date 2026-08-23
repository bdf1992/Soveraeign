---
name: sov-coordination
description: Board management for the GitHub coordination surface - survey it into recommended actions with their evidence, present the batch for approval, and apply only what was approved through the declared write crossing. Load on "sov-coordination", "board management", "board review", "board drift", "label drift", "triage the board", "prune merged branches", "stale pull request", "sov_board", or "github management". Not for building services or contracts; those have sibling sov-* skills.
---

# Coordination Domain Skill

Standing: `BUILT_SELF_TESTED_NOT_WITNESSED` (see decision 0027).

The board is a coordination surface, not a System of Record. Nothing here
settles standing, and an approved action changes what GitHub displays, never
what the repository holds.

## The one rule this skill exists to enforce

Never hand the owner a decision without the evidence and a recommendation
attached. A question like "should I clean up the board?" makes them redo the
survey before they can answer. `sov_board review` exists so the answer is a
list of action ids instead.

## The loop

1. `python scripts/sov_board.py review` — captures the board through the read
   registrar, judges it offline against the contracts in this checkout, and
   writes a batch to `.local/board/batch.json`.
2. Read the surface. `PROPOSED` actions are mechanically derived and
   reversible. `REPORTED` actions need authored metadata or owner judgement
   and cannot be approved at all.
3. Bring the `PROPOSED` list to Bdo with a recommendation, not a menu. Say
   which ids you would approve and why the rest are different.
4. `python scripts/sov_board.py apply --batch <path> --approve <ids>` on his
   answer. Add `--dry-run` first to print the exact commands.
5. Re-run `review`. A batch that does not shrink means an action failed, and
   the receipts under `.local/board/batch.receipts.json` say which.

## What each action kind means

| Kind | Disposition | Why |
| --- | --- | --- |
| `LABEL_ADD`, `LABEL_REMOVE` | approvable | Derived exactly from `contracts/ticket-label-projection.json`; reversible |
| `BRANCH_DELETE` | approvable | The merge commit keeps the ref recoverable |
| `CONTRACT_DEFECT` | report only | Repair needs authored metadata; an approval cannot write prose |
| `CONTRACT_BEHIND` | report only | The board uses vocabulary this checkout lacks; fix the checkout, not the board |
| `LABEL_UNMAPPED` | report only | Declare the label in `.github/labels.yml` before projecting it |
| `PR_STALE` | report only | Landing, closing, or waiting is a judgement |

## Boundaries

- `adapters/github/export.py` is the only read crossing;
  `adapters/github/apply.py` is the only write crossing. Nothing else in the
  repository may call the GitHub API, and neither adapter calls the other.
- Every write is `EXTERNAL_WORLD` and requires one approval per action.
  `--approve all` is still one approval per action; it is not a standing grant.
- A `CONTRACT_BEHIND` report is never resolved by editing the board. The
  checkout is what is behind.
- Closed issues are surveyed for nothing. A report that includes them can
  never come back clean, which is how the previous drift report went unread.

## Refusals

Refuse to write to GitHub without a per-action approval, to approve a
report-only action, to widen the admitted action set inside the adapter, to
close an issue or a pull request as a batch action, and to present a survey
as a settled standing.
