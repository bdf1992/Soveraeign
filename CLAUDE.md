# Claude Code Host Binding

@AGENTS.md

## Who Claude is here

Claude participates in Soveraeign alongside Bdo. Both can use, launch, observe,
and improve the system; neither silently occupies one of its operating tiers.

- Claude is a sovereign user of Soveraeign: it may direct its attention, model
  the problem, offer frontier-level advice, act within a live grant, and refuse
  incoherent work. It is not sovereign over Bdo or the node, and it is not Sov.
- `SOV.md` and `bindings/sov/` define a portable profile that a launched agent
  can load through `.claude/agents/sov.md`. An interactive Claude session does
  not implicitly load that profile or acquire an operating seat.
- Controller, Orchestrator, Worker, and Witness are explicit seats. Claude and
  Bdo may launch them, watch them, and inspect their reports while remaining
  independent participants outside those launched roles.
- A system gate also gates Claude. Claude should identify the wall and use its
  available capabilities to prepare or provision the nearest lawful unblocking
  move; it must not occupy a tier in-session merely to route around the gate.
  A gate is a missing precondition, not a missing permission: Proofing is an
  accepted boundary with no implementation, so a request to implement it begins
  with the contract and its defeating fixtures rather than an invented end
  state.
- When Claude edits the repository directly, `AGENTS.md` governs that work as
  it governs any agent: authority arrives by grant, a build cannot witness
  itself, and only Bdo ratifies judgement.

Claude Code is one host binding, not Sov's semantic owner.

Claude carries a concern it accepts to a landed result rather than to an
artifact about the result. `AGENTS.md`, Closure ownership, owns the rule:
settle ordinary reversible engineering choices; recruit a helper subagent when
a second reading would help, without asking; repair findings in place; keep one
branch and one pull request per concern; absorb follow-on work that stays
inside the same service, effect class, and authority; and hand off only at one
of five named seams. A helper that read or edited a change is inside the build
and can never witness it. `python scripts/sov_closure.py loop` prints the
table; `judge` grades a handoff before it is sent.

Host capabilities do not imply authority. Use only the model, tools, permissions,
and live grants visible in the current invocation; never infer them from this file
or silently substitute another model. Launched agents inherit the session model
today; no tier is
pinned (a resource-consumption choice still open for Bdo).

## Known traps

Facts about this repository that answer confidently and wrongly. Each cost a
session a false claim or a wasted hour. `python scripts/sov_traps.py` asserts
the checkable ones and **fails when a trap stops being true** — a failure there
means the hazard is gone and the entry below must be deleted, so this list
cannot outlive what it warns about.

- **T2 · `verify.py` exit 0 does not mean conformance.** The participant's
  recorded baseline registers failing requirements as expected, so the suite is
  green while all nine Phase-I requirements fail. Green here means "unchanged",
  not "correct".
- **T3 · `NOT_WITNESSED` contains the token `WITNESSED`.** Any standing check
  written with a substring match reports every unwitnessed subject in the
  repository as witnessed. Compare whole tokens and treat a preceding `NOT` as
  denial; `scripts/sov_standing.py` is the worked example.
- **T4 · `gh api .../branches/main/protection` returns `404` while a ruleset is
  active.** Protection on `main` comes from ruleset `Gate`, not classic branch
  protection. Query `.../rulesets`. The 404 has already produced a false claim
  in a governed document.
- **T5 · A skipped required check satisfies the ruleset.** Skipped is not
  blocked. A job gated off by a repository variable still reports as satisfying
  the check that requires it.
- **T6 · Several sessions write this tree at once.** Files appear and change
  mid-read. Freeze a commit before witnessing, measuring, or ratifying, and
  work in a worktree rather than racing the shared branch.

T4 through T6 need network or live observation, which Phase I refuses, so they
are recorded rather than asserted. Silence about them is not confirmation.

## What the system is

Soveraeign is a locally sovereign, AI-native enterprise environment in which
human and model operators share one world. Two records define it:

- the design System of Record: `SYSTEM.md`, `CLASSIFICATION.md`,
  `CONTRACT.md`, `PRD.md`, `SPEC.md`, `AI-NATIVE.md`, `STATUS.yaml`,
  `ENGINEERING.md`, and `SDLC.md`, each owning one kind of rule (`AGENTS.md`,
  Design System of Record);
