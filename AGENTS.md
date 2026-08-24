# Agent Operating Contract

This file governs the entire repository. A nearer `AGENTS.md` may add stricter
rules for its subtree, but it may not weaken this contract. `CONTRIBUTING.md`
explains the same workflow for human contributors; `ENGINEERING.md` defines the
current technical baseline.

Before a consequential change, read `STATUS.yaml`, `SYSTEM.md`, `CONTRACT.md`,
`PRD.md`, `SPEC.md`, `ENGINEERING.md`, `SDLC.md`, and `OPEN-SEAMS.md`.

## Design System of Record

The governing documents form one design System of Record with explicit roles:

- `SYSTEM.md` owns the system boundary and operating model;
- `CLASSIFICATION.md` owns architectural, information-role, and
  operating-loop vocabulary;
- `CONTRACT.md` owns invariants;
- `PRD.md` owns Phase-I requirements;
- `SPEC.md` owns logical objects, transitions, predicates, and refusals;
- `STATUS.yaml` owns current authority, standing, and open decisions;
- `ENGINEERING.md` owns the proposed reference implementation baseline;
- `SDLC.md` owns the operating loop: tiers, dyads, concern registry, skill
  axes, workflow templates, and the Red-gated release requirement.

Do not duplicate a rule in another file as a competing authority. Link to the
owning document and record genuine conflicts in `OPEN-SEAMS.md`.

## Authority

The root seat holds product-intent, naming, judgement, and phase-gate authority;
Bdo occupies the root seat (`decisions/0020`). Every other owner is the seat one
edge up: the seat that issued the live grant and settles the receipts. Ownership
does not chain. The root seat owns the control seat and does not thereby own
that seat's workers; the orchestrator does. `contracts/seat-registry.json` is
the current view.

A model, worker, adapter, credential, process, database, or provider receives no
authority merely by operating successfully. Every consequential transition uses
a typed, scoped, live grant at the operation boundary.

### The owner gate is acceptance, not permission

An owner seat accepts or rejects a finished result. It does not approve work
before it happens. Work whose effect class is `RECORD_LOCAL` or
`RESOURCE_CONSUMPTION`, and whose change a counter-record or a revert undoes,
proceeds without asking anyone: choose, sequence, implement, test, repair, and
present. Asking permission for that work is refused by `PREAPPROVAL_REQUESTED`.

A transition waits on an owner seat only for a reason
`contracts/acceptance-policy.json` names: an external-world effect, an
irreversible one, publication, owner identity or naming, a secret, destructive
administration, or a resource commitment. That list is exhaustive. Wanting the
owner's opinion is not on it.

When work is finished, it is written up as an acceptance packet under
`acceptance/`: the claim in one sentence, a command the owner can run to see it,
the exact evidence, why it matters, what would defeat it, and what is still
unfinished. The packet is addressed to the seat one edge up, and to no other
seat. `python scripts/sov_accept.py audit` fails the build if anything sits on
an owner seat without either an admissible reason or a packet.

A seat decides its own work. What to inspect, which legal operation to attempt,
how to sequence reversible changes, when to abandon a failed line: that is the
seat's own, needs no packet, and is refused if presented upward.

## Sov operating profile

`Sov` is the owner-selected name of Soveraeign's main operating agent. It is a
portable context profile loaded by a compatible underlying model, not a model,
provider, runtime, host, credential, authority slot, durable memory, or second
kernel. Read `SOV.md` for the entry point and `bindings/sov/profile.json` for
the machine target.

Host bindings may make Sov selectable without redefining it. Claude Code uses
`CLAUDE.md` as its repository entry point and `.claude/agents/sov.md` as the
thin named-agent binding; both defer to `SOV.md` and the portable profile.

Loading Sov grants no authority. Sov may direct its attention, select relevant
context and legal operations, propose, build and finish reversible work without
asking, present results for acceptance, refuse, escalate, and hand off. It may
not widen a grant, infer authority from context, ratify judgement, self-witness,
self-settle, keep private standing, bypass a governed transition, or silently
change models. Stopping to ask permission for reversible record-local work is
itself a refusal Sov is subject to (`contracts/acceptance-policy.json`).

Sov is the default candidate for the control seat, not its automatic holder;
every seat occupancy remains scoped by the current task and grant.

## Evidence and standing

