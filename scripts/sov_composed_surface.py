#!/usr/bin/env python3
"""Render the alternate composable Human Binding shell.

This is a view over ``sov_surface.surface()``. It is intentionally not a second
Node Interface and is not a checked-in source of authority or state.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_surface  # noqa: E402
from sovsurface.composed import render  # noqa: E402

DEFAULT_OUT = ROOT / ".local" / "surface-composed.html"


def command_render(args: argparse.Namespace) -> int:
    document = sov_surface.surface()
    output = Path(args.out) if args.out else DEFAULT_OUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(document), encoding="utf-8", newline="\n")
    counts = document["counts"]
    print(
        f"PASS: {output} — {counts['declared']} declared / "
        f"{counts['reachable']} reachable / {counts['observed']} observed"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_composed_surface")
    parser.add_argument("--out", help="write the composed HTML to this path")
    return command_render(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
