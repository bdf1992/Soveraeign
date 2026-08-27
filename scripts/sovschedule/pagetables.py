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
import json

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


def _edit_cell(row: Row, controls: bool) -> str:
    """A toggle per row, live only. The static page has nothing to open."""
    if not controls:
        return ""
    return (f'<td><button type="button" class="btn ed" data-edit="{e(row.name)}">'
            "edit</button></td>")


#: The fields an edit may touch, as they appear in the inline editor. `name` appears
#: only when creating; `enabled` never - it has its own operation.
INLINE = (("description", "text", "description"),
          ("target", "target", "runs"),
          ("cron", "text", "cadence"),
          ("mode", "select", "mode"),
          ("effect_class", "select", "effect"),
          ("isolation", "select", "isolation"),
          ("max_budget_usd", "number", "budget $"),
          ("timeout_seconds", "number", "timeout s"),
          ("args", "json", "args"),
          ("preconditions", "json", "preconditions"))

OPTIONS = {"mode": ("observe", "build"),
           "effect_class": ("RECORD_LOCAL", "RESOURCE_CONSUMPTION"),
           "isolation": ("tree", "worktree")}


def _options(values, chosen) -> str:
    return "".join(f'<option value="{e(v)}"{" selected" if v == chosen else ""}>'
                   f"{e(label)}</option>" for v, label in values)


def _field(field: str, kind: str, label: str, value: object, key: str,
           targets: tuple) -> str:
    ident = f"{field}-{key}"
    if kind == "select":
        inner = _options([(o, o) for o in OPTIONS[field]], value)
        control = f'<select id="{e(ident)}" data-field="{e(field)}">{inner}</select>'
    elif kind == "target":
        # Read off .claude/ the same way the loader checks it, so the list cannot offer
        # something the save then refuses.
        pairs = [("", "- pick one -")] + [
            (f'{t["kind"]}:{t["name"]}', f'{t["name"]} ({t["kind"]})') for t in targets]
        control = (f'<select id="{e(ident)}" data-field="target">'
                   f"{_options(pairs, value)}</select>")
    elif kind == "json":
        control = (f'<textarea id="{e(ident)}" data-field="{e(field)}" rows="2">'
                   f"{e(json.dumps(value))}</textarea>")
    else:
        control = (f'<input id="{e(ident)}" data-field="{e(field)}" '
                   f'type="{"number" if kind == "number" else "text"}" '
                   f'value="{e(value)}">')
    return f'<label class="f"><span>{e(label)}</span>{control}</label>'


def _editor(key: str, values: dict, columns: int, targets: tuple,
            creating: bool = False) -> str:
    """The editor, in the table, under the row it edits. Hidden until asked for."""
    fields = ""
    if creating:
        fields += _field("name", "text", "name", "", key, targets)
    fields += "".join(_field(f, kind, label, values.get(f, ""), key, targets)
                      for f, kind, label in INLINE)
    return (f'<tr class="ed-row" id="ed-{e(key)}"{"" if creating else " hidden"}>'
            f'<td colspan="{columns}"><div class="grid">{fields}</div>'
            f'<div class="save"><input id="why-{e(key)}" class="why" '
            f'placeholder="why - goes in the change log">'
            f'<button type="button" class="btn arm" data-save="{e(key)}">save</button>'
            f'<button type="button" class="btn" data-cancel="{e(key)}">cancel</button>'
            "</div></td></tr>")


def _values(row: Row) -> dict:
    limits = row.raw.get("limits") or {}
    target = row.raw.get("target") or {}
    return {"description": row.description, "target": row.target,
            "cron": row.cron_expression, "mode": row.mode,
            "effect_class": row.effect_class,
            "isolation": row.raw.get("isolation", "tree"),
            "max_budget_usd": limits.get("max_budget_usd", 0),
            "timeout_seconds": row.timeout_seconds, "args": target.get("args") or {},
            "preconditions": row.raw.get("preconditions") or {}}


BLANK = {"description": "", "target": "", "cron": "0 3 * * *", "mode": "observe",
         "effect_class": "RESOURCE_CONSUMPTION", "isolation": "tree",
         "max_budget_usd": 3, "timeout_seconds": 1800, "args": {},
         "preconditions": {"clean_tree": False, "lookback_minutes": 60}}


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


def declaration_table(rows: tuple[Row, ...], controls: bool = False,
                      token: str = "", targets: tuple = ()) -> str:
    columns = 8 if controls else 7
    head = ("<tr><th>schedule</th><th>switch</th>"
            + ("<th></th>" if controls else "")
            + "<th>runs</th><th>cadence</th><th>next due</th>"
            "<th>mode</th><th>budget</th></tr>")
    body = []
    for row in rows:
        limits = row.raw.get("limits") or {}
        body.append(
            f'<tr data-row="{e(row.name)}"><td class="id">{e(row.name)}</td>'
            + _switch_cell(row, controls)
            + _edit_cell(row, controls)
            + f'<td class="t">{e(row.target)}'
            + ("" if row.target_exists else ' <span class="tag bad">missing</span>')
            + ("" if row.defect is None else ' <span class="tag bad">refused</span>')
            + f'</td><td class="t">{e(row.cron_expression)}</td>'
            f'<td class="t">{e(stamp(row.next_due))}</td>'
            f'<td class="t">{e(row.mode)}</td>'
            f'<td class="n">${e(limits.get("max_budget_usd", "-"))}</td></tr>')
        if controls:
            body.append(_editor(row.name, _values(row), columns, targets))
    if controls:
        body.append(f'<tr><td colspan="{columns}">'
                    '<button type="button" class="btn ed" data-edit="__new__">'
                    "new schedule</button></td></tr>")
        body.append(_editor("__new__", dict(BLANK), columns, targets, creating=True))
        body[-1] = body[-1].replace('id="ed-__new__"', 'id="ed-__new__" hidden', 1)
    return f'<div class="wrap"><table>{head}{"".join(body)}</table></div>'


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
