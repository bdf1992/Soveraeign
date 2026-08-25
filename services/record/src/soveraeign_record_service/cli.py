"""The Record Service machine interface.

`AI-NATIVE.md` gates on reachability: a fresh model instance must discover the
state, the available operations, the required inputs and the returned result
through a stable declared path. Until this module existed the operational
System of Record had no such path. Everything that needed the journal imported
`core.py`, which meant every reader was inside the participant, and the witness
procedure declared on issue #7 could only be performed by the code being
witnessed.

Every command reads JSON arguments and writes one JSON object to stdout,
refusals included, so a caller never parses prose to learn what happened.
`operations` is the discovery command; it answers out of the service's own
manifest rather than out of this file, so the declared surface and the reachable
surface cannot drift apart silently.

Exit codes: 0 committed, 2 refused, 3 unknown record, 1 usage error.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import argparse
import json
import sys

from soveraeign_record_service.core import (
    BrokenChain,
    DesignRecordRefused,
    RecordService,
    UnknownEntry,
)

DEFAULT_ROOT = Path(".local") / "record"
# The service's own manifest. Discovery answers from it so that a command this
# CLI reaches and the manifest does not declare shows up as a defect rather than
# as a convenience.
MANIFEST = Path(__file__).resolve().parents[2] / "contracts" / "service.json"


def _emit(payload: dict[str, Any], code: int = 0) -> int:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return code


def _json_argument(raw: str | None, field: str) -> dict[str, Any]:
    """Read a JSON object argument, refusing anything that is not an object."""
    if raw is None:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a JSON object")
    return value


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def discover(_: RecordService, __: argparse.Namespace) -> dict[str, Any]:
    """Answer what may be done here, from the manifest the service declares."""
    manifest = _manifest()
    return {
        "service_id": manifest["service_id"],
        "standing": manifest["standing"],
        "operations": manifest["operations"],
        "local_refusals": manifest.get("local_refusals", {}),
        "forbids": manifest["forbids"],
        "authoritative": True,
        "note": "the journal is authoritative; every projection read here is not",
    }


def read_projection(service: RecordService, args: argparse.Namespace) -> dict[str, Any]:
    """Read one projection row, marked as derived on the way out.

    The row is rebuildable from the journal and carries no authority. Saying so in
    the payload is the difference between a caller that knows it holds a
    projection and one that discovers it later.
    """
    row = dict(service.projection(args.subject))
    row["authoritative"] = False
    row["rebuilt_from"] = "record-service-journal"
    return row


def reconstruct(service: RecordService, _: argparse.Namespace) -> dict[str, Any]:
    """Replay the journal, verifying every link, and return what verified."""
    entries = service.reconstruct()
    return {
        "entries": entries,
        "count": len(entries),
        "head": service.head(),
        "authoritative": True,
    }


def _commands() -> dict[str, Callable[[RecordService, argparse.Namespace], dict[str, Any]]]:
    return {
        "operations": discover,
        "append-entry": lambda s, a: s.append(
            a.kind, a.subject, a.actor, _json_argument(a.payload, "--payload"),
            a.source_address),
        "append-receipt": lambda s, a: s.receipt(
            a.outcome, a.event, a.subject, a.actor, _json_argument(a.detail, "--detail")),
        "counter-entry": lambda s, a: s.counter(a.entry, a.actor, a.reason),
        "read-entry": lambda s, a: s.entry(a.entry),
        "reconstruct-journal": reconstruct,
        "read-projection": read_projection,
        "drop-projections": lambda s, _: {"dropped": True, "authoritative": False},
        "rebuild-projections": lambda s, _: {"subjects": s.rebuild_projections(),
                                             "authoritative": False,
                                             "rebuilt_from": "record-service-journal"},
    }


def build_parser() -> argparse.ArgumentParser:
    """Declare every command and its required inputs."""
    parser = argparse.ArgumentParser(prog="soveraeign-record",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="journal store root (default .local/record)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("operations", help="discover legal operations and their required inputs")

    append = sub.add_parser("append-entry", help="append one entry to the journal")
    append.add_argument("--kind", required=True, choices=("EVENT", "RECEIPT",
                                                          "OBSERVATION", "COUNTER"))
    append.add_argument("--subject", required=True)
    append.add_argument("--actor", required=True)
    append.add_argument("--payload", help="entry payload as a JSON object")
    append.add_argument("--source-address", dest="source_address",
                        help="the address this entry came from, when it had one")

    receipt = sub.add_parser("append-receipt", help="append a terminal receipt")
    receipt.add_argument("--outcome", required=True)
    receipt.add_argument("--event", required=True)
    receipt.add_argument("--subject", required=True)
    receipt.add_argument("--actor", required=True)
    receipt.add_argument("--detail", help="receipt detail as a JSON object")

    counter = sub.add_parser("counter-entry",
                             help="counter an entry by appending; the original is untouched")
    counter.add_argument("--entry", required=True)
    counter.add_argument("--actor", required=True)
    counter.add_argument("--reason", required=True)

    entry = sub.add_parser("read-entry", help="read one entry by id")
    entry.add_argument("--entry", required=True)

    sub.add_parser("reconstruct-journal",
                   help="replay the journal, verifying every digest link")

    projection = sub.add_parser("read-projection", help="read one derived projection row")
    projection.add_argument("--subject", required=True)

    sub.add_parser("drop-projections", help="delete every projection; the journal is untouched")
    sub.add_parser("rebuild-projections", help="rebuild every projection from the journal alone")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = RecordService(args.root)
    try:
        if args.command == "drop-projections":
            service.drop_projections()
        return _emit(_commands()[args.command](service, args))
    # There is deliberately no handler for ProjectionNotAuthoritative. No command
    # here writes from a projection, so the refusal is unreachable through this
    # surface; the manifest's `forbids: projection-as-authority` is where the
    # prohibition is declared, and discovery is where an outside caller reads it.
    except DesignRecordRefused as refused:
        return _emit({"outcome": "REFUSED", "reason_code": "DESIGN_RECORD_REFUSED",
                      "message": str(refused)}, 2)
    except BrokenChain as broken:
        return _emit({"outcome": "REFUSED", "reason_code": "DIGEST_MISMATCH",
                      "message": f"the journal stops verifying at {broken}"}, 2)
    except UnknownEntry as missing:
        return _emit({"outcome": "REFUSED", "reason_code": "MISSING_PRECONDITION",
                      "message": f"no such record: {missing}"}, 3)
    except ValueError as invalid:
        return _emit({"outcome": "REFUSED", "reason_code": "MISSING_PRECONDITION",
                      "message": str(invalid)}, 2)
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
