#!/usr/bin/env python3
"""Grade `LESSONS.md` against the loop `decisions/0029` declares.

That record closed with a named residual - it added no check enforcing the
drain - and gave a reason for the half it declined: a check that fails on an
eighth lesson makes capture costly at exactly the moment capture matters. That
reasoning is unchanged here and the count still does not refuse. It is printed
every run and recorded as debt past the threshold.

What refuses is a standing the page asserts and the tree does not support.
`EFFECTIVE` is defined as running inside `scripts/verify.py` or
`scripts/lint.py`, so an entry claiming it while naming no path either one
reaches is a claim with no evidence, which is the defect the whole record
exists to refuse.

Every read is local. Nothing here reaches the coordination surface.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re

from sovverify.checks import CHECKS


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = "contracts/lessons-loop.json"
PAGE = "LESSONS.md"

ENTRY = re.compile(r"^### (?P<heading>.+)$", re.M)
IDENTIFIER = re.compile(r"\bL-(\d{4})\b")
STANDING = re.compile(r"^- Standing: `(?P<standing>[A-Z_]+)`", re.M)
LANDING = re.compile(r"^- Landing: `(?P<landing>[a-z-]+)`", re.M)
SUMMARY = re.compile(r"Standing now: \*\*(?P<count>\d+) `RECORDED`\*\*, threshold (?P<threshold>\d+)")
QUOTED_PATH = re.compile(r"`([A-Za-z0-9_./-]+\.(?:py|json|md|yaml))`")


def _text(relative: str) -> str:
    """Repository text as UTF-8, without newline translation."""
    return (ROOT / relative).read_bytes().decode("utf-8")


def _contract() -> dict:
    return json.loads(_text(CONTRACT))


def entries(page: str) -> list[dict]:
    """One record per `###` entry above the Dropped section."""
    body = page.split("## Entries", 1)[-1].split("\n## Dropped", 1)[0]
    found: list[dict] = []
    positions = [(match.start(), match.group("heading")) for match in ENTRY.finditer(body)]
    for index, (start, heading) in enumerate(positions):
        end = positions[index + 1][0] if index + 1 < len(positions) else len(body)
        block = body[start:end]
        identifier = IDENTIFIER.search(heading)
        standing = STANDING.search(block)
        landing = LANDING.search(block)
        found.append({
            "id": f"L-{identifier.group(1)}" if identifier else None,
            "heading": heading.strip(),
            "standing": standing.group("standing") if standing else None,
            "landing": landing.group("landing") if landing else None,
            "paths": sorted(set(QUOTED_PATH.findall(block))),
        })
    return found


def reachable_paths() -> set[str]:
    """Every path the check table runs or observes, plus what lint reads.

    Read from `CHECKS` rather than from a list of script names, so an entry
    claiming EFFECTIVE is graded against the table that actually runs.
    """
    paths: set[str] = set()
    for check in CHECKS:
        paths.update(str(part) for part in check.command if isinstance(part, str))
        paths.update(check.observes)
    paths.add("scripts/lint.py")
    paths.add("scripts/verify.py")
    return {path.replace("\\", "/") for path in paths}


def grade(page: str, contract: dict, reached: set[str] | None = None) -> list[dict]:
    """Every refusal the declared contract fires against this page."""
    reached = reachable_paths() if reached is None else reached
    defects: list[dict] = []
    records = entries(page)

    seen: set[str] = set()
    for record in records:
        name = record["id"] or record["heading"][:40]
        if not record["id"]:
            defects.append({"code": "UNNUMBERED_ENTRY",
                            "detail": f"{record['heading'][:60]} carries no L-<nnnn>"})
        elif record["id"] in seen:
            defects.append({"code": "UNNUMBERED_ENTRY",
                            "detail": f"{record['id']} appears more than once"})
        else:
            seen.add(record["id"])

        if record["standing"] is None:
            defects.append({"code": "UNKNOWN_STANDING", "detail": f"{name} states no standing"})
        elif record["standing"] not in contract["standings"]:
            defects.append({"code": "UNKNOWN_STANDING",
                            "detail": f"{name} stands {record['standing']}, "
                                      f"which this contract does not declare"})

        if record["landing"] is None:
            defects.append({"code": "UNDECLARED_LANDING",
                            "detail": f"{name} states no landing"})
        elif record["landing"] not in contract["landings"]:
            defects.append({"code": "UNKNOWN_LANDING",
                            "detail": f"{name} lands as {record['landing']}, "
                                      f"which this contract does not list"})

        if record["standing"] == "EFFECTIVE" and not (set(record["paths"]) & reached):
            defects.append({
                "code": "FALSE_EFFECTIVE",
                "detail": f"{name} stands EFFECTIVE and names no path verify or lint reaches",
            })
        if (record["standing"] in {"ADMITTED", "RATIFIED", "EFFECTIVE"}
                and record["landing"] in {"fixture", "lint"}):
            present = [path for path in record["paths"] if (ROOT / path).exists()]
            if not present:
                defects.append({
                    "code": "FALSE_ADMITTED",
                    "detail": f"{name} stands {record['standing']} with a "
                              f"{record['landing']} landing and names no path in the tree",
                })

    recorded = sum(1 for record in records if record["standing"] == "RECORDED")
    summary = SUMMARY.search(page)
    if summary is None:
        defects.append({"code": "HEADER_DISAGREES",
                        "detail": "the page states no 'Standing now' summary"})
    else:
        if int(summary.group("count")) != recorded:
            defects.append({
                "code": "HEADER_DISAGREES",
                "detail": f"the page says {summary.group('count')} RECORDED and "
                          f"its entries hold {recorded}",
            })
        if int(summary.group("threshold")) != contract["drain"]["threshold"]:
            defects.append({
                "code": "HEADER_DISAGREES",
                "detail": f"the page says threshold {summary.group('threshold')} and "
                          f"the contract declares {contract['drain']['threshold']}",
            })
    return defects


def drain(page: str, contract: dict) -> dict:
    """How close the inbox is to its declared drain, which never refuses."""
    records = entries(page)
    recorded = sum(1 for record in records if record["standing"] == "RECORDED")
    threshold = contract["drain"]["threshold"]
    return {
        "entries": len(records),
        "recorded": recorded,
        "threshold": threshold,
        "due": recorded >= threshold,
        "refuses": bool(contract["drain"]["refuses"]),
    }


def cmd_check(_: argparse.Namespace) -> int:
    contract = _contract()
    page = _text(PAGE)
    defects = grade(page, contract)
    state = drain(page, contract)

    print(f"lessons: {state['entries']} entries, {state['recorded']} RECORDED, "
          f"threshold {state['threshold']}")
    by_standing: dict[str, int] = {}
    for record in entries(page):
        by_standing[record["standing"] or "none"] = by_standing.get(record["standing"] or "none", 0) + 1
    for standing in sorted(by_standing):
        print(f"  {standing:12} {by_standing[standing]}")
    if state["due"]:
        print(f"  DEBT      the drain is due at {state['threshold']} and the page holds "
              f"{state['recorded']}; recorded, not refused")

    for defect in defects:
        print(f"  {defect['code']}: {defect['detail']}")
    if defects:
        print(f"FAIL: {len(defects)} lessons-loop defect(s)")
        return 1
    print("PASS: every entry declares a landing and no standing outruns its evidence")
    return 0


def cmd_read(_: argparse.Namespace) -> int:
    """Print the entries and the drain state as JSON."""
    page, contract = _text(PAGE), _contract()
    print(json.dumps({"entries": entries(page), "drain": drain(page, contract)},
                     indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="grade the page against the loop").set_defaults(run=cmd_check)
    sub.add_parser("read", help="print the entries and the drain state").set_defaults(run=cmd_read)
    args = parser.parse_args(argv)
    if not getattr(args, "run", None):
        return cmd_check(args)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
