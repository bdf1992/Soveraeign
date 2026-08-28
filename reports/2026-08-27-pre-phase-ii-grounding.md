# Pre–Phase II grounding and rescue pass

Read on 2026-08-27 by session-49406d, against `origin/main` at `deb9a0f` in a
private worktree, because the shared checkout is being written by four other
live sessions and measuring it would measure them.

This report observes. It settles nothing, ratifies nothing, and changes no
standing. Nothing was committed, cleaned, retired or landed while writing it.

---

## 1. The clean starting state

`origin/main` at `deb9a0f` is genuinely clean and genuinely green.

| Reading | Result |
| --- | --- |
| `python scripts/verify.py` | PASS, 48 checks, 22.4 s |
| Wall-clock grade | none earned; SILVER needs 15 s. Recorded as debt, does not refuse |
| Per-check budget | 8 checks over ceiling, 40.0 s above budget, attributed by name |
| `python scripts/lint.py` | PASS, 1064 text files, 479 modules, 10 named debt |
| `python conformance/run.py` | PASS, 20 cases, `coverage_gaps=0`, every defeating fixture fails as declared |
| `python scripts/sov_traps.py` | PASS, 2 traps still hold, 3 need attended checking |
| `python scripts/sov_snapshot.py` | PASS, 10 of 10 claims match |
| `python scripts/sov_diagrams.py` | PASS, 8 views current |
| `python scripts/sov_baseline.py` | PASS, 9 requirements, **8 failing as recorded** |
| `python scripts/sov_f2_gate.py` | OPEN, **36/44** predicates carry both fixtures, floor 36 |
| `python scripts/sov_custody.py phase` | `phase:i` CLOSED / NOT_EARNED / CLOSED_INCOMPLETE |
| `python scripts/sov_epic.py validate` | **FAIL, 1 defect** — story #67's parent #30 is not a live bit |

Two things moved since the last snapshot and are worth saying plainly.

**The F2 gate reads 36/44, not 0/44.** The recorded memory of this gate is that
`coverage_gaps=0` was a false comfort and the real number was zero. That is no
longer the state. Thirty-six of forty-four normative predicates now carry both a
positive and a defeating fixture, the floor is set at 36, and the eight that are
open are named individually with a stated reason.

**Trap T2 has weakened by one.** `CLAUDE.md` says all nine Phase-I requirements
fail against the recorded baseline. Eight fail. One now passes. The trap text is
stale by one requirement and should be corrected rather than left to be
rediscovered.

Two blemishes on an otherwise clean trunk:

- `STATUS.yaml` declares eight keys twice. A YAML reader keeps the last value and
  discards the first, so half of those eight statements are already invisible to
  every tool that reads the file. Lint warns; nothing refuses.
