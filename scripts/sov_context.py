#!/usr/bin/env python3
"""Grade the context surface a participant must traverse before it can act.

A compression pass that is graded on its own description is not graded. This
reads the tree instead: how much orientation text exists, how many entrypoints
nothing names, how many files restate one fact, and how many other documents
each governing document sends a reader to.

    python scripts/sov_context.py checkpoint          the current reading
    python scripts/sov_context.py checkpoint --json   the exact machine reading
    python scripts/sov_context.py baseline --write    pin this reading to compare against
    python scripts/sov_context.py delta               what has moved since the baseline

`delta` is what makes a reduction target checkable. It reports the change on
each headline number against `reports/context/baseline.json` and says plainly
which direction each one moved. It settles nothing: a smaller surface is not a
better one, and this file grades no participant's conduct.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovcontext.surface import checkpoint as read_surface  # noqa: E402

BASELINE = ROOT / "reports" / "context" / "baseline.json"

# Lower is a smaller traversal for every headline number this reads.
HEADLINES: tuple[tuple[str, str], ...] = (
    ("orientation_lines", "lines of orientation text (root docs, agents, skills, workflows)"),
    ("orientation_files", "files in that orientation set"),
    ("entrypoints", "scripts/*.py an agent could be told to run"),
    ("unreachable_entrypoints", "of those, named by no document"),
    ("duplicated_facts", "declared facts with more than one producer"),
    ("total_restatements", "restatements of those facts across the tree"),
    ("route_edges", "references between root governing documents"),
    ("mean_fanout", "other governing documents the average one sends you to"),
)


def _print_checkpoint(reading: dict[str, Any]) -> None:
    head = reading["headline"]
    print("== context surface ==")
    for key, label in HEADLINES:
        print(f"  {str(head[key]):>7}  {label}")

    print("\n== volume by surface ==")
    for row in reading["volume"]["surfaces"]:
        print(f"  {row['files']:>4} files {row['lines']:>7} lines  {row['surface']}")

    print("\n== facts with more than one producer ==")
    for fact in reading["redundancy"]["facts"]:
        if fact["producers"] > 1:
            print(f"  {fact['producers']:>3} producers  {fact['name']}")
            print(f"                owned by {fact['owner']}")

    unnamed = reading["reach"]["unnamed"]
    if unnamed:
        print(f"\n== {len(unnamed)} entrypoint(s) no document names ==")
        for name in unnamed:
            print(f"  {name}")

    print("\n== route fan-out, root documents ==")
    for row in reading["routes"]["by_document"][:8]:
        print(f"  {row['out']:>3} -> {row['doc']}")
    print(f"  ... {reading['routes']['documents']} documents, "
          f"{reading['routes']['edges']} edges total")
    print("\nThis is a reading of the tree's shape. It grades no participant, "
          "settles no standing,\nand a smaller number here is not by itself a better "
          "repository.")


def command_checkpoint(args: argparse.Namespace) -> int:
    """Read the surface now."""
    reading = read_surface(args.root)
    if args.as_json:
        print(json.dumps(reading, indent=2, sort_keys=True))
        return 0
    _print_checkpoint(reading)
    return 0


def command_baseline(args: argparse.Namespace) -> int:
    """Show or pin the reading a later delta is measured against."""
    if args.write:
        reading = read_surface(args.root)
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(reading, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        print(f"baseline written to {BASELINE.relative_to(ROOT)}")
        return 0
    if not BASELINE.exists():
        print("no baseline pinned; run: python scripts/sov_context.py baseline --write")
        return 1
    pinned = json.loads(BASELINE.read_text(encoding="utf-8"))
    print(json.dumps(pinned["headline"], indent=2, sort_keys=True))
    return 0


def command_delta(args: argparse.Namespace) -> int:
    """Report movement on every headline number since the pinned baseline."""
    if not BASELINE.exists():
        print("no baseline pinned; run: python scripts/sov_context.py baseline --write")
        return 1
    was = json.loads(BASELINE.read_text(encoding="utf-8"))["headline"]
    now = read_surface(args.root)["headline"]
    rows = []
    for key, label in HEADLINES:
        before, after = was.get(key), now.get(key)
        if before in (None, 0):
            pct = None
        else:
            pct = round((after - before) / before * 100, 1)
        rows.append({"metric": key, "label": label, "before": before,
                     "after": after, "change_pct": pct})
    if args.as_json:
        print(json.dumps({"baseline": was, "current": now, "rows": rows},
                         indent=2, sort_keys=True))
        return 0
    print("== movement since the pinned baseline ==")
    for row in rows:
        pct = "-" if row["change_pct"] is None else f"{row['change_pct']:+.1f}%"
        print(f"  {str(row['before']):>7} -> {str(row['after']):>7}  {pct:>8}  {row['label']}")
    print("\nA reduction here is a smaller traversal, not a settled improvement. "
          "What the\ncut cost in recoverable meaning is read from the documents, "
          "not from this table.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the parser for every context-surface subcommand."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("checkpoint", help="read the context surface now")
    check.add_argument("--json", action="store_true", dest="as_json")
    check.set_defaults(handler=command_checkpoint)

    base = sub.add_parser("baseline", help="show or pin the comparison reading")
    base.add_argument("--write", action="store_true", help="pin the current reading")
    base.set_defaults(handler=command_baseline)

    delta = sub.add_parser("delta", help="movement since the pinned baseline")
    delta.add_argument("--json", action="store_true", dest="as_json")
    delta.set_defaults(handler=command_delta)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one context-surface subcommand."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
