#!/usr/bin/env python3
"""Read daily or weekly repository compression pressure without creating authority.

The command is deliberately read-only. It composes existing repository facts:
phase state, the lessons loop, local Git history, and local ref topology. It does
not create a new ledger, settle a concern, change standing, or open a phase.
Scheduled harness runs already have their own gitignored capture/ledger.

Commands:

    python scripts/sov_compression.py daily
    python scripts/sov_compression.py weekly
    python scripts/sov_compression.py daily --json

The weekly reading is the same instrument over a longer window; the workflow
around it is responsible for deeper synthesis. Keeping one reader prevents the
ritual itself from creating two competing definitions of project health.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json
import re
import subprocess

import sov_lessons


ROOT = Path(__file__).resolve().parents[1]
WINDOW_HOURS = {"daily": 24, "weekly": 24 * 7}
ROOT_GOVERNING = {
    "AGENTS.md", "CANON.md", "CLASSIFICATION.md", "CONTRACT.md", "GROUND.md",
    "NAMING.md", "OPEN-SEAMS.md", "PRD.md", "PUBLICATION.md", "README.md",
    "ROADMAP.md", "SDLC.md", "SPEC.md", "STATUS.yaml", "SYSTEM.md",
}
KEY_VALUE = re.compile(r"^(?P<key>[a-zA-Z0-9_]+):\s*(?P<value>[^#\n]+?)\s*$", re.M)


class CompressionReadError(RuntimeError):
    """A repository fact required by the reading could not be read."""


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git failed"
        raise CompressionReadError(detail)
    return completed.stdout


def _status_values(text: str) -> dict[str, str]:
    """Read flat STATUS fields without pretending to parse the whole YAML document."""
    values: dict[str, str] = {}
    for match in KEY_VALUE.finditer(text):
        values[match.group("key")] = match.group("value").strip().strip("'\"")
    return values


def phase_reading(root: Path = ROOT) -> dict:
    text = (root / "STATUS.yaml").read_bytes().decode("utf-8")
    values = _status_values(text)
    return {
        "phase": values.get("phase"),
        "next_gate": values.get("next_gate"),
        "gap_preserved": values.get("phase") == "NONE_ACTIVE",
    }


def classify_path(path: str) -> str:
    """Broad, non-authoritative churn buckets for the compression reading."""
    normalized = path.replace("\\", "/")
    first = normalized.split("/", 1)[0]
    if normalized in ROOT_GOVERNING or first == "decisions":
        return "governance"
    if first == "contracts":
        return "contracts"
    if first == "services":
        return "services"
    if first in {"conformance", "witness", "reports"}:
        return "evidence"
    if first in {"docs", "diagrams", ".clarity"}:
        return "projection"
    if first in {"scripts", ".claude", ".github", "bindings", "adapters"}:
        return "harness"
    return "other"


def _commit_paths(root: Path, hours: int) -> list[tuple[str, list[str]]]:
    """Return exact commit/path observations in the time window.

    A NUL-separated stream avoids mistaking filenames for commit delimiters.
    Rename/copy output uses the resulting path because the ritual is interested
    in the current representation that received attention, not in reconstructing
    Git history semantics.
    """
    marker = "__SOV_COMMIT__"
    raw = _git(
        root, "log", f"--since={hours} hours ago", "--name-only", "-z",
        f"--format={marker}%H%x00",
    )
    tokens = [token for token in raw.split("\x00") if token]
    commits: list[tuple[str, list[str]]] = []
    current_sha: str | None = None
    current_paths: list[str] = []
    for token in tokens:
        if token.startswith(marker):
            if current_sha is not None:
                commits.append((current_sha, current_paths))
            current_sha = token[len(marker):].strip()
            current_paths = []
            continue
        path = token.strip()
        if path:
            current_paths.append(path)
    if current_sha is not None:
        commits.append((current_sha, current_paths))
    return commits


def summarize_commits(commits: list[tuple[str, list[str]]]) -> dict:
    path_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    for _sha, paths in commits:
        unique_in_commit = set(paths)
        path_counts.update(unique_in_commit)
        category_counts.update(classify_path(path) for path in unique_in_commit)
    return {
        "commits": len(commits),
        "unique_paths": len(path_counts),
        "category_touches": dict(sorted(category_counts.items())),
        "top_churn": [
            {"path": path, "commits_touched": count}
            for path, count in path_counts.most_common(12)
        ],
    }


def local_refs(root: Path = ROOT) -> dict:
    raw = _git(
        root, "for-each-ref", "--format=%(refname:short)",
        "refs/heads", "refs/remotes/origin",
    )
    refs = sorted({line.strip() for line in raw.splitlines() if line.strip()})
    non_main = [
        ref for ref in refs
        if ref not in {"main", "origin/main", "origin/HEAD"}
        and not ref.endswith("/HEAD")
    ]
    return {"observed_refs": refs, "non_main_refs": non_main}


def lessons_reading(root: Path = ROOT) -> dict:
    page = (root / sov_lessons.PAGE).read_bytes().decode("utf-8")
    contract = json.loads((root / sov_lessons.CONTRACT).read_bytes().decode("utf-8"))
    defects = sov_lessons.grade(page, contract)
    drain = sov_lessons.drain(page, contract)
    records = sov_lessons.entries(page)
    standings = Counter(record["standing"] or "none" for record in records)
    return {
        "entries": len(records),
        "standings": dict(sorted(standings.items())),
        "drain": drain,
        "defects": defects,
        "claims_clean": not defects,
    }


def reading(mode: str, root: Path = ROOT) -> dict:
    if mode not in WINDOW_HOURS:
        raise ValueError(f"unknown compression mode: {mode}")
    hours = WINDOW_HOURS[mode]
    revision = _git(root, "rev-parse", "HEAD").strip()
    commits = _commit_paths(root, hours)
    return {
        "schema": "soveraeign-compression-reading/v1",
        "mode": mode,
        "subject_revision": revision,
        "window_hours": hours,
        "authority": "NONE_OBSERVATION_ONLY",
        "phase": phase_reading(root),
        "git": summarize_commits(commits),
        "refs": local_refs(root),
        "lessons": lessons_reading(root),
        "routing": {
            "report": "observe one bounded window; creates no standing",
            "lesson": "generalize an evidenced invariant through the existing lessons loop",
            "decision": "use only when policy, authority, or a governing boundary changes",
            "concern": "use only when concrete work remains and must enter custody/settlement",
        },
    }


def render(result: dict) -> str:
    phase = result["phase"]
    lessons = result["lessons"]
    git = result["git"]
    refs = result["refs"]
    lines = [
        f"compression: {result['mode']} over {result['window_hours']}h @ {result['subject_revision'][:12]}",
        f"phase: {phase['phase'] or '-'}; next gate {phase['next_gate'] or '-'}; "
        f"gap preserved {'yes' if phase['gap_preserved'] else 'NO'}",
        f"git: {git['commits']} commit(s), {git['unique_paths']} unique path(s), "
        f"{len(refs['non_main_refs'])} non-main local/remote-tracking ref(s)",
        f"lessons: {lessons['entries']} entries, {lessons['drain']['recorded']} RECORDED, "
        f"drain {'due' if lessons['drain']['due'] else 'not due'}, "
        f"{len(lessons['defects'])} standing defect(s)",
    ]
    if git["top_churn"]:
        lines.append("top churn:")
        for row in git["top_churn"][:8]:
            lines.append(f"  {row['commits_touched']:>3}  {row['path']}")
    if lessons["defects"]:
        lines.append("lesson defects:")
        for defect in lessons["defects"]:
            lines.append(f"  {defect['code']}: {defect['detail']}")
    lines.append("reading only: no phase, standing, policy, concern, or authority changed")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=sorted(WINDOW_HOURS))
    parser.add_argument("--json", action="store_true", help="emit the exact machine reading")
    args = parser.parse_args(argv)
    try:
        result = reading(args.mode)
    except (CompressionReadError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else render(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
