#!/usr/bin/env python3
"""Make the witness layer measurable instead of merely declared.

`witness/README.md` states what a witness record and a probe are for. Nothing
recomputed any of it: receipts kept reading as evidence about the working tree
after the tree moved, and probes were never executed again after the day they
were written.

Three commands, none of which reads a declaration where it could measure a file:

    records   recompute every receipt's digests against the working tree
    probes    parse every probe and require its declared reach to still exist
    run       execute every probe and grade the process and the report it emits

`records` and `probes` are wired into `scripts/verify.py`. `run` is not: the
probes shipped on PR #119 cost 12.7s together, against a 15s ceiling for the
whole suite, so executing them is an attended action.

`records` measures bytes. `probes` and `run` grade a probe partly on what it
declares about itself, which is the defect this file exists to catch appearing
inside the file. `sovwitness/probes.py` records exactly where that line falls and
what does catch a probe that misreports; it is not claimed to be caught here.

Nothing here settles standing. A receipt that still matches the tree is not
thereby correct, and a probe that still reaches its subject has not thereby
witnessed anything. This reports whether the evidence is still live; what it
earns stays the reader's judgement, and ratification stays Bdo's.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovwitness import probes as probe_grader  # noqa: E402
from sovwitness import records as record_grader  # noqa: E402


def _emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))


def records(root: Path, as_json: bool) -> int:
    """Grade every receipt against the bytes it says it observed."""
    results = record_grader.grade_all(root)
    failing = [item for item in results if item["verdict"] in record_grader.FAILING_VERDICTS]
    drifted = [item for item in results if item["verdict"] == record_grader.STALE_SUBJECT]
    if as_json:
        _emit({"receipts": results, "failing": len(failing), "drifted": len(drifted)}, True)
        return 1 if failing else 0

    for item in results:
        print(f"{item['verdict']:13} {item['receipt']} ({item['graded']} digest(s) recomputed)")
        for moved in item["moved"]:
            print(f"              {moved}")
        for defect in item["defects"]:
            print(f"              {defect}")
        for debt in item.get("debts", []):
            print(f"DEBT:         {item['receipt']}: {debt}")
    if drifted:
        print(f"DEBT: {len(drifted)} receipt(s) describe a subject that has since moved. "
              "That is a record ageing, not a record failing: each one still observes the "
              "commit it names, and no longer covers the working tree.")
    verdict = "FAIL" if failing else "PASS"
    print(f"{verdict}: {len(results)} witness receipt(s) graded, {len(failing)} unusable, "
          f"{len(drifted)} stale against their subject")
    return 1 if failing else 0


def probes(root: Path, as_json: bool) -> int:
    """Parse every probe and require the reach it declares to still be there."""
    results = [probe_grader.inspect(path, root) for path in probe_grader.modules(root)]
    join_defects, join_debts = probe_grader.joins(root)
    failing = [item for item in results if item["verdict"] in probe_grader.FAILING_VERDICTS]
    debts = [f"{item['probe']}: {debt}" for item in results for debt in item["debts"]]
    debts.extend(join_debts)
    if as_json:
        _emit({"probes": results, "join_defects": join_defects, "debts": debts,
               "failing": len(failing)}, True)
        return 1 if failing or join_defects else 0

    for item in results:
        print(f"{item['verdict']:5} {item['probe']} reaches {', '.join(item['reaches']) or '-'}")
        for defect in item["defects"]:
            print(f"      {defect}")
    for defect in join_defects:
        print(f"DEAD  {defect}")
    for debt in debts:
        print(f"DEBT: {debt}")
    verdict = "FAIL" if failing or join_defects else "PASS"
    print(f"{verdict}: {len(results)} witness probe(s) inspected, "
          f"{len(failing) + len(join_defects)} unreachable, {len(debts)} debt(s). "
          "Graded on the reach each probe declares; a probe that names a path it does "
          "not take is not caught here.")
    return 1 if failing or join_defects else 0


def run(root: Path, as_json: bool) -> int:
    """Execute every probe and read reaching out of the report, never the exit code."""
    results = [probe_grader.run(path, root) for path in probe_grader.modules(root)]
    failing = [item for item in results if item["verdict"] in probe_grader.FAILING_VERDICTS]
    if as_json:
        _emit({"probes": results, "failing": len(failing)}, True)
        return 1 if failing else 0

    for item in results:
        print(f"{item['verdict']:5} {item['probe']} (exit {item.get('exit_code', '-')})")
        for defect in item["defects"]:
            print(f"      {defect}")
    verdict = "FAIL" if failing else "PASS"
    print(f"{verdict}: {len(results)} witness probe(s) executed, {len(failing)} reported "
          "trouble reaching their subject. Whether a subject survived is not graded here, "
          "and a probe that misreports its own reaching is not caught here either.")
    return 1 if failing else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("command", nargs="?", default="records",
                        choices=("records", "probes", "run"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    return {"records": records, "probes": probes, "run": run}[args.command](
        args.root, args.as_json)


if __name__ == "__main__":
    raise SystemExit(main())
