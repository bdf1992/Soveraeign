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
- `AI-NATIVE.md`: surface evaluation and qualification criteria;
- `STATUS.yaml`: current standing, authority, and open decisions;
- `ENGINEERING.md`: proposed reference stack and composition rules;
- `SDLC.md`: operating tiers, verification dyad, and release gate.

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
non-default effects remain visible.

`standing:` is one axis for the whole artifact lifecycle, and its colours ramp
with how much evidence stands behind the claim: `proposed`, `declared`,
`chartered`, `self-tested` (amber, because the witness is still outstanding),
`witnessed` (green), `ratified`, and `demoted` (red, a fall off the ramp rather
than a rung on it). `OPEN` is the default and carries no label, like
`effect: record-local`. Every standing projects to at most one label. The
separate `witness:` axis said the same thing a second time and is retired; a
surviving `witness:` label now reads as drift
(`decisions/0044-github-coordination-write-crossing.md`).

The canonical names, descriptions, and accessible colors live in
`.github/labels.yml`. The YAML block at the top of an issue is an instance of
`soveraeign-ticket/v1`; after YAML parsing it must validate against
`contracts/issue-metadata.schema.json`. Display labels are projections of that
metadata, not a second authority.

Use native relationships only for the containment tree: `child_issues` on the
epic and `village_issue` on each bit or stub, not `parent`, which a bit may
point at the epic while its village is the node that contains it. Cross-village
dependencies, multiple parent bits, dependency channels, and proof obligations
remain explicit in issue metadata, and are rendered into the body as plain
issue links inside the `sov:relations` delimiters so a reader sees them without
parsing YAML. The metadata stays authoritative; the rendered block is a
projection of it and never a second place to declare an edge. A branch or pull request may close
an implementation stub; it cannot by itself close its bit, promote a village,
satisfy independent witness, or ratify the epic.

A **story** (`kind: story`, `type: story`) is one participant crossing one
counter and finding the substrate short. It names its teller by the kernel's
`actor_kind` and a `CLASSIFICATION.md` participation `role`, the bit it walks
up to as `parent`, what the actor `expected`, what they `found`, the supports
the crossing `leans_on`, and the `asks` it addresses to the issues that own
the substrate. A story is told, then bound to a `scenario` in
`conformance/scenarios.json`, then walked. It is never taken as work: it
carries no `requires`, enters no queue, blocks nothing, and closes no
repository surface. Only an independent observation of its scenario moves a
story past `BUILT_SELF_TESTED_NOT_WITNESSED`; a pull request cannot close it.
Owner is not a role a story can name: it is the context that sets an
operator's Binding and Projection and travels in `authority`
(`decisions/0022-story-ticket-kind.md`).

An **unblock request** (`kind: unblock`, `type: unblock`) is a proven block
filed as work. Blocked is never a ticket status. A ticket that cannot advance
names the exact `blocked_transition`, the `missing_precondition`, the
`governing_rule`, the `requested_provision` (grant, judgement, contract,
fixture, capability, or observation), the tier it was `requested_by`, the tier
it is `requested_from`, the `unblock_condition` a receipt will settle, and
`reachable_alternative: NONE`. The held ticket lists the unblock request in
its `requires`, so it shows as held-by, like any dependency. A request with a
reachable alternative is refused: that ticket is dependency-mapped, not
blocked. A request whose provision is already some ticket's work is refused
for the same reason; link that ticket instead. A judgement is always asked of
the owner. The queue serves an unblock request at the tier it names and sorts
it by what it holds (`decisions/0032-unblock-ticket-kind.md`).

A **chore** (`kind: chore`, `type: chore`) maintains or retires a repository
surface. It names the `path` it acts on and carries a `chore_id`; it closes no
obligation, so `parent_bits`, `stub_id`, `bit_id`, `engagement_id`, and
`story_id` are refused on it. A chore may carry `requires`, because
housekeeping often waits on a decision that has not been taken. The test is
what the surface's absence would leave behind: if removing it leaves a bit
unclosed, that is a demotion of the stub that closed it and not a chore. It is
takeable work and enters the queue, sorting last among equally urgent tickets
because it maintains a surface rather than advancing one
(`decisions/0090-chore-ticket-kind.md`).

Changing the issue schema, label axes, color meanings, containment rule, or
milestone semantics is a reviewed contract change. Update this section, the JSON
Schema, and the label catalogue together.

## Checking the coordination surface

The board is checked the same way as the repository: capture it through the
declared registrar, then judge the capture offline.

```bash
python adapters/github/export.py --repo bdf1992/Soveraeign --out .local/registrar/tickets.json
python scripts/sov_ticket.py validate --export .local/registrar/tickets.json
python scripts/sov_ticket.py labels   --export .local/registrar/tickets.json --strict
python scripts/sov_ticket.py queue    --export .local/registrar/tickets.json --limit 20
```

