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
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
RECORD_SRC = ROOT / "services" / "record" / "src"
if str(RECORD_SRC) not in sys.path:
    sys.path.insert(0, str(RECORD_SRC))

from soveraeign_record_service import custody  # noqa: E402
from soveraeign_record_service.core import GENESIS, RecordService  # noqa: E402
from soveraeign_record_service.errors import BrokenChain  # noqa: E402

NODES = ROOT / "nodes"
REPORTS = ROOT / "reports" / "observations"
NODE_REGISTRY = ROOT / "contracts" / "fixtures" / "node-registry.reference.json"
HEAD_PREFIX = 12
ID_KEYS = ("entry_id", "receipt_id")
"""Keys whose string values in a self-report must name entries of the cited export."""


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
    """Restore an export into the empty store at `state/record`; refuse anything else.

    A refused restore leaves nothing behind that was not there before: the store the
    service opens to check its head is removed again when this call created it.
    """
    store = state / "record"
    existed = store.exists()
    service = RecordService(store)
    try:
        if service.head() != GENESIS:
            raise custody.RestoreRefused(f"{store} already holds a journal")
        return custody.restore_file(service, export_path, expected_head=expected_head)
    except custody.RestoreRefused:
        service.close()
        if not existed:
            shutil.rmtree(store, ignore_errors=True)
        raise
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


def _node_id_of(directory: str) -> str:
    """`nodes/node-local` names `node:local`: the first dash stands for the colon."""
    return directory.replace("-", ":", 1)


def _registered_nodes() -> set[str]:
    try:
        document = json.loads(NODE_REGISTRY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    return {str(node.get("node_id")) for node in document.get("nodes", [])}


def _grade_export(path: Path, registered: set[str]) -> tuple[str | None, list[str]]:
    """Replay one export; its filename, its directory and its node identity must agree."""
    shown = _relative(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        head = custody.verify_export(document)
    except (OSError, ValueError, custody.RestoreRefused, BrokenChain) as failure:
        return None, [f"{shown}: {failure}"]
    defects: list[str] = []
    if not head.startswith(path.stem):
        defects.append(f"{shown}: replays to {head[:HEAD_PREFIX]}, filename says {path.stem}")
    expected = _node_id_of(path.parent.parent.name)
    carried = {str(entry["payload"].get("node_id")) for entry in document["entries"]
               if isinstance(entry.get("payload"), dict) and entry["payload"].get("node_id")}
    if carried and carried != {expected}:
        defects.append(f"{shown}: entries name node {', '.join(sorted(carried))}, the directory "
                       f"names {expected}")
    if expected not in registered:
        defects.append(f"{shown}: {expected} is not in the node registry")
    return head, defects


def _ids_in(value: Any) -> set[str]:
    """Every entry or receipt id a self-report mentions, wherever it mentions it."""
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in ID_KEYS and isinstance(item, str) and item:
                found.add(item)
            else:
                found |= _ids_in(item)
    elif isinstance(value, list):
        for item in value:
            found |= _ids_in(item)
    return found


def _grade_citation(path: Path, report: dict[str, Any], heads: dict[str, str]) -> list[str]:
    journal = report.get("journal")
    if not isinstance(journal, dict):
        return []
    address = str(journal.get("address") or "")
    shown = _relative(path)
    if address not in heads:
        return [f"{shown}: cites {address or '(no address)'}, which is not a verified export "
                "under nodes/"]
    defects: list[str] = []
    if journal.get("head") != heads[address]:
        defects.append(f"{shown}: cites head {str(journal.get('head'))[:HEAD_PREFIX]} but "
                       f"{address} replays to {heads[address][:HEAD_PREFIX]}")
    export = json.loads((ROOT / address).read_text(encoding="utf-8"))
    if "entries" in journal and journal["entries"] != export["entry_count"]:
        defects.append(f"{shown}: cites {journal['entries']} entries, the export carries "
                       f"{export['entry_count']}")
    ids = {entry["entry_id"] for entry in export["entries"]}
    mentioned = set(report.get("cited_entries") or []) | _ids_in(report)
    missing = sorted(item for item in mentioned if item not in ids)
    if missing:
        defects.append(f"{shown}: names entries absent from {address}: " + ", ".join(missing[:5]))
    return defects


def grade(nodes: Path = NODES, reports: Path = REPORTS) -> tuple[list[str], dict[str, str]]:
    """One export per node replaying to its head; every citation into it resolves."""
    defects: list[str] = []
    heads: dict[str, str] = {}
    registered = _registered_nodes()
    per_node: dict[str, list[str]] = {}
    for path in _exports(nodes):
        head, found = _grade_export(path, registered)
        defects.extend(found)
        per_node.setdefault(path.parent.parent.name, []).append(_relative(path))
        if head is not None and not found:
            heads[_relative(path)] = head
    for node, paths in per_node.items():
        if len(paths) > 1:
            defects.append(f"nodes/{node}: a node has one head; found {len(paths)} exports: "
                           + ", ".join(paths))
    for path in sorted(reports.glob("*.json")) if reports.is_dir() else []:
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(report, dict):
            defects.extend(_grade_citation(path, report, heads))
    return defects, heads
