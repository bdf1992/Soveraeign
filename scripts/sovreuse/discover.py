"""What a fresh participant can read from the artifact about a result that stands.

Every read here is of a committed file under one root: the custody collection, the witness
record and receipts a member's `stage_observed_by` names, and the journal exports under
`nodes/`. Nothing reads the builder's session, a transcript, or the environment. A fact
that had to be read out of prose is reported as such, because a path embedded in a
sentence is discoverable only as long as the sentence keeps its shape. A malformed file
reads as a defect, never as a traceback.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re

from sovstanding import records

CUSTODY_COLLECTION = "contracts/custodies/phase-1-5.json"
NODES = "nodes"
WITNESS_PATH = re.compile(r"witness/[A-Za-z0-9_./-]+?\.(?:md|json)")
WITNESSED = "WITNESSED"


def _json(path: Path) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return document if isinstance(document, dict) else None


def _dicts(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def witnessed_members(root: Path, collection: str = CUSTODY_COLLECTION) -> list[dict[str, Any]]:
    """Every member the collection declares at `WITNESSED`, with the custody that holds it."""
    document = _json(root / collection) or {}
    return [{"custody_id": custody.get("custody_id"), "member": member}
            for custody in _dicts(document.get("custodies"))
            for member in _dicts(custody.get("members"))
            if member.get("standing") == WITNESSED]


def basis_addresses(member: dict[str, Any]) -> dict[str, Any]:
    """The witness record and receipts the member names, and how they had to be read.

    The custody schema has no evidence field, so the addresses live inside the free text
    of `stage_observed_by`. That is reported as `read_from: prose`: it works today and
    nothing guarantees it tomorrow.
    """
    addresses = WITNESS_PATH.findall(str(member.get("stage_observed_by") or ""))
    return {
        "record": [a for a in addresses if a.endswith(".md")],
        "receipts": [a for a in addresses if a.endswith(".json")],
        "read_from": "prose" if addresses else "none",
    }


def read_record(root: Path, address: str) -> dict[str, Any]:
    """The standing the record's own declaration block supports, read the gate's way."""
    path = root / address
    return {"address": address, "exists": path.is_file(),
            "standing_supported": records.supported_standing(path) if path.is_file() else None}


def read_receipt(root: Path, address: str) -> dict[str, Any]:
    """The machine-readable half of an observation, or the absence of one.

    `observed` pairs each observed address with its digest and is None when the receipt
    does not carry both lists at equal length: a receipt that names addresses without
    digests observed nothing this reader can measure.
    """
    document = _json(root / address)
    observed = document.get("observed") if document else None
    if not isinstance(observed, dict):
        return {"address": address, "exists": document is not None, "observed": None,
                "outside_head": None, "observer_relation": "", "standing_supported": None,
                "artifact_revision": None, "observer_id": None}
    node_state = observed.get("node_state")
    addresses = list(observed.get("observed_state_addresses") or [])
    digests = list(observed.get("observed_state_digests") or [])
    pairs = (dict(zip(addresses, digests))
             if addresses and len(addresses) == len(digests) else None)
    return {
        "address": address, "exists": True,
        "artifact_revision": _text(document.get("artifact_revision")),
        "observer_id": observed.get("observer_id"),
        "observer_relation": str(observed.get("observer_relation") or ""),
        "standing_supported": observed.get("standing_supported"),
        "observed": pairs,
        "outside_head": (_text(node_state.get("head_held_outside_the_export"))
                         if isinstance(node_state, dict) else None),
    }


def journals(root: Path, nodes: str = NODES) -> list[dict[str, Any]]:
    """Every journal export under `nodes/`, by the head each declares for itself."""
    found = []
    for path in sorted((root / nodes).glob("*/journal/*.json")):
        document = _json(path)
        if document is None:
            continue
        found.append({"node": path.parent.parent.name,
                      "address": path.relative_to(root).as_posix(),
                      "declared_head": document.get("head_digest"),
                      "entries": document.get("entry_count")})
    return found


def discover(root: Path, custody_id: str, collection: str = CUSTODY_COLLECTION) -> dict[str, Any]:
    """The result one custody carries at `WITNESSED`, and everything the artifact says about it.

    The journal joined to the result is the export whose declared head equals the head a
    witness receipt holds outside it; a journal nobody's receipt names is not reached.
    """
    members = [m for m in witnessed_members(root, collection) if m["custody_id"] == custody_id]
    if not members:
        return {"custody_id": custody_id, "member": None, "basis": None, "record": None,
                "receipts": [], "journal": None, "outside_head": None,
                "defects": [f"{custody_id} carries no member at {WITNESSED}"]}
    member = members[0]["member"]
    basis = basis_addresses(member)
    record = read_record(root, basis["record"][0]) if basis["record"] else None
    receipts = [read_receipt(root, address) for address in basis["receipts"]]
    heads = [r["outside_head"] for r in receipts if r["outside_head"]]
    outside_head = heads[-1] if heads else None
    journal = next((j for j in journals(root) if j["declared_head"] == outside_head), None)
    defects = []
    if record is None:
        defects.append("the member names no witness record")
    elif not record["exists"]:
        defects.append(f"witness record {record['address']} is absent")
    defects += [f"witness receipt {r['address']} is absent" for r in receipts if not r["exists"]]
    defects += [f"witness receipt {r['address']} observed no addresses this reader can measure"
                for r in receipts if r["exists"] and r["observed"] is None]
    return {"custody_id": custody_id, "member": member, "basis": basis, "record": record,
            "receipts": receipts, "journal": journal, "outside_head": outside_head,
            "defects": defects}
