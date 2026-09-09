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
import hashlib
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


class SettlementRefused(RuntimeError):
    """A settlement record cannot be written without destroying one already there."""


def _comparable(entry: dict[str, Any]) -> dict[str, Any]:
    """The record without its timestamp, so a re-run compares as the same settlement."""
    return {key: value for key, value in entry.items() if key != "closed_at"}



DATED = "[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"
"""The date shape a settlement filename opens with, anchored so a glob cannot slide."""


def _mark(lease_id: Any) -> str:
    """Eight hex of the lease identifier, so two ids that slug alike do not share a file.

    `_slug` is not injective: `lease:concern-a` and `lease:concern/a` both reduce to
    `lease-concern-a`, and without this the second settlement overwrote the first.
    """
    return hashlib.sha256(str(lease_id).encode("utf-8")).hexdigest()[:8]


def _recorded(directory: Path, slug: str, lease_id: Any) -> tuple[Path | None, dict[str, Any]]:
    """Find the record already standing for this lease, whatever date it carries.

    Anchored to the date shape and confirmed against the record's own `lease_id`. An
    unanchored `*-{slug}.json` matched other leases: `lease:concern-b-lease-concern-a`
    ends with `-lease-concern-a`, so closing it left `lease:concern-a` permanently
    unclosable behind a refusal naming the wrong record. Matching the filename is a
    guess; reading the identifier is the check.
    """
    for candidate in sorted(directory.glob(f"{DATED}-{slug}-{_mark(lease_id)}.json")):
        try:
            standing = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise SettlementRefused(
                f"{candidate.name} is not readable JSON ({error.msg} at line {error.lineno}); "
                "a settlement cannot be compared against a record that cannot be parsed"
            ) from None
        if standing.get("lease_id") == lease_id:
            return candidate, standing
    return None, {}


def write(lease: dict[str, Any], root: Path, *, now: datetime | None = None) -> Path | None:
    """Write the settlement record under `root`, returning the path, or None outside a tree.

    Returns None when `root` carries no `reports/` directory, so running a lease command
    from an unrelated checkout writes nothing rather than creating a stray tree.

    Refuses to replace a record that already stands for this lease and says something
    different. A closure is a governed claim, and `AGENTS.md` has retraction add a
    counter-record rather than erase the original; overwriting one settlement's receipt
    and evidence addresses with another's is that erasure. A re-run of the same closure
    is not: an identical record apart from its timestamp returns the existing path
    unchanged, so a close retried after a partial failure is idempotent.
    """
    if not (root / "reports").is_dir():
        return None
    entry = record(lease, now=now)
    directory = root / SETTLEMENTS
    directory.mkdir(parents=True, exist_ok=True)
    slug = _slug(str(entry["lease_id"] or "lease"))
    path = directory / f"{entry['closed_at'][:10]}-{slug}-{_mark(entry['lease_id'])}.json"
    held, standing = _recorded(directory, slug, entry["lease_id"])
    if held is not None:
        path = held
        if _comparable(standing) == _comparable(entry):
            return path
        raise SettlementRefused(
            f"{path.relative_to(root).as_posix()} already records a different settlement "
            f"for {entry['lease_id']} (receipt {standing.get('receipt_id')!r}, this close "
            f"carries {entry['receipt_id']!r}). A closure is not amended in place: retract "
            "with a counter-record, or close a successor lease."
        )
    path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def record_closure(lease: dict[str, Any], root: Path) -> tuple[Path | None, dict[str, str] | None]:
    """Write the closure's committed record, or return the defect that refuses the close.

    The caller appends the closure to the lease log only when this returns no defect, so
    a failure here leaves the lease held and nothing recorded in either place.
    """
    try:
        return write(lease, root), None
    except SettlementRefused as refusal:
        return None, {"code": "SETTLEMENT_ALREADY_RECORDED", "message": str(refusal)}
    except OSError as error:
        return None, {"code": "SETTLEMENT_UNWRITABLE",
                      "message": f"{type(error).__name__}: {error.strerror or 'write failed'}"
                                 f" under {SETTLEMENTS.as_posix()}. The lease is still "
                                 "held; nothing was recorded."}
