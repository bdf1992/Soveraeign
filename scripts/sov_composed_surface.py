#!/usr/bin/env python3
"""Render the alternate composable Human Binding shell.

This is a view over ``sov_surface.surface()``. It is intentionally not a second
Node Interface and is not a checked-in source of authority or state.

When the SOV session harness from PR #98 is present, this renderer also reads
its live-session projection and labels it HARNESS state. Rendering remains
read-only. ``--register-session`` is an explicit separate host action.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_surface  # noqa: E402
from sovsurface.composed import render  # noqa: E402
from sovsurface.session_presence import decorate, register, snapshot  # noqa: E402

DEFAULT_OUT = ROOT / ".local" / "surface-composed.html"


def command_render(args: argparse.Namespace) -> int:
    if args.register_session:
        ok, detail = register(ROOT, name=args.session_name, intent=args.intent or "")
        if not ok:
            print("REFUSED: session registration unavailable: " + detail, file=sys.stderr)
            return 1
        print("HARNESS: " + detail)
    document = sov_surface.surface()
    presence = snapshot(ROOT) if not args.no_sessions else {
        "available": False,
        "source": "disabled by --no-sessions",
        "reason": "session projection disabled for this rendering",
        "sessions": [],
        "held": {},
    }
    output = Path(args.out) if args.out else DEFAULT_OUT
    output.parent.mkdir(parents=True, exist_ok=True)
    page = decorate(render(document), presence)
    output.write_text(page, encoding="utf-8", newline="\n")
    counts = document["counts"]
    session_count = len(presence.get("sessions", [])) if presence.get("available") else 0
    print(
        f"PASS: {output} — {counts['declared']} declared / "
        f"{counts['reachable']} reachable / {counts['observed']} observed / "
        f"{session_count} live harness session(s)"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_composed_surface")
    parser.add_argument("--out", help="write the composed HTML to this path")
    parser.add_argument(
        "--register-session",
        action="store_true",
        help="explicitly register this host session through scripts/sov_session.py before rendering",
    )
    parser.add_argument("--session-name", help="override the SOV session registry name")
    parser.add_argument("--intent", help="intent recorded when explicitly registering")
    parser.add_argument(
        "--no-sessions",
        action="store_true",
        help="do not read the local SOV session harness for this rendering",
    )
    return command_render(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
