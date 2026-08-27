"""What makes the served page's switches work, and what the static page says instead.

Two surfaces render from one function. The file under ``docs/`` is a reading: it has no
process behind it, so its switch column stays a reading and the page says where the
working controls are rather than showing a button that does nothing. The served page
carries this script and posts to the operation.

The script is deliberately small and does one thing per click: ask, post, show what the
operation decided, reload. It never decides anything itself - it cannot, because the
authority check is in ``control.set_switch`` and this is a binding, not a shortcut past
one. A refusal is printed as the operation worded it rather than being translated here.
"""

from __future__ import annotations

from sovschedule.pagetables import e

#: Shown on the page under docs/, where nothing can be clicked.
STATIC_NOTE = (
    "This page is a reading. Its switch column shows state and cannot change it, because "
    "a file opened from disk has no process behind it. For working switches run "
    "<code>python scripts/sov_schedule.py console</code>, which serves this same read at "
    "<code>127.0.0.1</code> with the buttons live. The command line reaches the same "
    "operation: <code>python scripts/sov_schedule.py disable &lt;name&gt; --reason "
    "&lt;text&gt;</code>.")

#: Shown on the served page, where they can.
LIVE_NOTE = (
    "The switches below write <code>.claude/schedules/</code> and commit nothing, so a "
    "change sits in the working tree until someone lands it. Arming a schedule is the "
    "owner's - a model reaching this same operation gets a recorded proposal and the "
    "switch does not move. Every attempt, including every refusal, appends a line to "
    "<code>.claude/schedules/change-log.ndjson</code>.")

SCRIPT = """
<script>
(function () {
  var token = new URLSearchParams(window.location.search).get("t");
  var say = document.getElementById("say");
  function report(text, bad) {
    say.textContent = text;
    say.className = "say " + (bad ? "bad" : "ok");
  }
  document.querySelectorAll("button.btn").forEach(function (button) {
    button.addEventListener("click", function () {
      var schedule = button.dataset.schedule;
      var direction = button.dataset.direction;
      var reason = window.prompt(
        direction === "ENABLE"
          ? "Arming " + schedule + ". Why? This goes in the change log."
          : "Switching " + schedule + " off. Why? This goes in the change log.");
      if (reason === null) { return; }
      button.disabled = true;
      report("asking...", false);
      fetch("/switch", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({token: token, schedule: schedule,
                              direction: direction, reason: reason})
      }).then(function (response) {
        return response.json();
      }).then(function (answer) {
        report((answer.refusal || (answer.outcome + ": " + answer.detail)),
               !!answer.refusal || answer.outcome === "REFUSED");
        if (answer.moved) { window.setTimeout(function () {
          window.location.reload();
        }, 900); } else { button.disabled = false; }
      }).catch(function (error) {
        report("the console did not answer: " + error, true);
        button.disabled = false;
      });
    });
  });
})();
</script>
"""


def note(controls: bool) -> str:
    """The paragraph above the declaration table, which differs between the surfaces."""
    return f'<p class="note">{LIVE_NOTE if controls else STATIC_NOTE}</p>'


def say_line(controls: bool) -> str:
    """Where the operation's answer is printed, verbatim. Absent on the static page."""
    return '<div id="say" class="say"></div>' if controls else ""


def script(controls: bool) -> str:
    return SCRIPT if controls else ""


def links(controls: bool, token: str) -> str:
    """New and edit are reachable only where something can act on them."""
    if not controls:
        return ""
    return (f'<div class="row"><a class="btn arm" href="/new?t={e(token)}">'
            "new schedule</a></div>")


def banner(controls: bool, schedule_count: int) -> str:
    """One line naming which surface this is, so a screenshot cannot be misread."""
    if controls:
        return ('<div class="live">live console - '
                f'{e(schedule_count)} schedules, switches active</div>')
    return ('<div class="ro">read-only page - switches show state and do not change it</div>')
