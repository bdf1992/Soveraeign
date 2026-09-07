"""Discovery and reuse: prove the P15-X3 vertical slice closes, and that it can fail.

`run --principal ID` is the live reading: a participant with no private history reads the
artifact alone for the result `custody:phase-1-5/fresh-participation` carries at
`WITNESSED`, reconstructs why it stands from the witness record, its receipts, the bytes
now at every address the witness observed and the merge that landed it, restores the
node's journal to the head the witness holds outside the export, enters that node as the
principal it declares, and grades P15-Q3.1 and P15-Q3.2 on what it resolved. Whether the
node admits that principal is read from the node's records. `selfcheck` proves the reader
discriminates against a fixture artifact whose result a fixture principal built under a
fixture root: the positive variant passes and each defeating variant fails exactly the
predicates it declares. Neither command witnesses anything; a passing run is a build claim.
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

from sovreuse import fixture, reuse  # noqa: E402
from sovsession import principals, store  # noqa: E402

def _render(result: dict) -> str:
    lines = [f"discovery and reuse: {'PASS' if result['passed'] else 'FAIL'}"]
    lines += [f"  {step}" for step in result["trace"]]
    for predicate, defects in result["grades"].items():
        lines.append(f"  {predicate}: {'holds' if not defects else '; '.join(defects)}")
    lines += [f"  defect: {defect}" for defect in result["other_defects"]]
    facts = result["facts"]
    if facts["work_state_declared"] != facts["work_state_derived"]:
        lines.append(f"  note: member declares work_state {facts['work_state_declared']}; "
                     f"the history reads {facts['work_state_derived']}")
    return "\n".join(lines)


def cmd_run(args: argparse.Namespace) -> int:
    """The live reading: this repository as the artifact, this host's store as inventory."""
    principal_id = args.principal or os.environ.get(principals.ENV_PRINCIPAL, "").strip()
    if not principal_id:
        print("REFUSED PRINCIPAL_REQUIRED: declare the registered principal this participant "
              "speaks as with --principal or SOV_PRINCIPAL; the registry names, it does not guess")
        return 2
    registry = Path(args.registry) if args.registry else None
    sessions = Path(args.sessions_dir) if args.sessions_dir else store.store_dir(ROOT)
    with tempfile.TemporaryDirectory() as temp:
        result = reuse.run(ROOT, ROOT, Path(temp), principal_id, registry=registry,
                           sessions_dir=sessions)
    print(json.dumps(result, indent=2, sort_keys=True, default=str) if args.as_json
          else _render(result))
    return 0 if result["passed"] else 1


def cmd_selfcheck(args: argparse.Namespace) -> int:
    """Prove the reader passes the fixture result and fails each defeat for its own reason."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        built = fixture.build(Path(temp))
        positive = fixture.run_variant(built, "positive", Path(temp))
        if not positive["passed"]:
            failures.append("positive variant failed: " + _render(positive))
        for variant, expected in fixture.EXPECTED_FAILURES.items():
            result = fixture.run_variant(built, variant, Path(temp))
            for predicate in reuse.PREDICATES:
                defects = result["grades"][predicate]
                if predicate in expected and expected[predicate] not in defects:
                    failures.append(f"{variant}: {predicate} did not fail with "
                                    f"{expected[predicate]!r}: {defects}")
                if predicate not in expected and defects:
                    failures.append(f"{variant}: {predicate} failed alongside "
                                    f"{', '.join(sorted(expected))}: " + "; ".join(defects))
    if failures:
        print("FAIL: discovery and reuse probe does not discriminate")
        print("\n".join("  " + line for line in failures))
        return 1
    print(f"PASS: discovery and reuse slice closes on the positive variant and "
          f"{len(fixture.EXPECTED_FAILURES)} defeating variants each fail their own predicates for "
          "the reason they declare")
    return 0


def main(argv: list[str] | None = None) -> int:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--json", action="store_true", dest="as_json")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], parents=[shared])
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", parents=[shared],
                         help="one live discovery and reuse as a declared principal")
    run.add_argument("--principal", help="registered principal id this participant speaks as")
    run.add_argument("--registry", help="principal registry to read instead of "
                                        "contracts/principals.json")
    run.add_argument("--sessions-dir", help="session store to read inventory from instead "
                                            "of this repository's shared store")
    run.set_defaults(func=cmd_run)
    check = sub.add_parser("selfcheck", parents=[shared],
                           help="prove the probe passes and can fail, offline")
    check.set_defaults(func=cmd_selfcheck)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