- The epic tree has one containment defect (#67 → #30) and `sov_epic.py validate`
  exits non-zero on it.

### The live journal is broken, and the hook that reports it lies about how

This session opened with `soveraeign_record_service.core.BrokenChain` at
`entry_80767935e18c488fb45502df9d5c385e`. That is not a spurious warning. The
Record Service reads the live console journal and returns:

```
{"message": "the journal stops verifying at entry_80767935e18c488fb45502df9d5c385e",
 "outcome": "REFUSED", "reason_code": "DIGEST_MISMATCH"}
```

The service is behaving correctly — it refuses a chain it cannot verify. The
defect is upstream of that: `.claude/hooks/console_session.py` lets the exception
escape, so every session start prints a stack trace instead of a governed
refusal, and the read position that a session close is supposed to advance does
not advance. Every future session sees the same gap. **This is the one thing in
this report that is degrading daily and has nobody assigned to it.**

`origin/main` has no test for that hook at all.

---

## 2. What still needs rescue

### 2a. The shared working tree

The primary checkout (`C:/Users/bdf19/Desktop/Soveraeign`) is on
`feat/federation-harness-and-hardening`, which is **177 behind `origin/main` and
1 ahead**. The single unlanded commit is `bd1b4b8`, the automation cadence
controls, held by session-79c408.

It carries 106 changed paths. Reconciled against `origin/main` byte for byte:

- **27 files are byte-identical to `origin/main`.** Already landed; nothing to rescue.
- **44 files differ from `origin/main`.** Almost all are the old pre-merge base
  showing through, not new work. Treat individually; do not bulk-commit.
- **69 files exist nowhere but this working tree.**
- **1 file deleted** (`AGENT-BOOTSTRAP-PROMPT.md`) — deliberate on main, already gone there.

`sov_strand.py` names 6 of those as held by no ref at all. It is right, and it
undercounts: measured against `origin/main` rather than against local refs, 69
files are local-only, and **21 of them are claimed by no live session either**.
Those 21 are the genuine rescue set:

| Work | Files | Status |
| --- | --- | --- |
| Automation Service boundary | `services/automation/` (9 files), `decisions/0073` | unclaimed, unlanded |
| Peer network + cumulative evidence | `scripts/sovpeer/` (9), `contracts/peer-network.json`, `contracts/peer-evidence.schema.json`, `decisions/0084` | unclaimed, unlanded |
| Topology page | `scripts/sov_topology.py`, `scripts/sovtopology/` (3), `docs/topology.html` | unclaimed, unlanded |
| Work-item / worklist | `scripts/sov_worklist.py`, `scripts/sovworklist/` (3), `contracts/work-item.schema.json` | unclaimed, unlanded |
| Typed standing / node graph | `decisions/0074` | unclaimed, unlanded |
| Continuity-hook test | `scripts/tests/test_console_session_hook.py` | unclaimed — **and duplicated on `fix/continuity-hook-honest-failure`** |
| Acceptance packets | `acceptance/A7.json`, `A8.json`, `accepted/A11.json` | unclaimed |
| Landing attestation | `scripts/sovland/attest.py` | unclaimed |

### 2b. Dirty worktrees

Six of 46 worktrees hold uncommitted work. Five are trivial; one is not.

| Worktree | Branch | Dirty |
| --- | --- | --- |
| `.claude/worktrees/agent-a7a0ce3f…` | `fix/external-effect-preconditions` | **13 files** — contracts, fixtures, docs |
| `Desktop/Soveraeign` | `feat/federation-harness-and-hardening` | 106 (section 2a) |
| `…/wt-r3-asset` | detached | 2 generated docs pages |
| `…/wt-principal` | `feat/session-principal` | 1 (`scripts/sov_mutate.py`) |
| `…/wt-drain` | `feat/console-authority-enforced-only` | 1 untracked `reports/observations/` |
| `…/wt-125` | detached | 1 (`scripts/sovwitness/probes.py`) |

Rescue `fix/external-effect-preconditions` before retiring anything. The other
five are cheap to inspect and cheap to discard, but discard is your call.

### 2c. Two zip files loose in `decisions/`

Neither is a decision record and neither is tracked.

- **`0065-standing-grant-ratified.zip`** — a backup of 84 decision records.
  Seven of them are not on `origin/main`: 0066, 0073, 0074, 0075, 0084, 0092,
  0093. Six of those seven also exist as loose files in the working tree, so the
  zip's only unique content is `0066-chore-ticket-kind.md`. Verify that one, then
  the zip is redundant.
- **`soveraeign-record-ledger-compaction.zip`** — a migration proposal that turns
  the 84 markdown decision files into `decision-ledger.ndjson` plus a
  `governance-record.json` projection. **This is a second journal and a second
  truth store for governance.** It is exactly the shape you told me not to build.
  It needs your ruling; my recommendation is in section 10.

### 2d. One stash

`stash@{0}` removes 7 lines from `scripts/verify.py`. It is a merge-check
leftover from `tmp/merge-check`, a branch that no longer exists. Almost certainly
disposable, but it is a deletion so I did not drop it.

### 2e. Scale of what is unlanded

278 commits across 48 pushed-but-unmerged branches, and 46 open worktrees
(8 in temporary directories that a reboot will orphan). That is the backlog the
collapse into main did not reach.

---

## 3. Branch dispositions

Verified with `git cherry origin/main <branch>` and by checking whether each
branch's added files exist on `origin/main` at all. Names were not trusted.

### The branches you named

**`claude/console-terminal-interfaces-5d0lzg` — SOURCE_FOR gates + operator surface.**
9 unlanded commits, 49 changed files. Nothing landed. It adds
`contracts/gate-policy.json`, `contracts/operation-requirements.json`, an
Identity Service core, an Authority Service, and a `bindings/desk` operator
binding — **all absent from main**. Main's `services/identity` is a different
design (challenges + recovery, not the old core), so the implementation is
superseded. But its central idea — *an operation declares what admits it, and a
gate fails closed* — has no successor anywhere on main. Main's
`decisions/0031-transition-local-gates.md` is about self-direction, not gate
enforcement, despite the similar name. **Its decision numbers 0028–0034 collide
with seven different decisions on main; do not merge this branch.** Lift the
gate-policy idea; retire the implementation. Current owner: nobody. It needs one.

**`feat/f2-control-loop` — SOURCE_FOR the eight open F2 predicates.**
7 unlanded commits. Adds `sovkernel/source_transitions.py`,
`attestation_transitions.py`, `crossing_transitions.py` and
`conformance/tests/test_predicate_declarations.py` — none on main. Main has a
consolidated `sovkernel/transitions.py` instead, so the module layout is
superseded. But five of the eight predicates the F2 gate reports OPEN today
(`TRANS-capture_source`, `make_effective`, `begin_run`, `report_run`,
`observe_run`, `settle_run`) are exactly what those modules were closing. The
fixtures and the defeating cases are worth reading before rewriting them.

**`feat/f2-integration` — CONTAINED by `feat/f2-control-loop`.**
Its 8 commits are that branch plus a merge. It adds nothing of its own. Retire.

**`feat/gate-loop-pattern` — SOURCE_FOR scheduled control cycles.**
Contains all of f2-integration plus `sovschedule/patterns.py`,
`sovschedule/preflight.py`, `.claude/schedules/f2-gate-loop.json`,
`.claude/workflows/sov-gate-control.js` and three test modules. Main now has a
24-module `sovschedule` package from the automation work, so the capability
landed by a different route — but preflight and the gate-loop schedule pattern
did not. Read `preflight.py` before writing a Phase II control cycle; retire the
rest.

**`feat/work-coordination-kernel-participant` — LANDED.**
The console authority enforcement it carried is on main via
`feat/console-authority-enforced-only` (merged in PR #118). What remains unlanded
is two report files, `reports/2026-08-26-bravo-*.md`. Copy those two out if you
want the record; the branch is done.

**`fix/projection-drift-detection` — LIVE_RESIDUAL.**
4 unlanded commits. Adds `services/asset/src/soveraeign_asset_service/reads.py`,
`services/asset/tests/test_projection_drift.py` and a decision record. Main's
Asset Service has **no drift detection at all** — I grepped it. This branch also
went through an independent witness and a re-witness, so it carries observation
evidence main does not have. Its worktree at `Desktop/sov-digest` is clean. Its
decision number 0073 collides with the unlanded automation record of the same
number; renumber on landing. **This is the cheapest genuine rescue in the set.**

**`fix/continuity-hook-honest-failure` — LIVE_RESIDUAL, and now urgent.**
2 unlanded commits, 2 files, adds `scripts/tests/test_console_session_hook.py`.
Main has no test for that hook. The hook is failing at every session start today
(section 1). This branch is the fix for the reporting half of exactly that
defect. Its worktree is clean. **Land this one first.**

**`feat/sov-control-mesh` — SUPERSEDED, inspect nothing.**
21 unlanded commits, 13 files, but the whole branch is `.claude/CONTROL-MESH.md`
plus a mutation battery and pin-scanner for it. The session registry, custody
contracts and `sov_session.py` on main replaced what the mesh was coordinating.
You asked me to inspect it for mechanics not already replaced; I found none worth
carrying. Its mutation-battery testing style is a technique, not an artifact.
Retire.

**`feat/federation-harness-and-hardening` — LANDED except one commit, but NOT safe to retire.**
Only `bd1b4b8` is unlanded. **However, this is the branch checked out in the
shared working tree, and it carries 106 uncommitted paths including 21 files
claimed by nobody.** Retiring this branch before section 2a is drained destroys
unlanded work. Do not touch it until the rescue set is landed or explicitly
discarded.

### The other 40

Not individually dispositioned — that is a separate concern and would have
doubled this pass. `python scripts/sov_backlog.py` and the `sov-backlog` skill
exist for it. Three groups are visible from the strand reading and worth naming:

- **Six `fix/external-effect-preconditions*` and `fix/gate-publication-check*`
  variants** (v1/v2/v3 of each) — serial retry attempts at one concern. At most
  one of each is wanted; v3 is presumably it. One of them holds 13 dirty files.
- **`verify-main`, `probe/rebase`, `wt/pr43`, `wt/pr59-merge-main`, `tmp/*`** —
  scaffolding branches, no product content. Retire.
- **`feat/status-claims-*` (3 branches, ~110 commits)** — status-claims work is
  partly on main and partly not; three sessions were writing it concurrently
  today. Leave alone until those sessions finish.

---

## 4. What the vocabulary already means

For each term: what it means → what is implemented → what is missing → what must
not be duplicated.

**Board** — the management surface that surveys, recommends with evidence
attached, and exposes per-action owner approval (`decisions/0057`).
*Implemented:* `scripts/sov_board.py` with `review` / `apply` / `selfcheck`, and
a deliberate split so the only module that can write to GitHub is the only module
that can write to GitHub. *Missing:* it surveys coordination, not traversal; it
cannot show you a crossing that happened. *Do not duplicate:* any second
recommend-with-evidence surface.

**Work Circuit** — how far one initiative has been drawn toward capable
operation: `ROOT_POINT → VERTICAL_SLICE → HORIZONTAL_SURFACE → EXPLODED_SURFACE →
CAPABLE_NODE`, each stage admitted by the previous stage's evidence
(`contracts/work-circuit.json`). *Implemented:* fully, with eight named refusals
and defeating fixtures. *Missing:* nothing structural. *Do not duplicate:* the
word "circuit" is spent twice already — here, and as a breaker over peer evidence
edges in the unlanded `contracts/peer-network.json`.

**Phase** — a bounded campaign window whose definition is pinned by `sha256` at
open, so an exit is graded against the definition it was opened under
(`contracts/phases.json`). *Implemented:* `phase:i` is CLOSED / NOT_EARNED.
*Missing:* `phase:ii` has no record, and `succeeded_by` on `phase:i` is still
null. *Do not duplicate:* this is already the document-versioning mechanism. You
do not need a `revisions/` tree.

**Custody** — a bounded initiative held by a seat, aimed at a declared target
stage (`contracts/custodies.json`, 16 custodies). *Implemented:* contract,
schema, board, circuit, estimate, reconcile, orphans. *Missing:* nothing
structural. *Do not duplicate:* any second notion of "who is holding this".

**Surface** — a service boundary opened into named endpoints that a participant
arriving with no briefing can discover. *Implemented:* `docs/surface.html`,
`scripts/sov_surface.py`, `discover-operations`. *Missing:* the live defect the
work circuit itself names — nine BUILT console operations declare an authority
and check none. *Do not duplicate:* discovery lists.

**Crossing** — a record offered across the surfaces of two sovereign nodes, and
what the receiving node did about it. Carries an address and a digest, never
authority and never standing (`contracts/federation-crossing.schema.json`).
*Implemented:* the schema, and `AssetService.federation_cross()`, which
unconditionally returns `REFUSED / UNCONFIGURED` because no second node exists.
*Missing:* everything else. *Do not duplicate:* the word is also used loosely for
in-node operation boundaries; that second usage is sloppy but harmless.

**Session** — two different objects share this word. (a) A Console operator
session with continuity, threads and an unread cursor — BUILT. (b) An Asset
Service session that gates writes and can go not-live — BUILT, and it is what
actually refuses. *Missing:* they are not the same object and nothing reconciles
them. *Do not duplicate:* there is also a harness session registry
(`sov_session.py`) which is host plumbing and correctly holds no standing.

**Asset** — the strongest thing built here. 17 operations, all BUILT, all
self-tested: ingest, exact version read, version history, proposal and
ratification, collections, membership, derivation requests, retraction,
projection rebuild, library conformance. *Missing:* only 2 of 17 are reachable
through a route. *Do not duplicate:* anything content-addressed.

**Gateway** — transport-neutral dispatch from one declared `sov://` request to a
service route. *Implemented and this is the surprise:* the mechanism is fully
built (`services/gateway/src/.../core.py`, `contract.py`, `evidence.py`) and
carries five staged journal events per crossing — request, resolution, authority,
routing, return. *Missing:* the manifest still says `PROPOSED` with 0 of 9
operations built, which is true of the Gateway's *own* operations and misleading
about the Gateway itself. *Do not duplicate:* there are already two gateways —
this one, and `bindings/mcp/gateway.py`. Do not add a third.

**Identity** — who a node is, and which seat settles for it
(`contracts/node-identity.schema.json`), plus a principal registry with derived
identity grades (`contracts/principals.json`, 5 principals). *Implemented:*
schemas, registry, and challenge/recovery modules. *Missing:* **nothing on the
crossing path reads any of it.** The Gateway takes `actor` as a bare string.
*Do not duplicate:* the registry.

**Authority** — a typed, scoped, budgeted, time-bounded, revocable grant; the
only thing that carries authority (`contracts/authority-grant.schema.json`).
*Implemented:* grant, revoke, list, and a real check at the crossing that I drove
to a refusal. *Missing:* the grant schema stands `PROPOSED` while the enforcement
is live, and effect ceilings and budgets are declared but not enforced.
*Do not duplicate:* leases confer nothing; receipts record; only grants carry.

**Gates** — a precondition on a transition. *Implemented:* per-operation
`preconditions` and `refusals` lists on all 134 operations, plus
`sovkernel/transitions.py` with lease, observation, independent-observer and
authority checks. *Missing:* there is no `contracts/gate-policy.json` and no
fail-closed default. The one branch that built it never landed (section 3).
*Do not duplicate:* precondition lists.

**Registry** — resolve a declared name to what the node knows about it.
*Implemented:* `registry.resolve` is one of the five reachable routes and works.
*Missing:* 12 of 13 registry operations are unbuilt. *Do not duplicate:* the
capability map and the node interface are the projections; the registry reads
them.

**Record** — the append-preserving journal with a hash chain
(`soveraeign-record-chain/v3`). *Implemented:* 12 of 12 operations BUILT, plus an
independent witness. *Missing:* the Asset Service still keeps its own SQLite
tables rather than writing through the journal (PROD-I-8), and the live journal
is currently broken (section 1). *Do not duplicate:* **this is the journal. The
ledger-compaction zip proposes a second one.**

**Observation** — independent evidence of what occurred: what the observer looked
at, how it avoided relying on the executor's report, and which predicates held
(`contracts/observation.schema.json`). *Implemented:* the schema, and 49
hand-authored observation files under `reports/observations/`. *Missing:* the
Observation Service is PROPOSED with 0 of 8 operations built, and **no
observation is keyed to an operation** — see section 6. *Do not duplicate:* the
schema is right; it needs a producer, not a redesign.

**Leases and budgets** — one concern, actively possessed by one machine
principal, under a grant, inside a budget, against a stated closure condition
(`contracts/work-lease.schema.json`). *Implemented:* schema, `sov_lease.py`,
`sovkernel/lease_budget.py`, and a lease check inside transition evaluation.
*Missing:* nothing spends against a lease budget today; token and wall-clock
accounting is done by hand in `observe_journey_02.py`. *Do not duplicate:* the
lease says who is on the hook; it confers nothing.

**Evidence** — attributed input under `lineage/`, verified against
`lineage/SOURCES.lock`. Separately, `source_digests` pin every input by sha256 in
the node interface, the phase records and the receipts. *Implemented:* thoroughly
— this is the strongest discipline in the repository. *Missing:* nothing.
*Do not duplicate:* digest-pinning works; reuse it verbatim.

**Receipt** — the record returned by an attempted crossing: actor, interface,
inputs, input-state digest, grants, precondition results, effect class, outcome,
emitted records, observed evidence, and consumption (`contracts/receipt.schema.json`,
15 required fields). *Implemented:* the schema, and **exactly one** conforming
instance in the whole repository — `bindings/mcp/observations/journey-02-receipt.json`,
which was assembled field by field by a script. *Missing:* no gateway emits one.
See section 6. *Do not duplicate:* the schema is correct and complete.

**Owner judgement** — acceptance over a finished evidenced result, never
permission to begin (`decisions/0023`). *Implemented:* `contracts/acceptance-policy.json`
with seven exhaustive hold reasons, `acceptance/` packets, and `sov_accept.py audit`
which fails the build if anything sits on an owner seat without a packet.
*Missing:* nothing. `STATUS.yaml owner_holds` has exactly one entry (publication
clearance). *Do not duplicate:* the seven reasons are exhaustive by design.

---

## 5. Naming the connected shape

### Do not mint a new noun. The words are already in `CLASSIFICATION.md`.

`CLASSIFICATION.md` line 59 already reads:

> **Shared Kernel** is the available typology, **topology, traversal**, and
> invariant grammar used by every Node, Service, operation, and crossing.

Both concepts you are reaching for were named at founding and never given a
projection. That is a much better outcome than minting a fifth vocabulary.

**My recommendation:**

| Concept | Word | Where it already lives |
| --- | --- | --- |
| The whole connected shape | **Node Topology** | `CLASSIFICATION.md:59`; the projection is `contracts/fixtures/node-interface.reference.json` |
| A named operational place | **Operation** at a **logical endpoint** | `sov://asset/read-version`, already the identifier |
| An explicit connection | **Route** | `route_census()`, `AssetRoutes`, the `reachability` field |
| A gate | **Precondition** and **required authority** | already fields on every operation |
| A crossing between nodes | **Crossing** | `contracts/federation-crossing.schema.json` |
| An independent inspection | **Observation** | `contracts/observation.schema.json` |
| **One attributed walk through it** | **Traversal** — *the one word to mint* | `CLASSIFICATION.md:59`, unimplemented |

That is one new word instead of five.

### Why not Netlist, and why 0092's other four words also fail

`decisions/0092-phase-ii-netlist-and-the-control-cycle.md` is sitting uncommitted
in the shared tree, held by session-689543. It records you ruling in favour of
Netlist / Site / Net / Trace / Probe. You have now refused Netlist. Two of the
remaining four collide, which that record's vocabulary screen missed:

- **`Trace` is taken.** `scripts/sov_trace.py` and `scripts/tests/test_trace.py`
  already own it, for the vertical attribution walk receipt → capability →
  operation → journey → promise → ground. Minting it for horizontal traversal
  puts two different walks under one word.
- **`Probe` is taken.** `scripts/sovwitness/probes.py`,
  `scripts/sovcoldstart/probes.py`, and `conformance/fixtures/loop/observer-probe.json`.
- `Site` and `Net` are free but redundant: the repository already calls these
  things operations and routes, and both are load-bearing identifiers.

**0092 is still worth keeping for its reasoning.** Its collision analysis (why
there must not be a second Circuit), its ruling that a control cycle is a process
and not a record, and its ruling that percentages are projections over defeasible
predicates are all sound and all reusable. Only the minted words fail. That
record is `SOURCE_FOR` the vocabulary decision, and it needs a second reading
before it lands, not a rewrite.

### Why "topology" beats "circuit" as working language

A circuit implies current flowing through a closed loop, and the repository
already uses `Work Circuit` for a maturity ladder and `circuit breaker` for peer
evidence. A topology says only "what connects to what", which is the exact
question you asked it to answer, and it is already the word `CLASSIFICATION.md`
uses for that and for `seat-topology.reference.json` and
`diagrams/crossing-topology.md`.

---

## 6. Existing primitives to reuse, and the exact missing joins

### The topology already exists and is already graded

`contracts/fixtures/node-interface.reference.json` is the thing you were about to
ask someone to build. It is derived, not authored, from 49 pinned sources with
sha256 digests, and it holds 134 operations. Each one carries: logical endpoint,
service, standing, subject, CRUD, commit semantics, kernel paradigms, kernel
transition, required authority, effect class, admitted actor kinds,
preconditions, refusals, legal choices, policy endpoints per transport with
activation state, and route reachability with required arguments and source
addresses.

It already grades every operation on five marks — and the marks map almost
exactly onto the grading scale you asked for:

```
asset.read-version  [b9e4180ec5ab]
sov://asset/read-version
declared=yes  bound=yes  policy_active=yes  reachable=yes  observed=no
authority  read:version
effect     RECORD_LOCAL
actors     HUMAN, MODEL
route      READ (EXACT_READ_ROUTE_ACTIVE)
transition read_source
```

| Your grade | The projection's marks |
| --- | --- |
| REAL_AND_REACHABLE | `reachable=yes`, `observed=yes` |
| REAL_BUT_NOT_CONNECTED | `bound=yes`, `reachable=no` |
| DECLARED_ONLY | `declared=yes`, `bound=no` |
| ABSENT | not in the projection |
| WRONG_SHAPE | **no equivalent — this is the one grade the repo cannot express** |

The counts today:

```
declared 134   bound 134   policy_active 46   reachable 5   observed 0
```

Reuse verbatim: `sov_interface.py` (`build` / `check` / `show` / `invoke` /
`prove`), `sovnode/composition.py` (`LocalActionPath`, `route_census`),
`sovkernel/node_interface.py`, the Gateway's five-stage evidence, the receipt and
observation schemas, `contracts/phase-progress.json` (floor + `uncovered_on_purpose`),
and the digest-pinning discipline.

### Missing join 1 — nothing produces an observation keyed to an operation

`scripts/sovnode/interface_inputs.py:66` reads, in full:

```python
observations: dict[str, list[str]] = {}
```

Hardcoded empty. Everything downstream is built and waiting: the schema has an
`observation_ids` field, the record has an `observed` fact, the builder computes
a `reachable_not_observed` seam, the counts include `observed`, and
`interface_defects` refuses an observation whose subject is not a declared
operation. **The entire observation column of the node reads zero because one
input dict is a literal.**

There are 49 real observations in `reports/observations/`. They observe *changes*,
not *operations*, and nothing keys them to an `operation_id`.

### Missing join 2 — no gateway emits the receipt its own contract declares

I drove both gateways. Neither returns a `contracts/receipt.schema.json` receipt.

- `LocalActionPath` positive traversal returns the Asset Service's own row:
  `{id, outcome, event, subject_type, subject_id, actor, payload_json, created_at}`
  — 8 keys, **missing 13 of the 15 required receipt fields**.
- The refused traversal returns a journal RECEIPT row — **missing 14 of 15**.
- The MCP binding's journal RECEIPT rows — **missing 14 of 15**.

The terminal shape also differs per service: Registry and Host journal a RECEIPT
row, Asset returns its own object and journals none. The one conforming receipt
in the repository was hand-assembled by `observe_journey_02.py`.

This is the join that costs the most and is closest to done. The Gateway already
computes almost every required field — it has the actor, the interface, the
input state digest, the grants, the precondition results, the effect class, the
outcome, and the emitted addresses. It just does not assemble them.

### Missing join 3 — identity is declared and never read

`contracts/principals.json` registers 5 principals with derived identity grades.
The Gateway takes `actor` as a bare string and checks a grant against it. A
principal that is not in the registry is indistinguishable from one that is.

### Missing join 4 — no evidence surface for a traversal

Three `docs/*.html` pages exist. None renders a journal, a receipt, or a
traversal. There is no place for you to look at what happened.

### Missing join 5 — two projections disagree about "reachable"

`console_operations` discovery reports `reachable=46`; the node interface reports
`reachable=5`. The capability map counts policy-active endpoints; the node
interface counts bound routes. Both are defensible; the word is not shared. A
reader is told two different numbers for one question.

---

## 7. The first Asset proving path — executed, not estimated

I drove this against `origin/main` in a throwaway state root, using the real
`LocalActionPath` and the real Gateway. Every grade below is an observation of a
run, not a reading of a document.

| # | Step | Grade | What actually happened |
| --- | --- | --- | --- |
| 1 | Human identity resolved | **DECLARED_ONLY** | `principals.json` registers 5 principals; the Gateway takes `actor` as a bare string and reads the file never |
| 2 | Session opened | **REAL_AND_REACHABLE** | `session_02997dc8…` opened through the MCP binding; Asset sessions gate writes and go not-live |
| 3 | Gateway reached | **REAL_AND_REACHABLE** | 7 MCP endpoints; 5 `sov://` routes through `LocalActionPath` |
| 4 | Resolution | **REAL_BUT_NOT_CONNECTED** | `registry.resolve` works through `LocalActionPath` and is absent from the MCP surface; discovery answers instead, with a different `reachable` count |
| 5 | Authority / gate | **REAL_AND_REACHABLE** | grant issued, stored, and checked at the boundary |
| 5b | **Refused traversal** | **REAL_AND_REACHABLE** | `mallory` refused `AUTHORITY_REFUSED` at stage `check-authority`, with a durable journal row carrying `failure_class: GOVERNED_REFUSAL` |
| 6a | Asset write | **REAL_AND_REACHABLE** | ingested, `asset_… / source_… / version_…`, sha256 pinned |
| 6b | **Asset exact read/version** | **REAL_AND_REACHABLE** | `sov://asset/read-version` returned `version_id`, digest, `urn:sha256:…` payload address and metadata. Reachable through `LocalActionPath`; *not* exposed on the MCP surface |
| 7 | Record | **REAL_AND_REACHABLE** | 36 chained entries; 5 staged EVENTs per crossing (request, resolution, authority, routing, return) |
| 8 | Observation | **WRONG_SHAPE** | `observe_verify` runs the repo gate and journals an OBSERVATION row, but it is the gateway observing itself, with no `observer_relation` and no `predicate_results` |
| 9 | Receipt | **WRONG_SHAPE** | terminal evidence exists but is service-local; 13–14 of 15 required receipt fields missing, and the shape differs per service |
| 10 | Evidence visible to you | **ABSENT** | no surface renders a traversal |
| 11 | Your judgement | **REAL_BUT_NOT_CONNECTED** | acceptance packets and `sov_accept.py audit` work; nothing routes a traversal into one |

**The headline: steps 1 through 7 are real and working today, for both a
successful and a refused traversal, on the strongest Asset operation you have.
The path breaks at the receipt.** It is not missing a runtime, an authority
layer, a journal or a store. It is missing an assembly step and a surface.

I corrected step 6b upward after fixing my own probe: my first run reported it
not connected because I drove it through the MCP binding, which does not expose
it. Through `LocalActionPath` it works.

---

## 8. Baseline 50

### What it should mean

You said 50% should mean you can participate, not that enough backend exists. The
repository already agrees with you and already has the machinery.

`contracts/phase-progress.json` is the shape to copy. It holds a **floor** (36 of
44 predicates), refuses below it, and carries an `uncovered_on_purpose` list
where every gap is named with a reason. That is a percentage that something
refuses on, which is the only kind worth having.

### Recommended interpretation

**Baseline 50 is a profile, not a score: a named capability holds Baseline 50
when a human can complete one attributed traversal of it and inspect the evidence
afterwards without reading source code.**

Underneath, named predicates with defeating cases. I would start with these seven
and let the first Asset traversal prove or defeat them:

| Predicate | Holds when | Defeated by |
| --- | --- | --- |
| `reachable_route` | the operation has a bound route on an active transport | a declared endpoint no route reaches |
| `authority_enforced` | a grantless actor is refused at the boundary | an operation that declares an authority and checks none |
| `terminal_receipt` | the crossing emits a `receipt.schema.json` receipt | a service-local receipt shape |
| `independent_observation` | an observer that did not execute records `observer_relation` and `predicate_results` | the executor observing itself |
| `reconstructable` | the traversal replays from records alone | evidence that needs the original process |
| `human_inspectable` | a person can see what happened without reading code | evidence only a developer can read |
| `accounted` | token, wall-clock and tool spend attach to the traversal | a crossing with no measured cost |

`baseline_50(asset)` then reads PASS or FAIL with a defeating case underneath,
and a Board may render `4/7` over it as a steering aid.

### On your five hypothesis columns

Contract, Execution and Crossing posture are already first-class in the
repository — service manifests, kernel transitions, and
`federation-crossing.schema.json`. Evidence is the repository's strongest
discipline and does not need a column so much as a producer. **Human
Interface/Participation is the one that is genuinely absent and genuinely the
point**, and I would weight it far above the other four rather than treating the
five as equals. Today it scores zero on every capability: there is no surface
where you can watch a traversal happen.

### What must not happen

Do not record `Evidence: 27 → 41` as evidence. A bare delta is a claim no fixture
can reach. 0092's ruling 4 has this exactly right, and the unlanded
`contracts/peer-network.json` (`standing.no_single_score`) is stricter still and
disagrees with it. That disagreement is real, both are PROPOSED, and it is worth
one sentence of your ruling — see section 10.

---

## 9. Early and late federation

The qualification gate is `decisions/0039`: federation becomes real when a second
node appears in the registry and a local seat admits it. Nothing below weakens
that, because nothing below admits a peer.

### What can enter early, safely

**Assets.** The crossing schema already carries exactly the right shape: an offer
holds `record_kind`, `record_address`, `record_digest` and `standing_at_origin`,
and the schema says in its own text that origin standing is *"Reported, never
inherited. A receiving node reads this as a claim about somewhere else."* That
sentence is the whole federation discipline, already written.

Of the six aspects you named:

- **Reference** — safe now. An address plus a digest carries no authority. This
  is the correct early primitive.
- **Projection** — safe now. A projection is rebuildable by definition and a peer
  projection is a local cache of a foreign claim.
- **Materialization** — safe now, if the local copy enters at `RECORDED` and the
  local admission is a separate settled act. The schema already forces this.
- **Provenance** — safe now, and this is where digest-pinning already earns its
  keep.
- **Derivation** — safe with care. `request-derivative` is BUILT locally. A
  derivative *of* a foreign asset is fine; a derivative that carries the foreign
  asset's standing is not.
- **Withdrawal** — needs design before it enters. Retraction adds a
  counter-record and never claims an external effect was reversed. A withdrawal
  that crossed a node boundary cannot be un-crossed, and pretending otherwise
  would be the first real lie in the record.

**Sessions.** Visit and continuation are safe early; the rest is not.

- **Visit** — safe now. A foreign participant reaching a local surface, refused
  or admitted by local authority, is what the Gateway already does. This costs
  nothing new.
- **Continuation** — safe now, as a *local* record of a thread that a foreign
  session also reads. The Console continuity path is built.
- **Handoff** — safe only as an offer. The receiving node opens its own session;
  it does not adopt the sender's.
- **Local admission** — safe, and it is the qualification gate itself. Do not
  ship it early.
- **Local authority** — **never transfers, under any framing.**

### What must never transfer

Stated flatly, because this is the part that gets eroded by convenience:

1. **Authority.** A grant is local. A peer's grant is a fact about somewhere
   else. `node-identity.schema.json` is deliberately built so it *cannot express*
   a grant, a capability or a scope — copy that constraint into every federation
   contract.
2. **Standing.** `standing_at_origin` is reported. A record admitted locally
   enters at the local node's own standing, which starts at `RECORDED`.
3. **Session liveness.** A live session on node A says nothing about node B.
4. **Identity.** A principal registered on A is a foreign name on B until B
   admits it.
5. **Settlement.** The receiving Root settles its own admission and does not
   cross back. The schema already says this.
6. **Judgement.** Ratification is the local root seat's, always.

### The split

**Early (now, no gate movement):** references, projections, provenance,
materialization at `RECORDED`, visit, continuation. All of it is one node
describing a foreign thing to itself.

**Late (behind the qualification gate):** admission, handoff of a session,
withdrawal semantics, and any reciprocal settlement.

The line is clean: **early federation is representation; late federation is
admission.** Nothing in the early half requires a second node to exist, which is
why it can be built and defeated now.

---

## 10. What genuinely needs your judgement

Four things. Everything else in this report is a reversible engineering call and
I am not asking about those.

1. **The word.** I recommend **Node Topology** for the shape and **Traversal**
   for one attributed walk, both already in `CLASSIFICATION.md:59`, minting one
   word instead of five. `Trace` and `Probe` from 0092 collide and cannot be
   used. This is naming, which is yours.

2. **The ledger-compaction proposal** sitting as a zip in `decisions/`. It turns
   84 decision records into a second append-only journal plus a projection. My
   recommendation is **decline it**, on your own instruction not to add another
   journal or truth store — but it is a governance-shape decision and it is
   yours. It should not stay a zip either way.

3. **The peer-standing score seam.** 0092 ruling 4 permits a derived percentage
   as a steering aid; `contracts/peer-network.json` forbids any single score.
   Both PROPOSED, both unlanded, genuinely contradictory. One sentence settles
   it. My recommendation: peer standing is the exception — a distribution and
   named failing runs, no number — because that contract's reasoning ("a number
   invites the owner to judge the number") is the stronger argument.

4. **Whether to discard the five trivial dirty worktrees and `stash@{0}`.**
   Deletions, so I did not take them. `fix/external-effect-preconditions`
   (13 files) should be rescued regardless.

**Not asking you about:** which branches to retire (evidence is in section 3),
how to assemble the receipt, where the observation store lives, or how to render
the surface. Those are mine.

---

## 11. The next three bounded pieces of work, in order

Each is one concern, one branch, one pull request. Each ends in a landed result,
not an artifact about a result.

### First — make the continuity path tell the truth, and stop the bleeding

*Why first:* it is failing at every session start today, it degrades further each
session because the read cursor never advances, and the fix is already written
and unlanded.

- Land `fix/continuity-hook-honest-failure` (2 commits, clean worktree, adds the
  test main lacks).
- Reconcile it with the duplicate `scripts/tests/test_console_session_hook.py`
  sitting untracked in the shared tree — keep one.
- Diagnose the `DIGEST_MISMATCH` at `entry_80767935e18c488fb45502df9d5c385e`
  and either repair the chain or record a counter-entry. Do not delete the
  journal.
- Fix the eight duplicate keys in `STATUS.yaml` while there; half of those
  statements are already invisible.

Scope: `RECORD_LOCAL`. Absorbs cleanly — same service, same effect class, same
authority.

### Second — close the receipt join, and make the traversal observable

*Why second:* it converts the two WRONG_SHAPE steps of the proving path into
REAL, it needs no new subsystem, and it is what everything else waits on.

- Make `services/gateway` emit a `contracts/receipt.schema.json` receipt as the
  terminal record of every dispatch, positive and refused. The Gateway already
  computes almost every field; assemble them. Keep service-local receipts as
  emitted records referenced by the terminal one.
- Give `scripts/sovnode/interface_inputs.py:66` a real source. An observation
  store keyed by `operation_id`, written by a participant that did not execute
  the traversal, carrying `observer_relation` and `predicate_results`. The
  builder's `interface_defects` already refuses an unknown subject, so the
  defeating case is written.
- Positive and defeating fixtures for both, per the implementation order.
- Reconcile the two `reachable` counts (46 vs 5) or name them differently.

Expected reading afterward: `observed` moves off zero for the first time, and
`reachable_not_observed` starts to mean something.

Scope: `RECORD_LOCAL`. Two services, so if it does not absorb cleanly, split at
the receipt/observation line and do the receipt first.

### Third — one traversal you can watch, end to end

*Why third:* it needs the receipt to exist. This is where Baseline 50 becomes a
reading rather than a proposal.

- Drive one attributed traversal of `sov://asset/read-version` — a human actor
  resolved against `principals.json`, a session, a grant, an exact version read,
  a terminal receipt, an independent observation, all reconstructable from
  records alone.
- Drive one refused traversal beside it. `mallory` already gets refused
  correctly; give the refusal the same receipt shape.
- Render both on one page that shows: what was asked, what admitted or refused
  it, what it returned, who observed it and how they avoided the executor's
  report, what it cost in tokens, wall clock and tool calls, and **what is still
  missing** — absent joins left visibly absent, never filled with mocks.
- Declare the seven Baseline-50 predicates from section 8 and grade
  `baseline_50(asset)` against that one traversal.

Scope: `RECORD_LOCAL`, plus `RESOURCE_CONSUMPTION` for the measured run.

### What is deliberately not in these three

Branch retirement (section 3 is the evidence; the retirement is its own concern),
the 40 undispositioned branches, gate-policy from the terminal-interfaces branch,
projection drift, and the F2 predicates. All real, all wanted, none of them on
the critical path to one traversal you can watch.

---

## Residuals

- The 21 unclaimed local-only files (section 2a) are still unlanded and still
  held only by an untracked working tree. This report does not rescue them; it
  names them.
- 40 branches are undispositioned.
- `decisions/0092` is uncommitted and held by another live session; I did not
  edit it. Its vocabulary needs a second reading before it lands.
- `phase:ii` still has no record and `phase:i.succeeded_by` is still null.
- Trap T2 in `CLAUDE.md` is stale by one requirement.
- Steps 8 through 11 of the proving path were graded by inspection of what the
  code returns, not by an independent observer. This report was written by the
  same participant that ran the probes and can never witness itself.
