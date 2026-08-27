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

from soveraeign_record_service import custody
from soveraeign_record_service.core import (
    BrokenChain,
    DesignRecordRefused,
    ProfileNotAdopted,
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
        "export-journal": export_journal,
        "verify-export": verify_export_file,
        "restore-journal": restore_journal,
        "adopt-profile": adopt_profile,
    }


def adopt_profile(service: RecordService, args: argparse.Namespace) -> dict[str, Any]:
    """Move this store onto a newer chain profile, or report where it stands.

    Without `--to`, this reads and writes nothing: an operator asking what a store
    writes should not have to change it to find out. With `--to`, the returned
    entry is the first row under the new profile, and therefore the exact point an
    older reader stops verifying.
    """
    if not args.to:
        return {"writing_profile": service.writing_profile(), "adopted": False}
    entry = service.adopt_profile(args.to, args.actor)
    return {"writing_profile": service.writing_profile(), "adopted": True,
            "entry_id": entry["entry_id"], "supersedes": entry["payload"]["superseded"],
            "older_readers_stop_here": entry["entry_id"]}


def export_journal(service: RecordService, args: argparse.Namespace) -> dict[str, Any]:
    """Write a self-verifying export, or refuse if the journal does not verify first."""
    if args.out:
        return custody.write_export(service, args.out)
    return custody.export_document(service)


def verify_export_file(service: RecordService, args: argparse.Namespace) -> dict[str, Any]:
    """Replay an export's chain without touching this store."""
    document = json.loads(Path(args.export).read_text(encoding="utf-8"))
    return {"head": custody.verify_export(document, expected_head=args.expect_head),
            "entries": len(document.get("entries", [])), "verified": True}


def restore_journal(service: RecordService, args: argparse.Namespace) -> dict[str, Any]:
    """Replay an export into an empty store; a store holding a journal is refused."""
    return custody.restore_file(service, args.export)


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

    export = sub.add_parser("export-journal",
                            help="write a self-verifying export of the whole journal")
    export.add_argument("--out", type=Path,
                        help="write the export here; omitted, it is printed")

    verify = sub.add_parser("verify-export",
                            help="replay an export's chain without touching this store")
    verify.add_argument("--export", type=Path, required=True)
    verify.add_argument("--expect-head", dest="expect_head",
                        help="fail unless the replayed head is this digest")

    restore = sub.add_parser("restore-journal",
                             help="replay an export into an empty store")
    restore.add_argument("--export", type=Path, required=True)

    adopt = sub.add_parser("adopt-profile",
                           help="report which chain profile this store writes, or move it")
    adopt.add_argument("--to", help="the profile to adopt; omit to only report")
    adopt.add_argument("--actor", default="operator",
                       help="who is adopting it; recorded in the entry")
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
    except ProfileNotAdopted as refused:
        # STALE_STATE, not MISSING_PRECONDITION: nothing is missing, the store is
        # already at or past the profile asked for. The manifest declares both.
        return _emit({"outcome": "REFUSED", "reason_code": "STALE_STATE",
                      "message": str(refused)}, 2)
    except UnknownEntry as missing:
        return _emit({"outcome": "REFUSED", "reason_code": "MISSING_PRECONDITION",
                      "message": f"no such record: {missing}"}, 3)
    except (custody.ExportRefused, custody.RestoreRefused) as refused:
        return _emit({"outcome": "REFUSED", "reason_code": "MISSING_PRECONDITION",
                      "message": str(refused)}, 2)
    except custody.TruncatedExport as truncated:
        return _emit({"outcome": "REFUSED", "reason_code": "DIGEST_MISMATCH",
                      "message": str(truncated)}, 2)
    except ValueError as invalid:
        return _emit({"outcome": "REFUSED", "reason_code": "MISSING_PRECONDITION",
                      "message": str(invalid)}, 2)
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
