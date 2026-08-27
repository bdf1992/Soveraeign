"""Render the automation health read as a deterministic offline page.

Every value is derived. The page carries a provenance comment naming the instant
it was rendered at and the exact ledger bytes it read, because the two halves of
this page have different lifetimes: the declarations are committed and reproduce
on any machine, while the run history lives in gitignored machine-local state and
does not exist in CI at all.

So the history block is delimited. ``outside_history`` returns the page with that
block replaced, and the check compares those bytes everywhere and the full bytes
only where the ledger digest still matches. A machine that holds no ledger is told
the history half is UNCHECKED and why, rather than being shown a page graded as
current over records it never had.

The page holds no standing. A reading here is a report about records.
"""

from __future__ import annotations

import html
import json

from sovschedule.pagestyle import STYLE
from sovschedule.report import Digest, Row, stamp

PROVENANCE_PREFIX = "<!--sov:provenance "
PROVENANCE_SUFFIX = "-->"
HISTORY_OPEN = "<!--sov:history-->"
HISTORY_CLOSE = "<!--/sov:history-->"
HISTORY_ELIDED = "<!--sov:history-elided-->"
PROVENANCE_ELIDED = "<!--sov:provenance-elided-->"

READING_CLASS = {"UNHEALTHY": "bad", "DEGRADED": "warn",
                 "UNOBSERVED": "abs", "HEALTHY": "ok"}




def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    if seconds < 90:
        return f"{seconds:.0f}s"
    return f"{seconds / 60:.1f}m"


def _outcome(row: Row) -> str:
    """The run status, carrying the exit code where the executor left one."""
    if row.last_status is None:
        return "-"
    return (row.last_status if row.last_exit_code is None
            else f"{row.last_status} (exit {row.last_exit_code})")


def _tag(reading: str) -> str:
    return f'<span class="tag {READING_CLASS.get(reading, "abs")}">{_e(reading)}</span>'


def provenance(digest: Digest) -> dict:
    """What the check needs to know about how these bytes were produced."""
    return {
        "rendered_at": stamp(digest.rendered_at),
        "utc_offset_minutes": int(digest.utc_offset.total_seconds()) // 60,
        "ledger_path": digest.ledger.path,
        "ledger_present": digest.ledger.present,
        "ledger_digest": digest.ledger.digest,
        "ledger_entries": digest.ledger.entries,
        "table_id": digest.table["table_id"],
        "reading": digest.reading,
        "readings": {row.name: row.reading for row in digest.rows},
    }


def read_provenance(page: str) -> dict | None:
    """Parse the provenance comment back out of a rendered page."""
    start = page.find(PROVENANCE_PREFIX)
    if start < 0:
        return None
    end = page.find(PROVENANCE_SUFFIX, start)
    if end < 0:
        return None
    try:
        return json.loads(page[start + len(PROVENANCE_PREFIX):end])
    except json.JSONDecodeError:
        return None


def _elide(page: str, opener: str, closer: str, token: str) -> str:
    start = page.find(opener)
    end = page.find(closer, start + 1) if start >= 0 else -1
    if start < 0 or end < 0:
        return page
    return page[:start] + token + page[end + len(closer):]


def outside_history(page: str) -> str:
    """The page with the history block and the provenance comment replaced.

    What is left derives only from committed bytes and the recorded instant, so it
    reproduces on any checkout. This is what a machine holding no ledger can still
    grade. Splitting on explicit markers rather than on a heading keeps the seam
    inspectable: a reader can open the page and see exactly which half is which.
    """
    page = _elide(page, HISTORY_OPEN, HISTORY_CLOSE, HISTORY_ELIDED)
    return _elide(page, PROVENANCE_PREFIX, PROVENANCE_SUFFIX, PROVENANCE_ELIDED)


def _counts(digest: Digest) -> str:
    counts = digest.counts
    cells = ((counts["declared"], "declared"), (counts["enabled"], "enabled"),
             (counts["with_history"], "ever run"), (digest.ledger.entries, "ledger events"),
             (counts["findings"], "findings"), (counts["refusing"], "refusing"))
    body = "".join(f"<div><b>{_e(value)}</b><span>{_e(label)}</span></div>"
                   for value, label in cells)
    return f'<div class="counts">{body}</div>'


def _declaration_table(rows: tuple[Row, ...]) -> str:
    head = ("<tr><th>schedule</th><th>switch</th><th>target</th><th>cadence</th>"
            "<th>next due</th><th>mode</th><th>effect class</th><th>timeout</th></tr>")
    body = "".join(
        f'<tr><td class="id">{_e(row.name)}</td>'
        f'<td>{_tag("on" if row.enabled else "off")}</td>'
        f'<td class="t">{_e(row.target)}'
        + ("" if row.target_exists else ' <span class="tag bad">missing</span>')
        + ("" if row.defect is None else ' <span class="tag bad">refused</span>')
        + f'</td><td class="t">{_e(row.cron_expression)}</td>'
        f'<td class="t">{_e(stamp(row.next_due))}</td>'
        f'<td class="t">{_e(row.mode)}</td><td class="t">{_e(row.effect_class)}</td>'
        f'<td class="n">{_e(row.timeout_seconds)}s</td></tr>'
        for row in rows)
    return f'<div class="wrap"><table>{head}{body}</table></div>'


