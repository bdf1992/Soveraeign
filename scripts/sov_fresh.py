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

`open-office` is the act itself, performed on a persisted node under the registry's root
principal at that principal's recorded direction; `run --node-state` then enters that
node as a participant and seeds nothing. The node's journal is the receipt for both.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovfresh import layers, node as nodelayer, probe  # noqa: E402
from sovnode import journal  # noqa: E402
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
    node_state = Path(args.node_state) if args.node_state else None
    with tempfile.TemporaryDirectory() as temp:
        try:
            result = probe.run(ROOT, Path(temp), principal_id, args.variant,
                               registry=registry, issuer=args.issuer, node_state=node_state)
        except ValueError as refusal:
            print(f"REFUSED VARIANT_NOT_ADMITTED: {refusal}")
            return 2
    print(json.dumps(result, indent=2, sort_keys=True) if args.as_json else _render(result))
    return 0 if result["passed"] else 1


def _shown(path: Path) -> str:
    """A path as the record names it: repository-relative when inside the repository."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def cmd_open_office(args: argparse.Namespace) -> int:
    """Seat the registry's root as this node's root issuer and grant one operator.

    The act is the issuer's; this command performs it at the issuer's recorded direction
    and refuses any other name by the probe's own rule. Every grant lands in the node's
    journal with `granted_by`, which is the receipt. The act line appended beside the
    state names the registry in force by digest and the journal head before and after;
    it proves nothing the journal does not, and says so.
    """
    registry = Path(args.registry) if args.registry else ROOT / principals.REGISTRY_PATH
    root = layers.root_principal(ROOT, registry)
    if not args.issuer or args.issuer != root:
        print(f"REFUSED {nodelayer.PROBE_ISSUER_GATE}: issuer {args.issuer!r} is not the "
              f"registry's root principal {root!r}; nothing issued")
        return 2
    state = Path(args.node_state)
    capabilities = dict(item.split("=", 1) for item in args.capability or [])
    with nodelayer.open_node_at(state) as node:
        before = node.record.head()
        try:
            records = nodelayer.open_office(node, args.issuer, args.operator, capabilities)
        except nodelayer.console_authority.AuthorityRefused as refused:
            print(f"REFUSED AUTHORITY_REFUSED: the node refused {args.issuer}: {refused}")
            return 2
        after = node.record.head()
    act = {
        "act": "open-office", "node_state": str(state), "issuer": args.issuer,
        "operator": args.operator, "direction": args.direction,
        "directed_in": args.directed_in,
        "registry": {"path": _shown(registry),
                     "digest": "sha256:" + sha256(registry.read_bytes()).hexdigest()},
        "record_head_before": before, "record_head_after": after,
        "grants": [{k: r[k] for k in ("grant_id", "capability", "scope", "granted_by",
                                       "granted_at", "entry_id")} for r in records],
        "proves": "nothing the journal does not; the journal entries above are the receipt",
    }
    with (state / "office-acts.ndjson").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(act, sort_keys=True) + "\n")
    print(json.dumps(act, indent=2, sort_keys=True) if args.as_json else "\n".join(
        [f"office opened at {state} by {args.issuer} for {args.operator}"]
        + [f"  {r['grant_id']}  {r['capability']}  {r['scope']}" for r in records]))
    return 0


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


def _persisted_cases(state: Path, registry: Path) -> list[str]:
    """A node opened once under the fixture root, then entered by two participants."""
    failures: list[str] = []
    with nodelayer.open_node_at(state) as node:
        nodelayer.open_office(node, FIXTURE_ISSUER, FIXTURE_PRINCIPAL,
                              {"read:registry": nodelayer.SCOPE})
    granted = probe.run(ROOT, state.parent / "granted", FIXTURE_PRINCIPAL,
                        registry=registry, node_state=state)
    if not granted["passed"]:
        failures.append("persisted node, granted operator: " + _render(granted))
    ungranted = probe.run(ROOT, state.parent / "ungranted", "principal:bdo",
                          registry=registry, node_state=state)
    if not ungranted["grades"]["P15-Q1.3"] or ungranted["grades"]["P15-Q1.1"]:
        failures.append("persisted node, operator with no grant: Q1.3 must fail alone: "
                        + _render(ungranted))
    failures.extend(_custody_cases(state, registry))
    return failures


def _grant_count(state: Path) -> int:
    with nodelayer.open_node_at(state) as node:
        return sum(1 for entry in node.record.reconstruct()
                   if entry["payload"].get("record_kind") == "authority-grant")


def _custody_cases(state: Path, registry: Path) -> list[str]:
    """The journal leaves one node and carries the office into another, or refuses."""
    failures: list[str] = []
    exported = journal.export(state, state.parent / "exports")
    restored = state.parent / "restored"
    journal.restore(exported["path"], restored, exported["head"])
    before = _grant_count(restored)
    carried = probe.run(ROOT, state.parent / "carried", FIXTURE_PRINCIPAL,
                        registry=registry, node_state=restored)
    if not carried["passed"]:
        failures.append("restored node: the carried office did not admit the operator: "
                        + _render(carried))
    if _grant_count(restored) != before:
        failures.append("restored node: entering it issued a grant; the office must carry over")
    document = json.loads(exported["path"].read_text(encoding="utf-8"))
    document["entries"] = document["entries"][:-1]
    document["entry_count"] -= 1
    document["head_digest"] = document["entries"][-1]["entry_digest"]
    truncated = state.parent / "exports" / "truncated.json"
    truncated.write_text(json.dumps(document), encoding="utf-8")
    try:
        journal.restore(truncated, state.parent / "truncated", exported["head"])
        failures.append("truncated export: restore with the outside head did not refuse")
    except journal.custody.TruncatedExport:
        pass
    return failures


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
        failures.extend(_persisted_cases(Path(temp) / "persisted", registry))
    if failures:
        print("FAIL: fresh participation probe does not discriminate")
        print("\n".join("  " + line for line in failures))
        return 1
    print(f"PASS: fresh participation slice closes on the positive variant, "
          f"{len(EXPECTED_FAILURES)} defeating variants each fail their own predicates, and "
          "the office carries across an export and restore")
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
    run.add_argument("--node-state", help="enter the persisted node whose stores live "
                                          "here instead of opening a temporary one")
    run.set_defaults(func=cmd_run)
    office = sub.add_parser("open-office", parents=[shared],
                            help="seat the registry root as a persisted node's issuer and "
                                 "grant one operator, at the root's recorded direction")
    office.add_argument("--node-state", required=True)
    office.add_argument("--issuer", required=True, help="must be the registry's root principal")
    office.add_argument("--operator", required=True, help="the durable principal granted")
    office.add_argument("--capability", action="append", metavar="CAPABILITY=SCOPE",
                        help="a grant beyond open:session, repeatable")
    office.add_argument("--direction", required=True,
                        help="the issuer's own words directing this act")
    office.add_argument("--directed-in", required=True,
                        help="where those words are recorded, for example a session id")
    office.add_argument("--registry")
    office.set_defaults(func=cmd_open_office)
    check = sub.add_parser("selfcheck", parents=[shared],
                           help="prove the probe passes and can fail, offline")
    check.set_defaults(func=cmd_selfcheck)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
