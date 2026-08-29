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
    a failing check demonstrably failing over another session's
      concurrent edit                                              -> GLOBAL
    a non-zero exit with no failing check at all                   -> HOST
    any other failing check                                        -> CHANGE

Only `CHANGE` refuses. `GLOBAL` and `HOST` are recorded in the landing ledger as
attributed control readings, so they accumulate and stay visible rather than
being hidden by the thing that stopped blocking on them.

`GLOBAL` needs positive evidence, which is the correction soveraeign-fc's
observation of 1f27591 forced. The first version read the absence of a declared
overlap as proof the landing was innocent, and that is not proof: the check
"bootstrap and locked evidence" declares `observes` as
`("scripts/verify_bootstrap.py",)` while the script it runs reads a list of more
than twenty required files. A landing that deleted `AGENT-BOOTSTRAP-PROMPT.md`
made that check fail naming the deleted file, and this module attributed it
`GLOBAL` and permitted the landing. Incomplete as committed - no rename, no
drift, no elapsed time needed - and that file really did vanish from the shared
tree the same night with nobody able to say who removed it.

So the two permissive readings are now the two Bdo's ruling actually named, each
resting on something observed rather than on something not found: `HOST` on every
check having passed, `GLOBAL` on another session's uncommitted edit sitting
inside what the failing check declares it read. A failure this module cannot
positively account for refuses, which makes an incomplete `observes` tuple cost a
landing instead of silently buying one.

The known weakness, stated rather than discovered later: attribution is only as
good as each `Check.observes` tuple, and nothing anywhere grades a tuple against
what its check actually reads. `verify.py` does one thing with `observes` - it
drops any address that does not exist on disk - so a check whose observed path
was renamed quietly observes less, and a check whose implementation grows past
its declared addresses never notices. Either way the check fails over paths this
landing did touch, gets attributed `GLOBAL`, and stops refusing.

The reason that is worse than an ordinary bug: the failure mode is silence, not a
wrong answer. Nothing prints, so a drifted tuple can attribute `GLOBAL` forever
with no one finding out. Asserting `observes` against the paths a check touches,
even roughly, would convert a permanent blind spot into a maintained one; it is
not done here, and until it is, this paragraph is the whole of the defence.

That is why nothing here deletes a reading - the ledger keeps every one, and a
witness reads them against the diff. Credit for widening this from "incomplete
addresses" to "undetectable drift": soveraeign-df, reading the module cold.
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
              paths: set[str], foreign: set[str] | None = None) -> dict[str, Any]:
    """Attribute one verify run. Pure: no I/O, no clock, no subprocess.

    `paths` is what this landing carries. `foreign` is what some other participant
    has left uncommitted in the tree and this landing does not carry - the positive
    evidence a `GLOBAL` reading rests on. Omitting `foreign` means no failure can be
    shown to be somebody else's, so every failing check attributes `CHANGE`; an
    absent argument makes the gate stricter, never looser.
    """
    failing = [row for row in observations
               if (row.get("predicate_results") or {}).get("outcome") == "FAIL"]
    change, external = [], []
    for row in failing:
        addresses = row.get("observed_state_addresses") or []
        touched = _touches(addresses, paths)
        elsewhere = _touches(addresses, foreign or set())
        entry = {"check": row.get("subject"), "addresses": addresses,
                 "touched": touched, "foreign": elsewhere}
        # Touched wins over foreign. A check reading both this landing's paths and
        # another session's is a failure this landing may have caused, and the
        # reading that refuses is the one to keep.
        (change if touched or not elsewhere else external).append(entry)

    if exit_code == 0:
        verdict, attribution = "PASS", None
    elif change:
        verdict, attribution = "FAIL", CHANGE
    elif external:
        verdict, attribution = "PASS", GLOBAL
    else:
        verdict, attribution = "PASS", HOST

    return {
        "verify": verdict,
        "attribution": attribution,
        "exit_code": exit_code,
        "checks_observed": len(observations),
        "change_scoped": change,
        "readings": external,
    }


def foreign_paths(root: Path, paths: set[str]) -> set[str]:
    """What some other participant has left uncommitted here and this landing omits.

    This is the whole evidential basis for a `GLOBAL` reading, so it is read from
    git rather than from anybody's report. A path this landing carries is never
    foreign, however dirty it is: the landing is answerable for its own files.

    Failing to read git returns the empty set, which attributes every failure to
    the change. That is the strict direction on purpose.
    """
    done = subprocess.run(["git", "status", "--porcelain", "-z"],
                          cwd=root, capture_output=True, text=True)
    if done.returncode != 0:
        return set()
    dirty = set()
    for entry in done.stdout.split("\0"):
        if len(entry) > 3:
            # Porcelain v1: two status columns, a space, then the path. A rename
            # carries "old -> new" but -z splits those into separate entries, so
            # the path is always the whole remainder.
            dirty.add(entry[3:].replace("\\", "/").rstrip("/"))
    return {p for p in dirty if p not in {q.replace("\\", "/") for q in paths}}


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
    return attribute(rows, done.returncode, paths, foreign_paths(root, paths))


def describe(reading: dict[str, Any]) -> list[str]:
    """The lines a landing prints about its verify run. Never silent about a reading."""
    lines = [f"verify: {reading['verify']}"
             + (f" ({reading['attribution']} attributed)" if reading["attribution"] else "")]
    for entry in reading.get("change_scoped", []):
        if entry["touched"]:
            lines.append(f"  REFUSES: {entry['check']} reads {entry['touched']}, "
                         "which this landing changes")
    for entry in reading.get("change_scoped", []):
        if not entry["touched"]:
            lines.append(f"  REFUSES: {entry['check']} failed over {entry['addresses']}, "
                         "and nothing shows the failure belongs to another participant; "
                         "an unattributable failure refuses rather than passing")
    for entry in reading.get("readings", []):
        lines.append(f"  reading: {entry['check']} failed over {entry['addresses']}, "
                     f"which another participant is holding uncommitted "
                     f"({entry['foreign']}) and this landing does not carry")
    if reading["attribution"] == HOST:
        lines.append("  reading: the run exited non-zero with every check passing, "
                     "so the refusal was a ceiling on this host and not this change")
    return lines


__all__ = ["CHANGE", "GLOBAL", "HOST", "attribute", "describe", "verify_reading"]
