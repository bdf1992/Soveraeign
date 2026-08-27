# Request: I cannot see or steer my own automations

Standing: `DRAFT REQUEST · NOT A DECISION · NOTHING HERE IS SETTLED`

Written 2026-08-27 by Bdo, drafted with Claude in session `soveraeign-7b`.
This is a work order for a fresh session, not policy. Nothing in it changes
standing, and the placement question in it is genuinely open.

## What I want

I want to be able to look at one place and know whether my automations are
alive, when each last ran, whether it passed, and whether anything is drifting
— and I want to be able to turn one on or off without editing JSON by hand.

Right now neither Claude nor I would notice if a scheduled run started failing,
because nothing has ever run and nothing watches.

## What already exists — do not rebuild this

- `.claude/schedules/` holds seven schedule declarations and a JSON schema.
  Required keys are `name`, `enabled`, `target`, `cron`, `mode`, `effect_class`,
  `limits`; optional are `description`, `isolation`, `preconditions`.
- `scripts/sov_schedule.py` is the runner. Verbs: `validate`, `list`, `due`,
  `run <name> [--dry-run]`, `tick`, `ledger`, `task-command`.
- `services/automation/` is a chartered service that owns *when* work is
  requested without a human present. Its subscription lifecycle is built and
  self-tested. It owns nothing about whether the work is allowed, and no
  trigger in this repository can fire yet — `fire-trigger` refuses with
  `AUTHORITY_UNCONFIGURED`. Read `services/automation/CHARTER.md` and
  `KNOWN-GAPS.md` before touching it. Its boundary is packet `A7`, sitting in
  `owner_acceptance_queue` in `STATUS.yaml` and not yet accepted.
- `services/console/CHARTER.md` names five operator surfaces. Surface 3 is
  dashboards — "declared projections over receipts, events, standing, and
  judgement spend". Surface 1 is notifications. Only the continuity path is
  built; the other four are text.
- `decisions/0015-scheduled-runs.md` is the standing the harness schedules hold
  today.

## The state as measured on 2026-08-27

- Seven schedules declared, **all seven `enabled: false`**.
- `.local/schedules/` does not exist. **No scheduled run has ever executed on
  this machine.** `ledger` has nothing to read.
- No graphical or web surface covers schedules. `docs/` has three rendered
  pages — `documentation.html`, `surface.html`, `topology.html` — and none of
  them is about automation.
- So the honest description is: a working runner, seven switched-off
  declarations, an empty history, and no way to see any of it but the CLI.

## What to build

Two steps. Do the first one fully before opening the second.

### Step one — a health read

Something that answers, for every declared schedule: is it on, when is it next
due, when did it last run, did it pass, how long did it take, what did it
refuse, and how many consecutive runs have failed.

This is read-only. It changes nothing and needs no authority. It should be
reachable two ways, because the two readers are different:

- a command, for a model operator and for CI;
- a rendered page under `docs/`, for me, built the way the existing three pages
  are built so it cannot go stale silently.

The interesting part is the health rules, not the display. Decide and write down
what counts as unhealthy: a schedule enabled but never run, a schedule whose
last run failed, a run that took materially longer than its predecessor, a
schedule whose target no longer exists. Each of those needs a case that proves
it fires and a case that proves it does not fire when it should not.

### Step two — switching

A way to enable or disable a schedule that does not mean editing JSON by hand,
and that records who changed it and when.

Do not start this until step one is landed and I have said the health read is
right. The switching surface is worth much less than the seeing surface, and
building it first is how we end up able to change things we cannot observe.

## The decision I have already made, so you do not need to reopen it

This belongs in the Console as a dashboard over Automation's records — Console
surface 3 reading what `services/automation/` owns. It is not a new service and
it is not a new top-level script family.

But the *first* version does not need either service to be finished. Step one
can read `.claude/schedules/*.json` and the ledger directly and still be
correct, because those are the records that exist today. Write it so the reading
layer is separable from where the records come from, and say in the code where
the seam is, so the move into the Console is a change of source and not a
rewrite.

If you think that placement is wrong, say so with evidence and I will rule on
it. Do not silently build it somewhere else.

## Alerts

I asked for alerts and I want to be clear about what that can mean here. Phase I
forbids external-world effects, so an alert cannot be an email, a push, or
anything that leaves this machine. What it can be:

- a nonzero exit from a check that `scripts/verify.py` runs, so an unhealthy
  automation fails the build;
- a notification record on Console surface 1, so it is waiting for me the next
  time I open the console;
- a line in the completion report of any run that touches it.

Pick whichever of those you can evidence. Do not design an outbound channel.

## Out of scope

- Making `fire-trigger` able to succeed. That needs a `SYSTEM` principal, a
  verified identity, a live grant, and the Capability Broker. It is epic `#15`
  and it is not this.
- Registering anything with the Windows scheduler or any OS-level task. Nothing
  gets registered with my machine without me saying so explicitly.
- Enabling any schedule. Every one of the seven stays `enabled: false` until I
  turn it on myself.
- Moving `.claude/schedules/` into the Automation Service. That is the schedule
  lift in `services/automation/KNOWN-GAPS.md` and it is a separate concern.

## Constraints

Standard for this repository, listed so they are not rediscovered:

- Contract and its defeating fixture before implementation. Never weaken an
  oracle to make something pass.
- Python 3.11+, standard library only. A dependency needs a decision record.
- Modules stay under 300 lines. `scripts/lint.py` reads working-tree bytes and
  the repository pins LF.
- `python scripts/verify.py` and `python scripts/lint.py` both have to pass.
- Nine sessions write this tree at once. Take a worktree or stage explicit
  paths; blanket staging is refused here.
- A build cannot witness itself. Landing needs an observation from a
  participant that did not build it.

## What waits on me

- Whether the Console placement above is right, if you have evidence against it.
- Whether step one reads correctly, before step two starts.
- Turning any schedule on. That is mine and I have not done it.
