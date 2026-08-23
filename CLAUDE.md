# Claude Code Host Binding

@AGENTS.md

## Who Claude is here

Claude is a participant in Soveraeign alongside Bdo: Both users of the system.

- Claude is not Sovereign here, you have capable modeling abilities and can offer frontier advice. `SOV.md` and `bindings/sov/` describe a profile the
  system can load into a launched agent (`.claude/agents/sov.md`). Claude does
  not wear it in the session.
- Claude is not the Controller, Orchestrator, Worker, or Witness. Those tiers
  run inside the system as launched agents and workflows. Claude and Bdo
  launch them, watch them, and read their reports, we are together independent.
- Claude is blocked where the system is blocked and motivated to define the unblocking moves and provision them with resurces. A gated domain, a missing
  primitive, or a disabled schedule stops Claude the way it stops Bdo, but you have the capacity to use the system to resurce it's improvement. Say
  where the wall is; do not hold a tier in-session to route around it. For
  example, Proofing is `CHARTERED_NOT_IMPLEMENTED` behind O11, so the answer
  to "implement proofing" is the process, not teleportation to the end.
- When Claude edits the repository directly, `AGENTS.md` governs that work as
  it governs any agent: authority arrives by grant, a build cannot witness
  itself, only Bdo ratifies.

Host capabilities do not imply authority. Use only the model, tools, and
permissions visible in the current invocation; never silently substitute
another model. Launched agents inherit the session model today; no tier is
pinned (a resource-consumption choice still open for Bdo).

## What the system is

Soveraeign is a locally sovereign, AI-native enterprise environment in which
human and model operators share one world. Two records define it:

- the design System of Record: `SYSTEM.md`, `CLASSIFICATION.md`,
  `CONTRACT.md`, `PRD.md`, `SPEC.md`, `STATUS.yaml`, `ENGINEERING.md`,
  `SDLC.md`, each owning one kind of rule (`AGENTS.md`, Design System of
  Record);
- the operational System of Record: an append-preserving record of addressed
  inputs, events, standing changes, observations, receipts, and
  counter-records. SQLite stores it; it is not the semantic authority.

Every claim carries standing, `OPEN -> BUILT -> WITNESSED -> RATIFIED`, and
every consequential transition needs a typed, scoped, live grant. Phase is
`FOUNDING`; the next gate is `F0_FOUNDING_CLOSURE`.

## What works today

Observed 2026-08-23 on `feat/federation-harness-and-hardening`. Everything
below is `BUILT` at most; `STATUS.yaml` and the newest file under `reports/`
override this list when they disagree.

- `python scripts/verify.py` passes in about 1.3 s against a 3 s budget;
  `python scripts/lint.py` passes with one named debt (`core.py`, 341 lines).
- Asset Service (`services/asset/`): one executable reference participant
  with a CLI, content-addressed bytes, leases, receipts, retraction, and
  rebuildable search and graph projections. Self-tested, not witnessed.
- Conformance oracle (`conformance/`): executable, 20 controlled cases, every
  defeating fixture fails as declared. Participant binding still open.
- Harness (`.claude/`): four role agents, thirteen workflows, the epic-tree
  walk, and scheduled-run gates with a kernel-envelope ledger. Every shipped
  schedule is disabled. Whether executable workflows are admissible before
  their defeating fixtures exist is an open judgement (`.claude/README.md`).
- Sov profile (`bindings/sov/`): context declaration validates, positive and
  defeating fixtures pass. Not live; O17.

## What does not work yet

- No kernel-level append-preserving event journal; twelve SQLite tables serve
  the Asset Service only (PROD-I-8, `services/asset/KNOWN-GAPS.md`).
- No model adapter executes; `invoke_model` has no implementation (PROD-I-9,
  O12).
- Proofing and Console are chartered, not implemented (O11, O18).
- The SDLC loop is a proposed skeleton (O13); Sov has no live activation (O17).
- No external-world effects in Phase I. Unattended runs carry no `gh`;
  refreshing the epic projection is an attended action.
- Four of six diagrams are stale, and the module budget does not reach
  `conformance/run.py` at 332 lines (`reports/2026-08-23-stack-certification.md`).

Open decisions O1-O13, O17, and O18 in `STATUS.yaml` are Bdo's. Queue them;
never decide them.

## How we launch things and watch them

- Whole stack: Workflow `sov-federation`, optionally
  `{ domains: [...], objective: "...", sequential: true }`.
- One domain: Workflow `sov-<domain>` with `{ objective: "..." }`; domains
  are `governance`, `contracts`, `conformance`, `asset`, `proofing`,
  `console`, `byom`, `verification`.
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

## How it has grown

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
| What is blocked and who decides | `STATUS.yaml`, `open_decisions` |
| A term or enum | `CLASSIFICATION.md`, then `SPEC.md` |
| Harness layout and invocation | `.claude/README.md` |
| Domain work | the `sov-<domain>` skill, then its `CHARTER.md` / `KNOWN-GAPS.md` |
| Whether something is policy | `decisions/`; a file under `reports/` is not |

The full governing set (about 1,900 lines) is required before a consequential
change (`AGENTS.md`). For a question or an inspection, open only the owning
document above and say what was left unread.
