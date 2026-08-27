"""The three health verbs: read it, render the page, refuse a stale or unhealthy one.

`health` is for a model operator and for a person at a keyboard. `health-render`
writes `docs/automation.html`. `health-check` runs inside `scripts/verify.py` and
does two separate jobs that are easy to confuse:

- it grades the page against the tree, so the page cannot go stale silently;
- it applies the health gate itself, so an unhealthy automation fails the build.

The first is byte comparison. The second is a live judgement at the real clock,
because the rule that matters most - a tick that stopped firing - becomes true by
time passing and by nothing changing on disk at all.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import argparse
import json

from sovschedule import page, report
from sovschedule.committed import SourceUnavailable
from sovschedule.report import stamp

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "docs" / "automation.html"
RENDER_COMMAND = "python scripts/sov_schedule.py health-render"


def _digest(root: Path, now: datetime | None = None, offset: timedelta | None = None,
            source: str = report.WORKTREE) -> report.Digest:
    return report.assemble(root, now, utc_offset=offset, source=source)


def _print_findings(digest: report.Digest) -> None:
    for name, finding in digest.findings:
        print(f"  {finding.severity:<9} {name:<20} {finding.rule}: {finding.detail}")


def _headline(digest: report.Digest) -> str:
    counts = digest.counts
    return (f"{digest.reading}: {counts['declared']} declared, {counts['enabled']} enabled, "
            f"{counts['with_history']} with run history, {counts['findings']} finding(s)")


def command_health(args: argparse.Namespace) -> int:
    """Print every schedule's state, or the whole read as JSON."""
    digest = _digest(args.root, args.now)
    if args.json:
        print(json.dumps(_as_json(digest), indent=2, sort_keys=True))
        return 1 if digest.refuses else 0
    print(f"{'schedule':<20} {'switch':<7} {'next due':<26} {'last attempt':<26} "
          f"{'outcome':<17} {'took':<7} {'refused':<17} {'fails':<6} reading")
    for row in digest.rows:
        print(f"{row.name:<20} {'on' if row.enabled else 'off':<7} "
              f"{stamp(row.next_due):<26} {stamp(row.last_attempted_at):<26} "
              f"{_outcome(row):<17} {_took(row.last_duration_seconds):<7} "
              f"{(row.last_reason_code or '-'):<17} {row.consecutive_failures:<6} {row.reading}")
    if digest.findings:
        print("\nfindings:")
        _print_findings(digest)
    if not digest.ledger.present:
        print(f"\n{digest.ledger.absent_reason}")
    print(f"\n{_headline(digest)}")
    return 1 if digest.refuses else 0


def _took(seconds: float | None) -> str:
    return "-" if seconds is None else f"{seconds:.0f}s"


def _outcome(row: report.Row) -> str:
    """The run status, carrying the exit code where the executor left one."""
    if row.last_status is None:
        return "-"
    return (row.last_status if row.last_exit_code is None
            else f"{row.last_status} (exit {row.last_exit_code})")


def _as_json(digest: report.Digest) -> dict:
    return {
        "table_id": digest.table["table_id"],
        "read_at": stamp(digest.rendered_at),
        "reading": digest.reading,
        "counts": digest.counts,
        "ledger": {"path": digest.ledger.path, "present": digest.ledger.present,
                   "digest": digest.ledger.digest, "entries": digest.ledger.entries,
                   "absent_reason": digest.ledger.absent_reason},
        "schedules": [
            {"name": row.name, "enabled": row.enabled, "target": row.target,
             "target_present": row.target_exists, "cron": row.cron_expression,
             "next_due": stamp(row.next_due), "attempts": row.attempts,
             "last_run_id": row.last_run_id, "last_attempted_at": stamp(row.last_attempted_at),
             "last_status": row.last_status, "last_exit_code": row.last_exit_code,
             "last_duration_seconds": row.last_duration_seconds,
             "last_reason_code": row.last_reason_code,
             "consecutive_failures": row.consecutive_failures, "reading": row.reading,
             "findings": [{"rule": f.rule, "severity": f.severity, "detail": f.detail}
                          for f in row.findings]}
            for row in digest.rows],
    }


def command_render(args: argparse.Namespace) -> int:
    """Write the page from the declarations at HEAD, stamped with the instant it was read.

    Not from the working tree: eleven sessions share this checkout, and a page carrying
    another session's untracked schedule cannot be reproduced by anyone who clones the
    commit it ships in.
    """
    try:
        digest = _digest(args.root, args.now, source=report.COMMIT)
    except SourceUnavailable as error:
        print(f"FAIL: the declarations at HEAD could not be read: {error}")
        return 1
    out = Path(args.out) if args.out else args.page_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.render(digest), encoding="utf-8", newline="\n")
    print(f"PASS: {out.name} rendered - {_headline(digest)}")
    return 0