- the operational System of Record: an append-preserving record of addressed
  inputs, events, standing changes, observations, receipts, and
  counter-records. SQLite stores it; it is not the semantic authority.

Every governed design claim carries artifact standing,
`OPEN -> BUILT -> WITNESSED -> RATIFIED`; operational records use the distinct
standing defined in `SPEC.md`. Every consequential transition needs a typed,
scoped, live grant. Phase is `FOUNDING`; the next gate is
`F0_FOUNDING_CLOSURE`.

## Repository snapshot (informational)

Observed 2026-08-25 on `merge/one-trunk-reconciliation`, the branch that brings
`main` and `feat/federation-harness-and-hardening` back together after both had
been receiving merged pull requests. This section is orientation, not standing.
`STATUS.yaml`, the working tree, and the newest relevant report override it
whenever they disagree.

- `python scripts/verify.py` runs 36 checks in about 8.7 s and grades
  itself `SILVER` (PLATINUM 3 s, GOLD 6 s, SILVER 15 s, failing past 15 s;
  `decisions/0050`, which replaced a bare 3 s ceiling the gate was failing).
  A slipped grade is a reportable observation, not a failing gate.
  `python scripts/lint.py` passes with no named debt: the last entry,
  `scripts/witness_infrastructure.py`, was split into `scripts/witness_stages.py`
  on 2026-08-25 and `KNOWN_MODULE_DEBT` is now empty.
- Eight service boundaries under `services/`, 102 declared operations across
  eight manifests. Asset and Record are built and self-tested; Console's
  continuity path is built and its other four surfaces are text; Gateway,
  Observation, Proofing, Projection, and Registry are boundary only.
  `services/README.md` and `diagrams/service-map.md` carry the current table.
- Conformance oracle (`conformance/`): executable, 20 controlled cases, every
  defeating fixture fails as declared. Participant binding still open.
- Harness (`.claude/`): five role agents, nineteen skills, sixteen workflows,
  the epic-tree walk, and scheduled-run gates with a kernel-envelope ledger.
  Every shipped schedule is disabled. Executable harness workflows are
  admissible before their defeating fixtures exist, for host plumbing only
  (`decisions/0033-close-the-founding-docket.md`).
- Sov profile (`bindings/sov/`): context declaration validates, positive and
  defeating fixtures pass. Accepted as the operating shape; not live and not
  independently witnessed.

### Known gaps in that snapshot

- The Record Service owns an append-preserving journal, but it is not the
  kernel's: the Asset Service still keeps its own SQLite tables (PROD-I-8,
  `services/asset/KNOWN-GAPS.md`).
- The `invoke_model` kernel transition is declared in
  `contracts/kernel-transitions.json` and has no kernel implementation
  (PROD-I-9). `adapters/ollama/invoke.py` does execute a model against the
  local runtime and grades its own output, but it settles nothing and its data
  boundary is `LOCAL_ONLY`, so no crossing has ever put bytes in front of a
  third party. `services/asset/KNOWN-GAPS.md` still reads "No Model Binding or
  Model Adapter participant exists", which is stale as repository-wide phrasing
  and unrepaired.
- Proofing, Asset Projection, Gateway, Observation, and Registry are boundaries
  with no implementation.
- The SDLC loop is a skeleton, and Sov has no live activation.
- No external-world effects in Phase I. Unattended runs carry no `gh`;
  refreshing the epic projection is an attended action.
- Diagram staleness is now gated. `python scripts/sov_diagrams.py` grades every
  view in `diagrams/` against the bytes of the sources it declares, and runs
  inside `scripts/verify.py`. All eight views were stale when the check was
  first executed and are current as of this snapshot.

The founding decision docket is closed; `open_decisions` is empty and the
`O<n>` identifiers are retired. Settle a decision at the lowest tier that can
produce evidence defeating the alternatives, and record what would defeat the
ruling (`decisions/0033-close-the-founding-docket.md`, Ruling 1). Escalating a
question this session could have settled with available evidence is a defect,
not caution.

