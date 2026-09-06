"""Fresh participation: prove the P15-X1 vertical slice closes, and that it can fail.

`run --principal ID` is the live reading: a participant with no private history
enters this node from the artifact as the registered principal it declares, and the
three P15-Q1 predicates are graded on what it resolved. `selfcheck` proves the probe
discriminates: the positive variant passes and each declared defeating variant fails
its own predicate, against a temporary registry so the check claims no identity.
Neither command witnesses anything; a passing run is a build claim.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovfresh import probe  # noqa: E402
from sovsession import principals  # noqa: E402

FIXTURE_PRINCIPAL = "principal:fresh-probe"

EXPECTED_FAILURES = {
    "unregistered-principal": {"P15-Q1.1", "P15-Q1.3"},
    "work-dies-with-session": {"P15-Q1.2"},
    "borrowed-authority": {"P15-Q1.3"},
}
"""Which predicates each defeating variant must fail; every other predicate must hold.

An unidentified principal defeats fresh participation and identity separation at once,
which is the instrument reading correctly rather than two variants collapsed into one.
"""


def _render(result: dict) -> str:
    lines = [f"fresh participation [{result['variant']}]: "
             f"{'PASS' if result['passed'] else 'FAIL'}"]
    lines += [f"  {step}" for step in result["trace"]]
    for predicate, defects in result["grades"].items():
        lines.append(f"  {predicate}: {'holds' if not defects else '; '.join(defects)}")
    for defect in result["other_defects"]:
        lines.append(f"  defect: {defect}")
    return "\n".join(lines)


def cmd_run(args: argparse.Namespace) -> int:
    principal_id = args.principal or os.environ.get(principals.ENV_PRINCIPAL, "").strip()
    if not principal_id:
        print("REFUSED PRINCIPAL_REQUIRED: declare the registered principal this participant "
              "speaks as with --principal or SOV_PRINCIPAL; the registry names, it does not guess")
        return 2
    with tempfile.TemporaryDirectory() as temp:
        result = probe.run(ROOT, Path(temp), principal_id, args.variant)
    print(json.dumps(result, indent=2, sort_keys=True) if args.as_json else _render(result))
    return 0 if result["passed"] else 1


def _fixture_registry(temp: Path) -> Path:
    """The live registry plus one declared probe principal, controlled by the root.

    The copy exists so the self-check never asserts which model this host runs; the
    fixture principal is labelled as such and lives only for the run.
    """
    registry, reason = principals.load(ROOT)
    if registry is None:
        raise SystemExit(f"FAIL: {reason}")
    registry["principals"].append({
        "principal_id": FIXTURE_PRINCIPAL, "kind": "MODEL", "durability": "EPHEMERAL",
        "controller": registry["root_principal"],
        "anchor": {"kind": "fixture", "reference": "scripts/sov_fresh.py selfcheck"},
        "crossing_class": "in-node", "model": None, "delegation": None,
        "claim": {"claimed_at": "2026-09-06T00:00:00Z",
                  "claim_basis": "probe fixture; exists only for this self-check",
                  "verification": "UNVERIFIED"},
        "verification_channel": {"kind": "local-file", "reference": "temporary"},
        "revoked": None,
    })
    path = temp / "principals.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    return path


def cmd_selfcheck(args: argparse.Namespace) -> int:
    failures: list[str] = []
    saved = os.environ.get(principals.ENV_REGISTRY)
    with tempfile.TemporaryDirectory() as temp:
        os.environ[principals.ENV_REGISTRY] = str(_fixture_registry(Path(temp)))
        try:
            positive = probe.run(ROOT, Path(temp) / "positive", FIXTURE_PRINCIPAL)
            if not positive["passed"]:
                failures.append("positive variant failed: " + _render(positive))
            for variant, expected in EXPECTED_FAILURES.items():
                principal_id = ("principal:nobody" if variant == "unregistered-principal"
                                else FIXTURE_PRINCIPAL)
                result = probe.run(ROOT, Path(temp) / variant, principal_id, variant)
                for predicate in probe.PREDICATES:
                    failed = bool(result["grades"][predicate])
                    if predicate in expected and not failed:
                        failures.append(f"{variant}: {predicate} did not fail")
                    if predicate not in expected and failed:
                        failures.append(f"{variant}: {predicate} failed alongside "
                                        f"{', '.join(sorted(expected))}: "
                                        + "; ".join(result["grades"][predicate]))
        finally:
            if saved is None:
                os.environ.pop(principals.ENV_REGISTRY, None)
            else:
                os.environ[principals.ENV_REGISTRY] = saved
    if failures:
        print("FAIL: fresh participation probe does not discriminate")
        print("\n".join("  " + line for line in failures))
        return 1
    print(f"PASS: fresh participation slice closes on the positive variant and "
          f"{len(EXPECTED_FAILURES)} defeating variants each fail their own predicate")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", dest="as_json")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="one live fresh-participation run as a declared principal")
    run.add_argument("--principal", help="registered principal id this participant speaks as")
    run.add_argument("--variant", default="positive", choices=sorted(probe.VARIANTS))
    run.set_defaults(func=cmd_run)
    check = sub.add_parser("selfcheck", help="prove the probe passes and can fail, offline")
    check.set_defaults(func=cmd_selfcheck)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
