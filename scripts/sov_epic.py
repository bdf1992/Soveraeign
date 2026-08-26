#!/usr/bin/env python3
"""Walk the Soveraeign epic-of-epics issue tree from its checked-in projection.

``sync`` is the only command that reads the GitHub coordination surface, and it
is an attended action. Every other command reads ``.claude/epic/tree.json``, so
an unattended scheduled run stays inside RECORD_LOCAL. Nothing here settles
standing: a reconciliation is an observation, and a reachable issue is not an
admitted operation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovepic import projection, survey, walk  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]

LEGEND = (
    "States: READY routed with every requires satisfied; HELD an unsatisfied requires;\n"
    "UNROUTED no repository artifact evidences a domain owner; OWNER a judgement asked\n"
    "of the owner. Routing and readiness are independent readings, so an issue can be\n"
    "UNROUTED and HELD at once. Only OWNER waits on the owner seat."
)
"""Legend printed under ``status``; the three states are never merged into one field."""


def _survey(root: Path) -> dict:
    return survey.survey(root, projection.load(root), projection.villages(root))


def command_sync(args: argparse.Namespace) -> int:
    """Refresh the projection from the coordination surface."""
    now = args.now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    document = projection.build(projection.fetch_issues(), projection.repository_name(), now)
    path = projection.save(ROOT, document)
    print(f"synced {len(document['issues'])} issue(s) at {now} -> {path.relative_to(ROOT).as_posix()}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    """Report contract, label-projection, and containment defects."""
    result = _survey(ROOT)
    groups = (
        ("contract", result["contract_defects"]),
        ("label projection", result["label_defects"]),
        ("containment", result["containment_defects"]),
    )
    total = 0
    for name, defects in groups:
        print(f"== {name}: {len(defects)} defect(s) ==")
        for defect in defects:
            print(f"  {defect}")
        total += len(defects)
    print(f"\n{'FAIL' if total else 'PASS'}: {total} defect(s) across the open tree")
    print("Standing note: a reconciliation observes the tree; it settles nothing.")
    return 1 if total and args.strict else 0


def command_status(args: argparse.Namespace) -> int:
    """Print the survey counts and the per-village shape."""
    result = _survey(ROOT)
    counts = result["counts"]
    print(f"epic #{result['root_issue']}  synced {result['synced_at']}")
    print(
        f"issues {counts['issues']}  open {counts['open']}  "
        f"ready {counts['ready']}  held {counts['held']}  unrouted {counts['unrouted']}  "
        f"owner-held {counts['owner_held']}  stories {counts['stories']}"
    )
    print(
        f"defects: contract {len(result['contract_defects'])}  "
        f"label {len(result['label_defects'])}  containment {len(result['containment_defects'])}"
    )
    for entry in result["ready"]:
        print(f"  READY   #{entry['issue']:<3} {entry['domain']:<12} {entry['title'][:56]}")
    for entry in result["held"]:
        held = ",".join(entry["blocked_by"])
        print(f"  HELD    #{entry['issue']:<3} {entry['domain']:<12} blocked by {held}")
    for entry in result["unrouted"]:
        print(f"  UNROUTED #{entry['issue']:<3} {entry['readiness']:<9} {entry['title'][:50]}")
    for entry in result["owner_held"]:
        print(f"  OWNER   #{entry['issue']:<3} {entry['title'][:56]}")
    for entry in result["stories"]:
        short = ",".join(entry["short"]) or "-"
        print(
            f"  STORY   #{entry['issue']:<3} {entry['reading']:<9} "
            f"{entry['actor_kind']}/{entry['role']} at {entry['counter']}  short {short}"
        )
    print(LEGEND)
    return 0


def command_next(args: argparse.Namespace) -> int:
    """Print the reachable work, optionally narrowed to one village or domain."""
    result = _survey(ROOT)
    entries = result["ready"]
    if args.village:
        entries = [e for e in entries if e["village"] == args.village]
    if args.domain:
        entries = [e for e in entries if e["domain"] == args.domain]
    if not entries:
        print("no reachable work matches the filter")
        return 0
    for entry in entries:
        print(
            f"#{entry['issue']} [{entry['horizon']}] {entry['domain']} "
            f"<- {entry['village']}\n    {entry['title']}\n    standing {entry['standing']}"
        )
    return 0


def command_unrouted(args: argparse.Namespace) -> int:
    """Print open work no repository artifact gives a domain owner.

    Unrouted is not owner-held. Writing the charter, contract, implementation, or
    tests that would evidence a domain is ordinary reversible work at this tier
    (``AGENTS.md``, Closure ownership), so these lines are a domain backlog and
    never a queue for Bdo.
    """
    result = _survey(ROOT)
    for entry in result["unrouted"]:
        print(
            f"#{entry['issue']:<3} {entry['readiness']:<9} {entry['village']:<26} "
            f"{entry['title'][:52]}"
        )
    also_held = sum(1 for e in result["unrouted"] if e["readiness"] == walk.HELD)
    print(f"\n{len(result['unrouted'])} open issue(s) unrouted: no repository artifact")
    print("evidences a domain owner. Unrouted work needs a domain, which is not Bdo's call")
    print("to make and is not a judgement item; it is ordinary work at this tier.")
    print(f"{also_held} of them are HELD as well, by an unsatisfied requires edge.")
    print("That is a separate state with a separate fix; neither implies the other.")
    return 0


def command_owner_held(args: argparse.Namespace) -> int:
    """Print the open work that genuinely waits on the owner, and nothing else.

    Membership is decided by ``contracts/issue-metadata.schema.json``: an open
    ``unblock`` ticket whose ``requested_provision`` is a judgement, addressed to
    the owner. An unsatisfied dependency and a missing domain owner are other
    states and are absent from this list by construction.
    """
    result = _survey(ROOT)
    for entry in result["owner_held"]:
        print(f"#{entry['issue']:<3} {entry['village']:<26} {entry['title'][:52]}")
    print(f"\n{len(result['owner_held'])} open issue(s) owner-held.")
    print("Held and unrouted work is elsewhere and does not wait on the owner.")
    return 0


def command_report(args: argparse.Namespace) -> int:
    """Emit the whole survey as JSON for a workflow to consume."""
    print(json.dumps(_survey(ROOT), indent=2))
    return 0


COMMANDS = {
    "sync": command_sync,
    "validate": command_validate,
    "status": command_status,
    "next": command_next,
    "unrouted": command_unrouted,
    "owner-held": command_owner_held,
    "report": command_report,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync = subparsers.add_parser("sync", help="refresh the projection from GitHub (attended)")
    sync.add_argument("--now", help="override the sync timestamp (testing)")
    validate = subparsers.add_parser("validate", help="report defects in the projected tree")
    validate.add_argument("--strict", action="store_true", help="exit non-zero on any defect")
    subparsers.add_parser("status", help="counts, ready work, and held work")
    nxt = subparsers.add_parser("next", help="reachable work")
    nxt.add_argument("--village")
    nxt.add_argument("--domain")
    subparsers.add_parser("unrouted", help="open work no repository artifact gives a domain")
    subparsers.add_parser("owner-held", help="open work that genuinely waits on the owner")
    subparsers.add_parser("report", help="the whole survey as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except (projection.ProjectionError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
