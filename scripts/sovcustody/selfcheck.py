"""Prove every declared custody refusal fires against a fixture that defeats it.

Split from `sovcustody.commands` when the closure-check judge was added: the
subcommand bodies file was at its module ceiling, and a selfcheck that must
enumerate every judge in the package is its own responsibility rather than one
more command body.

A refusal nothing reaches is a refusal nobody has proved fires, which is why an
unreached code fails this reading as loudly as a case that did not discriminate.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import circuit as circuitmod  # noqa: E402
from sovcustody import closures as closuresmod  # noqa: E402
from sovcustody import estimate as estimatemod  # noqa: E402
from sovcustody import model as modelmod  # noqa: E402
from sovcustody import phase as phasemod  # noqa: E402

FIXTURES = ROOT / "conformance" / "fixtures" / "custody" / "circuit-cases.json"

def command_selfcheck(args: argparse.Namespace) -> int:
    """Prove every declared refusal fires against a fixture that defeats it."""
    cases = json.loads(FIXTURES.read_bytes().decode("utf-8"))
    expected = set(circuitmod.declared_refusals()) | set(estimatemod.declared_refusals()) \
        | set(modelmod.REFUSALS) | set(closuresmod.REFUSALS) \
        | set(phasemod.REFUSALS)
    fired: set[str] = set()
    failures: list[str] = []

    for case in cases:
        kind = case["judge"]
        if kind == "circuit":
            defects = circuitmod.judge_advance(
                case.get("from_stage", ""), case["to_stage"], case.get("evidence") or {},
                set(case.get("required_dimensions") or []))
        elif kind == "estimate":
            defects = estimatemod.grade(case.get("estimate"),
                                        set(case.get("required") or []), case.get("stage"))
        elif kind == "collection":
            defects = modelmod.grade_collection(case["custodies"])
        elif kind == "registry":
            defects = estimatemod.grade_registry(case["registry"])
        elif kind == "closure-live":
            _, defects = closuresmod.grade_live(case["custodies"],
                                                Path(case.get("root") or ROOT))
        elif kind == "closure":
            defects = closuresmod.grade_collection(case["custodies"],
                                                   Path(case.get("root") or ROOT))
        elif kind == "phase":
            defects = phasemod.grade(case["phase"], set(case.get("custody_ids") or []))
        else:
            defects = modelmod.grade(case["custody"], set(case.get("seats") or []))
        codes = {code for code, _ in defects}
        fired |= codes
        want = set(case.get("expect_refusals") or [])
        if case["polarity"] == "positive" and codes:
            failures.append(f"{case['id']}: admissible case refused by {sorted(codes)}")
        if case["polarity"] == "defeating" and not want <= codes:
            failures.append(f"{case['id']}: expected {sorted(want - codes)}, got {sorted(codes)}")

    # `fired` can carry codes outside the declared set - SCHEMA, raised by the
    # collection judge - so the reached count is intersected rather than taken raw.
    unreachable = sorted(expected - fired)
    reached = fired & expected
    print(f"{len(cases)} case(s), {len(reached)}/{len(expected)} declared refusals reached")
    for failure in failures:
        print(f"  FAIL  {failure}")
    for code in unreachable:
        print(f"  UNREACHED  {code}")
    if failures or unreachable:
        return 1
    print("selfcheck PASS")
    return 0
