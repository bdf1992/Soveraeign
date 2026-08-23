#!/usr/bin/env python3
"""Ticket coordination contract command line.

Reads a ticket export produced by the GitHub registrar under ``adapters/github/`` and
never contacts a network itself. Keeping the crossing in the adapter and the judgement
in this command means every check here runs offline, in CI, and inside the repository
verification budget.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovticket import labels as labelmod  # noqa: E402
from sovticket import queue as queuemod  # noqa: E402
from sovticket import transitions as transmod  # noqa: E402
from sovticket.jsonschema import validate  # noqa: E402
from sovticket.yamlblock import TicketBlockError, load_ticket  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "conformance" / "fixtures" / "tickets"


def _load_export(path: Path) -> list[dict[str, Any]]:
    """Load a ticket export array from the registrar."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"FAIL: {path} is not a ticket export array")
    return data


def _parse_all(export: list[dict[str, Any]]) -> tuple[list[queuemod.Ticket], list[str]]:
    """Parse every exported issue into a ticket, collecting parse defects."""
    tickets, defects = [], []
    for issue in sorted(export, key=lambda item: item["number"]):
        try:
            metadata = load_ticket(issue.get("body") or "")
        except TicketBlockError as error:
            defects.append(f"#{issue['number']}: {error}")
            continue
        tickets.append(
            queuemod.Ticket(
                number=issue["number"],
                title=issue.get("title", ""),
                state=issue.get("state", "OPEN"),
                metadata=metadata,
            )
        )
    return tickets, defects


def command_validate(args: argparse.Namespace) -> int:
    """Validate every exported ticket against the issue metadata schema."""
    schema = json.loads((ROOT / "contracts" / "issue-metadata.schema.json").read_text("utf-8"))
    tickets, defects = _parse_all(_load_export(Path(args.export)))
    for ticket in tickets:
        for defect in validate(ticket.metadata, schema):
            defects.append(f"{ticket.ref}: {defect}")
    for defect in defects:
        print(f"FAIL: {defect}")
    if defects:
        print(f"\nFAIL: {len(defects)} ticket contract defect(s) across {len(tickets)} tickets")
        return 1
    print(f"PASS: {len(tickets)} tickets satisfy soveraeign-ticket/v1")
    return 0


def command_labels(args: argparse.Namespace) -> int:
    """Report drift between live labels and the label projection."""
    projection = labelmod.load_projection(ROOT)
    catalogue = labelmod.load_catalogue(ROOT)
    tickets, defects = _parse_all(_load_export(Path(args.export)))
    export = {item["number"]: item for item in _load_export(Path(args.export))}
    drifted = 0
    for ticket in tickets:
        live = [entry["name"] for entry in export[ticket.number].get("labels", [])]
        drift = labelmod.compare(ticket.ref, ticket.metadata, live, projection)
        undeclared = sorted(set(drift.missing) - catalogue)
        if undeclared:
            defects.append(f"{ticket.ref}: projected label(s) absent from .github/labels.yml: {undeclared}")
        if not drift.clean:
            drifted += 1
            print(f"DRIFT: {drift.render()}")
    for defect in defects:
        print(f"FAIL: {defect}")
    if defects:
        return 1
    print(f"\n{drifted} of {len(tickets)} tickets drift from the declared label projection")
    return 1 if (drifted and args.strict) else 0


def command_queue(args: argparse.Namespace) -> int:
    """Print the prioritized takeable-work projection."""
    policy = queuemod.load_policy(ROOT)
    tickets, defects = _parse_all(_load_export(Path(args.export)))
    for defect in defects:
        print(f"WARN: unparsed ticket omitted from the queue: {defect}")
    entries = queuemod.build(tickets, policy)
    if args.json:
        print(json.dumps([entry.as_dict() for entry in entries[: args.limit or None]], indent=2))
    else:
        print(queuemod.render(entries, args.limit or None))
    return 0


def _request_from_body(path: Path) -> dict[str, Any] | None:
    """Extract a transition request from a fenced json block in a pull request body."""
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    block: list[str] | None = None
    for line in lines:
        if block is None:
            if line.strip().lower() in ("```json", "```jsonc"):
                block = []
            continue
        if line.strip() == "```":
            try:
                candidate = json.loads("\n".join(block))
            except json.JSONDecodeError:
                block = None
                continue
            if isinstance(candidate, dict) and "request_schema" in candidate:
                return candidate
            block = None
            continue
        block.append(line)
    return None


