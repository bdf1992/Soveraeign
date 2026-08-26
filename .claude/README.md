# Claude Harness Binding (Provisional)

This directory is the first harness binding of the operating loop defined in
`SDLC.md`, admitted as a provisional target by owner direction (decision
0013). It realizes the loop for the Claude Code harness; it owns no policy.

When the underlying Claude model is asked to act as Soveraeign's main operating
agent, load the portable `SOV.md` profile before selecting a tier skill. Claude
is the current model/host binding; Sov is the operating profile. Loading Sov
does not grant Control or any other authority.

Binding rules from `bindings/README.md` apply: this surface may project the
loop for this harness, but it may not introduce private standing, authority,
transitions, or direct storage writes. Every rule a skill applies is owned by
a governing document; skills point, they do not restate. On any divergence
between a skill and an owning document, the owning document prevails.

Model substitutability applies to the loop itself: a second, materially
different harness binding must be able to run the same loop from the
governing documents alone. Nothing in this directory may become
load-bearing for the loop's semantics.

## Two skill families are present, and their relationship is unresolved

The directory currently holds two prefixes, built in parallel by concurrent
sessions. They do not collide by name and neither is authoritative over the
other. **Which layer each occupies is an open judgement item for Bdo**; see
`reports/2026-08-23-harness-reconciliation.md` and
`reports/2026-08-23-merge-readiness.md`. Nothing below decides it.

| Prefix | Standing | Shape |
| --- | --- | --- |
| `sdlc-` | decision `0013-domain-mapped-sdlc-loop.md`, merged | tier and domain skills; no executable orchestration |
| `sov-` | decision `0026-federation-harness.md`, proposed | domain skills, four role agents, eighteen executable workflows |

One tension the merge does not dissolve: this file states that executable
orchestration scripts are not admitted before their logical specification and
defeating fixtures exist, and the `sov-` family ships eighteen of them. Either
those workflows fall outside the rule because they orchestrate harness agents
rather than kernel operations, or they are currently inadmissible. That is a
judgement, not a merge mechanic.

## The SDLC loop binding (`sdlc-`)

Skills are prefixed `sdlc-`. Tier skills: `sdlc-control`,
`sdlc-orchestration`, `sdlc-worker`. Domain skills: `sdlc-product`,
`sdlc-development`, `sdlc-qa`, `sdlc-release`, `sdlc-feedback`. Workflow
templates remain declarations in `SDLC.md`; executable orchestration scripts
are not admitted before their logical specification and defeating fixtures
exist.

## The federation harness (`sov-`)

Local Claude Code definitions that let a controller session orchestrate work on
this repository as a three-tier federation. Harness plumbing: nothing in it
holds standing or authority under `STATUS.yaml`, and running any of it grants
no right that `AGENTS.md` does not grant.

```text
Controller (agents/sov-controller.md, launched by Bdo or Claude interactively, or by a schedule headless;
            reports to Bdo)
  -> Domain workflows (workflows/sov-<domain>.js, one per domain)
       -> Stable roles (agents/): sov-orchestrator plans, sov-worker builds,
          sov-witness verifies
```

Agents are stable roles; the domain-specific layer is skills and workflows.
Adding a domain means adding a skill and a workflow - never a new agent.
Cross-cutting capabilities (`sov-qa`, `sov-scribe`) follow the same rule:
skill + workflow, riding the same roles.

- The controller launches `sov-federation` (or a single domain workflow),
  reads the aggregated report, and surfaces to Bdo only what an owner-held
  boundary genuinely reserves to him.
- Each domain workflow runs Scope -> Build -> Witness and returns a structured
  report. A domain is blocked only when no admissible operation exists for
  the objective; a gated end state with reachable precursors is a plan, not a
  block (`AGENTS.md`, Blocked edge is not blocked frontier). A blocked domain
  returns early with its judgement items instead of forcing work.
- Builders and witnesses are always different agents: a build report cannot
  witness itself (`AGENTS.md`, Evidence and standing).
