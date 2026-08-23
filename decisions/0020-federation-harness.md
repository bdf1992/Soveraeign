# 0020 · Local federation harness and role-based agents

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Renumbered twice, for the same reason both times: a locally drafted record
collides with one merged upstream in parallel, and the unmerged record moves.
`0013` went to `decisions/0013-domain-mapped-sdlc-loop.md`; `0018` then went to
`decisions/0018-verification-engagement-kind.md`, merged via pull request #60.
`0019` is claimed by the verification-channel projection, so `0020` is the first
number free of all of them. See `reports/2026-08-23-merge-readiness.md`.

## Decision

Operate model agents on this repository through a local Claude Code harness
under `.claude/`, structured as stable roles rather than per-domain agents:

- Roles: `sov-worker` executes one bounded operation; `sov-orchestrator`
  plans; `sov-witness` verifies through an independent path and may dissent;
  `sov-controller` dispatches and aggregates for headless runs.
- Domain specificity lives in one `sov-<domain>` skill and one `sov-<domain>`
  workflow per domain concern (governance, contracts, conformance, asset,
  proofing, byom, verification). Adding a domain adds a skill and a workflow,
  never an agent.
- Cross-cutting capabilities are also skill plus workflow on the same roles:
  `sov-qa` (independent observation sweep) and `sov-scribe` (templated
  writing with independent critique).
- The root `sov-federation` workflow dispatches domain workflows and
  aggregates reports and the judgement queue for Bdo.

## Consequences

- The harness is host plumbing: operating it grants no authority, and nothing
  in `.claude/` competes with the governing document set.
- Harness runs honor the STATUS.yaml open decisions, queue judgement-typed
  questions for Bdo, cap standing proposals at `BUILT -> WITNESSED`, keep
  builder and witness as different agents, and leave the working tree
  uncommitted for review.
- `.claude/README.md` owns the harness layout; `AGENTS.md` remains the
  authority on agent conduct.
- This record is a proposal; Bdo's ratification decides whether the harness
  pattern becomes repository policy.

## Source and authority

- `AGENTS.md` operating contract: authority, evidence and standing, directory
  boundaries, context hygiene
- `STATUS.yaml` open decisions O1-O12 and protected boundaries
- `CLASSIFICATION.md` role vocabulary
- Bdo's 2026-08-22 instructions to create per-domain workflows and skills,
  then to consolidate agents into stable worker/orchestrator/controller roles
  with QA and prompting carried as cross-cutting workflow plus skill
