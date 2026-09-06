"""Custody of a node's journal: export it under its own address, restore it, gate it.

A node's journal is the node's record. It leaves a host as the Record Service's own
self-verifying export, lives in the repository under `nodes/<node>/journal/<head>.json`,
and comes back onto another host by restore into an empty store, so the node's history
is one chain rather than a fresh genesis per host. A self-report that cites the journal
names the export by address and head and the entries it relies on by id; the gate here
checks that every such citation resolves, and that every export replays to the head its
filename carries. The head held outside any export belongs to a witness, not to this file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
RECORD_SRC = ROOT / "services" / "record" / "src"
if str(RECORD_SRC) not in sys.path:
    sys.path.insert(0, str(RECORD_SRC))

from soveraeign_record_service import custody  # noqa: E402
from soveraeign_record_service.core import GENESIS, RecordService  # noqa: E402

NODES = ROOT / "nodes"
REPORTS = ROOT / "reports" / "observations"
HEAD_PREFIX = 12


def export(state: Path, out_dir: Path) -> dict[str, Any]:
    """Export the journal at `state/record` to `out_dir/<head prefix>.json`."""
    service = RecordService(state / "record")
    try:
        document = custody.export_document(service)
    finally:
        service.close()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{document['head_digest'][:HEAD_PREFIX]}.json"
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"path": path, "head": document["head_digest"], "entries": document["entry_count"]}


def restore(export_path: Path, state: Path, expected_head: str | None = None) -> int:
    """Restore an export into the empty store at `state/record`; refuse anything else."""
    service = RecordService(state / "record")
    try:
        if service.head() != GENESIS:
            raise custody.RestoreRefused(f"{state / 'record'} already holds a journal")
        return custody.restore_file(service, export_path, expected_head=expected_head)
    finally:
        service.close()


def _relative(path: Path) -> str:
    """A path as a citation names it: repository-relative inside the repository."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _exports(nodes: Path) -> list[Path]:
    return sorted(nodes.glob("*/journal/*.json"))


def _grade_export(path: Path) -> tuple[str | None, list[str]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        head = custody.verify_export(document)
    except (OSError, ValueError, custody.RestoreRefused) as failure:
        return None, [f"{_relative(path)}: {failure}"]
    if not head.startswith(path.stem):
        return head, [f"{_relative(path)}: replays to {head[:HEAD_PREFIX]}, filename says "
                      f"{path.stem}"]
    return head, []


def _grade_citation(path: Path, report: dict[str, Any], heads: dict[str, str],
                    nodes: Path) -> list[str]:
    journal = report.get("journal")
    if not isinstance(journal, dict):
        return []
    address = str(journal.get("address") or "")
    export_path = ROOT / address
    defects: list[str] = []
    if address not in heads:
        return [f"{_relative(path)}: cites {address or '(no address)'}, which is not a verified "
                "export under nodes/"]
    if journal.get("head") != heads[address]:
        defects.append(f"{_relative(path)}: cites head {str(journal.get('head'))[:HEAD_PREFIX]} "
                       f"but {address} replays to {heads[address][:HEAD_PREFIX]}")
    ids = {entry["entry_id"] for entry in
           json.loads(export_path.read_text(encoding="utf-8"))["entries"]}
    missing = [item for item in report.get("cited_entries") or [] if item not in ids]
    if missing:
        defects.append(f"{_relative(path)}: cites entries absent from {address}: "
                       + ", ".join(missing[:5]))
    return defects


def grade(nodes: Path = NODES, reports: Path = REPORTS) -> tuple[list[str], dict[str, str]]:
    """Every export replays to its filename head; every citation into one resolves."""
    defects: list[str] = []
    heads: dict[str, str] = {}
    for path in _exports(nodes):
        head, found = _grade_export(path)
        defects.extend(found)
        if head is not None and not found:
            heads[_relative(path)] = head
    for path in sorted(reports.glob("*.json")) if reports.is_dir() else []:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(report, dict):
            defects.extend(_grade_citation(path, report, heads, nodes))
    return defects, heads
