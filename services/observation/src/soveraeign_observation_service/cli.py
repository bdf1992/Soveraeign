"""The Observation Service machine interface.

Until this module existed the five built operations were reachable only in-process, so the
one run ever observed through them (`urn:soveraeign:run:thin-circuit-1`) was observed by a
session-scratchpad driver a later participant could not re-run from the artifact
(`reports/2026-09-05-thin-circuit-1.md`, fizzle 12). Every command here reads a journal
export - a Record Service `export-journal` or `reconstruct-journal` document, JSON with an
`entries` list in the Record Service's entry shape - and writes one JSON object to stdout,
refusals included. The Record Service is never imported; the boundary is the entry shape.

State is the service's own, kept as one JSON file per record under `--store` (default
`.local/observation`) and rebuilt on every invocation, so predicates declared in one process
hold for an observation made in a later one. `observe-run` also prints, under `journal_entry`,
exactly what a caller passes to the Record Service's `append-entry --kind OBSERVATION`; this
command does not append it, because this service never writes the journal.

Exit codes: 0 committed, 2 refused, 3 unknown record. A refusal names the manifest's reason
code and, where the manifest maps a local code onto a kernel one, that too. A usage error is
argparse's: exit 2 with prose on stderr, before any attempt is made or receipted.

`infer-relation` records what the walk found and commits, `DIRECT` included: an inference is
a finding, not a permission. Only `observe-run` refuses `OBSERVER_NOT_INDEPENDENT`, which is
how the manifest declares the two operations. A second `observe-run` by the same observer over
the same addresses is the same observation again and refuses `OBSERVATION_RECORDED`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
import argparse
import json
import sys

from .errors import ObservationMissing, ObservationRefused, Unreadable
from .record import RunRecord, digest_address
from .service import ObservationService
from .store import FileStore

DEFAULT_STORE = Path(".local") / "observation"
MANIFEST = Path(__file__).resolve().parents[2] / "contracts" / "service.json"
COMMANDS = ("operations", "request-observation", "declare-predicates", "infer-relation",
            "observe-run", "read-observation")


def clock() -> str:
    """The host's moment, fixed width so the store replays records in recorded order."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _emit(payload: dict[str, Any], code: int = 0) -> int:
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return code


def _manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def load_journal(path: Path) -> list[dict[str, Any]]:
    """Entries from an export or reconstruction document, or `UNREADABLE`."""
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise Unreadable(f"journal {path}: {error}") from error
    entries = document.get("entries") if isinstance(document, dict) else document
    if not isinstance(entries, list):
        raise Unreadable(f"journal {path} carries no entries list")
    return entries


def file_reader(root: Path) -> Callable[[str], bytes]:
    """Read output bytes at `root/<address>`; an address that escapes the root is refused."""
    base = Path(root).resolve()

    def read(address: str) -> bytes:
        target = (base / address).resolve()
        if not target.is_relative_to(base):
            raise ValueError(f"{address} escapes {base}")
        return target.read_bytes()
    return read


def _record(args: argparse.Namespace) -> RunRecord:
    return RunRecord.from_entries(args.run, load_journal(args.journal))


def _predicates(args: argparse.Namespace, record: RunRecord) -> list[dict[str, Any]]:
    """The declared predicates: given as JSON, read from a file, or derived from the record.

    `--from-record` declares `DIGEST_EQUALS` for every address the run reported, expecting the
    digest the newest `OUTPUT` entry for that address declares. Those digests are the
    producers' word about their outputs, not the executor's report, so the declaration stays
    evaluable without the report.
    """
    if args.from_record:
        outputs = record.outputs()
        return [{"predicate_id": f"digest-{index}", "kind": "DIGEST_EQUALS", "address": address,
                 "expected": digest_address(outputs[address]["payload"].get("digest"))}
                for index, address in enumerate(record.reported_addresses())
                if address in outputs]
    raw = Path(args.predicates_file).read_text(encoding="utf-8") if args.predicates_file \
        else args.predicates
    if raw is None:
        raise ValueError("give --predicates, --predicates-file, or --from-record")
    predicates = json.loads(raw)
    if not isinstance(predicates, list):
        raise ValueError("predicates must be a JSON list")
    return predicates


def discover(_: ObservationService, args: argparse.Namespace) -> dict[str, Any]:
    """Answer what may be done here, from the manifest the service declares."""
    manifest = _manifest()
    return {
        "service_id": manifest["service_id"],
        "standing": manifest["standing"],
        "operations": manifest["operations"],
        "local_refusals": manifest.get("local_refusals", {}),
        "forbids": manifest["forbids"],
        "reachable_here": [name for name in COMMANDS if name != "operations"],
        "store": {"root": str(args.store), "records": FileStore(args.store).count()},
        "authoritative": False,
        "note": "the journal is the Record Service's; this service reads it and never writes it",
    }


def request_observation(service: ObservationService, args: argparse.Namespace) -> dict[str, Any]:
    """Ask that a terminal run be observed."""
    return {"request": service.request_observation(
        _record(args), args.requester, args.requester_kind, args.subject or args.run,
        args.proposed_observer)}


def declare_predicates(service: ObservationService, args: argparse.Namespace) -> dict[str, Any]:
    """State what must hold before anyone looks."""
    return {"declaration": service.declare_predicates(
        args.run, _predicates(args, _record(args)))}


