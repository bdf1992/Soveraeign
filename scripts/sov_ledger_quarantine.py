#!/usr/bin/env python3
"""Separate test traffic from the operational landing ledger, preserving every row.

`scripts/sov_land.py` bound the repository root at import while `sovland.repo` reads it at
call time. A test pointing the root at a temporary repository moved the git operations
there and left the ledger write behind, so verification runs appended to
`.local/landing/ledger.ndjson` - the accounting for real landings.

This does not delete. It moves rows that carry the marks of test traffic into a sibling
file beside the ledger and writes a header saying why, so the record of what happened
survives and can be read back. `report` shows what a move would take without moving
anything.

A row is quarantined when it names the fixture grant `grant:test`, or names no grant at
all, which no real landing does: a landing request is graded against a grant and records
its id. The rule is deliberately narrow. A row it cannot classify stays in the operational
ledger, because leaving a real row in place costs less than removing one.

The ledger is gitignored local state, so this changes nothing any other checkout can see
and nothing that lands. It settles no standing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovland.ledger import LEDGER_PATH  # noqa: E402

QUARANTINE = Path(".local") / "landing" / "ledger.quarantined.ndjson"
FIXTURE_GRANT = "grant:test"
REASON = ("written into operational accounting by a verification run, through the "
          "import-time root binding in scripts/sov_land.py repaired on 2026-09-08")


def classify(row: dict) -> str:
    """`TEST` when a row carries the marks of fixture traffic, `OPERATIONAL` otherwise."""
    grant = row.get("grant_id")
    if grant == FIXTURE_GRANT or grant is None:
        return "TEST"
    return "OPERATIONAL"


def read(path: Path) -> list[tuple[str, dict | None, str]]:
    """Every line with its verdict, keeping any line that will not parse."""
    out: list[tuple[str, dict | None, str]] = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            out.append((line, None, "OPERATIONAL"))
            continue
        out.append((line, row, classify(row)))
    return out


def command_report(root: Path) -> int:
    """Say what a move would take, and move nothing."""
    rows = read(root / LEDGER_PATH)
    test = [r for r in rows if r[2] == "TEST"]
    live = [r for r in rows if r[2] == "OPERATIONAL"]
    print(f"{len(rows)} row(s) in {LEDGER_PATH.as_posix()}")
    print(f"  {len(test)} carrying the marks of test traffic")
    print(f"  {len(live)} that would stay")
    if not rows:
        print("nothing to read; the ledger is absent or empty")
    return 0


def command_move(root: Path) -> int:
    """Move test rows into the quarantine file, preserving every byte of every row."""
    ledger, quarantine = root / LEDGER_PATH, root / QUARANTINE
    rows = read(ledger)
    test = [r for r in rows if r[2] == "TEST"]
    live = [r for r in rows if r[2] == "OPERATIONAL"]
    if not test:
        print("no test traffic found; nothing moved")
        return 0
    quarantine.parent.mkdir(parents=True, exist_ok=True)
    header = json.dumps({
        "quarantine_schema": "soveraeign-ledger-quarantine/v1",
        "moved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "moved": len(test),
        "left": len(live),
        "reason": REASON,
        "rule": f"grant_id == {FIXTURE_GRANT!r} or absent",
    }, sort_keys=True)
    with quarantine.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(header + "\n")
        for line, _, _ in test:
            handle.write(line + "\n")
    ledger.write_text("".join(line + "\n" for line, _, _ in live), encoding="utf-8", newline="\n")
    print(f"moved {len(test)} row(s) to {QUARANTINE.as_posix()}, left {len(live)} in place")
    print("no row was deleted; the quarantine file holds every moved line and why")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Report or move; never delete."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", nargs="?", default="report", choices=("report", "move"))
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    return {"report": command_report, "move": command_move}[args.command](args.root)


if __name__ == "__main__":
    raise SystemExit(main())
