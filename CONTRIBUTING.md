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

## Issue coordination contract

GitHub is the coordination surface; the issue body remains the compressed
specification. Each field has one role:

| Surface | Owns |
| --- | --- |
| Title | `Subject — bounded outcome`; no bracketed type or village prefixes |
| Labels | Stable filtering axes: type, village, horizon, non-default effect, and exceptional standing |
| Issue body metadata | Complete machine-readable contract validated by `contracts/issue-metadata.schema.json` |
| Relationships | Containment only: epic → village → bit or implementation stub |
| `requires` and `parent_bits` | The dependency DAG; never forced into GitHub's single-parent tree |
| Milestone | The next evidence gate, such as F0 through F6 or Federation |
| Project status | Volatile delivery state: proposed, ready, blocked, active, in witness, done, or demoted |
| Assignee | The human accountable for the next action; assignment grants no authority |
| Development | Branches and pull requests for implementation work, normally attached to stubs |

Titles do not repeat information already visible as labels. Use the title form
`Subject — bounded outcome`, retaining a well-known service or artifact name as
the subject.

Every issue receives exactly one `type:` label and, except the system epic,
exactly one `village:` label. It receives exactly one `horizon:` label.
`effect: record-local` is the default and is omitted from the visible label set;
non-default effects remain visible. `witness: pending` is carried by body
metadata or the project and is omitted from the list view until witness state
changes. Implementation stubs retain a `standing:` label when that standing
changes how the work may be treated.

The canonical names, descriptions, and accessible colors live in
`.github/labels.yml`. The YAML block at the top of an issue is an instance of
`soveraeign-ticket/v1`; after YAML parsing it must validate against
`contracts/issue-metadata.schema.json`. Display labels are projections of that
metadata, not a second authority.

Use native relationships only for the containment tree. Cross-village
dependencies, multiple parent bits, dependency channels, and proof obligations
remain explicit in issue metadata and prose. A branch or pull request may close
an implementation stub; it cannot by itself close its bit, promote a village,
satisfy independent witness, or ratify the epic.

Changing the issue schema, label axes, color meanings, containment rule, or
milestone semantics is a reviewed contract change. Update this section, the JSON
Schema, and the label catalogue together.

## Checking the coordination surface

The board is checked the same way the repository is: capture it through the declared
registrar, then judge the capture offline.

```bash
python adapters/github/export.py --repo bdf1992/Soveraeign --out .local/registrar/tickets.json
python scripts/sov_ticket.py validate --export .local/registrar/tickets.json
python scripts/sov_ticket.py labels   --export .local/registrar/tickets.json --strict
python scripts/sov_ticket.py queue    --export .local/registrar/tickets.json --limit 20
```

`validate` checks every issue body against `contracts/issue-metadata.schema.json`.
`labels` reports drift between the live labels and the projection declared in
`contracts/ticket-label-projection.json`. `queue` orders open tickets by the policy in
`contracts/ticket-queue-policy.json` and reports what is takeable, what is blocked and
by what, and what unblocks the most. The queue is a projection; position in it grants
nothing.

`adapters/github/export.py` is the only module permitted to call the GitHub API. Every
other check reads its export from disk, so all of them run offline, inside the day-zero
budget, and in a sealed CI job.

## Proposing a standing change

A pull request that only implements something proposes no standing change and needs no
transition block; it establishes `BUILT` evidence and nothing further. A pull request
that advances a ticket's standing carries a `soveraeign-ticket-transition/v1` request in
its body, and the purple gate evaluates it against
`contracts/ticket-transitions.json`.

```bash
python scripts/sov_ticket.py transition <request.json>
python scripts/sov_ticket.py transition --body <pull-request-body.md>
```

The table refuses what the contract forbids: skipped standings, a builder witnessing its
own work, an unconverged Red engagement, a confirmed finding with no permanent defeating
fixture, a finding the Red operator reproduced itself, and any machine claiming
`RATIFIED`. Run `python scripts/sov_ticket.py selfcheck` to exercise every declared
refusal; `python scripts/verify.py` runs it for you.

Ratification is not reachable from a check. It enters the repository through owner
review on `STATUS.yaml`, `decisions/`, and the governing set, per `.github/CODEOWNERS`.

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

## Own the work to closure

A contributor who accepts a bounded concern owns its path to a landable result.
Opening an issue, branch, pull request, review, or acceptance packet is not a
completion event. Those are working surfaces inside the contribution.

The normal contribution loop is:

`inspect -> build -> test -> recruit helper -> repair -> freeze -> witness -> land`

Do not create a new issue merely because you discovered another logical step in the
same work. If it is required to finish the current concern, remains inside the same
service and effect boundary, and does not require a new owner-held decision, do it on
the current branch. Create another issue only for a concern that should survive this
work independently: a separate service lifecycle, acceptance boundary, deferred
unresolvable dependency, or durable coordination need.

Keep WIP scarce. A contributor should normally have one active implementation branch
and one active pull request for the concern it is closing. Parallel branches are for
independent mergeable work, not for every uncertainty or possible follow-up.

### Bring your own copilot

Model workers are expected to recruit another model participant themselves when the
host supports it. Do not ask the owner to arrange ordinary review assistance. Give the
helper a bounded brief: the claim, relevant paths, current diff or revision, and the
strongest defeating case you want challenged. Use the helper to hunt for defects,
missing tests, unnecessary abstraction, authority leakage, scope drift, and simpler
ways to close the concern.

The primary worker owns every repair. A helper does not become the owner of the branch
and does not turn a finding into another ticket unless the finding is genuinely an
independent durable concern.

A helper that changed or directed the implementation is not an independent witness.
When `WITNESSED` standing is needed, freeze the revision and request a fresh non-editing
model invocation against that exact commit or digest. Preserve the witness report and
the claim it tested. If the witness defeats the result, repair the same concern, freeze
a new revision, and request witness again.

A smaller or cheaper model is often appropriate for this bounded counterpart role.
Model size is not authority. If another model cannot be invoked, record that capability
as unavailable and use the strongest independent local checks available; do not relabel
self-review as witness evidence.

### Land ordinary work yourself

For reversible work inside the live grant that does not cross an owner-acceptance
boundary, the worker is expected to chase CI and review to completion, resolve findings,
update or rebase, and merge the pull request once required checks pass, the head revision
is known, no genuine open seam is being silently decided, and the merge itself is
permitted.

Do not leave an ordinary PR open waiting for Bdo to “approve” engineering choices.
Owner-held acceptance PRs are different: keep those open until the owner explicitly
accepts or lands them.

The result we optimize for is not a richly organized queue. It is a short path from one
bounded concern to one landed result, with helpers and evidence pulled in by the worker
as needed.

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

The gate is dependency-free and network-free. Its wall time is graded rather
than pass/fail: `PLATINUM` at three seconds or less, `GOLD` at six, `SILVER`
at fifteen, failing past fifteen (`decisions/0050`). CI runs the same command.

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
