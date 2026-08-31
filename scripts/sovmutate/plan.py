"""Derive mutation work without executing mutants.

A mutation plan is the synchronous admission surface for expensive mutation
work. It proves the diff can be scoped, every changed production Python target
has an owning suite, and the exact source/line/suite inputs can be named before
any worker spends time running experiments.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from . import diffscope, operators, suites

SCHEMA = "soveraeign-mutation-plan/v1"


class PlanError(RuntimeError):
    """Mutation work cannot be admitted honestly."""


def _digest(data: bytes) -> str:
    return "sha256:" + sha256(data).hexdigest()


def _head(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(root), capture_output=True,
        text=True, check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise PlanError(f"cannot resolve mutation head: {detail}")
    return result.stdout.strip()


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise PlanError(f"{path} is outside mutation root {root}") from exc


def _suite(command: tuple[str, ...], cwd: Path, root: Path) -> dict:
    argv = list(command)
    if argv and Path(argv[0]).resolve() == Path(sys.executable).resolve():
        argv[0] = "<python>"
    return {"command": argv, "cwd": _relative(cwd, root) if cwd != root else "."}


def target(root: Path, path: Path, lines: set[int]) -> dict:
    """Describe one admitted mutation target deterministically."""
    owned = suites.suite_for(path, root)
    if owned is None:
        raise PlanError(f"no mutation suite owns {_relative(path, root)}")
    command, cwd = owned
    source = path.read_bytes()
    found = operators.sites(source.decode("utf-8"))
    eligible = [site for site in found if site.line in lines]
    return {
        "path": _relative(path, root),
        "source_digest": _digest(source),
        "changed_lines": sorted(lines),
        "mutable_sites": [
            {
                "index": site.index,
                "line": site.line,
                "operator": site.operator,
                "description": site.description,
            }
            for site in eligible
        ],
        "suite": _suite(command, cwd, root),
    }


def build(root: Path, base: str) -> dict:
    """Build the exact changed-line mutation work admitted against ``base``."""
    paths = diffscope.changed_files(root, base)
    unclaimed = [path for path in paths if suites.suite_for(path, root) is None]
    if unclaimed:
        names = ", ".join(_relative(path, root) for path in unclaimed)
        raise PlanError(f"changed production Python has no mutation suite owner: {names}")
    targets = [
        target(root, path, diffscope.changed_lines(root, base, path))
        for path in paths
    ]
    return {
        "schema": SCHEMA,
        "head": _head(root),
        "base": base,
        "targets": targets,
        "target_count": len(targets),
        "mutable_site_count": sum(len(row["mutable_sites"]) for row in targets),
    }


def render(value: dict) -> str:
    """Stable human/machine-readable representation of a plan."""
    return json.dumps(value, indent=2, sort_keys=True)
