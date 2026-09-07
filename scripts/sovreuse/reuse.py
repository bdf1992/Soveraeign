"""Reach the capability a result produced and use it, read for P15-Q3.2.

The capability the fresh-participation result produced is a node whose journal can be
brought back on any host: restore the export to the head the witness holds outside it,
then enter as a declared principal through the same probe the result is. Whether the node
admits that principal is the node's decision, read from its records; the reader reports
a refusal, it does not argue with one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import sys

from sovfresh import layers, node as nodelayer, probe
from sovnode import journal
from sovreuse import discover, settle

CONFORMANCE = Path(__file__).resolve().parents[2] / "conformance"
if str(CONFORMANCE) not in sys.path:
    sys.path.insert(0, str(CONFORMANCE))

import commissioning  # noqa: E402

PREDICATES = ("P15-Q3.1", "P15-Q3.2")
RESULT_CUSTODY = layers.EXIT_CUSTODY


def reach(root: Path, result: dict[str, Any], work_dir: Path) -> dict[str, Any]:
    """Restore the result's journal into an empty node under `work_dir`, or say why not."""
    export = result.get("journal")
    head = result.get("outside_head")
    if export is None or not head:
        reason = ("no witness receipt holds a head outside the export" if not head
                  else f"no export under nodes/ replays to {head[:12]}")
        return {"restored": None, "capability": None, "reason": reason}
    state = work_dir / "node"
    try:
        entries = journal.restore(root / export["address"], state, head)
    except journal.custody.RestoreRefused as refused:
        return {"restored": None, "capability": None, "reason": str(refused)}
    return {
        "restored": state, "reason": None, "entries": entries,
        "capability": (f"restore-journal {export['address']} to {head[:12]}, then "
                       f"{nodelayer.OPERATION} on the restored node"),
    }


def use(repo: Path, restored: Path, principal_id: str, work_dir: Path,
        registry: Path | None) -> dict[str, Any]:
    """Enter the restored node as the declared principal; read whether the crossing committed."""
    run = probe.run(repo, work_dir / "use", principal_id, registry=registry, node_state=restored)
    own = run["node"]["own"]
    return {"used": own.get("outcome") == "COMMITTED", "outcome": own.get("outcome"),
            "reason": run["node"].get("admitted") or own.get("reason"),
            "grant_id": run["observations"]["P15-Q1.3"]["identities"].get("grant_id"),
            "cleanup": run["observations"]["P15-Q1.2"]["work"]["cleanup_obligations"],
            "trace": run["trace"]}


def _not_attempted(reason: str) -> dict[str, Any]:
    return {"used": False, "outcome": None, "reason": reason, "grant_id": None,
            "cleanup": [], "trace": []}


def run(repo: Path, artifact: Path, work_dir: Path, principal_id: str, *,
        registry: Path | None = None, sessions_dir: Path | None = None,
        result_custody: str = RESULT_CUSTODY,
        collection: str = discover.CUSTODY_COLLECTION) -> dict[str, Any]:
    """One fresh discovery and reuse of the result `result_custody` carries.

    `artifact` is what the participant reads, and its git history is where the landing
    is read; `repo` is the repository whose product layers the participant runs. They
    are the same root in a live run and differ only under a fixture.
    """
    undeclared = layers.undeclared_inputs(registry is not None)
    trace: list[str] = []
    result = discover.discover(artifact, result_custody, collection)
    member = result.get("member") or {}
    trace.append(f"result {member.get('address') or 'NONE'} under {result_custody}; basis "
                 f"{(result.get('basis') or {}).get('read_from', 'none')}")
    settled = settle.readings(artifact, result, sessions_dir)
    facts = settled["facts"]
    trace.append(f"independence {facts['independence']}; revision "
                 f"{(facts['revision'] or 'NONE')[:12]}; drifted {facts['state']['drifted']}; "
                 f"landing {(facts['landing']['commit'] or 'NONE')[:12]}; inventory "
                 f"{settled['observation']['temporary_inventory_remaining']}")
    reached = reach(artifact, result, work_dir)
    trace.append(f"reach {reached['capability'] or reached['reason']}")
    used = _not_attempted("capability not reached")
    if reached["restored"] is not None:
        used = use(repo, reached["restored"], principal_id, work_dir, registry)
        trace.extend("  " + line for line in used["trace"])
    trace.append(f"use as {principal_id}: {used['outcome'] or 'NOT ATTEMPTED'} "
                 f"{used['reason'] or ''}".rstrip())
    record = result.get("record") or {}
    receipts = [r["address"] for r in result.get("receipts") or [] if r.get("exists")]
    observations = {
        "P15-Q3.1": settled["observation"],
        "P15-Q3.2": {
            "result_address": member.get("address"),
            "standing": record.get("standing_supported"),
            "basis": (f"{record['address']} at {facts['revision']}"
                      if record.get("exists") and facts["revision"] else None),
            "receipt_addresses": receipts,
            "capability": reached["capability"],
            "fresh_participant_used_result": used["used"],
            "oral_history_used": bool(undeclared),
        },
    }
    grades = {p: commissioning.evaluate(p, observations[p]) for p in PREDICATES}
    other = list(result.get("defects") or [])
    if member and member.get("standing") != record.get("standing_supported"):
        other.append(f"member declares {member.get('standing')}; the record supports "
                     f"{record.get('standing_supported')}")
    if (facts["work_state_declared"] == settle.LANDED
            and facts["work_state_derived"] != settle.LANDED):
        other.append("member declares LANDED; no merge on the current line carries it")
    if undeclared:
        other.append("undeclared environment inputs: " + ", ".join(undeclared))
    return {
        "principal": principal_id, "result_custody": result_custody, "result": result,
        "facts": facts, "reached": {k: v for k, v in reached.items() if k != "restored"},
        "used": {k: v for k, v in used.items() if k != "trace"},
        "observations": observations, "grades": grades, "other_defects": other,
        "passed": not any(grades.values()) and not other, "trace": trace,
    }
