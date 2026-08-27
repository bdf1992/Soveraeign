#!/usr/bin/env python3
"""Grade a surface against the AI-native standard, and refuse to be told the answer.

`AI-NATIVE.md` states four scored axes, one human judgement, nine qualifications and a
derived verdict. It states them in prose, so until now every claim that something here is
AI-native was an opinion someone typed. `contracts/ai-native-qualifications.json` compiles
that document, `contracts/ai-native-assessment.schema.json` shapes one reading, and
`scripts/sovainative/` derives the verdict from the recorded scores.

`grade` reads one assessment record, or every recorded one. `selfcheck` grades the declared
corpus and proves every refusal fires. `scenarios` prints what each qualification rests on
and whether that evidence executes yet. Nothing here writes standing, and a derived
`SOVERAEIGN_QUALIFIED` is evidence for an acceptance packet, never the acceptance.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovainative import standard  # noqa: E402
from sovainative.grade import grade  # noqa: E402


def _report(path: Path, result: dict) -> bool:
    """Print one reading and say whether it carried a defect."""
    shown = path.relative_to(standard.ROOT).as_posix()
    print(f"{shown}: {result['state']}"
          + (f" -> {result['verdict']}" if result["verdict"] else ""))
    for defect in result["defects"]:
        print(f"  {defect['code']}: {defect['detail']}")
    for held in result["held_by"]:
        print(f"  held: {held}")
    return bool(result["defects"])


def cmd_grade(args: argparse.Namespace) -> int:
    """Grade one assessment record, or every recorded one."""
    table, schema, statuses, registry = standard.context()
    targets = [Path(args.path)] if args.path else sorted(standard.ASSESSMENTS.glob("*.json"))
    if not targets:
        print("no assessment records to grade")
        return 0
    failed = False
    for path in targets:
        failed |= _report(path, grade(standard.read(path), table, schema, statuses, registry))
    return 1 if failed else 0


def cmd_scenarios(args: argparse.Namespace) -> int:
    """Print what each qualification rests on and whether that evidence executes yet."""
    table = standard.load_table()
    statuses = standard.scenario_status(standard.ROOT, table)
    executable = set(table["executable_scenario_status"])
    for name, entry in table["qualifications"].items():
        cited = entry["evidenced_by"]
        reads = ", ".join(f"{c}={statuses.get(c, 'ABSENT')}" for c in cited)
        ready = all(statuses.get(c) in executable for c in cited)
        print(f"{'READY ' if ready else 'SEEDED'} {name:24} {reads}")
    print(f"\n{sum(1 for s in statuses.values() if s in executable)} of {len(statuses)} "
          "founding scenarios can evidence a qualification today")
    return 0


def _compare(case: dict, result: dict) -> list[str]:
    """Every way one graded case differs from what the corpus declared."""
    failures = []
    for field in ("state", "verdict"):
        if case["expected"].get(field) != result[field]:
            failures.append(f"{case['id']}: expected {field} {case['expected'].get(field)!r}, "
                            f"read {result[field]!r}")
    codes = sorted(d["code"] for d in result["defects"])
    expected = sorted(case["expected"].get("defects", []))
    if expected != codes:
        failures.append(f"{case['id']}: expected defects {expected}, read {codes}")
    return failures


def selfcheck() -> list[str]:
    """Grade the declared corpus; every refusal in the table must fire at least once."""
    table, schema, statuses, registry = standard.context()
    cases = standard.read(standard.CORPUS)
    assert isinstance(cases, list)
    fired: set[str] = set()
    failures: list[str] = []
    for case in cases:
        result = grade(case["record"], table, schema, statuses, registry)
        fired.update(d["code"] for d in result["defects"])
        failures += _compare(case, result)
    return failures + [f"no case proves {code} fires"
                       for code in sorted(set(table["refusals"]) - fired)]


def cmd_selfcheck(args: argparse.Namespace) -> int:
    """Report the corpus grading."""
    failures = selfcheck()
    for failure in failures:
        print(f"FAIL {failure}")
    cases = standard.read(standard.CORPUS)
    assert isinstance(cases, list)
    print(f"{'FAIL' if failures else 'PASS'}: {len(cases)} case(s), "
          f"{len(standard.load_table()['refusals'])} declared refusal(s)")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    """Route one subcommand."""
    parser = argparse.ArgumentParser(description="Grade a surface against AI-NATIVE.md.")
    sub = parser.add_subparsers(dest="command", required=True)
    graded = sub.add_parser("grade", help="grade one assessment record, or every recorded one")
    graded.add_argument("path", nargs="?", help="path to an assessment record")
    graded.set_defaults(handler=cmd_grade)
    sub.add_parser("scenarios", help="what each qualification rests on").set_defaults(
        handler=cmd_scenarios)
    sub.add_parser("selfcheck", help="grade the declared corpus").set_defaults(
        handler=cmd_selfcheck)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
