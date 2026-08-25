#!/usr/bin/env python3
"""Check a Model Binding, an invocation record, or a two-model parity pair.

Commands: ``binding PATH``, ``invocation PATH``, ``parity PATH PATH``, ``bindings``.
Exit codes: 0 accepted, 2 refused with a reason code, 1 the input could not be read.
An accepted result is not a grant, a witness, or a ratification; it says only that the
declaration and the recorded runtime do not contradict each other.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from adapter import BINDINGS_DIR, Refusal, check_binding, check_invocation  # noqa: E402
from adapter import check_parity, load_json  # noqa: E402


def _emit(result: dict) -> int:
    print(json.dumps(result, indent=2))
    return 0


def _refused(subject: str, refusal: Refusal) -> int:
    print(json.dumps({"outcome": "REFUSED", "subject": subject,
                      "reason_code": refusal.reason_code, "detail": refusal.detail}, indent=2))
    return 2


def cmd_binding(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        return _emit(check_binding(load_json(path)))
    except Refusal as refusal:
        return _refused(path.name, refusal)


def cmd_invocation(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        return _emit(check_invocation(load_json(path)))
    except Refusal as refusal:
        return _refused(path.name, refusal)


def cmd_parity(args: argparse.Namespace) -> int:
    first, second = Path(args.first), Path(args.second)
    try:
        return _emit(check_parity(load_json(first), load_json(second)))
    except Refusal as refusal:
        return _refused(f"{first.name}+{second.name}", refusal)


def cmd_bindings(_: argparse.Namespace) -> int:
    """Check every declared binding. One refusal fails the command."""
    refused = 0
    for path in sorted(BINDINGS_DIR.glob("*.json")):
        try:
            result = check_binding(load_json(path))
            print(f"OK       {path.name:<24} {result['model_id']} "
                  f"{result['provider_kind']}/{result['data_boundary']}")
        except Refusal as refusal:
            refused += 1
            print(f"REFUSED  {path.name:<24} {refusal.reason_code}: {refusal.detail}")
    return 2 if refused else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    binding = sub.add_parser("binding", help="check one Model Binding instance")
    binding.add_argument("path")
    binding.set_defaults(handler=cmd_binding)
    invocation = sub.add_parser("invocation", help="check one invocation record")
    invocation.add_argument("path")
    invocation.set_defaults(handler=cmd_invocation)
    parity = sub.add_parser("parity", help="check two invocations of one operation")
    parity.add_argument("first")
    parity.add_argument("second")
    parity.set_defaults(handler=cmd_parity)
    listing = sub.add_parser("bindings", help="check every declared binding")
    listing.set_defaults(handler=cmd_bindings)
    args = parser.parse_args(argv)
    try:
        return args.handler(args)
    except (OSError, json.JSONDecodeError, KeyError) as error:
        print(json.dumps({"outcome": "UNREADABLE", "detail": str(error)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
