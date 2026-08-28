"""Accumulate what every landing already knows, instead of printing it and forgetting it.

A landing runs `verify`, runs `lint`, and grades an independent observation. Those
three readings are the most reliable evidence this repository ever holds about a
change, and until now all three were printed to a terminal and discarded. The
result is a node that can produce 598 commits and 86 decisions while its
accumulating ledgers hold one, two, and one record: every run reports, nothing
appends.

This module appends one line per landing attempt, permitted or refused, and
carries the phase-gate reading taken at that moment. That last field is the
point. `predicates_covered` recorded per landing is what makes movement
computable from the ledger alone, so "commits since the floor moved" stops being
a number recomputed from git and becomes an attributable series: this landing
moved a predicate, that one did not.

It never refuses a landing. An accounting layer must not hold a veto over the
gate that owns the decision, and a ledger that can block a merge would be a
second authority. Every failure here returns one line and lets the landing
proceed. That discipline is taken verbatim from `scripts/sovland/attest.py`,
which reached it first for peer evidence and has not landed.

Recording a landing settles nothing. The ledger is a projection of what
happened, never a claim that it was correct.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import sys

LEDGER_SCHEMA = "soveraeign-landing-ledger/v1"
LEDGER_PATH = Path(".local") / "landing" / "ledger.ndjson"

#: Outcomes a landing attempt can reach. `REFUSED_AUTHORITY` is the grant saying no;
#: `REFUSED_PREFLIGHT` is a guard between the verdict and the merge saying no. They
#: are kept apart because they route the reader to different repairs.
LANDED = "LANDED"
REFUSED_AUTHORITY = "REFUSED_AUTHORITY"
REFUSED_PREFLIGHT = "REFUSED_PREFLIGHT"


def _now() -> str:
    """This instant, spelled the way the sibling ledgers spell timestamps."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ledger_path(root: Path) -> Path:
    """Where the landing ledger lives, beside the acceptance and peer ledgers."""
    return root / LEDGER_PATH


def _gate_reading(root: Path) -> dict[str, Any]:
    """The phase gate as it reads at this landing, or why it could not be read.

    Costs about 40 ms and reads files this landing has already touched. It is
    taken here rather than derived later because a reading taken afterwards
    cannot say which landing it belonged to.

    The distinction this field does not blur: `predicates_covered` counts
    predicates that carry a declared positive and defeating fixture. It is a
    count of declarations, not of observed runs, and a ledger that recorded it as
    "evidence" would repeat the error this module exists to correct.
    """
    try:
        scripts = str(root / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)
        import sov_f2_gate

        gate = sov_f2_gate.read_gate()
        return {
            "reading": "DECLARED_FIXTURE_COVERAGE",
            "predicates_covered": gate["predicates_covered"],
            "predicates_total": gate["predicates_total"],
            "closed": gate["closed"],
            "open_predicates": sorted(row["id"] for row in gate["open"]),
        }
    except Exception as error:  # noqa: BLE001 - see the module docstring
        return {"reading": "UNREAD", "why": f"{type(error).__name__}: {error}"}


def _observation(request: dict[str, Any]) -> dict[str, Any] | None:
    """The observation this landing offered, reduced to what the ledger keeps.

    Addresses and verdicts, never the observation body. Context hygiene: the
    ledger records where the evidence is, not a second copy of it.
    """
    observation = (request.get("evidence") or {}).get("observation")
    if not observation:
        return None
    return {
        "observer_id": observation.get("observer_id"),
        "verdict": observation.get("verdict"),
        "contributed_to_build": bool(observation.get("contributed_to_build")),
        "observation_id": observation.get("observation_id"),
    }


