# 0015 · Scheduled runs as declared, gated, recorded attempts

Status: `PROPOSED · OWNER RATIFICATION PENDING`

## Decision

Let the host scheduler fire harness workflows and skills unattended through a
small set of primitives that reuse the kernel vocabulary instead of adding a
new one:

- A **schedule declaration** (`.claude/schedules/<name>.json`) is the
  schedule analogue of an operation plan: target, cadence, mode, effect
  class, preconditions, and limits are declared before anything fires. It is
  harness-owned and grants no authority.
- A **gate** refuses before invocation with a visible reason code:
  `SCHEDULE_DISABLED`, `EFFECT_CLASS_REFUSED` (`EXTERNAL_WORLD` is never
  schedulable in Phase I), `TREE_DIRTY` (build mode on a shared dirty tree),
  `RUN_IN_PROGRESS` (single-runner lock).
- A **run** is one headless `claude -p --agent sov-controller` session with
  mode-scoped tool rights. Commit, push, and history rewrites are denied by
  the harness invocation, not only by the prompt.
- A **ledger** (`.local/schedules/ledger.ndjson`, gitignored) appends kernel
  event envelopes that validate against
  `contracts/event-envelope.schema.json`: `ATTEMPTED` by the scheduler as a
  `SYSTEM` actor, `REPORTED` by the controller as a `MODEL` actor. A report
  outcome is `ATTEMPTED` or `FAILED`, never `COMMITTED`; settlement needs an
  independent observation.
- The **completion report** stays where controller reports already land:
  `reports/<date>-<name>.md`, judgement queue included.

The durable surface is the OS scheduler calling
`python scripts/sov_schedule.py tick` (the same pattern as the owner's
existing local maintenance task). In-session cron and `/loop` die with the
session and are not durable; cloud routines run outside the node and are not
admitted in Phase I.

## Consequences

- Scheduling changes nothing about authority: a fired run proposes at most
  `BUILT -> WITNESSED`, builders never witness themselves, and Bdo alone
  ratifies. The ledger is a record of attempts and reports, not evidence that
  anything committed.
- Shipped declarations are disabled. Enabling one, and registering the tick
  with the host scheduler, are owner actions with recurring resource
  consumption.
- `scripts/lint.py` skips `.local/` (runtime state, never repository text),
  and `scripts/verify.py` runs the harness tests under `scripts/tests/`.
- `sov-controller` gains the `Workflow` and `Agent` tools; without them it
  could not dispatch the workflows its definition describes.
- Worktree isolation (`--worktree <run_id>`) is declared but not yet
  exercised end to end; the first live firing is the witness step.

## Open questions for Bdo

1. Ratify this pattern together with `0013` (the reserved O13 harness
   question), or keep scheduling a separate decision?
2. Are completion reports written by scheduled runs committed, or does
   `reports/` stay local (baseline report item 7)?
3. Which credential may an unattended run use: the interactive login of the
   invoking user, or a dedicated API key with its own budget? This is a
   BYOM data-boundary question as much as an operations one.
4. Are cloud routines (repository cloned and run outside the node) ever
   admissible, and under which crossing contract?
5. Should scheduled-run reports become Console Service notifications or
   judgement requests once O14 settles, through a declared crossing?

## Source and authority

- `AGENTS.md`: State and execution (workers report; observation settles),
  Change protocol (effect class), Local orchestration harness
- `SPEC.md`: `Run`, `EventEnvelope`, `begin_run` / `report_run` /
  `observe_run` transitions
- `ENGINEERING.md`: Growth triggers ("durable work must outlive a process ->
  lease-backed queue component using the Run contract"); Kernel primitives
- `STATUS.yaml`: protected boundary `no_external_effects_in_phase_i`
- `decisions/0018-federation-harness.md`
- Bdo's 2026-08-22 request for the primitives needed to schedule agent action
  on workflows and skills
