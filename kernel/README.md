# Shared Kernel Reference

Status: `EXPERIMENTAL REFERENCE · BUILT · SELF-TESTED · NOT WITNESSED`

The shared kernel is the cross-cutting foundation `CLASSIFICATION.md` names: it
enforces gates, standing, typed authority, transitions, observation, settlement,
receipts, and retraction across services. It is not a service, a node, or a
second System of Record. This directory holds one executable reference for the
`SPEC.md` Transition contract so that "all services use the same kernel
semantics" is a checkable claim rather than a sentence. Issue #6 owns the
obligation; `decisions/0019-shared-kernel-reference.md` records the boundary.

## What it realizes

| `SPEC.md` transition | Method | Refuses with |
| --- | --- | --- |
| `submit_proposal` | `Kernel.submit_proposal` | `INCOMPLETE_PROPOSAL` |
| `admit` | `Kernel.admit` | `STALE_STATE`, `STANDING_REFUSED`, `ADMISSION_REFUSED` |
| `ratify` | `Kernel.ratify` | `STALE_STATE`, `STANDING_REFUSED`, `AUTHORITY_REFUSED` |
| `attest` | `Kernel.attest` | `STANDING_REFUSED`, `VALIDATOR_UNDECLARED` |
| `make_effective` | `Kernel.make_effective` | `STALE_STATE`, `STANDING_REFUSED`, `POLICY_REFUSED`, `DISSENTED`, `UNATTESTABLE` |
| `begin_run` | `Kernel.begin_run` | `INCOMPLETE_PLAN`, `EFFECT_CLASS_REFUSED`, `AUTHORITY_REFUSED` |
| `report_run` | `Kernel.report_run` | `STANDING_REFUSED`, `STALE_LEASE` |
| `observe_run` | `Kernel.observe_run` | `OBSERVER_NOT_INDEPENDENT`, `OBSERVATION_MISSING` |
| `settle_run` | `Kernel.settle_run` | `STALE_STATE`, `STANDING_REFUSED`, `OBSERVATION_MISSING` |
| `retract` | `Kernel.retract` | `AUTHORITY_REFUSED`, `POLICY_REFUSED` |

`capture_source`, `read_source`, `cross`, and `invoke_model` are not realized
here. They are service and adapter compositions of the primitives above
(`ENGINEERING.md`, Composing larger motion), and `invoke_model` is gated by O12.
`Kernel.transitions()` lists all fourteen legal names and the ten realized ones
so every binding discovers one list (`SPEC.md`, Interface parity).

## What every transition does

1. Opens one `Attempt` with the declared actor, exact inputs, grants, and
   effect class.
2. Checks the caller's declared pre-state digest against the kernel's current
   digest; a mismatch refuses `STALE_STATE` and nothing settles.
3. Evaluates the grant for type, capability, scope, budget, validity, and
   revocation at this moment; budget spend is derived from receipts on record.
4. Commits or refuses, appending exactly one `EventEnvelope` and exactly one
   `Receipt` to the journal. There is no other way to put either on record.

Standing `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE` climbs one rung per
transition. `ratify` never sets effectiveness; `make_effective` requires a
`REPRODUCED` attestation over the claim's exact input digests, so changed
inputs cannot inherit a reproduction. `retract` appends a counter-record, clears
current effectiveness, and leaves every rung, record, and receipt on record.

An executor's report is stored under a current lease fence and settles nothing.
`observe_run` refuses the executor and any observer whose relation is the
executor's report. `settle_run` reads observations, never the report.

## The journal

`Journal` is the reference in-memory realization of the append rule. Each entry
digests its body with the prior entry's digest. `Kernel.audit()` names every
visible defect: a broken chain, an event without a receipt, a receipt without
an event, more than one receipt for one event, a counter-record whose original
is missing, and a record whose in-memory standing or effectiveness disagrees
with what the journal supports. That is how "service writes authoritative state
around the kernel" is exposed rather than prevented. Durable storage behind the
same surface is issue #7.

## Running it

```bash
python -m unittest discover -s kernel/tests -v   # the transition matrix
python scripts/verify.py                          # includes it
```

`kernel/fixtures/transition-matrix.json` declares 39 cases, 12 positive and 27
defeating, at least one of each per realized transition. `kernel/tests/` executes each case
against the declared outcome and reason code, validates every emitted receipt
and envelope against `contracts/receipt.schema.json` and
`contracts/event-envelope.schema.json` through the independent validator in
`scripts/sovticket/jsonschema.py`, and fails if any declared case was not
exercised or any transition lacks its pair.

## Known gaps

| Gap | Observed | Required | Contract |
| --- | --- | --- | --- |
| Services not rebound | `services/asset/` keeps its own transition rules | All services use the same kernel semantics | C1; issue #6 acceptance 5; held issue #8 |
| Durability | In-memory journal only | Committed records survive restart and partial write | SPEC fault model; issue #7 |
| Attestation schema | Attestation fields follow `SPEC.md`; no JSON Schema authored | Historical reproduction and present applicability represented separately | O4 |
| Grant issuance | `register_grant` records a grant; no bootstrap authority attests the first issuer | First attestor authority | O3 |
| Proposed reason codes | `INCOMPLETE_PLAN`, `EFFECT_CLASS_REFUSED`, `STANDING_REFUSED`, `OBSERVATION_MISSING`, `TARGET_UNKNOWN`, `PREDICATE_FAILED`, `PREDICATE_UNRESOLVED` are not in `SPEC.md` | Named refusals comparable across bindings | O10 |
| Scope model | Grant scope is exact, `*`, or a `/`-prefix | Whatever O5 and the Gauge decide | O5 |
| Judgement queue | `UNRESOLVED` settlement is receipted; no persistent pending-right record is created | Pending judgement visible and non-blocking | PROD-I-6 |

These are reference gaps, not reasons to relax `SPEC.md`.