def build_record(root: Path, request: dict[str, Any], result: dict[str, Any],
                 branch: str, outcome: str, *, merge_commit: str | None = None,
                 refusal_detail: str | None = None) -> dict[str, Any]:
    """One landing, as the ledger keeps it. Pure: no clock beyond `recorded_at`, no I/O."""
    record: dict[str, Any] = {
        "ledger_schema": LEDGER_SCHEMA,
        "recorded_at": _now(),
        "outcome": outcome,
        "actor_id": request.get("actor_id"),
        "capability": request.get("capability"),
        "effect_class": request.get("effect_class"),
        "from_branch": branch,
        "target_branch": request.get("branch"),
        "verdict": result.get("verdict"),
        "grant_id": result.get("grant_id"),
        "refusal_code": result.get("code"),
        "refusal_detail": refusal_detail or (result.get("detail") if result.get("code") else None),
        "paths": list(request.get("paths") or []),
        "checks": dict((request.get("evidence") or {}).get("checks") or {}),
        "observation": _observation(request),
        "spend": request.get("spend"),
        "merge_commit": merge_commit,
        "goal": _gate_reading(root),
    }
    body = json.dumps({k: v for k, v in record.items() if k != "recorded_at"},
                      sort_keys=True, separators=(",", ":"))
    record["landing_id"] = "landing_" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return record


def record(root: Path, request: dict[str, Any], result: dict[str, Any], branch: str,
           outcome: str, *, merge_commit: str | None = None,
           refusal_detail: str | None = None, dry: bool = False) -> str:
    """Append this landing and return the line to print. Never raises, never refuses.

    Under ``dry`` it reports the reading it would append and writes nothing, so
    ``plan`` keeps its promise to change nothing while still showing what a real
    landing would record.
    """
    try:
        entry = build_record(root, request, result, branch, outcome,
                             merge_commit=merge_commit, refusal_detail=refusal_detail)
        goal = entry["goal"]
        if goal["reading"] == "UNREAD":
            reading = "gate unread"
        else:
            reading = f"{goal['predicates_covered']}/{goal['predicates_total']} declared"
        if dry:
            return f"landing ledger: would record {outcome} at {reading}"
        path = ledger_path(root)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return f"landing ledger: recorded {entry['landing_id']} {outcome} at {reading}"
    except Exception as error:  # noqa: BLE001 - see the module docstring
        return f"landing ledger: not recorded ({type(error).__name__}: {error})"


def load(root: Path) -> list[dict[str, Any]]:
    """Every landing recorded here, oldest first. A malformed line is skipped, not fatal."""
    path = ledger_path(root)
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def movement(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """What the ledger says about goal movement, and what it costs to say it.

    This is the reading the controller acts on. It answers one question: has the
    declared predicate set moved since the last landing that moved it, and how
    much landing activity has happened since.

    It reports. It refuses nothing. Making a stall refuse a landing is a policy
    change that belongs to Bdo and to a decision record, not to the module that
    first made the stall visible.
    """
    covered = [entry for entry in entries
               if (entry.get("goal") or {}).get("reading") != "UNREAD"]
    if not covered:
        return {"state": "NO_READING", "landings": len(entries)}

    latest = covered[-1]["goal"]
    last_move_index = None
    for index in range(len(covered) - 1, 0, -1):
        if covered[index]["goal"]["predicates_covered"] != \
                covered[index - 1]["goal"]["predicates_covered"]:
            last_move_index = index
            break

    since = len(covered) - 1 - last_move_index if last_move_index is not None else len(covered) - 1
    landed_since = sum(1 for entry in covered[(last_move_index or 0):]
                       if entry.get("outcome") == LANDED)
    spend_since = sum((entry.get("spend") or {}).get("amount", 0) or 0
                      for entry in covered[(last_move_index or 0):])
    return {
        "state": "MOVED" if since == 0 and last_move_index is not None else "NO_GOAL_DELTA",
        "predicates_covered": latest["predicates_covered"],
        "predicates_total": latest["predicates_total"],
        "open_predicates": latest.get("open_predicates", []),
        "landings": len(entries),
        "landings_since_movement": landed_since,
        "readings_since_movement": since,
        "spend_since_movement": spend_since,
        "ever_moved": last_move_index is not None,
    }


__all__ = ["LANDED", "REFUSED_AUTHORITY", "REFUSED_PREFLIGHT", "build_record",
           "ledger_path", "load", "movement", "record"]
