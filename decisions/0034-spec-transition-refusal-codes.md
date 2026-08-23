# 0034 · Two refusal codes added to the SPEC.md transition contract

Status: `PROPOSED · BDO HAS NOT RULED`

A check found this, not a person. `scripts/sov_kernel.py drift` compares the transition
names and named refusal codes stated by `SPEC.md` against
`contracts/kernel-transitions.json` on its first run and reported two disagreements.

## What disagreed

`contracts/kernel-transitions.json` names refusals that `SPEC.md` did not, on two rows
that admit no open reasoned refusal — so the contract could not be reading them as
specialisations of an open clause.

| Transition | `SPEC.md` said | The contract also names |
| --- | --- | --- |
| `admit` | `ADMISSION_REFUSED` | `STALE_STATE` |
| `settle_run` | `STALE_STATE` | `OBSERVATION_MISSING` |

Both are refused by the running kernel. `scripts/sovkernel/transitions.py` returns
`STALE_STATE` when a request declares no pre-state or a pre-state that is not current,
and `OBSERVATION_MISSING` when settlement is requested with no observation or an
unsatisfactory one. `conformance/fixtures/kernel/transition-cases.json` exercises both.

## What changed

`SPEC.md` rows 280 and 287 now name the two codes:

- `admit` refuses with `ADMISSION_REFUSED` or `STALE_STATE`;
- `settle_run` refuses with `STALE_STATE` or `OBSERVATION_MISSING`.

Nothing else moved. No precondition, commit, transition, or other refusal changed.

## Why this direction, and what it costs

The edit only adds declared refusals. A transition that refuses on more named grounds is
tighter, never looser: no request that `SPEC.md` previously refused is now admitted. The
alternative — deleting the two codes from the contract — would have made the kernel
accept requests it currently refuses, which is the direction that loses a control.

The cost is real and is the reason this record exists. `STATUS.yaml` records
`kernel_transition_contract_status: OWNER_ACCEPTED_COMPILED_SPEC`. Bdo accepted that
contract on the representation that it compiles `SPEC.md`. Editing `SPEC.md` so the
contract matches runs the direction of authority backwards: `SPEC.md` governs the
contract, not the reverse. This record is the counter-record. It does not claim Bdo
accepted the change, and `AGENTS.md` still holds — a green check is never authority.

It also costs the evidence. Once `SPEC.md` carries both codes the drift check passes and
the repository holds no trace that the two ever disagreed. The table above is that trace.

## Owner action

`ACCEPT` leaves `SPEC.md` as edited and `kernel_transition_contract_status` meaningful
again. `REJECT` restores the two `SPEC.md` cells and requires the two codes to leave
`contracts/kernel-transitions.json` and `scripts/sovkernel/transitions.py`, which is a
behaviour change in the kernel, not a documentation change.

## Demotion

Defeated by a reading in which `admit` must not refuse on a stale pre-state, or
`settle_run` must settle without an observation. Either would make the kernel wrong
rather than the specification short, and the repair would be to the kernel.

## Sources

- `SPEC.md`, Transition contract, rows `admit` and `settle_run`.
- `contracts/kernel-transitions.json`.
- `scripts/sovkernel/transitions.py`, `_check_pre_state` and `_check_observation`.
- `conformance/fixtures/kernel/transition-cases.json`.
- `scripts/sovkernel/projection.py` and `scripts/sov_kernel.py drift`, the check.
- Raised by session soveraeign-88; recorded by session soveraeign-fb.