def _history_table(rows: tuple[Row, ...]) -> str:
    head = ("<tr><th>schedule</th><th>reading</th><th>attempts</th><th>last attempt</th>"
            "<th>outcome</th><th>duration</th><th>refused</th><th>fails in a row</th></tr>")
    body = "".join(
        f'<tr><td class="id">{_e(row.name)}</td><td>{_tag(row.reading)}</td>'
        f'<td class="n">{_e(row.attempts)}</td>'
        f'<td class="t">{_e(stamp(row.last_attempted_at))}</td>'
        f'<td class="t">{_e(_outcome(row))}</td>'
        f'<td class="n">{_e(_duration(row.last_duration_seconds))}</td>'
        f'<td class="t">{_e(row.last_reason_code or "-")}</td>'
        f'<td class="n">{_e(row.consecutive_failures)}</td></tr>'
        for row in rows)
    return f'<div class="wrap"><table>{head}{body}</table></div>'


def _findings(digest: Digest, needs: str) -> str:
    entries = [(name, finding) for name, finding in digest.findings
               if digest.table["rules"][finding.rule]["needs"] == needs]
    if not entries:
        return "<p>Nothing fired.</p>"
    head = "<tr><th>schedule</th><th>rule</th><th>severity</th><th>what fired it</th></tr>"
    body = "".join(
        f'<tr><td class="id">{_e(name)}</td><td class="t">{_e(finding.rule)}</td>'
        f'<td>{_tag(finding.severity)}</td><td>{_e(finding.detail)}</td></tr>'
        for name, finding in entries)
    return f'<div class="wrap"><table>{head}{body}</table></div>'


def _rules(table: dict) -> str:
    blocks = []
    for name, rule in table["rules"].items():
        blocks.append(
            f'<div class="rule"><h4>{_e(name)} {_tag(rule["severity"])}</h4>'
            f'<p>{_e(rule["fires_when"])}</p>'
            f'<p class="q">Quiet when: {_e(rule["quiet_when"])}</p>'
            f'<p class="q">{_e(rule["why"])}</p></div>')
    return "".join(blocks)


def _verdict(digest: Digest) -> str:
    reading = digest.reading
    meaning = digest.table["readings"]["meanings"][reading]
    return (f'<div class="verdict {READING_CLASS.get(reading, "abs")}">'
            f'<b>{_e(reading)}</b><p>{_e(meaning)}</p></div>')


def _provenance_block(digest: Digest) -> str:
    absent = digest.ledger.absent_reason
    lines = [
        ("read at", stamp(digest.rendered_at)),
        ("clock", "UTC" if not digest.utc_offset else
         f"host local, {stamp(digest.rendered_at)[-6:]} from UTC - the clock "
         "scripts/sovschedule/runner.py matches cron in"),
        ("declarations", ".claude/schedules/*.json"),
        ("run history", digest.ledger.path if digest.ledger.present
         else f"{digest.ledger.path} (absent)"),
        ("ledger digest", digest.ledger.digest),
        ("rules", f"contracts/automation-health.json ({digest.table['table_id']}, "
                  f"{digest.table['status']})"),
        ("refuses at", digest.table["blocking"]["refuses_at"]),
    ]
    body = "".join(f"<b>{_e(label)}</b>{_e(value)}<br>" for label, value in lines)
    tail = f"<br>{_e(absent)}" if absent else ""
    return f'<div class="prov">{body}{tail}</div>'


def render(digest: Digest) -> str:
    """Deterministic bytes: derived rows, the declared table, no clock beyond the stamp."""
    table = digest.table
    head = json.dumps(provenance(digest), sort_keys=True)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Soveraeign - automation health</title>
<style>{STYLE}</style></head>
<body>{PROVENANCE_PREFIX}{head}{PROVENANCE_SUFFIX}
<main>
<h1>Automation health</h1>
<p class="sub">Every declared schedule on this node: whether it is switched on, when it is
next due, what happened the last time it ran, and which of the declared health rules fired.
Read-only. Nothing on this page enables, disables, or edits a schedule.</p>
{HISTORY_OPEN}
{_provenance_block(digest)}
{_counts(digest)}
{_verdict(digest)}
<h2>What the records say</h2>
<p>Derived from the run ledger, which is gitignored machine-local state. On a checkout that
holds no ledger this section is the part the staleness check reports as unchecked, because
re-deriving it there would prove only that an absent source produces an empty answer.</p>
{_history_table(digest.rows)}
<h3>Findings from run history</h3>
{_findings(digest, "history")}
{HISTORY_CLOSE}
<h2>What is declared</h2>
<p>Derived from <code>.claude/schedules/*.json</code>, which is committed. This section
reproduces on any checkout and is byte-compared everywhere.</p>
{_declaration_table(digest.rows)}
<h3>Findings from the declarations</h3>
{_findings(digest, "declaration")}
<h2>The rules</h2>
<p>{_e(table["note"])}</p>
{_rules(table)}
<footer><ul>
<li>Refuses at <code>{_e(table["blocking"]["refuses_at"])}</code>:
{_e(table["blocking"]["note"])}</li>
<li>Rebuild: <code>python scripts/sov_schedule.py health-render</code>. Grade:
<code>python scripts/sov_schedule.py health-check</code>, which
<code>scripts/verify.py</code> runs.</li>
<li>The reading layer is separable from where the records come from. The seam is
<code>scripts/sovschedule/history.py</code>; moving this onto Console surface 3 replaces
that module and leaves the rules and their fixtures untouched.</li>
<li>A reading is a report about records and holds no standing. A <code>REPORTED</code>
event in those records is the executor's own self-report, never an observation that the
run did what it said.</li>
</ul></footer>
</main></body></html>
"""
