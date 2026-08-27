#!/usr/bin/env python3
"""Declare, check, and fire scheduled runs of harness workflows and skills.

Commands: ``validate``, ``list``, ``due``, ``run NAME [--force] [--dry-run]``,
``tick [--dry-run]``, ``ledger [--schedule NAME] [--last N]``, ``task-command``,
``health [--json]``, ``health-render [--out PATH]``, ``health-check``.
The host scheduler (Windows Task Scheduler, cron) calls ``tick`` every few
minutes; everything else is for a human at the keyboard. Exit codes: 0 fired or
nothing due, 1 failed or invalid, 2 refused by a gate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

from sovschedule import ledger, runner, surface
from sovschedule.declaration import SCHEDULES_DIR, DeclarationError, load_all, load_declaration


ROOT = Path(__file__).resolve().parents[1]
TICK_MINUTES = 5


def _load() -> list:
    try:
        return load_all(ROOT)
    except DeclarationError as error:
        print(f"FAIL: {error}")
        raise SystemExit(1) from None


def _describe(decl) -> str:
    state = "enabled" if decl.enabled else "disabled"
    return (f"{decl.name:<24} {decl.target_kind}:{decl.target_name:<18} "
            f"cron '{decl.spec.expression}'  mode {decl.mode:<7} {decl.effect_class:<20} {state}")


def cmd_validate(_: argparse.Namespace) -> int:
    declarations = _load()
    for decl in declarations:
        print(f"OK   {_describe(decl)}")
    print(f"PASS: {len(declarations)} schedule declaration(s) checked")
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    for decl in _load():
        last = ledger.last_attempt(ROOT, decl.name)
        print(f"{_describe(decl)}  last attempt {ledger.timestamp(last) if last else 'never'}")
    return 0


def cmd_due(_: argparse.Namespace) -> int:
    now = datetime.now(timezone.utc)
    for decl in _load():
        due = runner.is_due(ROOT, decl, now)
        print(f"{decl.name:<24} {'due at ' + due.isoformat() if due else 'not due'}")
    return 0


def _fire(decl, dry_run: bool, force: bool) -> int:
    if dry_run:
        now = datetime.now(timezone.utc)
        run_id = runner.run_id_for(decl, now)
        prompt = runner.build_prompt(decl, run_id, now.astimezone().strftime("%Y-%m-%d"))
        print(json.dumps(runner.build_command(decl, run_id, prompt), indent=2))
        return 0
    result = runner.execute(ROOT, decl, force=force)
    if result.phase == "ATTEMPTED":
        print(f"REFUSED {result.run_id}: {result.reason_code}")
        return 2
    print(f"{result.outcome} {result.run_id}: exit {result.exit_code}; capture "
          f"{result.capture_path.relative_to(ROOT).as_posix() if result.capture_path else '-'}; "
          f"reports {', '.join(result.report_paths) or 'none'}")
    return 0 if result.outcome != "FAILED" else 1


def cmd_run(args: argparse.Namespace) -> int:
    path = ROOT / SCHEDULES_DIR / f"{args.name}.json"
    try:
        decl = load_declaration(ROOT, path)
    except DeclarationError as error:
        print(f"FAIL: {error}")
        return 1
    return _fire(decl, args.dry_run, args.force)


def cmd_tick(args: argparse.Namespace) -> int:
    now = datetime.now(timezone.utc)
    worst = 0
    for decl in _load():
        if not decl.enabled:
            continue
        due = runner.is_due(ROOT, decl, now)
        if due is None:
            continue
        print(f"due: {decl.name} (cron minute {due.isoformat()})")
        worst = max(worst, _fire(decl, args.dry_run, False))
    return worst


def cmd_ledger(args: argparse.Namespace) -> int:
    entries = ledger.read(ROOT, args.schedule)
    for entry in entries[-args.last:]:
        event = entry["event"]
        print(f"{event['occurred_at']} {entry['schedule']:<20} {event['event_phase']:<9} "
              f"{event['outcome']:<9} {event['reason']}")
    if not entries:
        print("ledger is empty")
    return 0


def cmd_task_command(_: argparse.Namespace) -> int:
    script = Path(__file__).resolve()
    print("# Register a Windows Task Scheduler tick (run in an elevated or user PowerShell):")
    print(f"$action = New-ScheduledTaskAction -Execute '{sys.executable}' "
          f"-Argument '\"{script}\" tick' -WorkingDirectory '{ROOT}'")
    print(f"$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) "
          f"-RepetitionInterval (New-TimeSpan -Minutes {TICK_MINUTES})")
    print("Register-ScheduledTask -TaskName 'sov-schedule-tick' -Action $action -Trigger $trigger")
    print("# cron equivalent:")
    print(f"*/{TICK_MINUTES} * * * * cd '{ROOT}' && '{sys.executable}' "
          "scripts/sov_schedule.py tick")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate").set_defaults(func=cmd_validate)
    sub.add_parser("list").set_defaults(func=cmd_list)
    sub.add_parser("due").set_defaults(func=cmd_due)
    run = sub.add_parser("run")
    run.add_argument("name")
    run.add_argument("--force", action="store_true", help="fire even when disabled")
    run.add_argument("--dry-run", action="store_true", help="print the command, do not run")
    run.set_defaults(func=cmd_run)
    tick = sub.add_parser("tick")
    tick.add_argument("--dry-run", action="store_true")
    tick.set_defaults(func=cmd_tick)
    led = sub.add_parser("ledger")
    led.add_argument("--schedule")
    led.add_argument("--last", type=int, default=20)
    led.set_defaults(func=cmd_ledger)
    sub.add_parser("task-command").set_defaults(func=cmd_task_command)
    surface.add_commands(sub)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
