#!/usr/bin/env python3
"""Start named Claude sessions on declared worktrees, without a human at a terminal.

Host plumbing, not a governed surface: it holds no standing and grants no
authority (`AGENTS.md`, Local orchestration harness). It answers where and how a
session starts. What that session may then do is decided by the same contracts
that govern any participant, and is not adjusted by having been launched here.

The problem it removes: a campaign that had already built the right worktrees
still needed Bdo to open three terminals and paste a loader line into each,
because a session started from inside another Claude session did not reliably
persist, register, or receive a bootstrap message. Orders now travel as the
opening prompt of the process, which is the one channel that cannot miss a
session that does not exist yet.

    python scripts/sov_hypervisor.py plan <plan.json>       grade every lane
    python scripts/sov_hypervisor.py launch <plan.json>     start the ready ones
    python scripts/sov_hypervisor.py status <plan.json>     what is live now
    python scripts/sov_hypervisor.py selfcheck              prove the refusals

`plan` and `status` start nothing. `selfcheck` runs a fake executable in a
temporary tree and never reaches the real `claude`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovhypervisor import launch as launchmod  # noqa: E402
from sovhypervisor import plan as planmod  # noqa: E402
from sovsession import store  # noqa: E402

DISCLAIMER = "HOST COORDINATION PROJECTION - NO SOVERAEIGN STANDING"
DETACHED = "(detached)"
DRY_RUN = "DRY_RUN"


def observe(path: str) -> dict[str, Any]:
    """What the working tree at `path` currently is, read through git."""
    tree = Path(path)
    if not tree.is_dir():
        return {"is_worktree": False}

    def git(*args: str) -> str:
        result = subprocess.run(["git", *args], cwd=str(tree), text=True,
                                capture_output=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""

    if git("rev-parse", "--is-inside-work-tree") != "true":
        return {"is_worktree": False}
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    return {"is_worktree": True, "sha": git("rev-parse", "HEAD"),
            "branch": "" if branch == "HEAD" else branch}


def live_sessions() -> dict[str, dict[str, Any]]:
    """The registry as it stands, keyed by session name."""
    try:
        return store.sessions(store.store_dir())
    except Exception:  # noqa: BLE001 - an unreachable registry is not a launch failure
        return {}


def graded(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]],
                                list[dict[str, Any]]]:
    """Read a plan and grade every lane in it."""
    document = planmod.load(path)
    lanes = planmod.lanes(document)
    live, seen = live_sessions(), set()
    return document, lanes, [planmod.check(lane, observe, live, seen) for lane in lanes]


def _render(document: dict[str, Any], lanes: list[dict[str, Any]],
            verdicts: list[dict[str, Any]]) -> str:
    """One block per lane, with a refusal's reason where its detail would be."""
    out = [f"SOV HYPERVISOR - {document.get('campaign')}", ""]
    for lane, verdict in zip(lanes, verdicts):
        state = verdict["verdict"]
        suffix = "  READ ONLY" if lane["mode"] == "read-only" else ""
        out.append(f"{lane['name']:<14} {state}{suffix}")
        if state == planmod.READY:
            sha = str(verdict.get("sha"))[:7]
            out.append(f"  worktree   {lane['worktree']}")
            out.append(f"  ref        {verdict.get('branch') or DETACHED} @ {sha}")
            out.append(f"  orders     {lane['orders_file'] or 'inline'}")
            out.append(f"  remote     {'on' if lane['remote_control'] else 'off'}")
        else:
            out.append(f"  {verdict['because']}")
        out.append("")
    out.append(DISCLAIMER)
    return "\n".join(out)


def cmd_plan(args: argparse.Namespace) -> int:
    """Grade every lane and start nothing."""
    document, lanes, verdicts = graded(Path(args.plan))
    if args.json:
        print(json.dumps({"campaign": document.get("campaign"), "lanes": verdicts},
                         indent=2))
    else:
        print(_render(document, lanes, verdicts))
    return 0 if all(v["verdict"] == planmod.READY for v in verdicts) else 1


