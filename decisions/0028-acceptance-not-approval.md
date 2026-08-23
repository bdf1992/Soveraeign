# 0028 · The owner gate is acceptance, not permission

Status: `OWNER-DIRECTED · PRESENTED FOR ACCEPTANCE AS acceptance/A3.json`

Numbering note: 0022 through 0027 are taken by records on unmerged branches, and
`0023-acceptance-not-approval.md` on `feat/acceptance-not-approval` is an earlier
prose draft of this same direction. This record takes 0028 to avoid a fourth
collision and supersedes that draft; the drain it carried is restated, extended,
and made checkable in `0029`.

## Decision

An owner seat accepts or rejects a finished, evidenced result. It does not
approve work before the work happens.

Work whose effect class is `RECORD_LOCAL` or `RESOURCE_CONSUMPTION`, and whose
change a counter-record or a revert undoes, proceeds without asking anyone. A
seat chooses, sequences, implements, tests, repairs, refactors, branches, and
presents. Stopping to ask permission for that work is refused by
`PREAPPROVAL_REQUESTED`.

A transition may wait on an owner seat only for one of seven reasons:
`EXTERNAL_WORLD_EFFECT`, `IRREVERSIBLE`, `PUBLICATION`,
`OWNER_IDENTITY_OR_NAMING`, `SECRET_EXPOSURE`, `DESTRUCTIVE_ADMIN`, or
`RESOURCE_COMMITMENT`. The list is exhaustive and lives in
`contracts/acceptance-policy.json`. Wanting an owner's opinion is not on it.

## Owner is a seat, and acceptance happens one edge up

`decisions/0020` defines `owner(X)` as the seat that issued X's grant and settles
its receipts: one edge up, never global, never chaining. That record specified
the topology and left it unapplied. This decision applies it.

`contracts/seat-registry.json` is the live view. Acceptance resolves through it:
a result presented by seat X is accepted by `owner_seat(X)` and by no other seat.
A worker's report is settled by the orchestrator that leased it. An
orchestration's operation is settled by the control seat that launched it. The
root seat accepts what the control seat presents and never reaches past it to
settle a worker's report.

Two further conditions bind. The accepting seat's `settles` list must contain the
claim's type, so a control seat that settles `VERIFICATION` may confirm that a
check held and may not settle what the product is for. And the seat must have a
recorded occupant, because authority is exercised by an attributable actor and
never by a position on a chart.

A work seat settles nothing above its own execution. What to inspect, which legal
operation to attempt, how to sequence reversible changes, when to abandon a
failed line: that is the seat's own. It needs no packet, and presenting it upward
is refused by `SELF_DIRECTION_PRESENTED`.

## The packet

An acceptance request arrives as a presentation, never as a bare question. Each
one lives at `acceptance/<id>.json` against
`contracts/acceptance-packet.schema.json` and carries:

1. **claim** — the one thing being accepted, in a sentence.
2. **subject** — the artifact and the standing it moves between.
3. **the acceptance edge** — presenting seat, accepting seat, claim type.
4. **visible result** — an exact command the owner can run, what it shows, what
   to expect.
5. **evidence** — addresses and digests, not adjectives.
6. **why it matters** — one connection to the accepted direction.
7. **what could defeat it** — the strongest known failures. An empty list is
   refused: a result with no stated defeater has not been examined.
8. **residuals** — what is known to be unfinished.
9. **on accept / on reject** — exactly what changes either way.

`python scripts/sov_accept.py present <id>` renders it. The presentation is meant
to make the call obvious from the output before anyone reads internals, which is
a demand for clarity and not a licence to omit a residual. A packet that hides a
defect to look finished is a defect against this contract.

## The audit

`python scripts/sov_accept.py audit` runs inside `scripts/verify.py`. It fails
when a question sits in the register with no ruling, no presentation, and no
admissible hold; when a hold names no declared reason, no single transition, or
nothing that stays reachable; when a standing default names no condition that
would overturn it; when a presented packet is incomplete or names no defeater;
or when a packet routes to a seat that does not own its presenter.

Before this existed, an agent could stop on "ask Bdo" for free. That is now a
build failure.

## Consequences

- Seventeen founding questions leave the owner queue. `0029` records what each
  became.
- `WITNESSED -> RATIFIED` requires an `acceptance_packet` in its evidence
  (`contracts/ticket-transitions.json`), so ratification cannot be asked for as a
  bare question. `TC-017` proves the refusal.
- `WITNESSED` stops being a waiting room in
  `contracts/ticket-queue-policy.json`; its next action is to present.
- `AGENTS.md` Authority is rewritten to the seat reading, applying the amendment
  text `0020` held.
- A new `/acceptance` directory boundary holds packets and never holds standing.

## What this decision does not do

- It does not weaken any evidence rule. A build still cannot witness itself, no
  seat settles its own output, and a green run is still not authority.
- It does not admit external-world effects. Three of them are recorded as holds
  and stay held.
- It does not verify identity. A seat claim is still attributable and unverified;
  that is `O3`, ruled in `0029` and unbuilt.
- It does not accept itself. This record is presented as `acceptance/A3.json` and
  stands at proposal until the root seat acts.

## Demotion

Demote this policy if the absence of pre-approval becomes cover for external
effects, owner impersonation, evidence inflation, or self-ratification; or if
acceptance packets become presentations that omit their defeaters. Both failures
are visible in the ledger and in the packets themselves.

## Source and authority

Bdo's direction, 2026-08-23: the human gate should only be acceptance, not
approval; acceptance requires evidence and a presentation that is engaging and
nearly self-evident from the output. Corrected the same day: owner is relative,
not a person — Bdo may own a controller while a worker owns its own work and
decisions. The seat reading in `0020` is that correction, and this record applies
it rather than restating it.

Drafted and built by the control seat. Presented, not settled.
