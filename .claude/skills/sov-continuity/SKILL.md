---
name: sov-continuity
description: Operate the Console Service continuity path - read what landed while this operator was away, post a message that a later session or another operator will receive, and read a thread through this binding. Load when a task mentions "sov-continuity", "continuity", "cross-session", "session context", "carry this to the next session", "leave a note for Bdo", "what did I miss", "unseen posts", "console session", "post to a thread", "open a thread", "unread cursor", or when the session-start briefing named a thread and the work continues in it. This is the operating skill for a built service; sov-console is the design skill for the same boundary and owns charter, schema and fixture work. Use sov-console to change what the service is, and this skill to use it.
---

# sov-continuity

## What this is for

A Claude Code session ends and everything in its context goes with it. The
Console Service is where anything that must outlive it goes: a threaded record
that a later session, or Bdo, or another agent, reads back.

Two different things are on offer and they are worth keeping apart.

- **Cross-session**: what landed while this operator was not in a session. The
  session-start hook already asked for this and put it at the top of the
  context. Nothing to do unless it named something.
- **Cross-session message**: a post you write now, addressed to whoever reads
  the thread next. This is the part you have to do deliberately.

## Before anything else

The session-start briefing is a projection, not the record. It is a rebuilt
read model over the Record Service journal and it says so. If it disagrees with
a thread you read directly, the thread read wins, and the disagreement is worth
reporting rather than working around.

If the briefing said continuity was unavailable, the console store is missing or
the service failed to run. Say so plainly and carry on; do not reconstruct
continuity by guessing from the repository.

## The machine path

Every operation goes through one CLI. There is no second way in, and a binding
that wrote console state directly would be the defeating case in
`services/console/conformance/006-thread-post-parity.yaml`.

```
PYTHONPATH=services/console/src;services/record/src \
python -m soveraeign_console_service.cli --root .local/console <command>
```

On Windows separate the two paths with `;`; elsewhere with `:`. Every command
prints one JSON object, refusals included. Exit codes: `0` committed, `2`
refused, `3` unknown record, `1` usage error.

Ask the service what it can do rather than trusting this file to stay current:

```
... cli operations --operator <operator>
```

The operator is required and the answer costs a live `read:session` grant scoped
to that operator. Bdo ruled on 2026-08-25 that every built console operation
checks the authority it declares, so asking anonymously is refused rather than
answered narrowly.

## Posting a message forward

```
... cli post --operator <operator> --session <console-session> \n      --thread <thread> --body "..." --mention Bdo
```

The console session id is in the session-start briefing. `--operator` must be the
session's own operator: holding a session id is not the same as being the operator
it belongs to, and since 2026-08-25 the service refuses the mismatch rather than
signing the post with the owner's name. `--mention` names an operator so the post
surfaces for them specifically; it changes nothing about authority.

**A post that makes a claim needs a proposal.** A `MODEL` post with `--claims`
and no `--proposal-id` is refused with `CLAIM_WITHOUT_PROPOSAL`, and the refusal
is recorded. This is not a formality to route around: a model's assertion is a
proposal until something outside the model settles it. If you are about to claim
something and have no proposal id, either write the post without the claim, or
say plainly that the claim needs one.

Three ordinary refusals, all of them recorded:

| Reason code | What actually happened |
| --- | --- |
| `NO_LIVE_GRANT` | This operator has no live grant for what it asked - `post:message` for a post, `read:thread` for a read, `read:session` for discovery or continuity. Bdo grants it; you cannot grant it to yourself, and since 2026-08-25 the service refuses the attempt rather than recording it. The message names the capability and not the scope, because a scope is an operator id, a channel or a thread and a caller holding nothing should not learn one. Ask Bdo which scope you need. |
| `ACTOR_ATTRIBUTION_MISMATCH` | The session named is not yours. Holding a session id is not being its operator. |
| `SESSION_CLOSED` | The console session ended. Open a new one. |
| `THREAD_ARCHIVED` | That thread is closed to new posts. Open a new thread. |

## Reading

```
... cli read-thread --operator <operator> --thread <thread> --binding claude-code
... cli session-context --reader <operator>
```

Both name who is reading, and both cost a grant: `read:thread` scoped to that
thread, and `read:session` scoped to that operator.

`read-thread` returns posts in append order with a content address and digest
each. Read a body with the address under `.local/console/`. A post is never
rewritten: a correction is a new post, and the wrong one stays readable.

## What this skill will not do

- Grant authority. Grants are journal records made by Bdo.
- Settle anything. Every console record enters at `RECORDED` and stays there;
  admission and ratification are kernel transitions the console does not own.
- Treat the projection as the record. If you need certainty, read the thread.

## Where the pieces live

| Thing | Path |
| --- | --- |
| Service | `services/console/src/soveraeign_console_service/` |
| Machine interface | `cli.py` in that package |
| Refusal vocabulary | `refusals.py` in that package |
| Session hooks | `.claude/hooks/console_session.py` |
| Store (never committed) | `.local/console/` |
| Design work on the boundary | the `sov-console` skill |
