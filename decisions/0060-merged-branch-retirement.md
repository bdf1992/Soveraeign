# 0060 · A merged feature branch retires itself

Status: `OWNER-DIRECTED`

## Decision

A same-repository pull-request head is temporary execution state. Once GitHub reports the
pull request merged, the remote head is retired automatically rather than remaining as
completed inventory for a later agent to explain or clean up.

This is one narrow addition to `contracts/external-effect-authorization.json`:
`coordination.branch_retirement / delete_merged_head_branch`. It does **not** authorize
arbitrary branch deletion, force-push, repository-setting changes, pull-request merge, or
any effect outside `bdf1992/Soveraeign`.

The effect is admitted only when the write crossing re-reads GitHub immediately before the
delete and proves all of these facts:

1. the named pull request is merged;
2. its exact head ref equals the branch to retire;
3. its exact head SHA equals the SHA supplied by the merge event;
4. the head repository is `bdf1992/Soveraeign`, not a fork;
5. its base ref is the base named by the event;
6. the branch is not the repository default branch;
7. the live branch ref still points at that exact merged head SHA; and
8. no open pull request still uses the branch as its base.

A caller, workflow event, model statement, green check, or stale export cannot substitute
for that live proof. A branch reused or advanced after merge refuses as
`BRANCH_HEAD_MOVED`; an open stacked child refuses as `STACK_BASE_LIVE`; the repository
default branch refuses as `PROTECTED_BRANCH`. The branch is therefore not deleted merely
because it is old, behind, quiet, or apparently contained.

## Why this is not the refused shared-branch deletion

Decision 0047 correctly refuses `delete_branch_shared`: removing a ref that other work
still names can strand coordination. A merged head that still points at the merged SHA and
has no open pull request based on it has crossed a stronger boundary. Its accepted history
is reachable through the merge commit and GitHub retains the pull-request/commit record;
the head ref itself no longer carries unfinished review work.

The distinction is mechanical, not semantic guesswork:

- **merged exact head + unchanged live ref + no open stacked child** → retire;
- **merged exact head + open stacked child** → keep and report the dependency;
- **merged PR + branch reused/advanced** → keep the new work and refuse deletion;
- **default/open/unmerged/changed/fork head** → refuse;
- **merely behind** → no deletion authority is implied.

## Execution shape

`.github/workflows/branch-retirement.yml` listens only for a merged, same-repository pull
request. It constructs a typed `BRANCH_DELETE` action containing the PR number, head SHA,
base ref, and authority basis. It has no GitHub write implementation of its own: the action
passes through `adapters/github/apply.py`, the existing coordination write crossing.

The crossing independently revalidates the eight facts above and leaves a receipt for the
attempt. The workflow publishes that receipt in the Actions step summary. A live stacked
child is a clean deferral; any other proof or write failure fails the workflow.

Local branches and worktrees are a separate host concern. After the remote head lands,
`python scripts/sov_branch.py retire --apply` remains the bounded local cleanup mechanism
for branches already contained by the chosen base.

## Relationship to 0057

`decisions/0057-board-management-role.md` required a fresh owner approval for every
`BRANCH_DELETE` and therefore prohibited unattended cleanup. That remains true for board
batches and arbitrary branch-delete proposals. This record supersedes only that one case:
the exact merged-head retirement above has standing authorization and does not wait for a
second owner gesture after every merge.

The board survey remains useful for historical residue and for reporting branches that
cannot be retired automatically. It is no longer the normal completion path for a newly
merged feature branch.

## Defeating cases

Demote this decision if the automation can delete an unmerged branch, a fork head, the
default branch, a branch whose live ref moved beyond the merged PR SHA, a branch still used
as an open PR base, or a branch merely because it is behind. Demote it if any deletion
bypasses the GitHub write crossing or leaves no attempt receipt.

## Source and authority

Bdo, 2026-08-25 interactive session, after observing merged branches accumulating:
completed and merged feature branches should close automatically, with better automation,
support, and tooling. The owner then supplied a bounded credential specifically so this
repository adjustment would not wait on a manual browser step. The credential itself is
not part of the repository, contract, workflow, receipt, or evidence.
