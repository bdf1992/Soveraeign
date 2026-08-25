#!/usr/bin/env python3
"""Render the Node Interface for humans and invoke its one reachable action.

The page consumes the same derived Node Interface that model readers receive.
It opens nothing by rendering. ``try`` rebuilds that interface from current
sources and then crosses the normal Gateway/service path; it never writes a
service store directly or creates a grant.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sov_interface import main as interface_main  # noqa: E402
from sovnode.interface_inputs import REFERENCE, rebuild  # noqa: E402
from sovsurface.page import render as render_page  # noqa: E402

PAGE = ROOT / "docs" / "surface.html"
SCRATCH = ROOT / ".local" / "surface-try"


def surface() -> dict[str, Any]:
    """Rebuild the canonical interface; the checked projection is never an input."""
    document, defects = rebuild()
    if defects:
        raise RuntimeError("Node Interface refused: " + "; ".join(defects))
    return document


def input_digest(document: dict[str, Any] | None = None) -> str:
    """Digest the semantic inputs and the human renderer that consumes them."""
    document = document or surface()
    material = sha256()
    material.update(document["input_state_digest"].encode("ascii"))
    material.update((ROOT / "scripts" / "sovsurface" / "page.py").read_bytes())
    return material.hexdigest()


def build() -> str:
    """Deterministic human rendering over the same record a model reads."""
    document = surface()
    return render_page(document) + f"\n<!-- inputs {input_digest(document)} -->\n"


def command_render(args: argparse.Namespace) -> int:
    out = Path(args.out) if args.out else PAGE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8", newline="\n")
    counts = surface()["counts"]
    print(f"PASS: {out.relative_to(ROOT)} ({counts['declared']} declared, "
          f"{counts['reachable']} reachable, {counts['observed']} observed)")
    return 0


def command_check(_: argparse.Namespace) -> int:
    document = surface()
    if not REFERENCE.exists() or json.loads(REFERENCE.read_text("utf-8")) != document:
        print("FAIL: contracts/fixtures/node-interface.reference.json is stale; "
              "run `python scripts/sov_interface.py build`")
        return 1
    if not PAGE.exists():
        print(f"FAIL: {PAGE.relative_to(ROOT)} has not been rendered")
        return 1
    if PAGE.read_text(encoding="utf-8") != build():
        print(f"FAIL: {PAGE.relative_to(ROOT)} is stale; "
              "run `python scripts/sov_surface.py render`")
        return 1
    counts = document["counts"]
    print("PASS: surface consumes the current Node Interface — "
          f"{counts['declared']} declared / {counts['reachable']} reachable / "
          f"{counts['observed']} observed")
    return 0


def command_try(args: argparse.Namespace) -> int:
    """Delegate action construction to the canonical Human/Model binding."""
    return interface_main([
        "invoke", args.operation, *args.arguments,
        "--binding", args.binding, "--actor", args.actor, "--scope", args.scope,
        "--state-root", args.state_root or str(SCRATCH),
    ])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_surface")
    sub = parser.add_subparsers(dest="command", required=True)
    render = sub.add_parser("render", help="write the offline human surface")
    render.add_argument("--out")
    render.set_defaults(handler=command_render)
    sub.add_parser("check", help="refuse stale interface or page bytes").set_defaults(
        handler=command_check)
    invoke = sub.add_parser("try", help="invoke one reachable operation through Gateway")
    invoke.add_argument("operation")
    invoke.add_argument("arguments", nargs="*", metavar="name=value")
    invoke.add_argument("--binding", choices=("HUMAN", "MODEL"), default="HUMAN")
    invoke.add_argument("--actor", required=True)
    invoke.add_argument("--scope", required=True)
    invoke.add_argument("--state-root")
    invoke.set_defaults(handler=command_try)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
