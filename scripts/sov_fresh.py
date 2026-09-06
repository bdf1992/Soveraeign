"""Fresh participation: prove the P15-X1 vertical slice closes, and that it can fail.

`run --principal ID` is the live reading: a participant with no private history enters
a node of this repository's shape as the registered principal it declares, and the three
P15-Q1 predicates are graded on what it resolved. A fresh node has recorded no grant, so
P15-Q1.3 reads unmet until an issuer opens the node's permits office; `--issuer ID` lets
the run seed that first grant, and by the probe's own rule only under the name the registry
in force names as root. `selfcheck` proves the probe
discriminates against a temporary registry and a fixture issuer: the positive variant
passes and each defeating variant fails exactly the predicates it declares. Naming the
root seat as issuer shows the mechanism; it is not evidence that the seat acted. Neither
command witnesses anything; a passing run is a build claim.
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
FIXTURE_ISSUER = "principal:fixture-root"

EXPECTED_FAILURES = {
    "unregistered-principal": {"P15-Q1.1", "P15-Q1.3"},
    "work-dies-with-session": {"P15-Q1.2"},
    "no-grant": {"P15-Q1.3"},
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
    if result["node"]["admitted"]:
        lines.append(f"  node: {result['node']['admitted']}")
    return "\n".join(lines)


def cmd_run(args: argparse.Namespace) -> int:
    principal_id = args.principal or os.environ.get(principals.ENV_PRINCIPAL, "").strip()
    if not principal_id:
        print("REFUSED PRINCIPAL_REQUIRED: declare the registered principal this participant "
              "speaks as with --principal or SOV_PRINCIPAL; the registry names, it does not guess")
        return 2
    registry = Path(args.registry) if args.registry else None
    with tempfile.TemporaryDirectory() as temp:
        result = probe.run(ROOT, Path(temp), principal_id, args.variant, registry=registry,
                           issuer=args.issuer)
    print(json.dumps(result, indent=2, sort_keys=True) if args.as_json else _render(result))
    return 0 if result["passed"] else 1


def fixture_registry(temp: Path) -> Path:
    """The checked-in registry plus a fixture root and one fixture principal under it.

    The copy is read from the repository path directly, never from the environment, and
    exists so the self-check never asserts which model this host runs or issues anything
    in the real root's name. Both fixtures are labelled and live only for the run.
    """
    try:
        registry = json.loads((ROOT / principals.REGISTRY_PATH).read_text(encoding="utf-8"))
    except (OSError, ValueError) as failure:
        raise SystemExit(f"FAIL: principal registry could not be read: {failure}") from None
    registry["root_principal"] = FIXTURE_ISSUER
    registry["principals"].append({
        "principal_id": FIXTURE_ISSUER, "kind": "HUMAN", "durability": "EPHEMERAL",
        "controller": None,
        "anchor": {"kind": "fixture", "reference": "scripts/sov_fresh.py selfcheck"},
        "crossing_class": "in-node", "model": None, "delegation": None,
        "claim": {"claimed_at": "2026-09-06T00:00:00Z",
                  "claim_basis": "fixture root of a temporary node; self-check only",
                  "verification": "UNVERIFIED"},
        "verification_channel": {"kind": "local-file", "reference": "temporary"},
        "revoked": None,
    })
    registry["principals"].append({
        "principal_id": FIXTURE_PRINCIPAL, "kind": "MODEL", "durability": "EPHEMERAL",
        "controller": FIXTURE_ISSUER,
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
    with tempfile.TemporaryDirectory() as temp:
        registry = fixture_registry(Path(temp))
        positive = probe.run(ROOT, Path(temp) / "positive", FIXTURE_PRINCIPAL,
                             registry=registry, issuer=FIXTURE_ISSUER)
        if not positive["passed"]:
            failures.append("positive variant failed: " + _render(positive))
        for variant, expected in EXPECTED_FAILURES.items():
            result = probe.run(ROOT, Path(temp) / variant, FIXTURE_PRINCIPAL, variant,
                               registry=registry, issuer=FIXTURE_ISSUER)
            for predicate in probe.PREDICATES:
                failed = bool(result["grades"][predicate])
                if predicate in expected and not failed:
                    failures.append(f"{variant}: {predicate} did not fail")
                if predicate not in expected and failed:
                    failures.append(f"{variant}: {predicate} failed alongside "
                                    f"{', '.join(sorted(expected))}: "
                                    + "; ".join(result["grades"][predicate]))
            if result["other_defects"]:
                failures.append(f"{variant}: " + "; ".join(result["other_defects"]))
    if failures:
        print("FAIL: fresh participation probe does not discriminate")
        print("\n".join("  " + line for line in failures))
        return 1
    print(f"PASS: fresh participation slice closes on the positive variant and "
          f"{len(EXPECTED_FAILURES)} defeating variants each fail their own predicates")
    return 0


def main(argv: list[str] | None = None) -> int:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--json", action="store_true", dest="as_json")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], parents=[shared])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", parents=[shared],
                         help="one live fresh-participation run as a declared principal")
    run.add_argument("--principal", help="registered principal id this participant speaks as")
    run.add_argument("--issuer", help="seed the temporary node's first grant under this name; "
                                      "the probe accepts only the registry's root principal")
    run.add_argument("--registry", help="principal registry to read instead of "
                                        "contracts/principals.json")
    run.add_argument("--variant", default="positive", choices=sorted(probe.VARIANTS))
    run.set_defaults(func=cmd_run)
    check = sub.add_parser("selfcheck", parents=[shared],
                           help="prove the probe passes and can fail, offline")
    check.set_defaults(func=cmd_selfcheck)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
