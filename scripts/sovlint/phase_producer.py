"""Refuse a governing document that restates the repository's phase state.

`STATUS.yaml` and `contracts/phases.json` are the sole producer of the current
phase name, its `next_gate` value, and any live `succeeded_by` reading. A
document that repeats one of those as fact goes stale the moment the producer
moves, whether or not the document is otherwise about the phase - this is what
staled 54 unrelated clarity reviews the first time Phase 1.5 opened. The rule
holds regardless of which value is current, so a document can still be caught
quoting a reading that used to be true and no longer is.

Population is root-level `.md`/`.cursorrules` files only: the small set that
states repository-wide claims, as opposed to a service's or skill's own scoped
notes. `archives/` and `decisions/` are exempt because a historical statement
is the point there, and neither is root-level in any case.
"""

from __future__ import annotations

from pathlib import Path
import json
import re

STATUS_PATH = "STATUS.yaml"
PHASES_PATH = "contracts/phases.json"
EXEMPT_PREFIXES = ("archives/", "decisions/")


def is_governing_root_doc(relative: str) -> bool:
    """A file this check reads: root-level `.md` or `.cursorrules`, not the producer."""
    if relative in (STATUS_PATH, PHASES_PATH):
        return False
    if relative.startswith(EXEMPT_PREFIXES):
        return False
    if "/" in relative:
        return False
    return relative.endswith(".md") or relative == ".cursorrules"


def producer_tokens(root: Path) -> dict[str, str]:
    """The live values only `STATUS.yaml`/`contracts/phases.json` may state.

    Returns an empty mapping when either producer file is missing or
    unreadable, so a fixture tree with no phase state simply has nothing to
    check rather than crashing the run.
    """
    status = root / STATUS_PATH
    phases = root / PHASES_PATH
    if not status.is_file() or not phases.is_file():
        return {}
    status_text = status.read_text(encoding="utf-8")
    phase_id = _field(status_text, "phase")
    next_gate = _field(status_text, "next_gate")
    try:
        phases_data = json.loads(phases.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        phases_data = {}
    title = next(
        (entry.get("title") for entry in phases_data.get("phases", [])
         if entry.get("phase_id") == phase_id),
        None,
    )
    tokens = {}
    if phase_id:
        tokens["phase_id"] = phase_id
    if next_gate:
        tokens["next_gate"] = next_gate
    if title:
        tokens["short_title"] = title.split(" - ", 1)[0].strip()
    return tokens


def _field(status_text: str, name: str) -> str | None:
    match = re.compile(rf"(?m)^{name}:\s*(\S+)\s*$").search(status_text)
    return match.group(1) if match else None


def _patterns(tokens: dict[str, str]) -> list[tuple[str, re.Pattern[str]]]:
    patterns = []
    if phase_id := tokens.get("phase_id"):
        patterns.append((
            f"current phase name `{phase_id}`",
            re.compile(re.escape(phase_id)),
        ))
    if next_gate := tokens.get("next_gate"):
        patterns.append((
            f"current next_gate value `{next_gate}`",
            re.compile(re.escape(next_gate)),
        ))
    if short_title := tokens.get("short_title"):
        escaped = re.escape(short_title)
        patterns.append((
            f"current phase name `{short_title}`",
            re.compile(rf"{escaped}\s+is\s+open\b"),
        ))
        patterns.append((
            f"current phase name `{short_title}`",
            re.compile(rf"\bopened\s+{escaped}\b"),
        ))
    patterns.append((
        "STATUS.yaml's phase reading",
        re.compile(
            r"(?:STATUS\.yaml|contracts/phases\.json)`?\s+(?:currently\s+)?"
            r"(?:records|remains|reads?|states?|says?)\s+`[^`]{1,40}`",
            re.IGNORECASE,
        ),
    ))
    patterns.append((
        "a succeeded_by reading",
        re.compile(
            r"succeeded_by`?\s+(?:names?|is)?\s*`?(?:null|none|phase:[\w.-]+)",
            re.IGNORECASE,
        ),
    ))
    return patterns


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def defects(relative: str, text: str, tokens: dict[str, str]) -> list[str]:
    """One defect line per match, naming the file, line, and what it restated."""
    if not tokens or not is_governing_root_doc(relative):
        return []
    found = []
    for label, pattern in _patterns(tokens):
        match = pattern.search(text)
        if match:
            line = _line_number(text, match.start())
            found.append(
                f"{relative}:{line}: restates {label} as fact; "
                f"STATUS.yaml and contracts/phases.json are the producer"
            )
    return found