def infer_relation(service: ObservationService, args: argparse.Namespace) -> dict[str, Any]:
    """Walk the run's record for a direct edge to the candidate observer."""
    return {"inference": service.infer_relation(_record(args), args.observer, args.observer_kind)}


def observe_run(service: ObservationService, args: argparse.Namespace) -> dict[str, Any]:
    """Observe the run and print what the observer would hand the journal."""
    observation = service.observe_run(_record(args), args.observer,
                                      file_reader(args.reader_root))
    inference = next(entry for entry in reversed(service.inferences)
                     if entry["run_id"] == args.run
                     and entry["candidate_observer_id"] == args.observer)
    declaration = next(entry for entry in reversed(service.declarations)
                       if entry["run_id"] == args.run)
    return {
        "observation": observation,
        "journal_entry": {
            "kind": "OBSERVATION",
            "subject": args.run,
            "actor": args.observer,
            "payload": {"event": "OBSERVED", "inference_id": inference["inference_id"],
                        "declaration_id": declaration["declaration_id"],
                        "observation": observation},
            "source_address": None,
        },
        "note": "journal_entry is what the observer passes to the Record Service's "
                "append-entry --kind OBSERVATION; this service does not append it",
    }


def read_observation(service: ObservationService, args: argparse.Namespace) -> dict[str, Any]:
    """The observation with the declaration, inference, and receipts it was judged through."""
    return service.read_observation(args.observation)


def _commands() -> dict[str, Callable[[ObservationService, argparse.Namespace], dict[str, Any]]]:
    return {
        "operations": discover,
        "request-observation": request_observation,
        "declare-predicates": declare_predicates,
        "infer-relation": infer_relation,
        "observe-run": observe_run,
        "read-observation": read_observation,
    }


def _run_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--journal", type=Path, required=True,
                        help="a Record Service journal export or reconstruct-journal document")
    parser.add_argument("--run", required=True, help="the run subject to read")


def build_parser() -> argparse.ArgumentParser:
    """Declare every command and its required inputs."""
    parser = argparse.ArgumentParser(prog="soveraeign-observation",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE,
                        help="where this service keeps its own records (default .local/observation)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("operations", help="discover legal operations and their required inputs")

    request = sub.add_parser("request-observation", help="ask that a terminal run be observed")
    _run_arguments(request)
    request.add_argument("--requester", required=True)
    request.add_argument("--requester-kind", default="MODEL",
                         choices=("HUMAN", "MODEL", "WORKER", "SYSTEM"))
    request.add_argument("--subject", help="what is to be observed (default: the run)")
    request.add_argument("--proposed-observer")

    declare = sub.add_parser("declare-predicates", help="state what must hold before looking")
    _run_arguments(declare)
    declare.add_argument("--predicates", help="a JSON list of predicates")
    declare.add_argument("--predicates-file", type=Path, help="a file holding that list")
    declare.add_argument("--from-record", action="store_true",
                         help="DIGEST_EQUALS over every reported address, from its OUTPUT entry")

    infer = sub.add_parser("infer-relation",
                           help="infer the candidate observer's relation to the run; DIRECT is "
                                "recorded and committed, only observe-run refuses it")
    _run_arguments(infer)
    infer.add_argument("--observer", required=True, help="the candidate observer's id")
    infer.add_argument("--observer-kind", default="MODEL",
                       choices=("HUMAN", "MODEL", "WORKER", "SYSTEM"))

    observe = sub.add_parser("observe-run", help="read the outputs and evaluate the predicates")
    _run_arguments(observe)
    observe.add_argument("--observer", required=True)
    observe.add_argument("--reader-root", type=Path, default=Path("."),
                         help="output bytes are read at <reader-root>/<address> (default .)")

    read = sub.add_parser("read-observation", help="read one observation by id")
    read.add_argument("--observation", required=True)
    return parser


def _refusal(refused: ObservationRefused, receipt: dict[str, Any] | None) -> dict[str, Any]:
    payload = {"outcome": "REFUSED", "reason_code": refused.reason_code,
               "message": refused.detail, "receipt": receipt}
    kernel = _manifest().get("local_refusals", {}).get(refused.reason_code)
    if kernel:
        payload["kernel_reason_code"] = kernel
    return payload


def _receipted(service: ObservationService, args: argparse.Namespace, before: int,
               refused: ObservationRefused) -> dict[str, Any]:
    """The receipt this attempt left; one is written if the refusal preceded the attempt."""
    if len(service.receipts) == before:
        subject = getattr(args, "run", None) or getattr(args, "observation", None) or ""
        service.record_refusal(args.command, subject, refused)
    return service.receipts[-1]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = FileStore(args.store)
    service = store.load(clock)
    before = len(service.receipts)
    try:
        result = _commands()[args.command](service, args)
    except ObservationMissing as missing:
        return _emit(_refusal(missing, _receipted(service, args, before, missing)), 3)
    except ObservationRefused as refused:
        return _emit(_refusal(refused, _receipted(service, args, before, refused)), 2)
    except (OSError, ValueError) as invalid:
        refused = ObservationRefused(str(invalid))
        return _emit(_refusal(refused, _receipted(service, args, before, refused)), 2)
    finally:
        store.save(service)
    if service.receipts and args.command != "operations":
        result["receipt"] = service.receipts[-1]
    return _emit(result)


if __name__ == "__main__":
    raise SystemExit(main())
