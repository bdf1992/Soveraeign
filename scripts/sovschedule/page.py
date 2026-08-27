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


def render(digest: Digest, controls: bool | str = False) -> str:
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
<p class="sub">Every declared schedule on this node: whether it is armed, when it is next
due, what happened the last time it ran, and which of the declared health rules fired.
Armed is not running - nothing on this node ticks a schedule yet.</p>
{HISTORY_OPEN}
{pagetables.provenance_block(digest)}
{pagetables.counts(digest)}
{pagetables.verdict(digest)}
<h2>What the records say</h2>
<p>Derived from the run ledger, which is gitignored machine-local state. On a checkout that
holds no ledger this section is the part the staleness check reports as unchecked, because
re-deriving it there would prove only that an absent source produces an empty answer.</p>
{pagetables.history_table(digest.rows)}
<h3>Findings from run history</h3>
{_findings(digest, "history")}
{HISTORY_CLOSE}
<h2>What is declared</h2>
<p>Derived from the declarations {source_line}. The two readers differ on purpose and
each says which it read: a committed page reproduces on any checkout and is byte-compared
everywhere, while the console shows the state an operator is looking at.</p>
{pagecontrols.note(live)}
{pagecontrols.say_line(live)}
{pagetables.declaration_table(digest.rows, controls=live)}
<h3>Findings from the declarations</h3>
{_findings(digest, "declaration")}
<h2>The rules</h2>
<p>{_e(table["note"])}</p>
{pagetables.rules(table)}
<footer><ul>
<li>Refuses at <code>{_e(table["blocking"]["refuses_at"])}</code>:
{_e(table["blocking"]["note"])}</li>
<li>Rebuild: <code>python scripts/sov_schedule.py health-render</code>. Grade:
<code>python scripts/sov_schedule.py health-check</code>, which
<code>scripts/verify.py</code> runs.</li>
<li>Switches: <code>python scripts/sov_schedule.py console</code> for this page with
working buttons, or <code>enable</code> / <code>disable</code> on the command line. Both
reach one operation, declared in
<code>contracts/automation-control.json</code>.</li>
<li>The reading layer is separable from where the records come from. The seam is
<code>scripts/sovschedule/history.py</code>; moving this onto Console surface 3 replaces
that module and leaves the rules and their fixtures untouched.</li>
<li>A reading is a report about records and holds no standing. A <code>REPORTED</code>
event in those records is the executor's own self-report, never an observation that the
run did what it said.</li>
</ul></footer>
</main>{pagecontrols.script(live)}</body></html>
"""
