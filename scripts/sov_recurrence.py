"""Definition recurrence: prove the P15-X4 reading closes, and that it can fail.

`run` is the live reading: settled experience under this repository, meaning the custody
members an independent participant observed and that landed; a candidate Definition
synthesized from that basis and cited back to it; an observation of whether synthesis moved
any governing record; and the ten governed primitives resolved and composed under an
institution the founder did not predict. P15-Q4.1 to Q4.3 are graded by
`conformance/commissioning.py`, which imports no participant code.

The basis is the settled member addresses and nothing else. An earlier revision also
scanned the observation directories for records naming a member, which counted a *refusal*
of one member as evidence that another had been observed; a witness caught it and the scan
is gone. What that leaves is stated rather than implied: this reader believes the custody
record's own `standing` and `work_state`. A member falsely written as `WITNESSED` would be
admitted, and no independent attribution exists here to refuse it.

`selfcheck` proves the reader discriminates against a fixture basis under a fixture root:
the positive variant passes, cites no member nobody witnessed, and each defeating variant
fails exactly the predicates it declares. Neither command witnesses anything; a passing run
is a build claim.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovrecurrence import fixture, recurrence  # noqa: E402


def _render(result: dict) -> str:
    lines = [f"definition recurrence: {'PASS' if result['passed'] else 'FAIL'}"]
    lines += [f"  {step}" for step in result["trace"]]
    for predicate, defects in result["grades"].items():
        lines.append(f"  {predicate}: {'holds' if not defects else '; '.join(defects)}")
    lines += [f"  defect: {defect}" for defect in result["other_defects"]]
    lines.append("  candidate: " + result["candidate"]["proposal_id"])
    lines.append("    " + result["candidate"]["claim"])
    return "\n".join(lines)


def cmd_run(args: argparse.Namespace) -> int:
    """The live reading: this repository as the basis, its own custody collection as source."""
    result = recurrence.run(ROOT)
    print(json.dumps(result, indent=2, sort_keys=True, default=str) if args.as_json
          else _render(result))
    return 0 if result["passed"] else 1


def cmd_selfcheck(args: argparse.Namespace) -> int:
    """Prove the reader passes the fixture basis and fails each defeat for its own reason."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        positive = fixture.run_variant(fixture.build(Path(temp) / "positive"), "positive")
        if not positive["passed"]:
            failures.append("positive variant failed: " + _render(positive))
        cited = set(positive["candidate"]["source_addresses"])
        if fixture.BUILT_ONLY_ADDRESS in cited:
            failures.append(f"positive variant cited {fixture.BUILT_ONLY_ADDRESS}, which no "
                            "independent participant observed")
        for variant, expected in fixture.EXPECTED_FAILURES.items():
            built = fixture.build(Path(temp) / variant)
            result = fixture.run_variant(built, variant)
            if result["passed"]:
                failures.append(f"{variant}: the reading passed; a declared defeat that does "
                                "not fail is not a defeat")
            for predicate in recurrence.PREDICATES:
                defects = result["grades"][predicate]
                if defects != expected.get(predicate, []):
                    failures.append(f"{variant}: {predicate} read {defects}; declared "
                                    f"{expected.get(predicate, [])}")
    if failures:
        print("FAIL: definition recurrence probe does not discriminate")
        print("\n".join("  " + line for line in failures))
        return 1
    print(f"PASS: definition recurrence closes on the positive variant, cites no unwitnessed "
          f"member, and {len(fixture.EXPECTED_FAILURES)} defeating variants each fail their own "
          "predicates for exactly the defects they declare")
    return 0


def main(argv: list[str] | None = None) -> int:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--json", action="store_true", dest="as_json")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], parents=[shared])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", parents=[shared],
                         help="one live definition-recurrence reading of this repository")
    run.set_defaults(func=cmd_run)
    check = sub.add_parser("selfcheck", parents=[shared],
                           help="prove the probe passes and can fail, offline")
    check.set_defaults(func=cmd_selfcheck)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