def command_transition(args: argparse.Namespace) -> int:
    """Evaluate one transition request against the declared table."""
    schema = json.loads((ROOT / "contracts" / "ticket-transition.schema.json").read_text("utf-8"))
    if args.body:
        request = _request_from_body(Path(args.body))
        if request is None:
            print("No standing transition is proposed in this pull request body.")
            print("PASS: the change may establish BUILT evidence only; nothing advances past it.")
            return 0
    else:
        request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    defects = validate(request, schema)
    if defects:
        for defect in defects:
            print(f"FAIL: {defect}")
        print("\nREFUSED [MALFORMED_REQUEST]: the request does not satisfy the transition schema")
        return 1
    decision = transmod.evaluate(request, transmod.load_table(ROOT))
    print(f"{request['ticket']} {request['from']} -> {request['to']}")
    print(decision.render())
    if decision.allowed:
        print("Note: an allowed transition is a permitted proposal, not a settlement or ratification.")
    return 0 if decision.allowed else 1


def _metadata_case_failures() -> tuple[list[str], list[dict[str, Any]]]:
    """Judge the metadata corpus against contracts/issue-metadata.schema.json.

    A defeating case declares the substring its refusal must contain, so a case cannot
    pass by raising some unrelated defect, and a weakened schema cannot hide behind a
    coincidental failure elsewhere in the instance.
    """
    schema = json.loads((ROOT / "contracts" / "issue-metadata.schema.json").read_text("utf-8"))
    corpus = json.loads((FIXTURES / "metadata-cases.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    for case in corpus["cases"]:
        defects = validate(case["metadata"], schema)
        case_id = case["case_id"]
        if case["expect"] == "VALID":
            if defects:
                failures.append(f"{case_id}: expected a valid instance, observed {defects[0]}")
            continue
        if not defects:
            failures.append(f"{case_id}: expected a refusal, none raised")
            continue
        wanted = case.get("refuses")
        if wanted and not any(wanted in defect for defect in defects):
            failures.append(f"{case_id}: expected a refusal naming {wanted!r}, observed {defects}")
    return failures, corpus["cases"]


def command_selfcheck(_: argparse.Namespace) -> int:
    """Run the declared positive and defeating fixture corpora without a network."""
    schema = json.loads((ROOT / "contracts" / "ticket-transition.schema.json").read_text("utf-8"))
    table = transmod.load_table(ROOT)
    cases = json.loads((FIXTURES / "transition-cases.json").read_text(encoding="utf-8"))
    failures = []
    for case in cases["cases"]:
        request = case["request"]
        schema_defects = validate(request, schema)
        if case["expect"] == "MALFORMED_REQUEST":
            if not schema_defects:
                failures.append(f"{case['case_id']}: expected a schema refusal, none raised")
            continue
        if schema_defects:
            failures.append(f"{case['case_id']}: unexpected schema defect {schema_defects[0]}")
            continue
        decision = transmod.evaluate(request, table)
        actual = "ALLOWED" if decision.allowed else decision.reason_code
        if actual != case["expect"]:
            failures.append(f"{case['case_id']}: expected {case['expect']}, observed {actual}")
    metadata_failures, metadata_cases = _metadata_case_failures()
    failures.extend(metadata_failures)
    total = len(cases["cases"]) + len(metadata_cases)
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"\nFAIL: {len(failures)} of {total} fixture cases")
        return 1
    positive = sum(1 for case in cases["cases"] if case["expect"] == "ALLOWED")
    positive += sum(1 for case in metadata_cases if case["expect"] == "VALID")
    print(
        f"PASS: {len(cases['cases'])} transition cases and "
        f"{len(metadata_cases)} metadata cases "
        f"({positive} positive, {total - positive} defeating)"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for every ticket subcommand."""
    parser = argparse.ArgumentParser(prog="sov_ticket", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, handler, needs_export in (
        ("validate", command_validate, True),
        ("labels", command_labels, True),
        ("queue", command_queue, True),
    ):
        sub = subparsers.add_parser(name, help=handler.__doc__)
        sub.set_defaults(handler=handler)
        if needs_export:
            sub.add_argument("--export", required=True, help="ticket export produced by the registrar")
    subparsers.choices["labels"].add_argument(
        "--strict", action="store_true", help="exit non-zero when any ticket drifts"
    )
    subparsers.choices["queue"].add_argument("--limit", type=int, default=0)
    subparsers.choices["queue"].add_argument("--json", action="store_true")

    transition = subparsers.add_parser("transition", help=command_transition.__doc__)
    transition.set_defaults(handler=command_transition)
    source = transition.add_mutually_exclusive_group(required=True)
    source.add_argument("request", nargs="?", help="path to a soveraeign-ticket-transition/v1 request")
    source.add_argument("--body", help="path to a pull request body carrying a fenced json request")

    selfcheck = subparsers.add_parser("selfcheck", help=command_selfcheck.__doc__)
    selfcheck.set_defaults(handler=command_selfcheck)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch one subcommand."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
