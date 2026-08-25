#!/usr/bin/env python3
"""Hold the Asset Service to its recorded conformance baseline.

`services/asset/conformance/BASELINE.md` records how the reference participant
scored against the frozen scenarios on a stated date. That record is only worth
keeping if something notices when reality leaves it, so this runs the documented
observation command, grades it through the frozen oracle, and compares.

The participant is expected to fail every requirement today; that is the
declared work surface, not a defect. This refuses on *divergence* — a new
failure, or a recorded failure that quietly started passing without the
baseline being updated to say so.

The oracle and scenarios are frozen during participant repair. Nothing here
edits either; it only invokes the command `services/asset/conformance/README.md`
already documents.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "services" / "asset" / "conformance" / "BASELINE.md"
OBSERVER = ROOT / "services" / "asset" / "scripts" / "conformance_observations.py"
SCENARIOS = ROOT / "conformance" / "scenarios.json"
ORACLE = ROOT / "conformance" / "run.py"


def recorded(baseline_text: str) -> dict[str, str]:
    """Requirement -> recorded verdict, from the BASELINE.md result table."""
    verdicts = {}
    for line in baseline_text.splitlines():
        if not line.startswith("| PROD-I-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        requirement = re.match(r"(PROD-I-\d+)", cells[0])
        if requirement:
            verdicts[requirement.group(1)] = cells[1]
    return verdicts


def observed(root: Path = ROOT) -> dict[str, str]:
    """Requirement -> verdict, by running the documented observation command."""
    env_path = str(root / "services" / "asset" / "src")
    with tempfile.TemporaryDirectory() as work:
        report = Path(work) / "observations.json"
        run = subprocess.run([sys.executable, str(OBSERVER)], cwd=root,
                             capture_output=True, text=True,
                             env={**_env(), "PYTHONPATH": env_path})
        if run.returncode:
            raise SystemExit(f"FAIL: the observation adapter refused\n{run.stderr.strip()}")
        report.write_bytes(run.stdout.encode("utf-8"))
        graded = subprocess.run(
            [sys.executable, str(ORACLE), "--cases", str(SCENARIOS),
             "--observations", str(report), "--json"],
            cwd=root, capture_output=True, text=True)
    if not graded.stdout.strip():
        raise SystemExit(f"FAIL: the oracle returned nothing\n{graded.stderr.strip()}")
    report_json = json.loads(graded.stdout)
    if report_json.get("suite") == "INVALID":
        raise SystemExit(f"FAIL: the oracle refused the report: {report_json.get('refused')}")
    return {result["requirement"]: result["verdict"] for result in report_json["results"]}


def _env() -> dict[str, str]:
    import os
    return dict(os.environ)


def compare(record: dict[str, str], live: dict[str, str]) -> list[str]:
    """Divergences between the recorded baseline and the current run."""
    divergences = []
    for requirement in sorted(set(record) | set(live)):
        was, now = record.get(requirement), live.get(requirement)
        if was is None:
            divergences.append(f"{requirement}: graded {now} but BASELINE.md does not record it")
        elif now is None:
            divergences.append(f"{requirement}: recorded {was} but the run did not grade it")
        elif was != now:
            direction = "improved" if was == "FAIL" else "regressed"
            divergences.append(
                f"{requirement}: recorded {was}, now {now} — {direction}; "
                "update BASELINE.md in the same change that moved it")
    return divergences


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--show", action="store_true",
                        help="print each requirement's recorded and current verdict")
    args = parser.parse_args(argv)

    record = recorded(BASELINE.read_bytes().decode("utf-8"))
    if not record:
        print("FAIL: BASELINE.md records no requirement verdicts")
        return 1
    live = observed()
    divergences = compare(record, live)

    if args.show:
        for requirement in sorted(record, key=lambda r: int(r.rsplit("-", 1)[1])):
            print(f"  {requirement:<12} recorded {record[requirement]:<6} "
                  f"now {live.get(requirement, '—')}")

    if divergences:
        for divergence in divergences:
            print(f"FAIL: {divergence}")
        return 1
    failing = sum(1 for verdict in live.values() if verdict != "PASS")
    print(f"PASS: participant matches its recorded baseline "
          f"({len(live)} requirements, {failing} failing as recorded)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
