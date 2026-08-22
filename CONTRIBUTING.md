# Contributing to Soveraeign

Soveraeign accepts small, inspectable changes that strengthen one governed
operation without silently changing the system around it. Humans and models use
the same contribution contract. `AGENTS.md` is normative; this document is the
working path through it.

## Design System of Record

Do not treat “System of Record” as “one file contains truth.” The repository's
governing set has explicit ownership:

- `SYSTEM.md`: system boundary and operating model;
- `CLASSIFICATION.md`: controlled vocabulary;
- `CONTRACT.md`: invariants;
- `PRD.md`: Phase-I requirements;
- `SPEC.md`: logical model, transitions, predicates, and refusals;
- `STATUS.yaml`: current standing, authority, and open decisions;
- `ENGINEERING.md`: proposed reference stack and composition rules.

The operational System of Record preserves events and receipts with their
standing. It can record disagreement, failure, and retraction without converting
them into an undifferentiated claim of truth.

## Before you change code

Read the governing set above, then inspect `OPEN-SEAMS.md`, the relevant service
charter and contract, its conformance scenario, and related `decisions/`.

If intended behavior is absent from a contract or conformance case, the first
contribution is a proposed contract and a defeating fixture—not hidden business
logic.

## Shape of an accepted change

A change identifies one named operation or repository concern, its service
owner, exact inputs and outputs, authority and effect class, positive and
defeating observations, refusal or counteraction behavior, and any standing
whose transition is requested.

Prefer a small vertical slice that produces a real receipt over a broad layer of
framework abstractions.

## Development baseline

Phase I proposes Python 3.11+, the standard library, SQLite, a filesystem
content-addressed store, JSON Schema Draft 2020-12, and `unittest`. This is a
reference baseline, not a claim that the logical system depends on Python or
SQLite.

Create frameworks only after repeated concrete use. Do not add a web server,
task queue, container platform, remote graph database, provider SDK, or general
plugin system to anticipate future needs. Introduce the smallest port or adapter
when an accepted operation requires it.

## Code, state, and formatting

Follow `AGENTS.md`: UTF-8, LF, four-space indentation, a 100-character target,
modules below 300 lines, future annotations, grouped and sorted imports, typed
boundaries, `pathlib`, explicit encodings, parameterized SQL, and injectable
nondeterminism.

Execution never owns authoritative state. Every consequential decision records
who acted, what operation was attempted, why, when, exact input/output addresses
and digests, authority, effect class, and terminal outcome. Projections are
rebuildable; counter-records preserve history.

Optional formatter/linter:

```sh
python -m ruff format --check .
python -m ruff check .
```

Required local gate:

```sh
python scripts/verify.py
```

The gate is dependency-free, network-free, and budgeted to complete in under
three seconds after Python starts. CI runs the same command.

## Tests and evidence

- Add service mechanics to `services/<domain>/tests/` with `unittest`.
- Add shared semantic requirements to `conformance/` before implementation.
- Include positive and defeating cases for consequential behavior.
- Keep the conformance oracle independent from participant code.
- Use temporary local state, fixed inputs, and bounded waits.
- Inspect durable state or emitted artifacts instead of trusting executor output.
- Preserve observed failures; never alter expectations merely to obtain green.

A passing self-test is `BUILT` evidence. Independent reconstruction is needed
for `WITNESSED`, and Bdo's judgement is needed for `RATIFIED`.

## Context hygiene

Keep each task to one named objective. Search before reading broadly, load only
the relevant governing sections and service surface, and do not paste entire
logs, large diffs, databases, generated artifacts, or historical evidence into
model prompts. Start a fresh task or bounded handoff when the objective changes.

Production modules remain below 300 lines. The current Asset Service core is
recorded implementation debt and must be split before adding further behavior
to it.

## Dependency rule

The default answer to a new runtime dependency is “not yet.” A necessary
dependency requires a decision recording the conformance case, containing port
or adapter, unavailable behavior, data/authority/cost/effect implications, and
replacement strategy. Provider-specific objects stop at their adapter.

## Secrets and local data

Never commit `.env`, credentials, tokens, private keys, local paths, runtime
databases, payload stores, logs, or prompt dumps. Copy `.env.example` to `.env`
for local configuration and keep values out of output. Receipts refer to an
opaque credential identifier, never credential material.

Run `python scripts/lint.py` to check syntax, repository text, module-size debt,
and common secret shapes locally without transmitting repository content.

## Directory ownership

Use the full boundary table in `AGENTS.md`. Services own domain lifecycles;
bindings present interfaces; adapters translate external systems; workers
report leased execution; projections are disposable; scripts verify or maintain
the repository; and historical evidence remains immutable.

## Branch and review strategy

Use short-lived `feat/<scope>`, `fix/<scope>`, `docs/<scope>`, `test/<scope>`, or
`chore/<scope>` branches and a reviewed pull request into `main`. Direct commits
to `main` require Bdo's explicit instruction. Avoid long-lived integration
branches and do not rewrite shared history.

Keep one coherent change per commit with an imperative message. Review must be
able to identify the changed behavior, authority, durable evidence, defeating
case, provider-loss behavior, counteraction boundary, and honest standing.
