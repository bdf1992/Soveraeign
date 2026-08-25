"""Project the local SOV session harness into the composed Human surface.

Session presence is deliberately outside the canonical Node Interface. The
session registry from PR #98 is host coordination state under ``.git`` and
therefore carries no Node standing or authority. This adapter reaches it only
through the public ``scripts/sov_session.py`` CLI and labels every projection
``HARNESS``.

Reading is the default. Registration is a separate explicit operation so
rendering the surface never creates presence by itself.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import html
import json
import subprocess
import sys

Runner = Callable[..., subprocess.CompletedProcess[str]]


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)


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
            "held": {},
        }
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "session CLI refused").strip()
        return {
            "available": False,
            "source": "scripts/sov_session.py list --json",
            "reason": detail,
            "sessions": [],
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
            "held": {},
        }
    if not isinstance(payload, dict):
        return {
            "available": False,
            "source": "scripts/sov_session.py list --json",
            "reason": "session CLI returned a non-object payload",
            "sessions": [],
            "held": {},
        }
    sessions = payload.get("sessions") if isinstance(payload.get("sessions"), list) else []
    held = payload.get("held") if isinstance(payload.get("held"), dict) else {}
    live = [item for item in sessions if isinstance(item, dict) and item.get("live")]
    return {
        "available": True,
        "source": "scripts/sov_session.py list --json",
        "reason": "",
        "sessions": live,
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


def _claim_count(snapshot_data: dict[str, Any], session: str) -> int:
    count = 0
    for holders in snapshot_data.get("held", {}).values():
        if not isinstance(holders, list):
            continue
        if any(isinstance(holder, dict) and holder.get("session") == session for holder in holders):
            count += 1
    return count


def _session_panel(item: dict[str, Any], snapshot_data: dict[str, Any]) -> str:
    session = str(item.get("session") or "unnamed-session")
    branch = str(item.get("branch") or "unknown branch")
    intent = str(item.get("intent") or "no intent recorded")
    principal = item.get("principal")
    verification = item.get("verification")
    identity = ""
    if principal:
        identity = (
            f'<div class="utility-row"><span>principal</span><b>{_e(principal)}</b></div>'
            f'<div class="utility-row"><span>verification</span>'
            f'<b>{_e(verification or "UNVERIFIED")}</b></div>'
        )
    claims = _claim_count(snapshot_data, session)
    return (
        '<div class="panel" data-component="session-card">'
        '<div class="eyebrow">HARNESS · live session</div>'
        f'<h3>{_e(session)}</h3>'
        f'<div class="utility-row"><span>branch</span><b>{_e(branch)}</b></div>'
        f'<div class="utility-row"><span>claims</span><b>{claims}</b></div>'
        f'{identity}<p class="muted">{_e(intent)}</p></div>'
    )


def fragment(snapshot_data: dict[str, Any]) -> str:
    """Render a utility-drawer fragment from one harness snapshot."""
    if not snapshot_data.get("available"):
        return (
            '<h2>Session harness</h2><div class="panel omission" '
            'data-component="session-harness-unavailable">'
            '<div class="eyebrow">HARNESS · unavailable</div>'
            '<h3>No session registry projection</h3>'
            f'<p class="muted">{_e(snapshot_data.get("reason") or "not available")}</p>'
            '</div>'
        )
    sessions = snapshot_data.get("sessions", [])
    cards = "".join(_session_panel(item, snapshot_data) for item in sessions)
    if not cards:
        cards = (
            '<div class="panel"><div class="eyebrow">HARNESS</div>'
            '<h3>No live sessions</h3><p class="muted">The registry is reachable; '
            'nothing is currently registered as live.</p></div>'
        )
    return (
        '<h2>Live sessions</h2>'
        '<div class="panel"><div class="utility-row"><span>source</span>'
        f'<b>{_e(snapshot_data.get("source"))}</b></div>'
        '<p class="muted">Host coordination only. Presence grants no authority, '
        'standing, route, or Node observation.</p></div>'
        + cards
    )


def decorate(page: str, snapshot_data: dict[str, Any]) -> str:
    """Insert harness presence into the composed utility drawer.

    The canonical renderer remains untouched. This decoration only targets the
    alternate composed shell and never changes its Node Interface input.
    """
    insertion = fragment(snapshot_data)
    marker = '</aside><footer class="status">'
    if marker not in page:
        return page
    page = page.replace(marker, insertion + marker, 1)
    if snapshot_data.get("available"):
        page = page.replace("No live presence implied", "Harness presence is explicit", 1)
        page = page.replace(
            "This shell does not fake an Active Now list.",
            "The live list below is host harness state, not governed Node state.",
            1,
        )
    return page