def _grade_page(live: report.Digest, root: Path, page_path: Path) -> tuple[int, str]:
    """Compare the rendered page against the tree. Returns (exit code, what was graded)."""
    name = page_path.name
    if not page_path.exists():
        return 1, f"FAIL: {name} has not been rendered; run `{RENDER_COMMAND}`"
    text = page_path.read_text(encoding="utf-8")
    recorded = page.read_provenance(text)
    if recorded is None:
        return 1, (f"FAIL: {name} carries no readable provenance comment; "
                   f"run `{RENDER_COMMAND}`")
    # Re-render in the clock the page recorded, not the checking host's. The page is
    # rendered where the runs happen and graded wherever the suite runs; a check that
    # imposed its own offset would report every page from another zone as stale.
    expected = page.render(_digest(
        root, report.parse_stamp(recorded["rendered_at"]),
        timedelta(minutes=recorded.get("utc_offset_minutes", 0)), source=report.COMMIT))
    if recorded.get("ledger_digest") != live.ledger.digest:
        if page.outside_history(text) != page.outside_history(expected):
            return 1, (f"FAIL: {name} is stale in its declared half; "
                       f"run `{RENDER_COMMAND}`")
        return 0, ("declared half matches; history half UNCHECKED - the page was rendered "
                   f"from a ledger of {recorded.get('ledger_entries')} event(s) "
                   f"({recorded.get('ledger_digest', '')[:23]}) and this checkout holds "
                   f"{live.ledger.entries}")
    if text != expected:
        return 1, f"FAIL: {name} is stale; run `{RENDER_COMMAND}`"
    shown = recorded.get("readings")
    now = {row.name: row.reading for row in live.rows}
    if shown != now:
        moved = sorted(k for k in set(shown) | set(now) if shown.get(k) != now.get(k))
        return 1, (f"FAIL: {name} shows a reading the records no longer support for "
                   f"{', '.join(moved)}; run `{RENDER_COMMAND}`")
    return 0, "page matches the tree, both halves"


def command_check(args: argparse.Namespace) -> int:
    """Grade the page, then apply the health gate at the real clock.

    A declaration the loader refuses does not stop either job: it becomes a row with
    DECLARATION_REFUSED against it, which is UNHEALTHY, which refuses here by name.
    """
    moment = args.now or datetime.now(timezone.utc)
    live = _digest(args.root, moment)
    try:
        committed = _digest(args.root, moment, source=report.COMMIT)
    except SourceUnavailable as error:
        print(f"FAIL: the declarations at HEAD could not be read: {error}")
        return 1
    code, note = _grade_page(committed, args.root, args.page_path)
    if code:
        print(note)
        return code
    if live.findings:
        print("findings:")
        _print_findings(live)
    if live.refuses:
        refusing = ", ".join(row.name for row in live.rows if row.reading == "UNHEALTHY")
        print(f"FAIL: automation health is {live.reading} - {refusing}; "
              f"{live.table['blocking']['refuses_at']} refuses by "
              f"{live.table['governed_by']}")
        return 1
    print(f"PASS: {_headline(live)}; {note}")
    return 0


#: Root, page and clock are namespace values rather than module constants so a test can
#: point the whole surface at a temporary tree at a fixed instant. A check whose only
#: subject is this repository cannot be shown to refuse anything, because this repository
#: is not unhealthy - and a rule nothing has ever exercised is a rule nobody should trust.
DEFAULTS = {"root": ROOT, "page_path": PAGE, "now": None}


def add_commands(sub: argparse._SubParsersAction) -> None:
    """Wire the three verbs onto the existing schedule CLI."""
    read = sub.add_parser("health", help="read every schedule's health")
    read.add_argument("--json", action="store_true", help="emit the whole read as JSON")
    read.set_defaults(func=command_health, **DEFAULTS)
    render = sub.add_parser("health-render", help="write docs/automation.html")
    render.add_argument("--out")
    render.set_defaults(func=command_render, **DEFAULTS)
    sub.add_parser(
        "health-check", help="refuse a stale page or an unhealthy automation",
    ).set_defaults(func=command_check, **DEFAULTS)


def namespace(**overrides) -> argparse.Namespace:
    """A command namespace with the defaults filled in, for tests and callers."""
    values = dict(DEFAULTS, json=False, out=None)
    values.update(overrides)
    return argparse.Namespace(**values)
