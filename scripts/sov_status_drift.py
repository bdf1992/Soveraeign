#!/usr/bin/env python3
"""Report drift between `STATUS.yaml`'s per-service claims and what `services/` holds.

`STATUS.yaml` states each service's implementation standing by hand — a human writes
`gateway_service_status: CHARTERED_BOUNDARY_NOT_IMPLEMENTED` and nothing checks it
against the tree again. A service can grow a `src/` package, a test suite, and
conformance fixtures while the hand-written line still says nothing is built, and
nobody notices because nothing reads the tree and compares it.

This is a reporter, not an editor. It never writes `STATUS.yaml`: the standing value
is Bdo's call, not a derived one, and `STATUS.yaml`'s own header text says implementation
is evidence about intent, never authority for it. This script only makes the evidence
visible. Exit status reflects whether the script itself ran cleanly, not whether drift
was found — drift is the point of running it, not a failure.

Derivation, per `services/<name>/`:
  has_src          `src/` exists and holds at least one file that is not a bare README
  has_tests        `tests/` exists and holds at least one non-empty `test_*.py` file
  has_conformance  `conformance/` exists and holds at least one file

The comparison is deliberately loose, matching how the file is actually written: a
status value containing `NOT_IMPLEMENTED` while the tree looks built is flagged
UNDERSTATED; a status value containing `BUILT` while the tree looks unbuilt is flagged
OVERSTATED. Everything else — including services with no `_service_status` field, and
services whose status already agrees with the tree — is reported without a flag.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVICES_DIR = ROOT / "services"
STATUS = ROOT / "STATUS.yaml"

# Same shape as scripts/sov_status_claims.py's FIELD: a column-zero `*_status:` line,
# read directly rather than through a YAML parser so a later duplicate key overwrites
# an earlier one exactly the way any ordinary YAML reader resolves it (last wins) —
# which is what "whatever STATUS.yaml currently states" means for a duplicated field.
FIELD = re.compile(r"^([a-z0-9_]+_status):\s*(\S+)\s*$")

README_NAMES = {"readme", "readme.md", "readme.rst", "readme.txt"}

NOT_IMPLEMENTED_MARKER = "NOT_IMPLEMENTED"
BUILT_MARKER = "BUILT"


def read_status_fields(text: str) -> dict[str, str]:
    """Every `*_status` field in `STATUS.yaml`, last occurrence wins (see FIELD above)."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD.match(line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def _has_real_file(directory: Path, *, name_filter=None) -> bool:
    """True if `directory` exists and holds at least one file `name_filter` admits.

    A missing directory, or one holding only a README, counts as empty: a service
    seeded with a boundary charter and a placeholder README is not yet "has src".
    """
    if not directory.is_dir():
        return False
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        if path.name.lower() in README_NAMES:
            continue
        if name_filter is not None and not name_filter(path):
            continue
        return True
    return False


def _is_nonempty_test_file(path: Path) -> bool:
    return path.name.startswith("test_") and path.suffix == ".py" and path.stat().st_size > 0


def derive_service_state(service_dir: Path) -> dict[str, bool]:
    """has_src / has_tests / has_conformance for one `services/<name>/` directory."""
    return {
        "has_src": _has_real_file(service_dir / "src"),
        "has_tests": _has_real_file(service_dir / "tests", name_filter=_is_nonempty_test_file),
        "has_conformance": _has_real_file(service_dir / "conformance"),
    }


def service_names(services_dir: Path = SERVICES_DIR) -> list[str]:
    if not services_dir.is_dir():
        return []
    return sorted(p.name for p in services_dir.iterdir() if p.is_dir())


def classify_drift(derived: dict[str, bool], status_value: str | None) -> str | None:
    """None (no drift, or nothing stated to compare against), else a drift label."""
    if status_value is None:
        return None
    built_in_tree = derived["has_src"] and derived["has_tests"]
    stated_not_implemented = NOT_IMPLEMENTED_MARKER in status_value
    stated_built = BUILT_MARKER in status_value
    if built_in_tree and stated_not_implemented:
        return "UNDERSTATED"
    if not derived["has_src"] and stated_built:
        return "OVERSTATED"
    return None


def collect_report(services_dir: Path = SERVICES_DIR, status_text: str | None = None) -> list[dict]:
    """One row per `services/<name>/` directory, in name order."""
    if status_text is None:
        status_text = STATUS.read_text(encoding="utf-8") if STATUS.is_file() else ""
    fields = read_status_fields(status_text)
    rows = []
    for name in service_names(services_dir):
        derived = derive_service_state(services_dir / name)
        field_name = f"{name}_service_status"
        status_value = fields.get(field_name)
        rows.append({
            "service": name,
            "field": field_name,
            "status_value": status_value,
            **derived,
            "drift": classify_drift(derived, status_value),
        })
    return rows


def _format_row(row: dict) -> str:
    flags = "".join([
        "S" if row["has_src"] else "-",
        "T" if row["has_tests"] else "-",
        "C" if row["has_conformance"] else "-",
    ])
    stated = row["status_value"] if row["status_value"] is not None else "(no *_service_status field)"
    line = f"  {row['service']:<14} [{flags}]  {stated}"
    if row["drift"]:
        line += f"   <-- DRIFT: {row['drift']}"
    return line


def _cmd_check(_args: argparse.Namespace) -> int:
    rows = collect_report()
    drifted = [row for row in rows if row["drift"]]
    print("status drift: [S]rc [T]ests [C]onformance derived from services/<name>/, "
          "compared against STATUS.yaml's stated *_service_status")
    for row in rows:
        print(_format_row(row))
    if drifted:
        print(f"\n{len(drifted)} service(s) drifted from what STATUS.yaml states:")
        for row in drifted:
            print(f"  {row['service']}: tree shows src={row['has_src']} tests={row['has_tests']} "
                  f"conformance={row['has_conformance']}, STATUS.yaml says {row['status_value']!r}")
        print("\nThis reporter does not edit STATUS.yaml. The standing value is Bdo's call.")
    else:
        print("\nno drift: every stated *_service_status agrees with what services/ holds")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command")
    check = subparsers.add_parser("check", help="print the drift report (default)")
    check.set_defaults(func=_cmd_check)
    parser.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
