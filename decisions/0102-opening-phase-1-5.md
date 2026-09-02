# 0102 · Opening Phase 1.5 is one command, staged here

Status: `PROPOSED · DRAFTED AT OWNER DIRECTION · ACCEPTANCE PENDING`

This record stages the Phase 1.5 opening packet. It does not open a phase,
change standing, or move `contracts/phases.json` or `STATUS.yaml`. Nothing
here has phase standing until seat:root runs the command this record names.

## What is staged

`contracts/phase-1-5-opening.json` pins three documents by sha256 digest as
they stand on this branch, and names the exact phase record `phase:1-5 ·
Phase 1.5 - Operational Commissioning` would carry:

| Document | Owns |
| --- | --- |
| `PRD.md` | the P15-Q1 through P15-Q4 qualification profile |
| `SPEC.md` | the twelve P15 commissioning predicates |
| `contracts/phase-1-5-phase-ii-horizon.md` | the campaign rationale and boundary |

The packet's four exit clauses, `PHASE-1-5-X1` through `PHASE-1-5-X4`, quote
`PRD.md`'s P15-Q1 through P15-Q4 verbatim and carry `NOT_EARNED` with a live
custody each:

| Clause | Restates | Held by |
| --- | --- | --- |
| `PHASE-1-5-X1` | P15-Q1 Fresh participation | `custody:phase-1-5/fresh-participation` |
| `PHASE-1-5-X2` | P15-Q2 Evidenced and fairly judged work | `custody:phase-1-5/evidenced-judgement` |
| `PHASE-1-5-X3` | P15-Q3 Discovery, continuity, and reuse | `custody:phase-1-5/discovery-reuse` |
| `PHASE-1-5-X4` | P15-Q4 Definition recurrence and institution-neutral composition | `custody:phase-1-5/definition-recurrence` |

`contracts/custodies-phase-1-5.json` holds those four custodies, each naming
the exact P15 predicates it carries to closure and a closure check command,
`python scripts/sov_opening_readiness.py --instrument --json`. All four carry
`status: PROPOSED` and no work lease; nothing is drawn under any of them yet.

## The one command

`scripts/sov_open_phase.py` reads the packet and recomputes every pinned
digest against the working tree. With no arguments it prints the exact change
it would make and writes nothing, exiting non-zero with a named reason if a
pinned digest, the predecessor phase, the `STATUS.yaml` line, or a custody id
no longer matches what the packet assumes.

**`scripts/sov_open_phase.py --apply` is the only path that writes**, and it
is seat:root's act, not this record's:

- appends the pinned phase record to `contracts/phases.json`;
- sets `phase:i`'s `succeeded_by` to `phase:1-5`;
- sets `STATUS.yaml`'s `phase` to `PHASE_1_5_OPEN`;
- merges the four staged custodies into `contracts/custodies.json`.

`scripts/sov_open_phase.py --apply --dry-run` computes the identical write and
prints it, proven by `scripts/tests/test_sov_open_phase.py` to leave
`contracts/phases.json` and `STATUS.yaml` byte-identical.

## What this record does not do

This record does not rule that Phase 1.5 should open now, does not change
`STATUS.yaml` or `contracts/phases.json`, and does not create a live custody.
Preparation was already recorded as having no phase standing in
`contracts/phase-1-5-phase-ii-horizon.md`; this record adds the exact,
pinned, one-command opening act that document said a future root opening
would need, and nothing more.
