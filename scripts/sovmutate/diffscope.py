"""Derive the exact changed-file and changed-line scope for mutation scoring.

The PR mutation gate says it scores "the mutants this change admits". This
module makes that phrase mechanical: production Python files come from the
merge-base diff, and mutable sites are eligible only on new-side lines named by
zero-context hunks. Failure to derive either scope is a refusal, never an empty
score that could be mistaken for success.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
SKIP_PARTS = ("tests", "lineage", ".git", "sovmutate")


class DiffScopeError(RuntimeError):
    """The changed-file or changed-line scope could not be derived honestly."""


def changed_files(root: Path, base: str) -> list[Path]:
    """Production Python files changed against ``base``."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD", "--", "*.py"],
        cwd=str(root), capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise DiffScopeError(
            f"git diff could not derive changed Python files against {base}: {detail}")

    files: list[Path] = []
    for name in result.stdout.splitlines():
        name = name.strip()
        if not name:
            continue
        path = root / name
        if path.is_file() and not any(part in SKIP_PARTS for part in path.parts):
            files.append(path)
    return files


def parse_changed_lines(diff: str) -> set[int]:
    """New-side line numbers named by zero-context unified-diff hunks."""
    changed: set[int] = set()
    for row in diff.splitlines():
        match = HUNK.match(row)
        if match is None:
            continue
        start = int(match.group(1))
        count = int(match.group(2) or "1")
        changed.update(range(start, start + count))
    return changed


def changed_lines(root: Path, base: str, path: Path) -> set[int]:
    """New-side lines in ``path`` changed against ``base``."""
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise DiffScopeError(f"{path} is outside mutation root {root}") from exc

    shown = str(relative).replace("\\", "/")
    result = subprocess.run(
        ["git", "diff", "--unified=0", "--no-color", f"{base}...HEAD", "--", shown],
        cwd=str(root), capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise DiffScopeError(
            f"git diff could not derive changed lines for {shown} against {base}: {detail}")
    return parse_changed_lines(result.stdout)
