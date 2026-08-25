#!/usr/bin/env python3
"""Build, inspect, and invoke the derived Node Interface."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovnode.bindings import (  # noqa: E402
    HUMAN, MODEL, BindingRefusal, invocation_request, render_human, render_model, resolve,
)
from sovnode.composition import LocalActionPath  # noqa: E402
from sovnode.interface_inputs import REFERENCE, rebuild  # noqa: E402
from sovnode.proof import run as run_proof  # noqa: E402

DEFAULT_STATE = ROOT / ".local" / "node-interface"


def _current() -> dict[str, Any]:
    document, defects = rebuild()
    if defects:
        raise RuntimeError("; ".join(defects))
    return document


def command_build(_: argparse.Namespace) -> int:
    document = _current()
    REFERENCE.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    counts = document["counts"]
    print(f"BUILT: {REFERENCE.relative_to(ROOT)} — "
          f"{counts['declared']} declared / {counts['reachable']} reachable / "
          f"{counts['observed']} observed")
    print("Standing note: the projection is PROPOSED and grants nothing.")
    return 0


def command_check(_: argparse.Namespace) -> int:
    document, defects = rebuild()
    for defect in defects:
        print(f"DEFECT: {defect}")
    if defects:
        return 1
    if not REFERENCE.exists():
        print(f"FAIL: {REFERENCE.relative_to(ROOT)} has not been built")
        return 1
    if json.loads(REFERENCE.read_text("utf-8")) != document:
        print("FAIL: Node Interface is stale; run `python scripts/sov_interface.py build`")
        return 1
    counts = document["counts"]
    print("PASS: Node Interface matches its sources — "
          f"{counts['declared']} declared, {counts['bound']} bound, "
          f"{counts['policy_active']} policy-active, {counts['reachable']} reachable, "
          f"{counts['observed']} observed")
    print("Standing note: these are independent facts, not a health score or authority.")
    return 0


def command_show(args: argparse.Namespace) -> int:
    document = _current()
    if not args.operation:
        print(json.dumps({key: document[key] for key in
                          ("interface_schema", "status", "node", "kernel", "counts", "seams",
                           "omissions")},
                         indent=2, sort_keys=True))
        return 0
    record = resolve(document, args.operation)
    if args.binding == HUMAN:
        print(render_human(record))
    else:
        print(render_model(record))
    return 0


def _arguments(pairs: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for pair in pairs:
        name, separator, value = pair.partition("=")
        if not separator or not name:
            raise BindingRefusal("ARGUMENT_INVALID", pair)
        result[name] = value
    return result


def command_invoke(args: argparse.Namespace) -> int:
    try:
        document = _current()
        request = invocation_request(
            document, args.operation, args.binding, args.actor, args.scope,
            _arguments(args.arguments))
    except BindingRefusal as refusal:
        print(f"REFUSED {refusal.code}: {refusal}")
        return 0
    state = Path(args.state_root) if args.state_root else DEFAULT_STATE
    with LocalActionPath(state) as node:
        receipt = node.dispatch(request)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


def command_prove(_: argparse.Namespace) -> int:
    print(json.dumps(run_proof(), indent=2, sort_keys=True))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="sov_interface", description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("build", help="rebuild the checked-in read projection").set_defaults(
        handler=command_build)
    sub.add_parser("check", help="refuse stale or contradictory inputs").set_defaults(
        handler=command_check)
    show = sub.add_parser("show", help="render the Node or one operation")
    show.add_argument("operation", nargs="?")
    show.add_argument("--binding", choices=(HUMAN, MODEL), default=HUMAN)
    show.set_defaults(handler=command_show)
    invoke = sub.add_parser("invoke", help="call one reachable operation through Gateway")
    invoke.add_argument("operation")
    invoke.add_argument("arguments", nargs="*", metavar="name=value")
    invoke.add_argument("--binding", choices=(HUMAN, MODEL), default=HUMAN)
    invoke.add_argument("--actor", required=True)
    invoke.add_argument("--scope", required=True)
    invoke.add_argument("--state-root")
    invoke.set_defaults(handler=command_invoke)
    sub.add_parser("prove", help="drive Human/Model parity and defeating cases").set_defaults(
        handler=command_prove)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except (BindingRefusal, RuntimeError) as error:
        code = error.code if isinstance(error, BindingRefusal) else "INTERFACE_INVALID"
        print(f"REFUSED {code}: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
