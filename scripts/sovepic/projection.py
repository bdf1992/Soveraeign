"""Read and write the checked-in projection of the epic-of-epics issue tree.

The projection is a derived view of the GitHub coordination surface, not a
second authority: the issue body remains the compressed specification
(``CONTRIBUTING.md``, Issue coordination contract). Refreshing it reads an
external surface and is therefore an attended action - ``sov_epic.py sync`` run
by a human or an interactive session. Scheduled runs read the checked-in file
only, which keeps the unattended loop inside ``RECORD_LOCAL``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
import json
import subprocess

from sovepic import metadata


PROJECTION_PATH = Path(".claude") / "epic" / "tree.json"
VILLAGES_PATH = Path(".claude") / "epic" / "villages.json"
PROJECTION_SCHEMA = "soveraeign-epic-projection/v1"
ROOT_ISSUE = 1
GH_FIELDS = "number,title,state,labels,url,updatedAt,body"


class ProjectionError(RuntimeError):
    """The projection is missing, malformed, or could not be refreshed."""


@dataclass(frozen=True)
class Issue:
    """One projected issue: what GitHub shows, and what its body declares."""

    number: int
    title: str
    state: str
    labels: list[str]
    url: str
    updated_at: str
    metadata: dict[str, Any] | None
    parse_error: str | None

    @property
    def kind(self) -> str | None:
        return (self.metadata or {}).get("kind")


def fetch_issues(limit: int = 300) -> list[dict]:
    """Read every issue from the GitHub coordination surface via ``gh``."""
    command = ["gh", "issue", "list", "--limit", str(limit), "--state", "all", "--json", GH_FIELDS]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise ProjectionError(f"gh issue list failed ({result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


def build(raw_issues: list[dict], repository: str, now: str) -> dict:
    """Turn raw ``gh`` records into the projection document."""
    issues = {}
    for record in sorted(raw_issues, key=lambda r: r["number"]):
        parsed: dict | None = None
        error: str | None = None
        try:
            parsed = metadata.parse_body(record.get("body") or "")
        except metadata.MetadataError as exc:
            error = str(exc)
        issues[str(record["number"])] = {
            "number": record["number"],
            "title": record["title"],
            "state": record["state"],
            "labels": sorted(label["name"] for label in record.get("labels", [])),
            "url": record.get("url", ""),
            "updated_at": record.get("updatedAt", ""),
            "metadata": parsed,
            "parse_error": error,
        }
    return {
        "projection_schema": PROJECTION_SCHEMA,
        "note": "Derived view of the issue tree. Non-authoritative; refresh with sov_epic.py sync.",
        "source": {"repository": repository, "root_issue": ROOT_ISSUE},
        "synced_at": now,
        "issues": issues,
    }


def repository_name(runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> str:
    """Owner/name of the coordination surface, read from the git remote."""
    result = runner(
        ["git", "config", "--get", "remote.origin.url"], capture_output=True, text=True, check=False
    )
    url = (result.stdout or "").strip()
    if not url:
        return "unknown"
    return url.rsplit("/", 2)[-2] + "/" + url.rsplit("/", 1)[-1].removesuffix(".git")


def save(root: Path, document: dict) -> Path:
    """Write the projection with LF endings and a trailing newline."""
    path = root / PROJECTION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def load(root: Path) -> dict:
    """Read the checked-in projection."""
    path = root / PROJECTION_PATH
    if not path.exists():
        raise ProjectionError(f"{PROJECTION_PATH.as_posix()} is absent; run sov_epic.py sync")
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("projection_schema") != PROJECTION_SCHEMA:
        raise ProjectionError(f"unknown projection schema {document.get('projection_schema')!r}")
    return document


def issues(document: dict) -> dict[int, Issue]:
    """Projected issues keyed by number."""
    return {
        record["number"]: Issue(
            number=record["number"],
            title=record["title"],
            state=record["state"],
            labels=list(record["labels"]),
            url=record["url"],
            updated_at=record["updated_at"],
            metadata=record["metadata"],
            parse_error=record["parse_error"],
        )
        for record in document["issues"].values()
    }


def villages(root: Path) -> dict:
    """Read the village-to-domain routing table."""
    path = root / VILLAGES_PATH
    if not path.exists():
        raise ProjectionError(f"{VILLAGES_PATH.as_posix()} is absent")
    return json.loads(path.read_text(encoding="utf-8"))
