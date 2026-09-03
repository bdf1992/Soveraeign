# Claude Code Host Binding

@AGENTS.md

## Who Claude is here

Claude Code is one host binding for Soveraeign. An interactive Claude session is
not Sov and does not silently occupy Controller, Orchestrator, Worker, or Witness.
Those are explicit launched roles.

`AGENTS.md` governs direct repository work. Host capabilities do not create
authority: use only the tools, permissions, model, and live grants present in the
current invocation. A gate is a missing precondition, not permission to invent a
different path around it.

Carry a concern to a landed result when the host exposes the required capability.
Settle ordinary reversible choices, repair findings in place, use a helper for a
second reading when useful, and keep independent witness separate from anyone who
built or edited the change. `python scripts/sov_closure.py loop` prints the closure
rules and `python scripts/sov_land.py` owns the governed landing path.

Human-facing output uses `.claude/skills/unslop/SKILL.md` by default. Persisted
covered prose also needs a `clarity` review and receipt.

## Known traps

Facts about this repository that answer confidently and wrongly. Each cost a
session a false claim or a wasted hour. `python scripts/sov_traps.py` asserts
the checkable ones and **fails when a trap stops being true** — a failure there
means the hazard is gone and the entry below must be deleted, so this list
cannot outlive what it warns about.

- **T2 · `verify.py` exit 0 does not mean conformance.** The participant's
  historical Phase-I baseline still records failing requirements as expected, so
  the suite can be green while that historical qualification remains unmet. Green
  here means "unchanged", not "qualified".
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

T4 through T6 need network or live observation, so this offline trap checker
records rather than asserts them. Current external effects are scoped by live
authority; silence from an offline checker is still not confirmation.

## What the system is

Read `GROUND.md` and `CANON.md` for the product, then `SYSTEM.md` for the operating
model. `AGENTS.md`, `CONTRIBUTING.md`, and this file govern participants; they do
not own product claims.

Operational state preserves addressed inputs, events, standing changes,
observations, receipts, and counter-records. SQLite is the current storage
mechanism, not semantic authority. Consequential transitions require typed live
grants. Phase I is terminal `CLOSED_INCOMPLETE`. Phase 1.5, Operational
Commissioning, is open since 2026-09-03 (`decisions/0102`); its six exit clauses
and their live custody are in `contracts/custodies/phase-1-5.json`, and
`python scripts/sov_active_phase_progress.py` grades them.

## Repository snapshot (informational)

Observed 2026-08-27 on `merge/one-trunk-reconciliation`, the branch that brings
`main` and `feat/federation-harness-and-hardening` back together after both had
been receiving merged pull requests. This section is orientation, not standing.
`STATUS.yaml`, the working tree, and the newest relevant report override it
whenever they disagree.

- `python scripts/verify.py` runs 50 checks. Total wall time is graded by the
  bands in `contracts/verification-budget.json` but is advisory rather than a
  repository failure by itself. The landed budget policy reruns a pooled suspect
  alone and fails catastrophically only when that isolated read still exceeds the
  contract's catastrophic ceiling. `scripts/sovverify/budget.py` implements that
  distinction. A total overrun on a busy host is performance evidence, not
  automatic semantic failure. `python scripts/lint.py` remains the required
  text/syntax/hygiene companion.
- 10 service boundaries under `services/`, 135 declared operations
  across 10 manifests. Asset and Record are built and self-tested; Console's
  continuity path is built; Gateway has one in-process Asset route; Registry has
  a built resolve slice; Observation has a witnessed thin slice (relation
  inference and observe-run); Proofing, Projection, and the remainder of
  those services are incomplete. `services/README.md` and the live issue graph
  carry the detailed standing; declarations are not reachability.
- Conformance oracle (`conformance/`): executable, 33 controlled cases, every
  defeating fixture fails as declared. Every normative predicate `SPEC.md`
  states carries both polarities (`python scripts/sov_f2_gate.py` reads none
  open); the F2 gate waits only on its second bound participant. Participant
  binding still open.