- Treat `lineage/evidence/` as immutable attributed input.
- Verify historical evidence against `lineage/SOURCES.lock` before relying on it.
- Cite evidence paths and clause or section identifiers in governing changes.
- Mark new claims as proposals and preserve open contradictions.
- Never treat recency, repetition, eloquence, confidence, model consensus, a
  green build, or executor self-report as authority.
- Preserve the standing lifecycle: `OPEN -> BUILT -> WITNESSED -> RATIFIED`.
- A build report cannot witness itself, and no seat settles its own output.
- Only a seat that settles `JUDGEMENT` can ratify a judgement claim, and it does so
  by accepting a presented result rather than by answering a question.

## Change protocol

Before changing policy, contracts, schemas, transitions, authority, persistence,
or external effects, record in the working note or change description:

1. requested outcome and current authoritative state;
2. affected contracts, fixtures, and sources;
3. preconditions and expected observable result;
4. effect class: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, or `EXTERNAL_WORLD`;
5. rollback, counteraction, or refusal boundary.

After the change, inspect the result through a path independent of the code that
performed it, record residual failures, and change only what the observation
disproves.

## Implementation order

1. Name the operation and the owned service lifecycle.
2. Add or update the contract and its positive and defeating conformance case.
3. Make the smallest implementation change that satisfies the visible case.
4. Add focused unit tests for local mechanics and edge cases.
5. Run `python scripts/verify.py` from a clean repository root.
6. Record any changed policy in `decisions/` and any changed standing in
   `STATUS.yaml`.

Do not write business logic that has no prior contract, fixture, or explicit
experimental label. Never weaken an oracle merely to make a participant pass.

## State and execution

The operational System of Record is the append-preserving record of addressed
inputs, events, standing changes, observations, receipts, and counter-records.
SQLite is the current storage mechanism; it is not the semantic authority.

- Execution requests state through a declared operation plan; it does not own
  state.
- Every consequential human or model decision emits an attributable event with
  actor, operation, reason, timestamp, exact input addresses/digests, output
  addresses/digests, authority grants, effect class, and outcome.
- Workers may emit reports. Independent observation and kernel settlement decide
  whether a run committed.
- Mutable tables, search indexes, graphs, and UI caches are projections unless a
  contract explicitly says otherwise. Projections must be rebuildable.
- Retraction adds a counter-record. It never erases the original event or claims
  that resource consumption or external effects were reversed.

## Technical baseline

- Use Python 3.11 or newer for the Phase-I reference implementation.
- Prefer the Python standard library. A runtime dependency requires a named
  boundary, an observed need, failure behavior, and a decision record.
- Keep the local reference record in SQLite and immutable payload bytes in the
  filesystem content-addressed store. Search and graph stores are projections.
- Use JSON and JSON Schema Draft 2020-12 at machine boundaries. YAML is allowed
  for small human-authored status and narrative fixtures; do not create a second
  semantic contract in YAML.
- Start with local process calls and a CLI. Add HTTP, queues, containers,
  orchestration, or remote databases only when a conformance case requires them.
- Models and enterprise systems integrate only through declared bindings and
  adapters. No provider SDK type may enter a kernel or service contract.

See `ENGINEERING.md` for the primitive set and boundary rationale.

## Python style and imports

- Encode text as UTF-8, use LF endings, four spaces, and a final newline.
- Target a 100-character line length and keep modules below 300 lines. Split by
  owned responsibility, not by arbitrary line count. Named existing debt must be
  recorded rather than silently grandfathered.
- Add `from __future__ import annotations` to new Python modules.
- Order imports in three groups separated by one blank line: standard library,
  third party, then local project imports. Sort names lexically within a group.
- Use absolute project imports in production code. Relative imports are allowed
  only inside one package when they make that package boundary clearer.
- Do not manipulate `sys.path` in production code. A test bootstrap may do so
  until the root workspace is packaged.
- Use `pathlib.Path`, context managers, explicit encodings, and parameterized
  SQL. Do not construct SQL from untrusted strings.
- Keep timestamps, identifiers, randomness, model clients, and external I/O
  injectable when their nondeterminism affects a test or receipt.
- Domain terms and enum values must match `CLASSIFICATION.md` and `SPEC.md`.
  Do not create synonyms for existing standing, event, effect, or role terms.
- Public functions, classes, schemas, and refusal reason codes require concise
  documentation. Comments explain constraints or reasons, not line-by-line code.

If Ruff is available, run `python -m ruff format --check .` and
`python -m ruff check .`. Ruff is a development convenience, not a runtime
dependency or a substitute for repository verification.

## Testing and verification

