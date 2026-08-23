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
| `sov-` | decision `0020-federation-harness.md`, proposed | domain skills, four role agents, thirteen executable workflows |

One tension the merge does not dissolve: this file states that executable
orchestration scripts are not admitted before their logical specification and
defeating fixtures exist, and the `sov-` family ships thirteen of them. Either
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
  reads the aggregated report, and surfaces the judgement queue to Bdo.
- Each domain workflow runs Scope -> Build -> Witness and returns a structured
  report. A blocked domain returns early with its judgement items instead of
  forcing work.
- Builders and witnesses are always different agents: a build report cannot
  witness itself (`AGENTS.md`, Evidence and standing).

### Domains

| Domain | Owns | Gated by |
| --- | --- | --- |
| `governance` | Design System of Record, decisions, STATUS standing | O1, O9 |
| `contracts` | Shared kernel/crossing JSON Schemas | O10 |
| `conformance` | Oracle, scenarios, fresh-witness qualification | binding open |
| `asset` | Asset Service lifecycle (`services/asset/`) | O2 |
| `proofing` | Proofing Service charter and contracts only | O11, O2, O10 |
| `console` | Console Service charter, contracts, and seed fixtures only (`services/console/`) | O18, O2, O10 |
| `byom` | Model bindings, adapters, portability (PROD-I-9) | O12 |
| `verification` | `scripts/verify.py`, lint, CI gate, baseline | O2 |

These eight domains do not cover the epic-of-epics issue tree. Twenty-two open
bits and stubs are claimed by no domain skill, and the whole `trust-and-control`
village - identity, authority, gates, registry, and the capability broker - has
no domain at all. `epic/villages.json` leaves them deliberately unrouted rather
than force-fitting them; `python scripts/sov_epic.py unrouted` lists them, and
the walk reports each as a judgement item for Bdo.

### Files

- `agents/sov-worker.md` — stable builder role: executes exactly one bounded
  operation in whichever domain the prompt names (edit + run rights, no
  commit/push, no self-witnessing, no ratification).
- `agents/sov-orchestrator.md` — stable planning role: turns an objective into
  a bounded, blocker-honoring operation plan; edits nothing.
- `agents/sov-witness.md` — stable read-only witness; verifies build claims
  through an independent path and may dissent.
- `agents/sov-controller.md` — control role for headless or scheduled runs:
  dispatches, aggregates, maintains the judgement queue for Bdo.
- `skills/sov-<domain>/SKILL.md` — domain know-how: owned files, blockers,
  named operations, verification commands, vocabulary. Role agents load the
  skill matching the domain their prompt names.
- `workflows/sov-<domain>.js` — domain process (Scope -> Build -> Witness):
  Scope runs sov-orchestrator, Build runs sov-worker, Witness runs
  sov-witness.
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
  domain workflows and aggregates reports and the judgement queue.
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