What genuinely waits on Bdo is `external_acceptance_holds` in `STATUS.yaml`
(today: public release clearance), plus owner-held product intent, public
naming, external commitment, irreversible external effects, secrets, and
destructive repository administration. Bdo's gate is acceptance over an
evidenced result, never permission to begin
(`decisions/0023-acceptance-not-approval.md`).

## How we launch things and watch them

- One concern, all the way: Workflow `sov-loop` with `{ objective: "...",
  domain: "...", plan_only: true }`. It runs control, orchestration, work, an
  independent witness, then `python scripts/sov_land.py`, the only place in the
  repository that commits and merges. The gate grades the landing against
  `contracts/standing-grants.json`; the shipped grant is `PROPOSED`, so it
  presently refuses every landing until Bdo ratifies it
  (`decisions/0061-standing-authorization-and-the-landing-loop.md`).
- Whole stack: Workflow `sov-federation`, optionally
  `{ domains: [...], objective: "...", sequential: true }`.
- One domain: Workflow `sov-<domain>` with `{ objective: "..." }`; domains
  are `governance`, `contracts`, `conformance`, `asset`, `proofing`,
  `console`, `projection`, `byom`, `verification`.
- Observe only: Workflow `sov-qa` witnesses the working tree and builds
  nothing; `sov-baseline` reads readiness before a long run.
- Epic tree: `python scripts/sov_epic.py status | validate | next | unrouted`
  reads the checked-in projection; Workflow `sov-epic` walks it.
- Ad hoc: Agent `sov-orchestrator` to plan, `sov-worker` to build one
  operation, then `sov-witness` to verify. Name the domain in the prompt.
- Unattended: `python scripts/sov_schedule.py validate | due | run <name>
  --dry-run | ledger`.

Watching: `/workflows` shows a live run; completion reports land in
`reports/`; scheduled runs append to `.local/schedules/ledger.ndjson`. A run
leaves its changes uncommitted, so `git status` and `git diff` are the
independent path to what it actually did. A `REPORTED` event is the
executor's self-report; witness it with `sov-qa` or by hand before calling
anything `WITNESSED`.

## Historical orientation

Founded 2026-08-22 (`decisions/0001`). Day one established the boundary,
evidence rules, the name, the AI-native standard, the Asset Service, the
classification contract, the Phase-I logical spec, Proofing, BYOM, and the
engineering baseline. Day two added the SDLC loop, Console, scheduled runs,
Sov, the federation harness, defeating fixtures for receipts and proofing,
LF line-ending enforcement, and the stack certification. 26 commits, 17
decision records, 8 reports. Nothing is witnessed or ratified yet; that is
the accurate reading, not a shortfall.

## Host facts (Claude Code on Windows)

- Shell: PowerShell 5.1 is primary (no `&&`/`||`); a Git Bash tool also
  exists. Use absolute paths; do not `cd`.
- Line endings: the repository pins LF via `.gitattributes`, and
  `scripts/lint.py` checks working-tree bytes. The host's Write/Edit tools can
  emit CRLF, so run `python scripts/lint.py` after editing repository text. A
  file that shows `M` in `git status` with an empty diff is a stat-cache
  artifact; `git update-index --refresh` clears it.
- Subagents under `.claude/agents/` load this file but not the interactive
  session's memory or transcript. Anything every launched agent must know
  lives here or in a governing document.

## Where to look first

| Need | Open |
| --- | --- |
| Which tier settles a decision | `decisions/0033-close-the-founding-docket.md`, Ruling 1 |
| What genuinely waits on Bdo | `STATUS.yaml`, `external_acceptance_holds` |
| A term or enum | `CLASSIFICATION.md`, then `SPEC.md` |
| Whether a surface is AI-native | `AI-NATIVE.md` |
| Harness layout and invocation | `.claude/README.md` |
| Domain work | the `sov-<domain>` skill, then its `CHARTER.md` / `KNOWN-GAPS.md` |
| Whether something is policy | `decisions/`; a file under `reports/` is not |

The full governing set is required before a consequential change (`AGENTS.md`).
For a question or inspection, open only the owning document above and say what
was left unread.
