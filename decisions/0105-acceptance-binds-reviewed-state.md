# Bind an acceptance decision to the reviewed state

Status: `PROPOSED`

No owner decision, grant, or product standing changes here.

Bdo requested finished product versions that can be accepted asynchronously, then directed
the acceptance repair to proceed on 2026-09-09. This change serves `GROUND-005` and
`PROMISE-16`: a consequential decision keeps the exact state and meaning it acted on.
It also supports `GROUND-015` by making a completed decision recoverable after its
recording process disappears. It does not claim that the full commissioning circuit is built.

The existing CLI could present a file, accept after its bytes changed, and append the same
decision twice before someone moved the packet into `acceptance/accepted/`. Its repeat test
only covered a packet that had already been moved. The action did not execute a standing
change or deployment; the demonstrated duplicate was a decision record.

## Choice

`present` prints a `--review` token identifying the complete canonical JSON packet and the
SHA-256 of its single local subject file. JSON whitespace has no meaning; every field,
including residuals and the consequence of acceptance, does. Actions require this token
and refuse changed packet or subject content. A version manifest may be the subject, but
this patch does not independently verify every artifact a manifest names.

The owner action reads prior decisions, checks the selected presentation and existing seat
rules, and records under one OS lock. The ledger remains `.local/acceptance/ledger.ndjson`.
Each fresh row includes the reviewed packet and review identity. Writing replaces the file
atomically with its exact old bytes plus one complete row, synced before success is reported.
No historical byte is rewritten. A process crash releases the lock; an incomplete or
unreadable existing ledger refuses recording rather than disappearing from duplicate checks.

An exact retry returns its original receipt, including its original timestamp, even after
the subject or queue changes. Retry identity includes the packet id, review token, action,
accepting seat, actor and note. Different content is a conflict, not a retry. A changed mind
uses a new packet under the existing policy; the prior decision remains evidence.

Old packets remain readable, including descriptive multi-document subjects. Old decisions
block reuse of their packet ids without being assigned invented review digests. A fresh
action over a descriptive or unavailable subject requires a concrete file presentation.
The existing packet schema stays compatible; the new review schema owns only review identity.

This is repository acceptance tooling. It records a decision without performing its stated
consequence. It adds neither authentication for caller-supplied actor names nor product
console judgement operations. A token identifies reviewed state; possession grants no right.
Publication, ratification and any external consequence retain their existing authority checks.

## Change protocol and evidence

Effect class: `RECORD_LOCAL`, with bounded engineering `RESOURCE_CONSUMPTION`.
Affected contracts: acceptance policy, acceptance review schema and acceptance fixtures.
Preconditions: one selected valid queued packet, existing seat rules and a matching review
token; an exact retry instead resolves its already-recorded receipt. All tests use fictional
actors and temporary stores, including concurrent CLI processes and interrupted recording.

Expected result: changed state is refused; repeated delivery returns one decision; historical
records remain readable. Defeating cases are exercised in `scripts/tests/test_sov_accept_replay.py`
and the acceptance review fixture. Passing tests establish a build claim, not owner acceptance.

Rollback: revert implementation and contract changes while retaining recorded decisions.
An older writer does not understand the transaction rule and must not write concurrently
with the new one. The guarantee is local process interruption and serialized participating
writers; distributed filesystems, hostile filesystem writers and machine power-loss recovery
are outside this patch. A decision binds the bytes read, not a claim that nobody can edit the
working file after that read. Its eventual consequence must use and check the pinned state.
