"""The committed half of a lease closure.

`decisions/0056` draws the line and then stores both sides on one side of it: "a session
record is host plumbing and holds no standing. A lease carries a grant reference and a
closure claim, so it is a governed record... They share storage. They do not share
standing." Storage under the common git directory was taken there as a default, recorded
as reversible, and chosen because it is where the readers already look.

Liveness belongs there and should stay: nineteen worktrees read one store, and committing
a heartbeat would be noise. A closure does not belong there alone. It carries a receipt
identifier, the evidence addresses behind the claim, and the standing reached, and the
common git directory travels with no clone, so a settled result is unreachable to every
participant that did not perform it. `reports/2026-09-08-commissioning-circuit-reconnaissance.md`
records a fresh participant finding a settled result only through hand-written prose.

So closure, and only closure, also writes a committed file here. This is evidence in the
same sense as `reports/observations/`, not a second authority: the lease log remains the
producer, and this file states what it recorded.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

SETTLEMENTS = Path("reports/settlements")
"""Committed settlement records, one file per closed lease, relative to the repository."""

RECORD_SCHEMA = "soveraeign-lease-settlement/v1"


def _slug(text: str) -> str:
    """Reduce a lease identifier to a filename-safe stem."""
    kept = [character if character.isalnum() else "-" for character in text.lower()]
    return "".join(kept).strip("-").replace("--", "-") or "lease"


def record(lease: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Build the settlement record for one closed lease.

    Reads only what the closure already established. It adds no claim of its own: the
    standing here is the standing the lease evaluator admitted, and the witness is
    whatever the closure named, including nothing.
    """
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    evidence = lease.get("closure_evidence") or {}
    holder = lease.get("holder") or {}
    concern = lease.get("concern") or {}
    closure = lease.get("closure") or {}
    grant = lease.get("grant") or {}
    return {
        "record_schema": RECORD_SCHEMA,
        "lease_id": lease.get("lease_id"),
        "concern": concern.get("reference"),
        "concern_kind": concern.get("kind"),
        "held_by": holder.get("principal_id"),
        "parent_lease": holder.get("parent_lease"),
        "definition": (holder.get("definition") or {}).get("definition_id"),
        "definition_provenance": (holder.get("definition") or {}).get("provenance"),
        "closure_condition": closure.get("condition"),
        "defeating_condition": closure.get("defeating_evidence"),
        "grant_id": grant.get("grant_id"),
        "effect_ceiling": grant.get("effect_ceiling"),
        "receipt_id": evidence.get("receipt_id"),
        "standing_reached": evidence.get("standing_reached"),
        "evidence_addresses": list(evidence.get("evidence_addresses") or []),
        "witnessed_by": evidence.get("witnessed_by"),
        "closed_at": moment.isoformat().replace("+00:00", "Z"),
    }


def write(lease: dict[str, Any], root: Path, *, now: datetime | None = None) -> Path | None:
    """Write the settlement record under `root`, returning the path, or None outside a tree.

    Returns None when `root` carries no `reports/` directory, so running a lease command
    from an unrelated checkout writes nothing rather than creating a stray tree.
    """
    if not (root / "reports").is_dir():
        return None
    entry = record(lease, now=now)
    directory = root / SETTLEMENTS
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{entry['closed_at'][:10]}-{_slug(str(entry['lease_id'] or 'lease'))}"
    path = directory / f"{stem}.json"
    path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path
