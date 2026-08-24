#!/usr/bin/env python3
"""Read this node's identity and the peers it has admitted.

Every command reads checked-in files: ``contracts/fixtures/node-registry.reference.json``
for who this node is and whom it has admitted, and
``contracts/fixtures/seat-topology.reference.json`` for the seats it holds. Nothing here
contacts a peer, opens a socket, or admits anything. Federation is at proposal standing
and no transport is chosen, so an unattended run of this script stays inside
``RECORD_LOCAL`` by construction rather than by policy (decisions/0039).

Reading the registry settles nothing. A peer listed here was admitted by a local seat at
some point; that is a record of a judgement, not evidence that the peer is sound.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel.jsonschema import validate  # noqa: E402
from sovkernel.node_identity import registry_defects  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
REGISTRY_PATH = FIXTURES / "node-registry.reference.json"
TOPOLOGY_PATH = FIXTURES / "seat-topology.reference.json"
NODE_SCHEMA_PATH = CONTRACTS / "node-identity.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry() -> tuple[dict, list[dict], dict]:
    document = _load(REGISTRY_PATH)
    return document, document["nodes"], _load(TOPOLOGY_PATH)


def holder_defects(document: dict) -> list[str]:
    """Ways the registry document disagrees with the records inside it.

    Separate from ``command_validate`` so the check is reachable without running the
    command, and so a test can defeat it with a document rather than by editing the
    checked-in file.
    """
    nodes = document.get("nodes", [])
    holders = [node["node_id"] for node in nodes if node.get("relation") == "SELF"]
    declared = document.get("self_node")
    if not holders:
        return ["registry declares no node with relation SELF"]
    if len(holders) > 1:
        return [f"registry has {len(holders)} holders: {', '.join(sorted(holders))}"]
    if declared != holders[0]:
        return [f"registry declares self_node {declared} but {holders[0]} holds it"]
    return []


def command_status(_: argparse.Namespace) -> int:
    """Print this node's identity and its peer count."""
    document, nodes, _topology = _registry()
    holder = next((node for node in nodes if node["relation"] == "SELF"), None)
    peers = [node for node in nodes if node["relation"] == "PEER"]
    if holder is None:
        print("no node in the registry declares relation SELF")
        return 1
    print(f"node       {holder['node_id']} ({holder['display_name']})")
    print(f"root seat  {holder['root_seat']}")
    print(f"founded    {holder['founded_at']}")
    print(f"peers      {len(peers)}")
    if not peers:
        print("           none admitted; federation is a proposal and carries no transport")
    return 0


def command_peers(_: argparse.Namespace) -> int:
    """List every peer a local seat has admitted, with who admitted it and when."""
    _document, nodes, _topology = _registry()
    peers = sorted((node for node in nodes if node["relation"] == "PEER"),
                   key=lambda node: node["node_id"])
    for peer in peers:
        print(f"{peer['node_id']}\t{peer['display_name']}\t"
              f"admitted by {peer['admitted_by']} at {peer['known_since']}")
    if not peers:
        print("no peers admitted")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    """Check every record against its contract and the registry against the topology."""
    document, nodes, topology = _registry()
    schema = _load(NODE_SCHEMA_PATH)
    defects: list[str] = []
    for node in nodes:
        defects.extend(f"{node.get('node_id', '?')}: {defect}"
                       for defect in validate(node, schema))
    defects.extend(registry_defects(nodes, topology))
    defects.extend(holder_defects(document))
    for defect in defects:
        print(f"DEFECT: {defect}")
    if defects:
        print(f"FAIL: {len(defects)} defect(s) in {REGISTRY_PATH.relative_to(ROOT).as_posix()}")
        return 1
    print(f"PASS: {len(nodes)} node record(s); registry agrees with the seat topology")
    return 0 if not args.strict or not defects else 1


def build_parser() -> argparse.ArgumentParser:
    """Declare every command. Each one reads checked-in files and writes nothing."""
    parser = argparse.ArgumentParser(prog="sov_node", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help=command_status.__doc__)
    sub.add_parser("peers", help=command_peers.__doc__)
    validate_parser = sub.add_parser("validate", help=command_validate.__doc__)
    validate_parser.add_argument("--strict", action="store_true",
                                 help="exit non-zero on any defect")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return {"status": command_status, "peers": command_peers,
            "validate": command_validate}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
