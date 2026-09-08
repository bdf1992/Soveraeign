"""Settled experience under one root, read as the basis a candidate Definition may cite.

Experience is settled here in the repository's own sense and no looser one: a custody
member that an independent participant observed (`standing: WITNESSED`) and that landed
(`work_state: LANDED`), together with the witness records and receipts its own
`stage_observed_by` names. A member that is merely built has not been judged by anyone
else, and a member that is witnessed but unlanded settled nothing, so neither is basis.

Every address is resolved to bytes under `root` and digested. An address a member names
that is not present is reported as a defect rather than skipped, because a basis that
silently shrinks is exactly what P15-Q4.1 exists to catch.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import re

CUSTODY_COLLECTION = "contracts/custodies/phase-1-5.json"
EVIDENCE_PATH = re.compile(r"(?:witness|reports)/[A-Za-z0-9_./-]+?\.(?:md|json)")
EVIDENCE_MARKERS = ("witness/", "reports/")
LANDED = "LANDED"
SETTLED_STANDINGS = ("WITNESSED", "RATIFIED")
"""Standings that mean an independent participant has judged the member. `RATIFIED` is
above `WITNESSED` on the lifecycle, so admitting only the exact token `WITNESSED` would
silently drop a member that a seat had since settled. Compared as whole tokens, never as
substrings: `NOT_WITNESSED` contains `WITNESSED` (`CLAUDE.md`, trap T3)."""


def digest(path: Path) -> str | None:
    """The sha256 at `path`, or None when nothing is readable there.

    A directory digests as its tree: every file under it, in sorted relative-path order,
    each contributing its path and its bytes. A member whose address is a service is then
    pinned by what the service contains, not merely by the fact that a directory exists.
    """
    if path.is_dir():
        rolling = sha256()
        for entry in sorted(path.rglob("*")):
            if not entry.is_file():
                continue
            rolling.update(str(entry.relative_to(path)).replace("\\", "/").encode("utf-8"))
            try:
                rolling.update(entry.read_bytes())
            except OSError:
                return None
        return rolling.hexdigest()
    try:
        return sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _members(collection: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every member of every custody in the collection, paired with its clause."""
    pairs: list[tuple[str, dict[str, Any]]] = []
    for custody in collection.get("custodies") or []:
        if not isinstance(custody, dict):
            continue
        clause = str(custody.get("exit_clause") or custody.get("custody_id") or "?")
        for member in custody.get("members") or []:
            if isinstance(member, dict):
                pairs.append((clause, member))
    return pairs


def gather(root: Path, collection_path: str = CUSTODY_COLLECTION) -> dict[str, Any]:
    """Read every settled member under `root` and the evidence each one's record names.

    Returns the settled sources with their digests, the clauses they came from, and the
    defects found. The reading is of committed files only; no session, transcript, or
    environment is consulted, so a second participant reproduces it from the artifact.
    """
    defects: list[str] = []
    try:
        collection = json.loads((root / collection_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as unreadable:
        return {"sources": [], "clauses": [], "defects": [f"{collection_path}: {unreadable}"],
                "collection": collection_path}
    sources: dict[str, dict[str, Any]] = {}
    clauses: set[str] = set()
    for clause, member in _members(collection):
        if member.get("standing") not in SETTLED_STANDINGS:
            continue
        if member.get("work_state") != LANDED:
            continue
        address = member.get("address")
        if not isinstance(address, str) or not address:
            defects.append(f"{clause}: a settled member declares no address")
            continue
        clauses.add(clause)
        observed_by = str(member.get("stage_observed_by") or "")
        named = EVIDENCE_PATH.findall(observed_by)
        if not named and any(marker in observed_by for marker in EVIDENCE_MARKERS):
            defects.append(f"{clause}: {address} names evidence under "
                           f"{' or '.join(EVIDENCE_MARKERS)} that this reader resolved none of, "
                           "so the basis it cites is smaller than the record it read")
        for candidate in [address] + named:
            found = digest(root / candidate)
            if found is None:
                defects.append(f"{clause}: {address} names {candidate}, which is not present")
                continue
            sources.setdefault(candidate, {"address": candidate, "digest": found,
                                           "clause": clause, "role":
                                           "member" if candidate == address else "evidence"})
    return {
        "sources": [sources[key] for key in sorted(sources)],
        "clauses": sorted(clauses),
        "defects": defects,
        "collection": collection_path,
    }
