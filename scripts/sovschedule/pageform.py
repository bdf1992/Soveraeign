"""The form for creating a schedule and for editing one.

A separate page from the health read, because they answer different questions and
cramming an editor into a status table makes both worse. The health page links here and
this links back.

Every choice the form offers is one the save can accept. The target list is read off the
filesystem the same way the loader's target check reads it, so the dropdown cannot offer
a workflow that the save then refuses; the enums come from the schema rather than from a
list typed here. The one free-text field that can still fail is the arguments object,
which is JSON and is checked on save.

The form does not decide anything. It posts to ``authoring.create`` or
``authoring.update``, where the grant is tested, and prints whatever those return.
"""

from __future__ import annotations

import json

from sovschedule.pagestyle import STYLE
from sovschedule.pagetables import e

MODES = ("observe", "build")
#: EXTERNAL_WORLD is deliberately absent: the phase refuses it, so offering it would be
#: offering a choice whose only outcome is a refusal.
EFFECTS = ("RECORD_LOCAL", "RESOURCE_CONSUMPTION")
ISOLATIONS = ("tree", "worktree")


def _text(label: str, field: str, value: object, hint: str = "",
          disabled: bool = False) -> str:
    lock = " disabled" if disabled else ""
    note = f'<span class="hint">{hint}</span>' if hint else ""
    return (f'<label><span>{e(label)}</span>{note}'
            f'<input type="text" name="{e(field)}" value="{e(value)}"{lock}></label>')


def _number(label: str, field: str, value: object, hint: str = "") -> str:
    note = f'<span class="hint">{hint}</span>' if hint else ""
    return (f'<label><span>{e(label)}</span>{note}'
            f'<input type="number" name="{e(field)}" value="{e(value)}" min="0"></label>')


def _select(label: str, field: str, value: object, options, hint: str = "") -> str:
    note = f'<span class="hint">{hint}</span>' if hint else ""
    cells = "".join(
        f'<option value="{e(option)}"{" selected" if option == value else ""}>'
        f'{e(option)}</option>' for option in options)
    return (f'<label><span>{e(label)}</span>{note}'
            f'<select name="{e(field)}">{cells}</select></label>')


def _target_select(targets: list[dict], kind: str, name: str) -> str:
    """One dropdown over both kinds, because an operator picks a thing, not a category."""
    current = f"{kind}:{name}"
    options = ['<option value="">- pick what this runs -</option>']
    for target in targets:
        value = f'{target["kind"]}:{target["name"]}'
        chosen = " selected" if value == current else ""
        options.append(f'<option value="{e(value)}"{chosen}>{e(target["name"])}'
                       f'  ({e(target["kind"])})</option>')
    return ('<label><span>Runs</span><span class="hint">the workflow or skill this '
            'schedule executes. Read off .claude/, so everything listed here is '
            'something the loader will accept.</span>'
            f'<select name="target">{"".join(options)}</select></label>')


def _textarea(label: str, field: str, value: str, hint: str, rows: int = 6) -> str:
    return (f'<label><span>{e(label)}</span><span class="hint">{hint}</span>'
            f'<textarea name="{e(field)}" rows="{rows}">{e(value)}</textarea></label>')


