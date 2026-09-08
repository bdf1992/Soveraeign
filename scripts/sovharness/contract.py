"""Grade the grader's own coverage contract against what the grader actually does.

`contracts/harness-claims.json` exists to stop a green run being read as wider
assurance than it is. That only works if the contract is true, and the first
version was not: it said "two of the five claim kinds are derived" while
documenting six kinds and three derived, and it stated the PUBLIC-CLEARANCE
footprint as eight workflow prompts and three skills when the tree held twelve
files and fourteen occurrences, omitting `.claude/README.md` entirely.

Both were hand-written numbers about a population, which is the exact defect
class `scripts/sov_counts.py` grades in prose - and contract JSON is outside its
reach. An independent witness caught both; no check could have. So the contract's
own claims are now derived here: the kind set against the module's check
functions, the drift footprint against the tree.
"""

from __future__ import annotations

from pathlib import Path
import json
import subprocess


def _footprint(root: Path, term: str) -> tuple[list[str], int]:
    """Files and occurrences of a term under .claude/, from git's index."""
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], cwd=root, capture_output=True,
                              text=True).stdout
    files = sorted(git("grep", "-l", term, "--", ".claude/").split())
    occurrences = len(git("grep", "-o", term, "--", ".claude/").strip().splitlines())
    return files, occurrences


def check_contract(root: Path, kinds: set[str]) -> list[tuple[str, str]]:
    """Return (where, detail) for every claim the contract makes that is untrue.

    `kinds` is the set the module's check functions actually emit, passed in
    rather than imported, so this grades observed behaviour and not a second
    copy of the same list.
    """
    contract = json.loads((root / "contracts" / "harness-claims.json").read_text(
        encoding="utf-8"))
    coverage = contract["coverage"]
    # Every mapping under `coverage` describes kinds; `not_covered` is a list of
    # prose and describes none. Reading the block by shape rather than by a fixed
    # set of key names means removing a whole group - as withdrawing the two
    # phrase-list kinds did - does not silently stop the grading.
    declared = {kind for group in coverage.values() if isinstance(group, dict)
                for kind in group}
    defects = []

    missing = kinds - declared
    extra = declared - kinds
    if missing:
        defects.append(("contracts/harness-claims.json coverage",
                        f"the module emits {sorted(missing)}, which the contract does not "
                        f"describe; an ungraded kind is one a reader cannot size"))
    if extra:
        defects.append(("contracts/harness-claims.json coverage",
                        f"the contract describes {sorted(extra)}, which the module does not "
                        f"emit; a described kind that never runs reads as coverage"))

    for entry in contract.get("known_drift", []):
        stated = entry.get("footprint")
        if not stated:
            defects.append((f"contracts/harness-claims.json known_drift {entry['term']}",
                            "declares no footprint, so a reader cannot size what is "
                            "deliberately unenforced"))
            continue
        files, occurrences = _footprint(root, entry["term"])
        if [stated.get("files"), stated.get("occurrences")] != [len(files), occurrences]:
            defects.append((
                f"contracts/harness-claims.json known_drift {entry['term']}",
                f"states {stated.get('files')} files and {stated.get('occurrences')} "
                f"occurrences; the tree holds {len(files)} and {occurrences}"))
        elif sorted(stated.get("paths", [])) != files:
            defects.append((
                f"contracts/harness-claims.json known_drift {entry['term']}",
                f"the listed paths are not the {len(files)} files that cite it"))
    return defects
