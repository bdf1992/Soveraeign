"""Whether a skill vendored from another repository declares where it came from.

Presence, not recomputation. Recomputing the digest means reimplementing the
origin repository's rule here, and two implementations of one rule drift into
disagreeing about what a copy is. Verifying it is a DEPENDENCY_SEAM.
"""

from __future__ import annotations

from pathlib import Path
import re

#: The fields that make a vendored copy an accountable projection, not a fork.
FIELDS = ("author", "origin", "adopted", "verified", "artifact_digest")


def missing_fields(root: Path) -> list[tuple[str, list[str]]]:
    """(repo-relative path, missing fields) for each vendored skill that is short."""
    out = []
    for path in sorted((root / ".claude" / "skills").glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        if "bdos: true" not in text:
            continue
        missing = [f for f in FIELDS if not re.search(rf"^\s*{f}:", text, re.M)]
        if missing:
            out.append((str(path.relative_to(root)), missing))
    return out
