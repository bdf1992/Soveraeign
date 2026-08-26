---
name: sov-hypervisor
description: Launch and inspect named Claude sessions on declared worktrees without a human opening a terminal or pasting a bootstrap prompt. Load when sustained work needs more than one independent session, when a campaign needs lanes started on exact branches, when a launched session did not register or acquired a duplicate `session-*` identity, or when a task names "sov-hypervisor", "hypervisor", "launch plan", "campaign lane", "fleet lane", "launch a session", or "start a witness session". Covers plan grading, launch, live status and the declared refusals. Not for deciding what the launched sessions should do - that is the `sov` profile and the domain skills - and not for the session registry itself, which is `scripts/sov_session.py`.
---

# sov-hypervisor

## Purpose

Establish where and how a Claude session runs. Nothing else.

`sov` decides what work to coordinate. The hypervisor deterministically puts a
session in the right tree, on the right commit, under one name, holding its
orders. Neither is an authority layer, and the second is host plumbing:
`AGENTS.md`, Local orchestration harness. A lane gets no standing, no grant and
no seat from having been launched here.

## What it removes

A campaign that had already built the right worktrees still needed Bdo to open
three terminals and paste a loader line into each. Sessions started from inside
another Claude session did not reliably persist, register, or receive a
cross-session bootstrap message.

Orders now travel as the opening prompt of the process. That is the only
channel that cannot miss a session which does not exist yet. `SendMessage` is
for coordination after launch: a changed assumption, a moved dependency, a peer
that landed.

## Commands

    python scripts/sov_hypervisor.py plan <plan.json>       grade every lane
    python scripts/sov_hypervisor.py launch <plan.json>     start the ready ones
    python scripts/sov_hypervisor.py status <plan.json>     what is live now
    python scripts/sov_hypervisor.py selfcheck              prove the refusals

`plan` and `status` start nothing. `launch --dry-run` writes each lane's script
and prints its argv without running it; read that before a first launch on a
new plan.

## A plan

Host configuration, not governed state. Keep it under `.local/`.

```json
{
  "campaign": "kernel-dogfood-01",
  "sessions": [
    {
      "name": "fleet-alpha",
      "worktree": "C:/Users/bdf19/Desktop/soveraeign-fleet-alpha",
      "expected_ref": "feat/sov-control-mesh",
      "mode": "write",
      "agent": "sov",
      "model": "opus",
      "orders_file": ".local/campaign/alpha.md",
      "remote_control": true
    }
  ]
}
```

`expected_ref` is a branch name or a commit prefix of at least seven
characters. `mode` is `write` or `read-only`; a read-only lane is started in
plan mode and must be sitting on a detached commit, so a witness cannot land
what it reviewed. `orders_file` is resolved against the lane's worktree.

## Before launching

- Run `python scripts/sov_session.py brief` and read who is already live.
- Reuse the worktrees that already exist; `python scripts/sov_session.py
  worktree list` shows them. Take git's own paths in Windows form
  (`C:/Users/...`), because a POSIX-style path silently creates a second tree
  at `C:\c\Users\...`.
- Choose the smallest useful number of lanes.
- Give every lane an exact ref. A lane with no ref is refused.

Never open a terminal by hand and never paste a bootstrap prompt while this is
available.

## Refusals

Each is a precondition checked before a process exists.

| Refusal | Meaning |
| --- | --- |
| `PLAN_UNREADABLE`, `PLAN_INVALID` | the plan is absent, is not JSON, or declares no sessions |
| `LANE_NAME_INVALID`, `LANE_DUPLICATED` | a name that cannot address a lane, or one declared twice |
| `WORKTREE_MISSING` | the declared path is not a git working tree |
| `REF_MISMATCH` | the tree is not on the ref the lane named |
| `READ_ONLY_LANE_ON_BRANCH` | a read-only lane pointed at a writable branch |
| `ORDERS_MISSING` | no orders, which is a lane waiting for a human to paste one |
| `LANE_OCCUPIED` | that name is already live; end it or choose another |
| `SESSION_REGISTRATION_TIMEOUT` | the process started and never registered |
| `SESSION_REGISTERED_ELSEWHERE` | it registered against a different tree |

A launched process is not a live lane. `READY` is reported only after the
registry shows the expected name, live, in the expected tree.

## What it does to a session

Sets `SOV_SESSION` so the name Claude displays, the registry name, the Remote
Control name and the lane are one string. Sets
`CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1` so a session launched under an
inherited Claude environment stays persistent and resumable.

It removes nothing from the environment. A lane that erased its parentage to
look independent would be lying about where it came from; persistence is bought
with the documented override instead.

## State

There is no hypervisor journal and no second event log. Liveness, trees,
branches and claims all come from the existing registry at
`scripts/sov_session.py`. `status` is a join of the plan against that registry
and says so on every render:

    HOST COORDINATION PROJECTION - NO SOVERAEIGN STANDING

## Related

- `scripts/sov_session.py` owns the registry, claims, worktrees and the brief.
- `.claude/hooks/session_registry.py` registers a session at SessionStart and
  honours `SOV_SESSION`; a session started before that repair still carries a
  duplicate `session-*` row, and `status` names it under `ALIAS`.
- `scripts/tests/test_sov_hypervisor.py` holds every case, and launches nothing.
