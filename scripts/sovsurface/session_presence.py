"""Project the local SOV session harness into the composed Human surface.

Session presence is deliberately outside the canonical Node Interface. The
session registry from PR #98 is host coordination state under ``.git`` and
therefore carries no Node standing or authority. This adapter reaches it only
through the public ``scripts/sov_session.py`` CLI and labels every projection
``HARNESS``.

Reading is the default. Registration is a separate explicit operation so
rendering the surface never creates presence by itself.

This module is the boundary only. ``sovsurface.sessions`` turns what it returns
into cards and inspectors; nothing here renders.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
import json
import subprocess
import sys

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _script(root: Path) -> Path:
    return root / "scripts" / "sov_session.py"


def _invoke(
    root: Path,
    arguments: list[str],
    *,
    runner: Runner = subprocess.run,
) -> subprocess.CompletedProcess[str]:
    script = _script(root)
    if not script.exists():
        raise FileNotFoundError("scripts/sov_session.py is not present in this working tree")
    return runner(
        [sys.executable, str(script), *arguments],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
    )


def snapshot(root: Path, *, runner: Runner = subprocess.run) -> dict[str, Any]:
    """Read live sessions through the harness CLI without importing its store."""
    try:
        result = _invoke(root, ["list", "--json"], runner=runner)
    except (FileNotFoundError, OSError) as error:
        return {
            "available": False,
            "source": "scripts/sov_session.py list --json",
            "reason": str(error),
            "sessions": [],
            "records": [],
            "held": {},
        }
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "session CLI refused").strip()
        return {
            "available": False,
            "source": "scripts/sov_session.py list --json",
            "reason": detail,
            "sessions": [],
            "records": [],
            "held": {},
        }
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "available": False,
            "source": "scripts/sov_session.py list --json",
            "reason": "session CLI returned non-JSON output",
            "sessions": [],
            "records": [],
            "held": {},
        }
    if not isinstance(payload, dict):
        return {
            "available": False,
            "source": "scripts/sov_session.py list --json",
            "reason": "session CLI returned a non-object payload",
            "sessions": [],
            "records": [],
            "held": {},
        }
    sessions = payload.get("sessions") if isinstance(payload.get("sessions"), list) else []
    held = payload.get("held") if isinstance(payload.get("held"), dict) else {}
    live = [item for item in sessions if isinstance(item, dict) and item.get("live")]
    records = [item for item in sessions if isinstance(item, dict)]
    return {
        "available": True,
        "source": "scripts/sov_session.py list --json",
        "reason": "",
        "sessions": live,
        "records": records,
        "held": held,
    }


def register(
    root: Path,
    *,
    name: str | None = None,
    intent: str = "",
    runner: Runner = subprocess.run,
) -> tuple[bool, str]:
    """Explicitly register this host session through the SOV session CLI."""
    args = ["register", "--json"]
    if name:
        args.extend(["--name", name])
    if intent:
        args.extend(["--intent", intent])
    try:
        result = _invoke(root, args, runner=runner)
    except (FileNotFoundError, OSError) as error:
        return False, str(error)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "session registration refused").strip()
    return True, "registered through scripts/sov_session.py"
