#!/usr/bin/env python3
"""Read the Phase 1.5 opening packet and, only when explicitly asked, apply it.

`contracts/phase-1-5-opening.json` pins the exact definition bytes and the exit
clauses seat:root would open Phase 1.5 against. This script never opens the
phase on its own. With no arguments it recomputes every pinned digest against
the working tree and prints the exact change it would make to
`contracts/phases.json` and `STATUS.yaml`, writing nothing. `--apply` is the
only path that writes, and `--apply --dry-run` proves the write path is
computed correctly without touching the working tree, so the refusal and
preview paths stay trustworthy without ever exercising the live write.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, NamedTuple
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

PACKET_PATH = "contracts/phase-1-5-opening.json"
CUSTODIES_PACKET_PATH = "contracts/custodies-phase-1-5.json"
PHASES_PATH = "contracts/phases.json"
CUSTODIES_PATH = "contracts/custodies.json"
STATUS_PATH = "STATUS.yaml"

PREDECESSOR_PHASE_ID = "phase:i"
STATUS_LINE_BEFORE = "phase: NONE_ACTIVE"
STATUS_LINE_AFTER = "phase: phase:1-5"
NEXT_GATE_BEFORE = "next_gate: SUCCESSOR_PHASE_OPENING"
NEXT_GATE_AFTER = "next_gate: PHASE_1_5_OPERATIONAL_ACCEPTANCE"

REFUSALS = {
    "MISSING_DEFINITION_DOCUMENT": "a pinned definition document is absent from the repository",
    "UNPINNED_DEFINITION": "a pinned definition document's digest no longer matches the file, "
                           "so the exit this packet would open is not the exit on disk",
    "PHASE_ALREADY_RECORDED": "phase:1-5 already appears in contracts/phases.json",
    "PREDECESSOR_NOT_FOUND": "phase:i is absent from contracts/phases.json",
    "PREDECESSOR_ALREADY_SUCCEEDED": "phase:i already names a successor other than phase:1-5",
    "STATUS_PHASE_NOT_NONE_ACTIVE": "STATUS.yaml phase is not NONE_ACTIVE, so this packet no "
                                     "longer matches the state it was staged against",
    "STATUS_LINE_NOT_FOUND": "STATUS.yaml does not carry the exact line this packet expects to "
                              "replace",
    "CUSTODY_ALREADY_RECORDED": "a Phase 1.5 custody id already appears in contracts/custodies.json",
}


class Defect(NamedTuple):
    code: str
    detail: str


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def load_packet(root: Path = ROOT) -> dict[str, Any]:
    return _read_json(root / PACKET_PATH)


def load_custodies_packet(root: Path = ROOT) -> dict[str, Any]:
    return _read_json(root / CUSTODIES_PACKET_PATH)


def check_digests(root: Path, packet: dict[str, Any]) -> list[Defect]:
    """Recompute every pinned digest against the working tree."""
    defects: list[Defect] = []
    for pinned in packet.get("phase", {}).get("definition") or []:
        document = str(pinned.get("document"))
        path = root / document
        if not path.is_file():
            defects.append(Defect("MISSING_DEFINITION_DOCUMENT", document))
            continue
        actual = _digest(path)
        if actual != pinned.get("digest"):
            defects.append(Defect(
                "UNPINNED_DEFINITION",
                f"{document} now digests {actual}, pinned at {pinned.get('digest')}"))
    return defects


def check_target_state(root: Path, packet: dict[str, Any],
                        custodies_packet: dict[str, Any]) -> list[Defect]:
    """Refuse when the targets this packet would change no longer match its assumptions."""
    defects: list[Defect] = []
    phase_id = packet["phase"]["phase_id"]

    phases_doc = _read_json(root / PHASES_PATH)
    records = phases_doc.get("phases") or []
    if any(item.get("phase_id") == phase_id for item in records):
        defects.append(Defect("PHASE_ALREADY_RECORDED", phase_id))

    predecessor = next((item for item in records if item.get("phase_id") == PREDECESSOR_PHASE_ID),
                        None)
    if predecessor is None:
        defects.append(Defect("PREDECESSOR_NOT_FOUND", PREDECESSOR_PHASE_ID))
    elif predecessor.get("succeeded_by") not in (None, phase_id):
        defects.append(Defect("PREDECESSOR_ALREADY_SUCCEEDED",
                               f"{PREDECESSOR_PHASE_ID} names {predecessor.get('succeeded_by')}"))

    status_text = (root / STATUS_PATH).read_text(encoding="utf-8")
    status_lines = status_text.splitlines()
    if STATUS_LINE_BEFORE not in status_lines:
        defects.append(Defect("STATUS_PHASE_NOT_NONE_ACTIVE", STATUS_LINE_BEFORE))
    elif status_lines.count(STATUS_LINE_BEFORE) != 1:
        defects.append(Defect("STATUS_LINE_NOT_FOUND",
                               f"{STATUS_LINE_BEFORE!r} appears "
                               f"{status_lines.count(STATUS_LINE_BEFORE)} times"))

    custodies_doc = _read_json(root / CUSTODIES_PATH)
    existing_ids = {item.get("custody_id") for item in custodies_doc.get("custodies") or []}
    for custody in custodies_packet.get("custodies") or []:
        custody_id = custody.get("custody_id")
        if custody_id in existing_ids:
            defects.append(Defect("CUSTODY_ALREADY_RECORDED", str(custody_id)))

    return defects


def build_plan(root: Path, packet: dict[str, Any],
                custodies_packet: dict[str, Any]) -> dict[str, Any]:
    """Describe the exact change --apply would make, without reading target files twice."""
    phase_record = packet["phase"]
    return {
        "contracts/phases.json": {
            "append_phase": phase_record["phase_id"],
            "set": {f"phases[phase_id={PREDECESSOR_PHASE_ID}].succeeded_by":
                    phase_record["phase_id"]},
        },
        "STATUS.yaml": {
            "replace_line": {"from": STATUS_LINE_BEFORE, "to": STATUS_LINE_AFTER},
            "replace_next_gate": {"from": NEXT_GATE_BEFORE, "to": NEXT_GATE_AFTER},
        },
        "contracts/custodies.json": {
            "append_custodies": [item.get("custody_id")
                                  for item in custodies_packet.get("custodies") or []],
        },
    }


def apply_changes(root: Path, packet: dict[str, Any], custodies_packet: dict[str, Any],
                   dry_run: bool) -> None:
    """Perform the write --apply promises. Never called unless --apply was passed."""
    if dry_run:
        return

    phase_record = packet["phase"]
    phases_path = root / PHASES_PATH
    phases_doc = _read_json(phases_path)
    records = phases_doc.get("phases") or []
    for item in records:
        if item.get("phase_id") == PREDECESSOR_PHASE_ID:
            item["succeeded_by"] = phase_record["phase_id"]
    records.append(phase_record)
    phases_doc["phases"] = records
    _write_json(phases_path, phases_doc)

    status_path = root / STATUS_PATH
    status_text = status_path.read_text(encoding="utf-8")
    status_lines = status_text.splitlines()
    status_lines = [STATUS_LINE_AFTER if line == STATUS_LINE_BEFORE
                    else NEXT_GATE_AFTER if line == NEXT_GATE_BEFORE
                    else line
                    for line in status_lines]
    status_path.write_text("\n".join(status_lines) + "\n", encoding="utf-8", newline="\n")

    custodies_path = root / CUSTODIES_PATH
    custodies_doc = _read_json(custodies_path)
    custodies = custodies_doc.get("custodies") or []
    custodies.extend(custodies_packet.get("custodies") or [])
    custodies_doc["custodies"] = custodies
    _write_json(custodies_path, custodies_doc)


def run(root: Path, apply: bool, dry_run: bool) -> tuple[int, list[Defect], dict[str, Any]]:
    packet = load_packet(root)
    custodies_packet = load_custodies_packet(root)

    defects = check_digests(root, packet)
    if defects:
        return 1, defects, {}

    defects = check_target_state(root, packet, custodies_packet)
    if defects:
        return 1, defects, {}

    plan = build_plan(root, packet, custodies_packet)
    if apply:
        apply_changes(root, packet, custodies_packet, dry_run)
    return 0, [], plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true",
                        help="write contracts/phases.json, STATUS.yaml, and "
                             "contracts/custodies.json; the only path that writes")
    parser.add_argument("--dry-run", action="store_true",
                        help="with --apply, compute and print the write without touching disk")
    parser.add_argument("--json", action="store_true", help="print the plan as JSON")
    args = parser.parse_args(argv)

    code, defects, plan = run(ROOT, apply=args.apply, dry_run=args.dry_run)

    if defects:
        print("REFUSED: Phase 1.5 opening packet")
        for defect in defects:
            print(f"  {defect.code}: {REFUSALS.get(defect.code, '')} ({defect.detail})")
        return code

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    if args.apply and not args.dry_run:
        print("APPLIED: Phase 1.5 recorded in contracts/phases.json, STATUS.yaml set to "
              f"{STATUS_LINE_AFTER!r}, and its four custodies merged into "
              "contracts/custodies.json")
    elif args.apply and args.dry_run:
        print("DRY RUN: the following change was computed and nothing was written")
    else:
        print("PREVIEW: python scripts/sov_open_phase.py --apply would make this change; "
              "nothing was written")
    for target, change in plan.items():
        print(f"  {target}: {json.dumps(change, sort_keys=True)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
