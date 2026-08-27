"""What makes the served page's controls work, and what the static page says instead.

Two surfaces render from one function. The file under ``docs/`` is a reading: no process
sits behind it, so its controls stay readings and the page says in one line where the
working ones are. The served page carries this script.

Editing happens in the table. A row opens under itself, you change a field, you say why,
you save. There was a separate form page for a moment and it was the wrong shape - it
took you away from the thing you were reading in order to change one field of it, and
restated every column as a label on the way.

The script decides nothing. It posts to the operations, where the grants are tested, and
prints back whatever they return, worded as they worded it.
"""

from __future__ import annotations

STATIC_NOTE = ("A reading. For working controls: "
               "<code>python scripts/sov_schedule.py console</code>.")

LIVE_NOTE = ("Edits write <code>.claude/schedules/</code> and commit nothing. Arming, "
             "and any change to something already armed, is the owner's. Every attempt "
             "lands in <code>change-log.ndjson</code>.")

SCRIPT = """
<script>
(function () {
  var token = new URLSearchParams(window.location.search).get("t");
  var say = document.getElementById("say");
  function report(text, bad) {
    say.textContent = text;
    say.className = "say " + (bad ? "bad" : "ok");
  }
  function post(path, payload, done) {
    payload.token = token;
    fetch(path, {method: "POST", headers: {"Content-Type": "application/json"},
                 body: JSON.stringify(payload)})
      .then(function (r) { return r.json(); })
      .then(function (answer) {
        if (answer.outcome || answer.refusal || answer.refusal_code) {
          report(answer.refusal || answer.detail || answer.outcome,
                 !!(answer.refusal || answer.refusal_code)
                 || answer.outcome === "REFUSED");
        }
        done(answer);
      })
      .catch(function (error) { report("no answer: " + error, true); done(null); });
  }
  function reloadSoon() {
    window.setTimeout(function () { window.location.reload(); }, 900);
  }
  function collect(name) {
    var row = document.getElementById("ed-" + name);
    var body = {limits: {}, target: {}};
    var bad = null;
    row.querySelectorAll("[data-field]").forEach(function (input) {
      var field = input.dataset.field;
      if (field === "max_budget_usd" || field === "timeout_seconds") {
        body.limits[field] = Number(input.value);
      } else if (field === "args" || field === "preconditions") {
        try {
          var parsed = JSON.parse(input.value || "{}");
          if (field === "args") { body.target.args = parsed; }
          else { body.preconditions = parsed; }
        } catch (error) { bad = field + " are not JSON: " + error; }
      } else if (field === "target") {
        var pair = (input.value || "").split(":");
        body.target.kind = pair[0] || "";
        body.target.name = pair[1] || "";
      } else if (field !== "name") {
        body[field] = input.value;
      }
    });
    if (bad) { report(bad, true); return null; }
    return body;
  }
  // The proposal comes back keyed by declaration field; the inputs are keyed by what
  // they edit, and two of them live inside nested objects. Mapped here rather than
  // flattened on the way out, so the operation keeps taking whole objects.
  function fill(key, changes) {
    var touched = [];
    function set(field, value) {
      var input = document.getElementById(field + "-" + key);
      if (!input) { return; }
      input.value = (typeof value === "object") ? JSON.stringify(value) : value;
      input.classList.add("moved");
      touched.push(field);
    }
    Object.keys(changes).forEach(function (field) {
      var value = changes[field];
      if (field === "limits") {
        set("max_budget_usd", value.max_budget_usd);
        set("timeout_seconds", value.timeout_seconds);
      } else if (field === "target") {
        set("target", value.kind + ":" + value.name);
        if (value.args !== undefined) { set("args", value.args); }
      } else {
        set(field, value);
      }
    });
    return touched;
  }
  document.addEventListener("click", function (event) {
    var el = event.target;
    if (el.dataset.ask) {
      var key = el.dataset.ask;
      var text = document.getElementById("ask-" + key).value;
      if (!text.trim()) { return; }
      el.disabled = true;
      report("asking the local model...", false);
      post("/interpret", {name: key, request: text}, function (answer) {
        el.disabled = false;
        if (!answer || answer.refusal_code) { return; }
        var touched = fill(key, answer.changes || {});
        report("proposed: " + touched.join(", ") + " - " + answer.why
               + "  [" + answer.model + ", " + answer.seconds + "s, nothing saved]",
               false);
      });
      return;
    }
    if (el.dataset.edit) {
      var row = document.getElementById("ed-" + el.dataset.edit);
      row.hidden = !row.hidden;
      el.textContent = row.hidden ? "edit" : "close";
      return;
    }
    if (el.dataset.cancel) {
      document.getElementById("ed-" + el.dataset.cancel).hidden = true;
      return;
    }
    if (el.dataset.save) {
      var key = el.dataset.save;
      var body = collect(key);
      if (!body) { return; }
      var creating = key === "__new__";
      var name = creating ? document.getElementById("name-__new__").value : key;
      el.disabled = true;
      post("/save", {mode: creating ? "create" : "update", name: name,
                     reason: document.getElementById("why-" + key).value, body: body},
           function (answer) {
             if (answer && answer.outcome === "EFFECTED") { reloadSoon(); }
             else { el.disabled = false; }
           });
      return;
    }
    if (el.dataset.schedule) {
      var reason = window.prompt("Why? This goes in the change log.");
      if (reason === null) { return; }
      el.disabled = true;
      post("/switch", {schedule: el.dataset.schedule,
                       direction: el.dataset.direction, reason: reason},
           function (answer) {
             if (answer && answer.moved) { reloadSoon(); } else { el.disabled = false; }
           });
    }
  });
})();
</script>
"""


def note(controls: bool) -> str:
    return f'<p class="note">{LIVE_NOTE if controls else STATIC_NOTE}</p>'


def say_line(controls: bool) -> str:
    """Where the operations' answers are printed, verbatim. Absent on the static page."""
    return '<div id="say" class="say"></div>' if controls else ""


def script(controls: bool) -> str:
    return SCRIPT if controls else ""


def banner(controls: bool, schedule_count: int) -> str:
    """One line naming which surface this is, so a screenshot cannot be misread."""
    if controls:
        return '<div class="live">live console - controls active</div>'
    return '<div class="ro">read-only page</div>'
