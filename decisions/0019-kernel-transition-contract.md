# 0019 · Kernel transition contract

Status: `PROPOSED · OWNER RATIFICATION PENDING`

## Decision

Compile the `SPEC.md` Transition contract into two machine-readable kernel
contracts: `contracts/kernel-transitions.json`, which declares the fourteen
transitions with their preconditions, commit outcome, and refusal codes, and
`contracts/transition.schema.json`, which types a request to perform one.

Move the bounded JSON Schema validator from `scripts/sovticket/jsonschema.py`
to `scripts/sovkernel/jsonschema.py`. It was never ticket-specific; it was a
kernel primitive living in the first package that happened to need it.

## Why the table was the gap

`SPEC.md` already says every sentence this table now states. Every transition
checks its declared pre-state. A stale pre-state cannot settle. Executor
completion is a report, not settlement. `report_run` stores the report and does
not settle it. `settle_run` needs a satisfactory observation, and `observe_run`
refuses an observer who is not independent.

None of it was compiled. So each participant restated the same semantics
privately and differently:

- `scripts/sovticket/transitions.py` carries its own transition table with its
  own refusal codes for tickets.
- `services/asset` enforces lease fencing, TTL expiry, and `STALE_LEASE` in
  SQL, and separately keeps `report` at `ATTEMPTED` so that `observe` stays a
  distinct step.

Both are correct. Neither can be checked against the other, and nothing stops a
third participant restating them a third way. Issue #6's fifth acceptance
criterion - all services use the same kernel semantics rather than private
transition rules - was unmeetable while the semantics existed only as prose.

## What this decision does not do

It does not migrate the ticket workflow or the Asset Service onto the kernel
table. Both keep working exactly as they do today. Migration is the next
bounded operation and is where the criterion is actually met; this decision only
makes the target exist.

It does not author an attestation contract. `attest` and `make_effective` appear
as declared rows because `SPEC.md` declares them, but O4 blocks the attestation
record schema and nothing here authors one.

It grants nothing. A permitted decision means the declared preconditions hold.
It never means the transition happened, and never that the caller may make it
happen.

## Consequences

- The kernel gains its first offline fixture corpus,
  `conformance/fixtures/kernel/transition-cases.json`: sixteen cases, four
  positive and twelve defeating, running in `scripts/verify.py` and the `blue`
  lane. The three defeating cases named on issue #6 are `K-005` (a stale
  pre-state settling), `K-006` (a successful executor report offered as its own
  observation), and `K-007` (a report settling itself, which is how a
  participant settles around the kernel).
- Every refusal the evaluator can raise has at least one case proving it fires.
  Seven deliberate weakenings of the table were each caught by exactly the cases
  that claim to cover them.
- A case states what the kernel can see in `current`. A key omitted there is
  unknown rather than satisfied, so the check that depends on it is skipped
  rather than silently passing.
- `verify_bootstrap.py` now asserts both new contract files exist and parse.
- Verification runs green at 0.967s against the 3.000s budget.

## Residuals

- Six of the fourteen declared transitions are exercised by the corpus. The
  remaining eight are declared and unexercised, which the selfcheck reports on
  every run rather than leaving to be discovered.
- The two private implementations are not rewritten onto the kernel. They are
  bound to it instead, by `contracts/kernel-parity.json` and the `parity` check:
  five declared correspondences, each driven on both sides and compared. This is
  what `SPEC.md` means by admitting reference implementations as participants
  tested against the contract, and it is how the fifth acceptance criterion on
  issue #6 is met without a rewrite standing in as its own evidence.
- `ratify` names `pre_state_digest` both as a declared precondition, because
  `SPEC.md` lists it, and as a typed request field, because the kernel checks it
  structurally. The duplication is deliberate but ungainly.
- Vocabulary drift, queued rather than renamed: `CLASSIFICATION.md` admits actor
  kind `SYSTEM`, and `contracts/ticket-transitions.json` admits only `HUMAN`,
  `MODEL`, and `WORKER`. `transition.schema.json` follows `CLASSIFICATION.md`.
  The two contracts now disagree, which is a judgement item for Bdo under O9.

## Open review

The table, the request shape, and the relocation of the validator are proposed,
not ratified. `SPEC.md` is not frozen (O10) and the vocabulary is not ratified
(O9), so a mismatch found against this table queues as a judgement item rather
than a rename. `contracts/` is owner-reviewed; this reaches `RATIFIED` only
through owner judgement, never through a green check.

## Source and authority

- `SPEC.md` Transition contract, fault model, effects, and the `Run` and
  `Observation` objects
- `CONTRACT.md` C1-C15
- `CLASSIFICATION.md` actor kind, authority type, outcome, and event phase
- `AGENTS.md` change protocol, standing lifecycle, and evidence and standing
- `services/asset` lease fencing and the separation of report from observation
- issue #6, `BIT-GROUND-KERNEL`, and its three declared defeating cases
- Bdo's 2026-08-23 direction to take the head of the takeable queue rather than
  continue working around it