- Use dependency-free `unittest` for the Phase-I reference participant.
- Put local unit tests beside their service under `services/<domain>/tests/`.
- Put cross-participant semantic cases in `conformance/`; the oracle must not
  import participant implementation code.
- Every consequential behavior needs at least one positive case and one case
  proving the required refusal, counteraction, or failure.
- Tests use temporary directories, fixed inputs, bounded waits, and no network.
- Tests distinguish attempted, reported, observed, and settled outcomes.
- A test may establish `BUILT`; it may not claim `WITNESSED` or `RATIFIED`.
- The required local and CI command is `python scripts/verify.py`; its default
  execution budget is three seconds after Python starts.

## Context hygiene

- Work one named operation or repository concern at a time.
- Read the governing set plus only the service, contract, decision, and fixture
  relevant to that operation. Use search before opening broad files.
- Do not paste complete logs, large diffs, generated files, database contents,
  or historical evidence into model context. Provide addresses and bounded
  excerpts.
- Keep production modules below 300 lines and functions focused on one owned
  transition or calculation.
- Begin a fresh agent task or handoff for a distinct objective. The handoff names
  current standing, changed files, observed checks, residuals, and next action;
  it does not carry the entire conversation forward.

## Secrets and local boundaries

- Never commit `.env`, credentials, private keys, tokens, local absolute paths,
  runtime databases, payload stores, logs, or model prompt dumps.
- Use `.env.example` for names and safe descriptions only; never place a usable
  secret in it.
- Never print secrets or raw credentials in logs, receipts, exceptions, prompts,
  fixtures, or test snapshots. Record only an opaque credential reference.
- Remote crossings require a declared adapter, data-boundary mode, exact input
  projection, authority, and receipt. Silent provider fallback is forbidden.
- Run `python scripts/lint.py`; it checks repository text, Python syntax, module
  size, and common secret shapes without transmitting content.

## Directory boundaries

| Path | Owns | Must not own |
| --- | --- | --- |
| `/contracts` | Shared kernel and crossing schemas | Service-specific lifecycle logic |
| `/conformance` | Independent scenarios, oracle controls, witness inputs | Participant implementation or direct participant imports |
| `/services/<domain>` | One bounded lifecycle, contract, implementation, and tests | Another service's state or provider-specific authority |
| `/bindings` | Human/model realizations of declared interfaces | Authoritative writes or semantic forks |
| `/adapters` | Translation to a named external system | Standing, ratification, settlement, or hidden fallback |
| `/workers` | Scoped leased execution and reports | Self-settlement or self-witnessing |
| `/scripts` | Verification and bounded repository maintenance | Product business logic |
| `/acceptance` | Finished results presented to an owner seat, one packet per claim | Standing changes, which land in the owning document |
| `/decisions` | Consequential choices, status, rationale, consequences | Mutable runtime state |
| `/lineage` | Attributed ancestry and immutable historical evidence | Current policy by implication |

Cross-service work goes through a declared contract and receipt. Bindings,
adapters, workers, projections, and databases never bypass kernel transitions to
write authoritative state.

## Branch and commit strategy

- `main` is the releasable design System of Record. Keep it passing.
- Normal work uses a short-lived branch named `feat/<scope>`, `fix/<scope>`,
  `docs/<scope>`, `test/<scope>`, or `chore/<scope>` and a reviewed pull request.
- Direct commits to `main` require Bdo's explicit instruction for that change.
- Rebase or update before merge; do not use long-lived integration branches.
- Keep one coherent policy or behavior change per commit. Use an imperative
  message such as `docs: define engineering baseline`.
- Do not force-push a shared branch, rewrite published history, or bypass a
  failing verification gate.

## Repository protections

- Preserve `product_name: Soveraeign` and `repository_name: Soveraeign` unless
  Bdo explicitly changes the name.
- Do not import a predecessor repository wholesale. Carry an ancestor forward
  through an invariant, decision, fixture, schema, or reviewed implementation.
- Record substantial policy and dependency changes in `decisions/`.
- Do not initialize a remote, publish, or enable external effects without an
  explicit instruction.
- Public publication includes canonical synthesis and implementation artifacts
  only. Publishing `lineage/`, ancestor registries, raw evidence, or source-lock
  inventories requires a separate explicit owner instruction.

## Completion report

Report files changed, checks and observations, standing changes, decisions that
still require owner judgement, assumptions introduced, and the next bounded
operation. Do not call work complete merely because files were written or tests
returned zero.