SCRIPT = """
<script>
(function () {
  var token = new URLSearchParams(window.location.search).get("t");
  var form = document.getElementById("form");
  var say = document.getElementById("say");
  var mode = form.dataset.mode;
  function report(text, bad) {
    say.textContent = text;
    say.className = "say " + (bad ? "bad" : "ok");
  }
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    var data = new FormData(form);
    var target = (data.get("target") || "").split(":");
    var args, pre;
    try { args = JSON.parse(data.get("args") || "{}"); }
    catch (error) { report("arguments are not JSON: " + error, true); return; }
    try { pre = JSON.parse(data.get("preconditions") || "{}"); }
    catch (error) { report("preconditions are not JSON: " + error, true); return; }
    var body = {
      description: data.get("description"),
      target: {kind: target[0] || "", name: target[1] || "", args: args},
      cron: data.get("cron"),
      mode: data.get("mode"),
      effect_class: data.get("effect_class"),
      isolation: data.get("isolation"),
      preconditions: pre,
      limits: {max_budget_usd: Number(data.get("max_budget_usd")),
               timeout_seconds: Number(data.get("timeout_seconds"))}
    };
    report("saving...", false);
    fetch("/save", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({token: token, mode: mode, name: data.get("name"),
                            reason: data.get("reason"), body: body})
    }).then(function (response) { return response.json(); })
      .then(function (answer) {
        report(answer.refusal || (answer.outcome + ": " + answer.detail),
               !!answer.refusal || answer.outcome === "REFUSED");
        if (answer.outcome === "EFFECTED") {
          window.setTimeout(function () {
            window.location.href = "/?t=" + encodeURIComponent(token);
          }, 1400);
        }
      }).catch(function (error) {
        report("the console did not answer: " + error, true);
      });
  });
})();
</script>
"""


def render(targets: list[dict], body: dict, token: str, creating: bool) -> str:
    """The form, filled from ``body``. ``creating`` decides the name field and the verb."""
    target = body.get("target") or {}
    limits = body.get("limits") or {}
    name = body.get("name", "")
    heading = "New schedule" if creating else f"Edit {name}"
    fields = "".join([
        _text("Name", "name", name,
              "lower case, digits and hyphens. It is the file name, so it cannot be "
              "changed later - a rename is a new schedule and the removal of this one."
              if creating else "the file name, and not editable", disabled=not creating),
        _text("Description", "description", body.get("description", ""),
              "one sentence, for whoever reads this at three in the morning"),
        _target_select(targets, target.get("kind", ""), target.get("name", "")),
        _text("Cadence", "cron", body.get("cron", ""),
              "five cron fields, read in this host's local clock"),
        _select("Mode", "mode", body.get("mode"), MODES,
                "observe reports and changes nothing; build writes"),
        _select("Effect class", "effect_class", body.get("effect_class"), EFFECTS,
                "EXTERNAL_WORLD is absent because the phase refuses it"),
        _select("Isolation", "isolation", body.get("isolation"), ISOLATIONS,
                "worktree gives the run its own checkout; several sessions share this one"),
        _number("Budget, USD", "max_budget_usd", limits.get("max_budget_usd", 3)),
        _number("Timeout, seconds", "timeout_seconds", limits.get("timeout_seconds", 1800)),
        _textarea("Arguments", "args",
                  json.dumps(target.get("args", {}), indent=2),
                  "JSON, passed to the workflow or skill", rows=6),
        _textarea("Preconditions", "preconditions",
                  json.dumps(body.get("preconditions", {}), indent=2),
                  "JSON. clean_tree false lets it run on a dirty tree", rows=4),
        _textarea("Reason", "reason", "",
                  "why you are making this change. It goes in the change log and is "
                  "required.", rows=2),
    ])
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Soveraeign - {e(heading)}</title>
<style>{STYLE}</style></head>
<body><main>
<div class="live">live console - this form writes .claude/schedules/ and commits nothing</div>
<h1>{e(heading)}</h1>
<p class="sub">A schedule says when to run one workflow or skill, with what arguments and
under what budget. It does not compose services - that is what the workflow itself does,
and writing one is a code change rather than a form.</p>
<p class="note">Saved switched off. Arming is a separate decision with its own record, and
editing an armed schedule needs the owner because it changes what runs unattended.</p>
<form id="form" data-mode="{"create" if creating else "update"}">
{fields}
<div class="row"><button type="submit" class="btn arm">
{"Create it" if creating else "Save changes"}</button>
<a class="btn" href="/?t={e(token)}">back to health</a></div>
</form>
<div id="say" class="say"></div>
</main>{SCRIPT}</body></html>
"""
