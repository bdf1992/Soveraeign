# Scheduled Runs

Declarations that let the host scheduler fire harness workflows and skills
unattended. Like the rest of `.claude/`, this is plumbing: a schedule grants no
authority, a fired run may propose at most `BUILT -> WITNESSED`, and the
scheduler's own record is an attempt-and-report ledger that a later witness
may observe. Standing of the pattern: `decisions/0015-scheduled-runs.md`
(proposed).

## The primitives

| Primitive | Where | What it is |
| --- | --- | --- |
| Declaration | `.claude/schedules/<name>.json` | The schedule analogue of an operation plan: target, cron, mode, effect class, preconditions, limits. Checked against `schedule.schema.json`. |
| Gate | `scripts/sovschedule/runner.py` | Refuses before invocation with a reason code: `SCHEDULE_DISABLED`, `EFFECT_CLASS_REFUSED`, `TREE_DIRTY`, `RUN_IN_PROGRESS`. |
| Run | `claude -p --agent sov-controller` | One headless controller session with mode-scoped tool rights; `git commit`, `git push`, and history rewrites are denied by the harness, not by the prompt. |
| Ledger | `.local/schedules/ledger.ndjson` | Append-only kernel event envelopes (`ATTEMPTED` by the scheduler as `SYSTEM`, `REPORTED` by the controller as `MODEL`), validating against `contracts/event-envelope.schema.json`. Gitignored runtime state. |
| Capture | `.local/schedules/runs/<run_id>.json` | Exact command, exit code, stdout, stderr, timestamps. |
| Report | `reports/<date>-<name>.md` | The human-facing completion report the controller writes, judgement queue included (its commit-or-ignore status is queued for Bdo). |
| Lock | `.local/schedules/lock.json` | One scheduled run in the working tree at a time. |

## Lifecycle of one firing

```text
tick -> due? -> gates -> ATTEMPTED event -> claude -p (sov-controller)
     -> capture + REPORTED event -> (later) sov-qa or a human observes
```

`REPORTED` is the executor's self-report. Its outcome is `ATTEMPTED` on a
zero exit code and `FAILED` otherwise; it never says `COMMITTED`, because
settlement needs an independent observation (`AGENTS.md`, State and
execution). A refused firing still leaves an `ATTEMPTED` event with outcome
`REFUSED` and the reason code, and it counts as an attempt so a refusal does
not retry every tick.

## Declaration fields

- `name` — equals the file stem; `enabled` — shipped declarations are `false`
  until Bdo turns one on.
- `target.kind` `workflow` | `skill`, `target.name` must exist under
  `.claude/workflows/<name>.js` or `.claude/skills/<name>/SKILL.md`;
  `target.args` is passed verbatim.
- `cron` — five fields, local time, `*` `N` `N-M` `*/S` and lists only.
- `mode` — `observe` (Read, Grep, Glob, Agent, Workflow, Skill, Write, and
  read-only git and python via Bash) or `build` (adds Edit). Both deny commit,
  push, reset, rebase, checkout, switch, and stash.
- `effect_class` — the kernel enum; `EXTERNAL_WORLD` is refused at load and at
  the gate (`no_external_effects_in_phase_i`).
- `isolation` — `tree` (default) or `worktree` (passes `--worktree <run_id>`;
  the flag exists in the installed CLI but has not been exercised end to end).
- `preconditions.clean_tree` — default `true` for `build`, `false` for
  `observe`; a build-mode declaration on the shared tree may not set it false.
  `preconditions.lookback_minutes` — how far back a never-fired schedule looks
  for a due minute (default 60).
- `limits.max_budget_usd` and `limits.timeout_seconds` — passed as
  `--max-budget-usd` and the subprocess timeout; the lock TTL is twice the
  timeout.

## Operating it

```bash
python scripts/sov_schedule.py validate          # check every declaration
python scripts/sov_schedule.py list              # declarations and last attempt
python scripts/sov_schedule.py due               # what would fire now
python scripts/sov_schedule.py run nightly-qa --dry-run   # print the command
python scripts/sov_schedule.py run nightly-qa --force     # fire a disabled one now
python scripts/sov_schedule.py tick              # fire everything enabled and due
python scripts/sov_schedule.py ledger --last 10  # read the ledger
python scripts/sov_schedule.py task-command      # print the Task Scheduler / cron registration
python scripts/sov_schedule.py health            # is each one alive, late, failing, drifting
python scripts/sov_schedule.py health --json     # the same read, for a model or for CI
python scripts/sov_schedule.py health-render     # write docs/automation.html
python scripts/sov_schedule.py health-check      # refuse a stale page or an unhealthy schedule
```

The three `health` verbs read and change nothing. What counts as unhealthy is
declared in `contracts/automation-health.json` and defeated by
`conformance/fixtures/automation-health/cases.json`; `decisions/0083` records why
each rule is what it is. `health-check` runs inside `scripts/verify.py`, so an
unhealthy schedule fails the build - the only alert Phase I admits. On a checkout
holding no ledger, which is every CI runner, it can only refuse on a declaration
defect; run health is watched where the runs are.

Registering the tick with the host scheduler is a human action; the runner
never registers itself. Headless runs use whatever credential the `claude`
CLI resolves for the invoking user (the same as an interactive session); the
runner holds no credential and records none.

Not exercised yet: a real headless firing on this machine. The tests stub the
invoker; the first live `run --force` is the witness step.