- A worker carries its operation to closure and recruits its own helpers. A
  helper subagent that read or edited the change is inside the build and can
  never be its witness, which is why recruiting one costs nothing and proves
  nothing (`AGENTS.md`, Closure ownership;
  `contracts/closure-ownership.json`). Grade any handoff a run produces with
  `python scripts/sov_closure.py judge <claim.json>` before it reaches Bdo.

### Domains

| Domain | Owns | What it is waiting on |
| --- | --- | --- |
| `governance` | Design System of Record, decisions, STATUS standing | nothing; `PUBLIC-CLEARANCE` blocks release only |
| `contracts` | Shared kernel/crossing JSON Schemas | a fixture pair per schema |
| `conformance` | Oracle, scenarios, fresh-witness qualification | a participant binding |
| `asset` | Asset Service lifecycle (`services/asset/`) | an independent witness, and the `core.py` split |
| `proofing` | Proofing Service charter and contracts only | its contract and defeating fixtures |
| `trust` | Identity and Registry Services (`services/identity/`, `services/registry/`) | an independent witness of both built slices |
| `console` | Console Service charter, contracts, and seed fixtures only (`services/console/`) | its contract and defeating fixtures |
| `projection` | Asset Projection Service charter, parity ledger, and seed fixtures (`services/projection/`) | executable fixtures, then the asset `core.py` split |
| `byom` | Model bindings, adapters, portability (PROD-I-9) | an independent witness of the adapter |
| `verification` | `scripts/verify.py`, lint, CI gate, baseline | nothing |

Nothing in this table waits on Bdo. Each entry names a missing precondition a
tier can produce, which is what `decisions/0033-close-the-founding-docket.md`
Ruling 1 asks a column like this to say.

These ten domains do not cover the whole epic-of-epics issue tree. Twenty open
bits and stubs are claimed by no domain skill. `epic/villages.json` leaves them
unrouted rather than force-fitting them; `python scripts/sov_epic.py unrouted`
lists them, and the walk reports each as unrouted work needing a domain, not as
a question for Bdo. Writing the artifact that would route one is ordinary
reversible work at this tier (`AGENTS.md`, Closure ownership).