- Harness (`.claude/`): 5 agent definitions (four roles and the Sov binding),
  31 skills, 23 workflows, the epic-tree walk, and scheduled-run gates with a
  kernel-envelope ledger.
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
- Proofing and Asset Projection are boundaries with no implementation; Gateway has
  the one in-process route named above and nothing more.
  Observation has five of eight operations built, self-tested, and independently
  witnessed through their declared surface (`witness/observation-service.md`),
  the first `WITNESSED` standing on file; no service's runs are observed yet, so
  the independent-observation check in `AI-NATIVE.md` still reads
  `UNATTESTABLE` everywhere.
- The SDLC loop is a skeleton, and Sov has no live activation.
- Phase I is closed. Current external-world effects are neither ambient nor
  phase-refused: they require an explicit live grant, admitted scope, and receipt
  under the accepted scoped-authority policy and current closure repair. Unattended
  runs still carry no `gh`; refreshing the epic projection remains an attended
  coordination action.
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

What genuinely waits on Bdo is `owner_holds` in `STATUS.yaml`
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
  `contracts/standing-grants.json`. `grant:standing-landing-loop` is `RATIFIED`
  (Bdo, 2026-08-25, `decisions/0065-standing-grant-ratified.md`): actor `sov`,
  capabilities `repository.commit` and `repository.land`, scope excluding
  `decisions/`, `STATUS.yaml`, `lineage/`, `.github/` and every root governing
  document. What refuses a landing now is evidence, not permission: the grant
  requires `verify` PASS, `lint` PASS, and an independent observation from a
  participant that did not build the change
  (`decisions/0064-standing-authorization-and-the-landing-loop.md`).
- Whole stack: Workflow `sov-federation`, optionally
  `{ domains: [...], objective: "...", sequential: true }`.
- One domain: Workflow `sov-<domain>` with `{ objective: "..." }`; domains
  are `governance`, `contracts`, `conformance`, `asset`, `proofing`, `trust`,
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
LF line-ending enforcement, and the stack certification. At the end of day two
the record held 26 commits, 17 decision records and 8 reports; it now holds
942 commits, 90 decision records and 30 reports. The
first independently witnessed work landed on 2026-08-25; owner-accepted packets
now exist and are enumerated under `STATUS.yaml` `owner_accepted`.

Those two sentences are checked. `python scripts/sov_snapshot.py` grades the
numbers on this page against the record and fails when they drift, because this
snapshot was stale within a day of being written and every launched agent reads
it as current (`LESSONS.md` L-0001). Correct the page rather than the tolerance.

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
- A host may withhold a tool this repository expects, most often the helper
  subagent tool. That is a capability the invocation did not grant, never a
  rule Soveraeign made, and reporting it as one is a defect. Name the tool and
  the host, do the second reading in-session, and ask for the tool as a
  capability at `DEPENDENCY_SEAM`. Recruiting a helper is
  `RESOURCE_CONSUMPTION` and needs no one's permission up to the ceiling in
  `contracts/closure-ownership.json` (`helper_policy.recruitment`); past it the
  spend is `RESOURCE_COMMITMENT` and is asked before it is spent, not reported
  after. `scripts/sov_closure.py` refuses both mistakes by name.

## Where to look first

| Need | Open |
| --- | --- |
| Which tier settles a decision | `decisions/0033-close-the-founding-docket.md`, Ruling 1 |
| Whether something is built/witnessed | `STATUS.yaml`, `services/README.md` |
| Product requirement | `PRD.md`, `contracts/requirements.json` |
| Product semantics / architecture | `SPEC.md`, `SYSTEM.md`, `CLASSIFICATION.md` |
| Operation / capability shape | `contracts/capability-map.schema.json`, `contracts/fixtures/capability-map.reference.json` |
| Whether an operation is reachable | `contracts/fixtures/node-interface.reference.json`, `docs/surface.html` |
| How to work a concern | `AGENTS.md`, `CONTRIBUTING.md`, `SDLC.md` |
| How to use a skill | `.claude/skills/` and the skill named by the concern |
