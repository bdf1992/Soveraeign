"""Branch, worktree, and merge management for one repository with many trees checked out.

`sov_branch.py` owns the command line; the modules here own what each command does:

  gitio      read-only git, and the object-database merge probe
  ledger     one joined record per branch
  mergeplan  a merge sequence proved against a rolling accumulation
  execute    the two operations that change something
  render     human output

Host plumbing. It holds no standing and grants no authority (`AGENTS.md`).
"""

from __future__ import annotations