def cmd_launch(args: argparse.Namespace) -> int:
    """Start every ready lane, then wait for each to register before saying so."""
    document, lanes, verdicts = graded(Path(args.plan))
    refused = [v for v in verdicts if v["verdict"] != planmod.READY]
    if refused and not args.partial:
        print(_render(document, lanes, verdicts))
        print("LAUNCH REFUSED: " + ", ".join(v["refusal"] for v in refused))
        return 1

    into = (Path(args.scripts) if args.scripts
            else store.repo_root() / ".local" / "hypervisor")
    results: list[dict[str, Any]] = []
    for lane, verdict in zip(lanes, verdicts):
        if verdict["verdict"] != planmod.READY:
            results.append(verdict)
            continue
        spec = launchmod.spec(lane, claude=args.claude)
        script = launchmod.write_script(spec, into)
        if args.dry_run:
            results.append({"lane": lane["name"], "verdict": DRY_RUN,
                            "script": str(script), "argv": spec["argv"]})
            continue
        launchmod.start(spec, script, terminal=args.terminal or None)
        results.append(launchmod.await_registration(
            lane["name"], lane["worktree"], live_sessions, timeout=args.timeout))

    for result in results:
        line = f"{result['lane']:<14} {result['verdict']}"
        if result["verdict"] in (launchmod.READY, DRY_RUN):
            print(line)
        else:
            print(line + "\n  " + str(result.get("because", "")))
        if result["verdict"] == DRY_RUN:
            print("  " + " ".join(result["argv"]))
    print(DISCLAIMER)
    return 0 if all(r["verdict"] in (launchmod.READY, DRY_RUN) for r in results) else 1


def cmd_status(args: argparse.Namespace) -> int:
    """Join the plan against the registry. Reads only."""
    document, lanes, _ = graded(Path(args.plan))
    live = live_sessions()
    print(f"SOV HYPERVISOR - {document.get('campaign')}\n")
    for lane in lanes:
        record = live.get(lane["name"]) or {}
        print(f"{lane['name']:<14} {'LIVE' if record.get('live') else 'ABSENT'}")
        if record:
            print(f"  pid        {record.get('pid')}")
            print(f"  tree       {record.get('tree')}")
            print(f"  branch     {record.get('branch') or DETACHED}")
        for alias in aliases_of(record, live, lane["name"]):
            print(f"  ALIAS      also registered as {alias}")
        print()
    print(DISCLAIMER)
    return 0


def aliases_of(record: dict[str, Any], live: dict[str, dict[str, Any]],
               name: str) -> list[str]:
    """Other live names registered against this lane's process.

    One process holding two registry rows is the defect the SessionStart hook
    repair removed at its source. A session that started before that repair is
    still carrying its twin, so status names it rather than showing a clean
    lane that is not clean.
    """
    pid = record.get("pid")
    if not pid:
        return []
    return sorted(other for other, entry in live.items()
                  if other != name and entry.get("live") and entry.get("pid") == pid)


def cmd_selfcheck(_: argparse.Namespace) -> int:
    """Run the shipped defeating cases; launch nothing real."""
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [sys.executable, "-m", "unittest", "-q", "scripts.tests.test_sov_hypervisor"],
        cwd=str(root), check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    """Assemble the command line."""
    parser = argparse.ArgumentParser(description="deterministic session launch")
    sub = parser.add_subparsers(dest="command", required=True)

    grade = sub.add_parser("plan", help="grade every lane; start nothing")
    grade.add_argument("plan")
    grade.add_argument("--json", action="store_true")
    grade.set_defaults(handler=cmd_plan)

    go = sub.add_parser("launch", help="start every ready lane")
    go.add_argument("plan")
    go.add_argument("--dry-run", action="store_true", help="write scripts, start nothing")
    go.add_argument("--partial", action="store_true", help="launch the ready lanes anyway")
    go.add_argument("--claude", default="claude", help="the executable to launch")
    go.add_argument("--terminal", default="wt.exe", help="terminal host; empty for none")
    go.add_argument("--scripts", default="", help="where to write the lane scripts")
    go.add_argument("--timeout", type=float, default=90.0)
    go.set_defaults(handler=cmd_launch)

    state = sub.add_parser("status", help="what is live now")
    state.add_argument("plan")
    state.set_defaults(handler=cmd_status)

    sub.add_parser("selfcheck", help="prove every declared refusal fires"
                   ).set_defaults(handler=cmd_selfcheck)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch one command."""
    args = build_parser().parse_args(argv)
    try:
        return int(args.handler(args))
    except planmod.PlanError as error:
        print(f"REFUSED  {error.refusal}: {error.because}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