`validate` checks every issue body against
`contracts/issue-metadata.schema.json`. `labels` reports drift between the live
labels and the projection declared in
`contracts/ticket-label-projection.json`. `queue` orders open tickets by the
policy in `contracts/ticket-queue-policy.json` and reports what is takeable,
what is blocked and by what, and what unblocks the most. The queue is a
projection; position in it grants nothing.

A declaration reaches the surface through the registrar's write half, which
plans offline and performs only what a local declaration already determined:

```bash
python adapters/github/apply.py --repo bdf1992/Soveraeign --export .local/registrar/tickets.json
python adapters/github/apply.py --repo bdf1992/Soveraeign --export .local/registrar/tickets.json --apply
```

Without `--apply` it prints the plan and stops. It writes the label catalogue,
containment edges, and the rendered relations block, and nothing else; it never
opens, closes, comments on, assigns, or milestones an issue, and it writes no
standing. See `adapters/github/README.md` for both crossings' declarations.

`adapters/github/` is the only directory permitted to call the GitHub API.
Every other check reads its export from disk, so all of them run offline,
inside the day-zero budget, and in a sealed CI job.

## Proposing a standing change

A pull request that only implements something proposes no ticket-standing
change and needs no transition block; it establishes `BUILT` evidence and
nothing further. A pull request that advances a ticket's standing carries a
`soveraeign-ticket-transition/v1` request in its body, and the purple gate
evaluates it against
`contracts/ticket-transitions.json`.

```bash
python scripts/sov_ticket.py transition <request.json>
python scripts/sov_ticket.py transition --body <pull-request-body.md>
```

The table refuses what the contract forbids: skipped standings, a builder
witnessing its own work, an unconverged Red engagement, a confirmed finding
with no permanent defeating fixture, a finding the Red operator reproduced
itself, and any machine claiming `RATIFIED`. Run
`python scripts/sov_ticket.py selfcheck` to exercise every declared refusal;
`python scripts/verify.py` runs it for you.

Ratification is not reachable from a check. It enters the repository through
owner review on `STATUS.yaml`, `decisions/`, and the governing set, per
`.github/CODEOWNERS`.

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

## Carrying a concern to closure

A contributor who takes a bounded concern carries it to a landed result:
inspect, implement, test, recruit a helper, repair, verify, then present or
land. `AGENTS.md`, Closure ownership, is normative; this is the working path
through it, and `contracts/closure-ownership.json` is the table both read.

The coordination surface above exists to make work legible, not to stand in
for it. An issue, a branch, a pull request, a review finding, a TODO, or a
question for Bdo records a concern; none of them advances one. Opening one is
progress only when it is the shortest remaining path to the result.

- Settle ordinary reversible engineering choices yourself. Which reachable
  design, what to call a local symbol, what the defeating case should be, when
  to split an oversized module — these are yours, and asking another tier for
  one is a defect rather than caution.
- Recruit a helper model or subagent when a second reading would help, without
  asking anyone. Point it at the defect you cannot see, the missing test, the
  scope drift, the abstraction you did not need, and the authority you assumed.
  Then repair what it finds. A helper that read or edited the change is inside
  your build and can never witness it.
- Repair review findings and failing checks inside the concern. A finding
  turned into a second ticket has moved the defect away from the work that owns
  it.
- Keep one bounded concern, one branch, one pull request. Chasing CI, review
  findings, rebases, and ordinary merge work to completion is part of the
  concern.
- Absorb follow-on work that stays inside the same service, the same effect
  class, and the same authority. Crossing any one of those three mints a
  separate concern. That is the whole line between absorption and scope creep.
- Hand off only at one of five seams: `AUTHORITY_SEAM`, `POLICY_SEAM`,
  `EFFECT_SEAM`, `DEPENDENCY_SEAM`, `ACCEPTANCE_SEAM`. Judgement is asked of
  Bdo and of no one else.

Write a handoff as a `soveraeign-closure-handoff/v1` claim and grade it before
you send it:

```bash
python scripts/sov_closure.py loop
python scripts/sov_closure.py judge <claim.json>
```

`loop` prints the declared loop, the work-in-progress ceiling, and the seams.
`judge` returns `PERMITTED` with the seam it accepted, or `REFUSED` with the
code and the reason. A refused claim is work you still hold.
`python scripts/sov_closure.py selfcheck` proves every declared refusal fires,
and `python scripts/verify.py` runs it for you.

Bdo's gate does not change: acceptance over a finished evidenced result, never
approval to begin (`decisions/0023-acceptance-not-approval.md`).

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

`.gitattributes` pins `* text=auto eol=lf` so checkout produces LF on every
platform regardless of your `core.autocrlf` setting, and exempts `lineage/`
whose evidence digests must stay byte-exact. `scripts/lint.py` reads file bytes
and fails on any CR it finds; do not work around either by normalizing at commit
time only.

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
at fifteen, failing past fifteen (`decisions/0050`). The grade prints on every
passing run. Losing a grade does not fail the gate; it is worth reporting
anyway. CI runs the same command.

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

Run `python scripts/lint.py` to check syntax, repository text encoding and line
endings, module-size debt, and common secret shapes locally without transmitting
repository content.

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
