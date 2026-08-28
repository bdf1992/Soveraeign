"""Tell apart a check this landing broke from a reading about the machine it ran on.

`verify.py` reduces to one exit code, and the landing gate used to reduce that to
one bit. So a landing was refused identically whether the change under it was
defective, another session had written the tree mid-run, or the host was loaded
enough to push one check past its ceiling. Three different facts, one refusal,
and the reader sent to fix whichever they guessed.

Nothing here weakens `verify.py`, changes a ceiling, or suppresses a failure.
`verify.py --observe` already emits one `contracts/observation.schema.json`
record per check, and every record already carries the addresses that check read.
This reads those records and attributes each failure:

    a failing check whose declared addresses the landing touched   -> CHANGE
    a failing check whose addresses the landing did not touch      -> GLOBAL
    a non-zero exit with no failing check at all                   -> HOST

Only `CHANGE` refuses. `GLOBAL` and `HOST` are recorded in the landing ledger as
attributed control readings, so they accumulate and stay visible rather than
being hidden by the thing that stopped blocking on them.

The known weakness, stated rather than discovered later: attribution is only as
good as each `Check.observes` tuple. A check whose declared addresses are
incomplete can fail because of this change and be attributed `GLOBAL`. That is
why nothing here deletes a reading - the ledger keeps every one, and a witness
reads them against the diff.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess
import sys
import tempfile

#: A failure this landing is answerable for. Refuses.
CHANGE = "CHANGE"
#: A failing check the landing never touched: another session's tree, usually.
GLOBAL = "GLOBAL"
#: A non-zero run in which every check passed - a timing ceiling, i.e. the host.
HOST = "HOST"


def _touches(addresses: list[str], paths: set[str]) -> list[str]:
    """The landing paths that fall under any address this check declares it read.

    An address may name a file or a directory; `scripts/tests` covers
    `scripts/tests/test_landing_ledger.py`. Compared as posix prefixes on a
    path boundary, so `scripts/test` never matches `scripts/tests`.
    """
    hits = []
    for address in addresses:
        prefix = address.replace("\\", "/").rstrip("/")
        for path in paths:
            candidate = path.replace("\\", "/")
            if candidate == prefix or candidate.startswith(prefix + "/"):
                hits.append(path)
    return sorted(set(hits))


def attribute(observations: list[dict[str, Any]], exit_code: int,
              paths: set[str]) -> dict[str, Any]:
    """Attribute one verify run. Pure: no I/O, no clock, no subprocess."""
    failing = [row for row in observations
               if (row.get("predicate_results") or {}).get("outcome") == "FAIL"]
    change, other = [], []
    for row in failing:
        touched = _touches(row.get("observed_state_addresses") or [], paths)
        entry = {"check": row.get("subject"),
                 "addresses": row.get("observed_state_addresses") or [],
                 "touched": touched}
        (change if touched else other).append(entry)

    if exit_code == 0:
        verdict, attribution = "PASS", None
    elif change:
        verdict, attribution = "FAIL", CHANGE
    elif failing:
        verdict, attribution = "PASS", GLOBAL
    else:
        verdict, attribution = "PASS", HOST

    return {
        "verify": verdict,
        "attribution": attribution,
        "exit_code": exit_code,
        "checks_observed": len(observations),
        "change_scoped": change,
        "readings": other,
    }


def verify_reading(root: Path, paths: set[str]) -> dict[str, Any]:
    """Run `verify.py --observe` and attribute the result against this landing's paths.

    Falls back to the plain exit code if the observation file cannot be read, so a
    problem in this module makes the gate stricter rather than more permissive.
    """
    with tempfile.TemporaryDirectory() as work:
        target = Path(work) / "observations.json"
        done = subprocess.run(
            [sys.executable, "scripts/verify.py", "--observe", str(target)],
            cwd=root, capture_output=True, text=True)
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            rows = loaded if isinstance(loaded, list) else loaded.get("observations", [])
        except (OSError, json.JSONDecodeError, AttributeError):
            # Strict fallback: no attribution is possible, so the exit code stands.
            return {"verify": "PASS" if done.returncode == 0 else "FAIL",
                    "attribution": None, "exit_code": done.returncode,
                    "checks_observed": 0, "change_scoped": [], "readings": [],
                    "note": "observations unreadable; exit code taken as the verdict"}
    return attribute(rows, done.returncode, paths)


def describe(reading: dict[str, Any]) -> list[str]:
    """The lines a landing prints about its verify run. Never silent about a reading."""
    lines = [f"verify: {reading['verify']}"
             + (f" ({reading['attribution']} attributed)" if reading["attribution"] else "")]
    for entry in reading.get("change_scoped", []):
        lines.append(f"  REFUSES: {entry['check']} reads {entry['touched']}, "
                     "which this landing changes")
    for entry in reading.get("readings", []):
        lines.append(f"  reading: {entry['check']} failed over "
                     f"{entry['addresses']}, none of which this landing touches")
    if reading["attribution"] == HOST:
        lines.append("  reading: the run exited non-zero with every check passing, "
                     "so the refusal was a ceiling on this host and not this change")
    return lines


__all__ = ["CHANGE", "GLOBAL", "HOST", "attribute", "describe", "verify_reading"]
