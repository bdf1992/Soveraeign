"""Render the automation health read, as a static page or as a live console.

Every value is derived. The page carries a provenance comment naming the instant it was
rendered at and the exact ledger bytes it read, because the two halves of this page have
different lifetimes: the declarations are committed and reproduce on any machine, while
the run history lives in gitignored machine-local state and does not exist in CI at all.

So the history block is delimited. ``outside_history`` returns the page with that block
replaced, and the check compares those bytes everywhere and the full bytes only where
the ledger digest still matches. A machine that holds no ledger is told the history half
is UNCHECKED and why, rather than being shown a page graded as current over records it
never had.

The node verdict sits inside the history block rather than at the top of the page. It
is a function of both halves, so a page carrying it outside would change its declared
half the moment a ledger appeared - which is the byte comparison the staleness check
depends on. A test drives exactly that.

``controls`` is the one switch between the two surfaces. False - the default, and what
``docs/automation.html`` is built with - renders a reading whose switch column shows
state. A token renders the same document with working buttons that post to
``control.set_switch``. The static bytes are unaffected by the live surface existing,
which is why the staleness check still grades a file it never serves.

The page holds no standing. A reading here is a report about records.
"""

from __future__ import annotations

import json

from sovschedule import pagecontrols, pagetables
from sovschedule.pagestyle import STYLE
from sovschedule.pagetables import READING_CLASS, e as _e  # noqa: F401 - re-exported
from sovschedule.report import Digest, stamp

PROVENANCE_PREFIX = "<!--sov:provenance "
PROVENANCE_SUFFIX = "-->"
HISTORY_OPEN = "<!--sov:history-->"
HISTORY_CLOSE = "<!--/sov:history-->"
HISTORY_ELIDED = "<!--sov:history-elided-->"
PROVENANCE_ELIDED = "<!--sov:provenance-elided-->"

#: The sections this page prints findings under. A rule's ``needs`` selects one.
SECTIONS = ("history", "declaration")


class UnrenderableFinding(ValueError):
    """A rule whose ``needs`` names no section this page prints.

    ``needs`` is not a label. It decides which of the two sections a finding appears
    under, and there are exactly two call sites. A third value is not a third section:
    it is a finding that appears under neither, so the page prints "Nothing fired."
    twice while the headline reading above it still counts that finding and still says
    UNHEALTHY. Refusing to render is the only honest answer, because the alternative is
    a page that under-reports what its own judge found. A witness found this reachable
    and unpinned; the table alone could open it again.
    """


def _findings(digest: Digest, needs: str) -> str:
    """Kept as a name because the tests and the section wiring both address it."""
    return pagetables.findings(digest, needs)


def provenance(digest: Digest) -> dict:
    """What the check needs to know about how these bytes were produced."""
    return {
        "rendered_at": stamp(digest.rendered_at),
        "declaration_source": digest.source,
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


def _refuse_unrenderable(table: dict) -> None:
    """Every rule must name a section that exists, or the page cannot be trusted."""
    stray = {name: rule["needs"] for name, rule in table["rules"].items()
             if rule["needs"] not in SECTIONS}
    if stray:
        raise UnrenderableFinding(
            f"these rules name a section this page does not print: {stray}. "
            f"It prints {list(SECTIONS)}. A finding under any other name is counted "
            "in the reading and shown nowhere.")


def render(digest: Digest, controls: bool | str = False, targets: tuple = ()) -> str:
    """Deterministic bytes: derived rows, the declared table, no clock beyond the stamp.

    ``controls`` is falsy for the committed reading and the console's token for the
    served one. Only the served page carries buttons and a script; the static bytes are
    what the staleness check grades, and they do not move when a console is running.
    """
    table = digest.table
    _refuse_unrenderable(table)
    live = bool(controls)
    source_line = ("in the working tree, which is the state you are about to change"
                   if live else
                   "tracked at <code>HEAD</code>, not from the working tree")
    head = json.dumps(provenance(digest), sort_keys=True)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Soveraeign - automation health</title>
<style>{STYLE}</style></head>
<body>{PROVENANCE_PREFIX}{head}{PROVENANCE_SUFFIX}
<main>
{pagecontrols.banner(live, len(digest.rows))}
<h1>Automation health</h1>
<p class="sub">Armed is not running: nothing on this node ticks a schedule yet.
Declarations read {source_line}.</p>
{pagecontrols.note(live)}
{pagecontrols.say_line(live)}
{pagetables.declaration_table(digest.rows, controls=live,
                              token=str(controls or ""), targets=targets)}
{_findings(digest, "declaration")}
{HISTORY_OPEN}
{pagetables.verdict(digest)}
<h2>Runs</h2>
{pagetables.counts(digest)}
{pagetables.history_table(digest.rows)}
{_findings(digest, "history")}
{pagetables.provenance_block(digest)}
{HISTORY_CLOSE}
<details><summary>The {len(table["rules"])} health rules</summary>
<p>{_e(table["note"])}</p>
{pagetables.rules(table)}
<ul>
<li>Refuses the build at <code>{_e(table["blocking"]["refuses_at"])}</code>.</li>
<li>Rebuild <code>docs/automation.html</code>:
<code>python scripts/sov_schedule.py health-render</code>.</li>
<li>Same operations without a browser: <code>enable</code>, <code>disable</code>,
<code>create</code>, <code>edit</code>, <code>changes</code>.</li>
<li>A reading is a report about records and holds no standing. A <code>REPORTED</code>
event is the executor's own self-report, not an observation.</li>
</ul></details>
</main>{pagecontrols.script(live)}</body></html>
"""