`trust` is the first domain added under that rule rather than by opinion.
`services/identity/` and `services/registry/` already carry charters, service
manifests, implementations, and tests - `scripts/verify.py` runs the identity
cases as `Identity component tests` - so issues #11 and #14 route there on that
evidence and are now visible as `HELD` by #8 rather than hidden behind a missing
domain. The rest of `trust-and-control` has no such artifact: authority (#12),
gates (#13), and the capability broker (#15) stay unrouted. So does #39, whose
`infrastructure/` and `scripts/deployment.py` exist but which no domain skill
claims; it is the only unrouted issue with every `requires` edge satisfied, so it
is the cheapest one to route once something owns deployment.

The walk keeps three states apart, because merging any two of them sends ordinary
work to Bdo:

| State | Means | Who moves it |
| --- | --- | --- |
| `HELD` | an unsatisfied `requires` edge | whichever tier can build the prerequisite |
| `UNROUTED` | no repository artifact evidences a domain owner | whichever tier can write the charter, contract, or tests |
| `OWNER_HELD` | an open `unblock` ticket asking the owner for a judgement | Bdo, and only here |

Routing and readiness are independent readings, so an issue can be `UNROUTED` and
`HELD` at once and both are reported. `epic/README.md` carries the detail and
`python scripts/sov_epic.py owner-held` lists what genuinely waits on Bdo.

### Files

- `agents/sov-worker.md` — stable builder role: executes exactly one bounded
  operation in whichever domain the prompt names (edit + run rights, no
  commit/push, no self-witnessing, no ratification).
- `agents/sov-orchestrator.md` — stable planning role: turns an objective into
  a bounded, blocker-honoring operation plan; edits nothing.
- `agents/sov-witness.md` — stable read-only witness; verifies build claims
  through an independent path and may dissent.
- `agents/sov-controller.md` — control role for headless or scheduled runs:
  dispatches, aggregates, and packages evidenced results for Bdo's acceptance.
- `hooks/console_session.py` — session hooks, wired in `settings.json`. On
  `SessionStart` it opens (or resumes) a Console Service operator session and
  prints what landed while this operator was away, which becomes the starting
  session's context; on `SessionEnd` it closes that session so the read position
  advances. It reaches the console only through the service's own CLI, writes no
  console state itself, and never fails a session: an unreachable console prints
  a note and exits 0. Standing: host plumbing, none
  (`decisions/0036-operator-continuity-before-the-screen.md`).
- `skills/sov-continuity/SKILL.md` — operating skill for the built continuity
  path: read what landed, post a message a later session or another operator
  will receive, read a thread. Distinct from `skills/sov-console/`, which is the
  design skill for the same boundary; use that one to change what the service
  is, this one to use it.
- `skills/sov-<domain>/SKILL.md` — domain know-how: owned files, blockers,
  named operations, verification commands, vocabulary. Role agents load the
  skill matching the domain their prompt names.
- `workflows/sov-<domain>.js` — domain process (Scope -> Build -> Witness):
  Scope runs sov-orchestrator, Build runs sov-worker, Witness runs
  sov-witness. `sov-trust.js` names its owner-held list `owner_held_items`
  rather than `judgement_queue`, so a held or unrouted item cannot be filed
  upward by naming.
- `workflows/sov-loop.js` — one concern from selected to landed: Select
  (sov-controller names the concern and checks it against the standing grant's
  scope) -> Plan (sov-orchestrator) -> Build (sov-worker) -> Witness (an
  independent sov-witness that writes its observation to `reports/observations/`)
  -> Land. The Land phase runs `python scripts/sov_land.py`, the only place in
  the repository that commits and merges; it grades the request against
  `contracts/standing-grants.json` and refuses with the kernel's own refusal
  code when the grant does not cover it. Every other workflow here stops at an
  uncommitted tree. Standing: `decisions/0064-standing-authorization-and-the-landing-loop.md`
  (proposed, and the shipped grant is `PROPOSED`, so the gate presently refuses
  every landing until Bdo ratifies it).
- `workflows/sov-qa.js` — cross-domain QA sweep: sov-witness observes the
  current working tree per domain and aggregates residuals; builds nothing.
- `workflows/sov-baseline.js` — foundational control loop run before a
  long-horizon session: Orient -> Scout (one read-only sov-orchestrator per
  domain: standing, checks, available operations, blockers, touchpoints) ->
  Reconcile (file-overlap and ownership conflicts detected in code, each
  probed by sov-witness, looped until dry or the round cap) -> Report. Builds
  nothing; the invoking controller writes the human-facing report.
- `workflows/sov-scribe.js` + `skills/sov-scribe/SKILL.md` — cross-cutting
  writing capability: a templated request becomes a drafted, independently
  critiqued prompt or document (Frame -> Draft -> Critique).
- `workflows/sov-federation.js` — the only workflow allowed to nest: dispatches
  domain workflows and aggregates reports and rulings taken.
- `workflows/sov-epic.js` + `epic/` — the walk of the epic-of-epics issue tree
  (`#1 — Soveraeign system of villages`). `epic/tree.json` is a checked-in
  projection of the GitHub issue tree so an unattended run never crosses an
  external boundary; `epic/villages.json` joins the four villages to the
  domains above. Reconcile (one `sov-witness` over contract, label-projection,
  and containment drift) -> Select (one `sov-orchestrator` per village) and,
  only with `{ advance: true }`, Advance -> Witness. It does not nest; see
  `epic/README.md`.
- `schedules/<name>.json` + `schedules/README.md` — scheduled-run
  declarations (target workflow or skill, cron, mode, effect class,
  preconditions, limits) checked against `schedules/schedule.schema.json`.
  `python scripts/sov_schedule.py tick`, called by the host scheduler, gates
  each due declaration, fires one headless `sov-controller` session with
  commit and push denied, and appends kernel event envelopes to the gitignored
  ledger under `.local/schedules/`. Shipped declarations are disabled.
  Standing: `decisions/0015-scheduled-runs.md` (proposed).

### Invocation

- One concern, all the way: run workflow `sov-loop` with
  `{ objective: "...", domain: "...", target: "main", plan_only: true }`.
  `plan_only` rehearses the gate without landing, and the loop falls back to a
  rehearsal on its own whenever the witness dissents or the concern reaches
  outside the standing grant.
- Whole stack: run workflow `sov-federation` (optionally with
  `{ domains: [...], objective: "...", sequential: true }`; sequential keeps
  each domain's verify run attributable at the cost of wall-clock).
- One domain: run workflow `sov-<domain>` with `{ objective: "..." }`.
- QA only: run workflow `sov-qa` (optionally `{ domains: [...],
  focus: "..." }`) — witnesses the current state, builds nothing.
- Baseline before a long run: run workflow `sov-baseline` (optionally
  `{ domains: [...], horizon: "...", max_rounds: 2, max_probes_per_round: 3,
  run_date: "YYYY-MM-DD" }`) — returns readiness per domain, real
  cross-domain conflicts with ordering, dependencies, residuals, and the
  judgement queue. The invoking controller writes the human-facing report to
  the repository-root `reports/`.
- Epic tree: run workflow `sov-epic` (optionally `{ villages: [...],
  advance: true, max_operations: 1, objective: "..." }`) — reconciles the
  projected issue tree and names the next legal operation per village.
  Refresh the projection first, attended: `python scripts/sov_epic.py sync`.
  Read it without a run: `python scripts/sov_epic.py status | validate |
  next | unrouted | report`.
- Writing: run workflow `sov-scribe` with `{ request: ... }` per the request
  template in `skills/sov-scribe/SKILL.md`.
- Ad-hoc: spawn `sov-orchestrator` to plan and `sov-worker` to execute one
  bounded operation (name the domain in the prompt; the agent loads the
  matching `sov-<domain>` skill), then `sov-witness` to verify the claim.
- Unattended: `python scripts/sov_schedule.py validate | due | run <name>
  [--force|--dry-run] | tick | ledger | task-command` — see
  `schedules/README.md`. A scheduled run's REPORTED event is the executor's
  report, not an observation; witness it with `sov-qa` or by hand.

## Standing rules both families encode

- Lifecycle `OPEN -> BUILT -> WITNESSED -> RATIFIED`; a harness run may propose
  at most `WITNESSED`. Only Bdo ratifies.
- Judgement-typed questions queue in reports; they never block and are never
  decided by an agent.
- Runs leave changes uncommitted in the working tree for review; branch and
  commit decisions follow `AGENTS.md`.
- No external-world effects in Phase I.

## The live-session registry (`sov_session`)

Git answers "what changed" and never "who is changing it right now". On
2026-08-23 seven concurrent sessions in one working tree produced three lost
updates to `scripts/verify.py`, a decision-number collision across 0039-0041, a
blanket commit that swept four sessions' uncommitted work onto one branch, and
several cycles spent diagnosing a red gate caused by somebody else's in-flight
edit. Every one of those is invisible to version control by construction.

`scripts/sov_session.py` and `.claude/hooks/session_registry.py` answer the
question git cannot. Standing: host plumbing, no authority, no standing
(`AGENTS.md`, Local orchestration harness).

### Where the record lives

Under `git rev-parse --git-common-dir`/`sov-sessions/`, as two append-only logs:
`sessions.ndjson` and `claims.ndjson`. That directory is shared by every
worktree of the repository, so a claim taken in `../sov-registry` is visible
from the shared tree with nothing committed and nothing synced. Current state is
a projection over the events; nothing is ever edited.

### Commands

| Need | Command |
| --- | --- |
| Who else is here, holding what | `python scripts/sov_session.py list` |
| Who holds one path | `python scripts/sov_session.py who <path>` |
| The starting-session briefing | `python scripts/sov_session.py brief` |
| Is this red mine? | `python scripts/sov_session.py contested` |
| Hold a path or a port | `python scripts/sov_session.py claim <path> --resource port:8787` |
| A decision number nobody else took | `python scripts/sov_session.py reserve-decision <slug>` |
| A worktree from a base that builds | `python scripts/sov_session.py worktree new <name>` |
| Every worktree and its occupant | `python scripts/sov_session.py worktree list` |
| Prove the logic offline | `python scripts/sov_session.py selfcheck` |

### What the hooks do

Claims are taken automatically on write, so the record stays accurate without
anyone declaring anything.

- **SessionStart** registers the session and prints who else is live, in which
  tree, on which branch, holding which paths. This is the only channel that
  reaches a session which does not exist yet. A freeze announced to five live
  sessions on 2026-08-23 was broken by three that started afterwards; all five
  had acknowledged. The failure was arrival, not compliance.
- **PreToolUse on Edit/Write** refuses a write to a path another live session
  touched in the last 15 minutes *in the same working tree*. Cross-tree is
  reported, never refused: those are different files on disk, and the edits meet
  at merge rather than clobbering.
- **PreToolUse on Bash/PowerShell** refuses a blanket stage or a destructive
  reset in a tree shared with another live session, and reports a gate piped
  into `tail` before `&&`, whose exit status is the pipe's and never the gate's.
- **PostToolUse on Edit/Write** records the claim and refreshes liveness.
- **SessionEnd** releases everything.

### Why it cannot wedge the repository

It wedged the repository twice on 2026-08-24 before these held, once by a hook
path that did not expand and once by a path resolved against a tool's persisted
working directory. Both times every session lost Bash, Write and Edit at once,
and no session could edit its way out because the editor was behind the same
hook.

- The hook command is `python -c <bootstrap> <script> <mode>`. The bootstrap
  walks up from wherever the tool happens to be until it finds `.claude/hooks/`,
  so a subdirectory, a worktree, or a persisted `cd` all resolve.
- It ends in `sys.exit(0)` unconditionally, wrapping the run in
  `except BaseException`. Python exits 2 when it cannot open the file it was
  told to run, and 2 is the PreToolUse block code, so a plumbing fault was
  indistinguishable from a policy refusal. Refusals now travel only through the
  JSON protocol on stdout.
- A claim expires on heartbeat age, so a session that dies mid-write releases
  everything rather than holding a path forever.
- Every refusal names its escape.

### Known gaps

- A clobber by a session that is no longer live is not caught. A post-write
  check for unintended removed lines would catch that class and does not exist.
- Generated artifacts (`docs/documentation.html`, `docs/surface.html`) need a
  stronger rule than a claim. Rebuilding one sweeps in every other session's
  uncommitted source, and a claim on the output does not stop that. Both pages
  are generated downstream of the service manifests, of `scripts/`, and of
  `.claude/`, so any session editing a manifest, `verify.py`, `lint.py`, or this
  file must re-render both or the gate fails on staleness. Appending this
  section staled `docs/documentation.html` within a minute of writing it.
- Nothing signals that one file is being appended to by several sessions at
  once. `scripts/verify.py` took 40 uncommitted lines from several sessions on
  2026-08-23 and crossed the module limit; no session could see that happening.
  `contested` reports only what a registered session holds, and every session
  that started before these hooks landed is invisible to it.
- Nothing reconciles a claim against a filename already taken on another
  branch, which is the collision `OPEN-SEAMS` S16 records.

### Two defects the first live run exposed

Both were found by reading the store rather than by testing, and both made the
registry record data it then refused to use.

- **Liveness read dead for every session.** `pid_alive` used `os.kill(pid, 0)`,
  the POSIX idiom. CPython's Windows implementation opens the process with
  PROCESS_ALL_ACCESS and calls TerminateProcess with the signal number as the
  exit code, so that call would have killed the process it asked about. It
  failed safe only because opening the parent was denied - which also meant
  every liveness question answered "no", and sessions expired on the 30-minute
  heartbeat backstop alone. It now asks Windows through
  OpenProcess/GetExitCodeProcess with the narrowest access right, and a test
  proves the subject survives being asked.
- **Six sessions never registered.** SessionStart fires only for sessions that
  begin after the hook lands. Every session already running got the write hooks
  and none of the registration, so each one heartbeated and took claims that the
  projection discarded. Sessions now register on first contact, so the record
  populates without waiting for a restart.
