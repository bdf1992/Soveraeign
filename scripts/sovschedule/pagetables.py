"""The tables and blocks the automation page is built out of.

Split from ``page.py`` when the controls column arrived and the document skeleton and
the cell rendering stopped fitting in one module under the 300-line ceiling. The seam
is real rather than arithmetic: this file knows what a row looks like, and ``page.py``
knows what a document looks like.

Every function here returns a fragment and reads nothing. The switch column is the one
piece that renders differently between the two surfaces, and it takes the difference as
an argument rather than looking anything up.
"""

from __future__ import annotations

import html

from sovschedule.report import Digest, Row, stamp

READING_CLASS = {"UNHEALTHY": "bad", "DEGRADED": "warn",
                 "UNOBSERVED": "abs", "HEALTHY": "ok"}


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def duration(seconds: float | None) -> str:
    if seconds is None:
        return "-"
    if seconds < 90:
        return f"{seconds:.0f}s"
    return f"{seconds / 60:.1f}m"


def outcome(row: Row) -> str:
    """The run status, carrying the exit code where the executor left one."""
    if row.last_status is None:
        return "-"
    return (row.last_status if row.last_exit_code is None
            else f"{row.last_status} (exit {row.last_exit_code})")


def tag(reading: str) -> str:
    return f'<span class="tag {READING_CLASS.get(reading, "abs")}">{e(reading)}</span>'


def counts(digest: Digest) -> str:
    values = digest.counts
    cells = ((values["declared"], "declared"), (values["enabled"], "armed"),
             (values["with_history"], "ever run"), (digest.ledger.entries, "ledger events"),
             (values["findings"], "findings"), (values["refusing"], "refusing"))
    body = "".join(f"<div><b>{e(value)}</b><span>{e(label)}</span></div>"
                   for value, label in cells)
    return f'<div class="counts">{body}</div>'


def _switch_cell(row: Row, controls: bool) -> str:
    """The switch, as a live control or as a reading.

    Read-only is the default and the static page keeps it, because a button that
    silently does nothing is worse than no button. The served page passes controls=True
    and gets one that posts to the operation.
    """
    state = "on" if row.enabled else "off"
    if not controls:
        return f"<td>{tag(state)}</td>"
    direction = "DISABLE" if row.enabled else "ENABLE"
    label = "switch off" if row.enabled else "arm"
    kind = "off" if row.enabled else "arm"
    return (f'<td class="sw">{tag(state)}'
            f'<button type="button" class="btn {kind}" data-schedule="{e(row.name)}" '
            f'data-direction="{direction}">{e(label)}</button></td>')


def declaration_table(rows: tuple[Row, ...], controls: bool = False) -> str:
    head = ("<tr><th>schedule</th><th>switch</th><th>target</th><th>cadence</th>"
            "<th>next due</th><th>mode</th><th>effect class</th><th>timeout</th></tr>")
    body = "".join(
        f'<tr data-row="{e(row.name)}"><td class="id">{e(row.name)}</td>'
        + _switch_cell(row, controls)
        + f'<td class="t">{e(row.target)}'
        + ("" if row.target_exists else ' <span class="tag bad">missing</span>')
        + ("" if row.defect is None else ' <span class="tag bad">refused</span>')
        + f'</td><td class="t">{e(row.cron_expression)}</td>'
        f'<td class="t">{e(stamp(row.next_due))}</td>'
        f'<td class="t">{e(row.mode)}</td><td class="t">{e(row.effect_class)}</td>'
        f'<td class="n">{e(row.timeout_seconds)}s</td></tr>'
        for row in rows)
    return f'<div class="wrap"><table>{head}{body}</table></div>'


def history_table(rows: tuple[Row, ...]) -> str:
    head = ("<tr><th>schedule</th><th>reading</th><th>attempts</th><th>last attempt</th>"
            "<th>outcome</th><th>duration</th><th>refused</th><th>fails in a row</th></tr>")
    body = "".join(
        f'<tr><td class="id">{e(row.name)}</td><td>{tag(row.reading)}</td>'
        f'<td class="n">{e(row.attempts)}</td>'
        f'<td class="t">{e(stamp(row.last_attempted_at))}</td>'
        f'<td class="t">{e(outcome(row))}</td>'
        f'<td class="n">{e(duration(row.last_duration_seconds))}</td>'
        f'<td class="t">{e(row.last_reason_code or "-")}</td>'
        f'<td class="n">{e(row.consecutive_failures)}</td></tr>'
        for row in rows)
    return f'<div class="wrap"><table>{head}{body}</table></div>'


def findings(digest: Digest, needs: str) -> str:
    entries = [(name, finding) for name, finding in digest.findings
               if digest.table["rules"][finding.rule]["needs"] == needs]
    if not entries:
        return "<p>Nothing fired.</p>"
    head = "<tr><th>schedule</th><th>rule</th><th>severity</th><th>what fired it</th></tr>"
    body = "".join(
        f'<tr><td class="id">{e(name)}</td><td class="t">{e(finding.rule)}</td>'
        f'<td>{tag(finding.severity)}</td><td>{e(finding.detail)}</td></tr>'
        for name, finding in entries)
    return f'<div class="wrap"><table>{head}{body}</table></div>'


def rules(table: dict) -> str:
    blocks = []
    for name, rule in table["rules"].items():
        blocks.append(
            f'<div class="rule"><h4>{e(name)} {tag(rule["severity"])}</h4>'
            f'<p>{e(rule["fires_when"])}</p>'
            f'<p class="q">Quiet when: {e(rule["quiet_when"])}</p>'
            f'<p class="q">{e(rule["why"])}</p></div>')
    return "".join(blocks)


def verdict(digest: Digest) -> str:
    reading = digest.reading
    meaning = digest.table["readings"]["meanings"][reading]
    return (f'<div class="verdict {READING_CLASS.get(reading, "abs")}">'
            f'<b>{e(reading)}</b><p>{e(meaning)}</p></div>')


def provenance_block(digest: Digest) -> str:
    absent = digest.ledger.absent_reason
    lines = [
        ("read at", stamp(digest.rendered_at)),
        ("clock", "UTC" if not digest.utc_offset else
         f"host local, {stamp(digest.rendered_at)[-6:]} from UTC - the clock "
         "scripts/sovschedule/runner.py matches cron in"),
        ("declarations", ".claude/schedules/*.json"
         + (" at HEAD" if digest.source == "COMMIT" else " in the working tree")),
        ("run history", digest.ledger.path if digest.ledger.present
         else f"{digest.ledger.path} (absent)"),
        ("ledger digest", digest.ledger.digest),
        ("rules", f"contracts/automation-health.json ({digest.table['table_id']}, "
                  f"{digest.table['status']})"),
        ("refuses at", digest.table["blocking"]["refuses_at"]),
    ]
    body = "".join(f"<b>{e(label)}</b>{e(value)}<br>" for label, value in lines)
    tail = f"<br>{e(absent)}" if absent else ""
    return f'<div class="prov">{body}{tail}</div>'
