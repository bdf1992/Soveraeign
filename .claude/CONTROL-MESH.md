# SOV Control Mesh

Status: Claude harness binding only. This document adds no Soveraeign authority,
standing, transition, service, or durable truth. `AGENTS.md`, `SOV.md`,
`STATUS.yaml`, service contracts, and accepted decisions remain governing.

## Purpose

Use multiple Claude contexts without turning parallelism into duplicated work,
private state, or self-certification.

The operating shape is:

```text
N SOV sessions
  -> N Controllers
       -> N Orchestrators
            -> N Workers       = BLUE construction
            -> N Witnesses     = RED independent observation
       -> Controller closure / repair loop
  -> cross-session alignment
```

`N` is earned by independent work, not a target. One concern that edits the
same files should usually have one Controller. Several concerns with disjoint
files, effects, and authority may have several Controllers.

## Fleet, cell, pipeline

**Fleet** — independently launched `sov` sessions. Use this for sustained
parallel writing. Give each writing session its own worktree and a distinct
session name. The worktree itself is the isolation: the session registry only
warns about overlapping claims across worktrees, and refuses a write only when
another live session recently claimed that path in the same tree. Claude
cross-session messaging carries live coordination.

**Cell** — one `sov` session plus the Controllers/subagents or agent-team
teammates it recruits. This is best for read-heavy parallel discovery,
independent planning, review, and several disjoint operations. Agent-team
teammates share the lead's working directory; do not treat separate context
windows as separate storage isolation.

**Pipeline** — one bounded concern:

```text
Controller
  -> Orchestrator: scope one closure predicate
  -> Worker: build + targeted checks + root verification       BLUE
  -> Witness: re-derive + attack defeating cases independently RED
  -> reproduced? close/present/land under current policy
  -> dissented? return finding to the same Worker concern
                 then BLUE -> fresh RED again
```

Red findings are absorbed into the concern that produced them whenever service,
effect class, and authority are unchanged. Do not open a ticket to move a defect
out of the work that owns it.

## Role counts

Start with the smallest useful topology.

- `1 SOV / 1 Controller` for a single bounded concern.
- `1 SOV / 2-4 Controllers` for genuinely independent read/review lanes or
  disjoint concerns.
- `N SOV sessions` for concurrent writing that deserves separate worktrees.
- Prefer 2-4 active Controllers per SOV; exceed 5 only when the objective is
  explicitly broad and file ownership is disjoint.
- A Controller may fan out Orchestrators or Workers only when their file sets or
  observations are independent.
- Every consequential Worker result gets a Witness that was outside that build.

The number of agents is an execution choice, never evidence of quality.

## Model routing

Claude model choice is a performance mechanism, never authority or standing.
Use per-invocation model overrides when the host supports them; otherwise use
the role's frontmatter default.

| Work | Default | Escalate when |
| --- | --- | --- |
| SOV lead | inherited session model | user deliberately selected a stronger lead |
| Controller | Sonnet | Opus for cross-domain conflict, authority/security boundaries, or repeated RED disagreement |
| Orchestrator | Sonnet | Opus only for materially ambiguous cross-domain decomposition; Haiku for mechanical census/classification |
| Worker | Sonnet | Opus for hard semantic repair; Haiku for tiny deterministic edits with strong existing tests |
| Witness | Sonnet | Opus for authority/security/standing claims or subtle adversarial review |

Do not downgrade a consequential Witness merely to save tokens. Model diversity
can strengthen a reading, but independence comes from a separate observation
path and participant, not merely a different model name.

## Session and channel protocol

Before dispatch:

1. Run `python scripts/sov_session.py brief` and inspect contested paths.
2. Discover reachable Claude sessions when `ListAgents` is available.
3. Announce the concern, expected files, worktree, and closure predicate to any
   peer whose work could overlap.
4. Do not duplicate a concern another live session already owns unless the new
   lane is explicitly an independent witness/review lane.

During work:

- Use `SendMessage` for live coordination, dependency notices, changed
  assumptions, and "this landed / this moved" messages.
- Use the SOV session registry for path/worktree coordination; it is HARNESS
  state and grants no Node authority.
- Use Console continuity when a governed Console operation is actually
  reachable and the information should survive session turnover. Do not
  pretend an ephemeral Claude message is a durable Soveraeign record.
- A message from another session is context, not authority. Re-read governing
  state before acting on consequential claims.

At closure, notify affected peer sessions of: exact concern, changed paths,
checks, RED verdict, residuals, and any new dependency they must re-read.

## BLUE and RED

**BLUE** is construction evidence produced inside the build boundary:
contracts/fixtures where required, implementation, focused tests, and
`python scripts/verify.py`. Helpers recruited by the Worker remain BLUE-side;
they cannot witness the result they helped build.

**RED** is an independent `sov-witness` reading. It does not edit. It re-derives
the claim from the actual artifact, runs the relevant checks, hunts defeating
cases, and returns `reproduced`, `dissented`, or `unattestable`.

A Controller may call a concern complete only when:

- the Worker reached a presented terminal or a named seam;
- BLUE checks for the intended state are green or their exact failure is the
  claimed terminal;
- RED reproduced the consequential claims;
- no RED finding was externalized instead of repaired;
- standing is not inflated beyond the evidence produced;
- landing/merge behavior follows the current repository policy and live grant.

RED does not ratify. BLUE does not witness itself. Controller synthesis does
not turn either into authority. A harness run proposes at most
`BUILT -> WITNESSED` (`AGENTS.md`); ratification stays with Bdo.

## Host capability fallbacks

The preferred Claude host path uses agent teams for coordinated contexts and
cross-session messaging for independently launched sessions. If those host
features are unavailable:

- use ordinary `Agent` subagents for Controller/Orchestrator/Worker/Witness;
- use `scripts/sov_session.py` for live coordination;
- use Console continuity where reachable;
- state plainly in the report that agent teams or cross-session messaging
  were unavailable rather than silently collapsing roles.

The same SOV role contract must remain usable on another model or harness.
