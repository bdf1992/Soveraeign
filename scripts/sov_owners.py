#!/usr/bin/env python3
"""Read and judge the domain owner register.

``check`` grades ``contracts/domain-owners.json`` against its schema and against the sources
that own what it names: PRD.md for requirement ids, the service manifests for declared
services, and ``.claude/schedules`` for anything that fires. ``status`` prints the board,
including every declared service the register does not cover.

Nothing here grants anything. An owner record names the authority an owner would need and the
witness that checks it; it never holds either.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel.jsonschema import validate

ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "contracts" / "domain-owners.json"
SCHEMA_PATH = ROOT / "contracts" / "domain-owners.schema.json"
PRD_PATH = ROOT / "PRD.md"
SCHEDULE_DIR = ROOT / ".claude" / "schedules"

STANDING_NOTE = ("Standing note: an owner record is an accountability declaration at its own "
                 "standing; declaring an owner neither grants authority nor starts work.")


def load_table() -> dict[str, Any]:
    """Parse the register."""
    return json.loads(TABLE_PATH.read_text(encoding="utf-8"))


def declared_services() -> set[str]:
    """Every service that has a manifest on disk, read at check time."""
    return {path.parents[1].name for path in (ROOT / "services").glob("*/contracts/service.json")}


def prd_requirements() -> set[str]:
    """Requirement ids PRD.md actually carries, read from its bytes rather than assumed."""
    return set(re.findall(r"PROD-I-[1-9]", PRD_PATH.read_text(encoding="utf-8")))


def _parse_deadline(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def defects(table: dict[str, Any]) -> list[str]:
    """Every defect in the register, in a stable order."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    found = [f"schema: {defect}" for defect in validate(table, schema, schema, "/")]
    if found:
        return found
    services = declared_services()
    requirements = prd_requirements()
    seen: set[str] = set()
    for entry in table["owners"]:
        domain = entry["domain"]
        if domain in seen:
            found.append(f"{domain}: declared twice")
        seen.add(domain)
        owner = entry["owner"]["actor_id"]
        witness = entry["witness"]["actor_id"]
        if owner == witness:
            found.append(f"{domain}: owner and witness are both {owner!r}; a build report "
                         f"cannot witness itself")
        if entry["subject_kind"] == "service" and domain not in services:
            found.append(f"{domain}: declared as a service but services/{domain}/contracts/"
                         f"service.json does not exist")
        for requirement in entry["requirements"]:
            if requirement not in requirements:
                found.append(f"{domain}: requirement {requirement} does not appear in PRD.md")
        if entry["budget"]["max_usd_per_run"] <= 0:
            found.append(f"{domain}: budget max_usd_per_run must be greater than zero")
        if _parse_deadline(entry["deadline"]) is None:
            found.append(f"{domain}: deadline {entry['deadline']!r} is not a real date")
        schedule = entry.get("schedule")
        if schedule is not None and not (SCHEDULE_DIR / f"{schedule}.json").exists():
            found.append(f"{domain}: schedule {schedule!r} has no declaration in "
                         f".claude/schedules")
    return found


def _cmd_check(args: argparse.Namespace) -> int:
    table = load_table()
    found = defects(table)
    if found:
        for defect in found:
            print(f"DEFECT: {defect}")
        print(f"FAIL: {len(found)} defects in {TABLE_PATH.relative_to(ROOT).as_posix()}")
        return 1
    owned = len(table["owners"])
    unowned = sorted(declared_services() - {entry["domain"] for entry in table["owners"]})
    print(f"PASS: {owned} owner records, no defect")
    if unowned:
        print(f"UNOWNED: {len(unowned)} declared service(s) with no owner: {', '.join(unowned)}")
    print(STANDING_NOTE)
    return 0


def _row(entry: dict[str, Any], today: date) -> str:
    budget = entry["budget"]
    envelope = f"${budget['max_usd_per_run']:g}x{budget['runs_per_period']}/{budget['period']}"
    deadline = _parse_deadline(entry["deadline"])
    days = "?" if deadline is None else f"{(deadline - today).days:+d}d"
    schedule = entry.get("schedule") or "-"
    return (f"{entry['domain']:<12} {entry['owner']['actor_id']:<20} "
            f"{entry['witness']['actor_id']:<16} {envelope:<14} {entry['deadline']} {days:>6} "
            f"{schedule:<12} {entry['standing']}")


def _cmd_status(args: argparse.Namespace) -> int:
    table = load_table()
    today = date.fromisoformat(args.today) if args.today else date.today()
    if args.json:
        print(json.dumps(table["owners"], indent=2))
        return 0
    print(f"{'DOMAIN':<12} {'OWNER':<20} {'WITNESS':<16} {'BUDGET':<14} {'DEADLINE':<10} "
          f"{'LEFT':>6} {'SCHEDULE':<12} STANDING")
    for entry in sorted(table["owners"], key=lambda row: row["deadline"]):
        print(_row(entry, today))
    unowned = sorted(declared_services() - {entry["domain"] for entry in table["owners"]})
    for domain in unowned:
        print(f"{domain:<12} {'-':<20} {'-':<16} {'-':<14} {'-':<10} {'-':>6} {'-':<12} UNOWNED")
    print(f"\n{len(table['owners'])} owned, {len(unowned)} unowned, table status "
          f"{table['status']}")
    print(STANDING_NOTE)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    checker = sub.add_parser("check", help="judge the register against its sources")
    checker.set_defaults(handler=_cmd_check)
    shower = sub.add_parser("status", help="print the owner board")
    shower.add_argument("--json", action="store_true", help="print the records as JSON")
    shower.add_argument("--today", help="grade days remaining against this ISO date")
    shower.set_defaults(handler=_cmd_status)
    args = parser.parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
