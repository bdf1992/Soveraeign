"""Live-session coordination for a repository worked by several agents at once.

This package is host plumbing. It holds no standing and grants no authority
(`AGENTS.md`, Local orchestration harness). It answers one question the version
control system cannot: *which live session is presently writing this path*, and
it makes that answer visible before a write lands rather than after a clobber.

The record is append-preserving, matching the repository's own shape: events are
appended, never edited, and current state is a projection over them.
"""

from __future__ import annotations
