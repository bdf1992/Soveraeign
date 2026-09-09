#!/usr/bin/env bash
# Entry point for a Claude Code remote environment's setup script.
#
# Host plumbing. `.claude/` holds no standing and grants no authority
# (`AGENTS.md`, Local orchestration harness).
#
# Paste this into the environment's setup-script field. It looks where the host
# actually puts clones and does nothing when it finds none. On the Anthropic
# hosted container the session user's home is /root while the repositories are
# under /home/user, so a glob rooted at $HOME alone matches nothing there:
#
#   for s in /home/*/*/.claude/bootstrap/remote-session-setup.sh \
#            "$HOME"/*/.claude/bootstrap/remote-session-setup.sh; do
#     [ -f "$s" ] && bash "$s"
#   done; true
#
# It exits 0 on every path. A container that cannot be configured is a session
# without a briefing, not a reason to refuse to start work.

set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  echo "sov-bootstrap: not a remote session, nothing written."
  exit 0
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." 2>/dev/null && pwd)" || REPO_ROOT=""
if [ -z "$REPO_ROOT" ]; then
  echo "sov-bootstrap: could not resolve the repository root, nothing written."
  exit 0
fi

PYTHON="$(command -v python3 2>/dev/null || command -v python 2>/dev/null)" || PYTHON=""
if [ -z "$PYTHON" ]; then
  echo "sov-bootstrap: no python on PATH, nothing written."
  exit 0
fi

"$PYTHON" "$REPO_ROOT/.claude/bootstrap/remote_session_setup.py" "$REPO_ROOT" || true
exit 0
