# Shared kernel witness, 2026-08-23

Status: `WITNESSED AT BUILT · NOT RATIFIED`

Issue #6, branch `feat/6-shared-kernel-transitions`, draft PR #61. The builder
was the interactive Claude session; the witness was a separately launched
`sov-witness` agent given only the clean worktree at commit `681861e`, no
network, no edit rights. This file records the observation and what the build
did with it. A report under `reports/` is evidence, not policy.

## What the witness reproduced

| Claim | Verdict | Evidence |
| --- | --- | --- |
| `verify.py` passes under budget with the kernel suite | reproduced | exit 0, 0.964 s, 51 tests OK |
| lint passes; every kernel module under 300 lines | reproduced | exit 0; largest `base.py` 210 |
| 39 declared cases; coverage test fails on an unexercised case | reproduced | independent count; removing a case from `COVERED` fails the suite naming it |
| every emitted receipt and envelope meets the contracts | reproduced, extended | 167 receipts and 167 envelopes across all tests, zero defects |
| the five #6 defeats are refused or exposed | reproduced | one non-tautological test per defeat; "service writes around the kernel" reproduced with caveat |
| exactly one terminal receipt per attempt | by construction for closing attempts; by test otherwise | `Attempt._close` is the only append path; a crash between open and close leaves nothing |
| standing does not collapse | reproduced | `ratify` never sets `effective`; changed-input attestation refuses `UNATTESTABLE` |

Standing supported by the witness: `OPEN -> BUILT`. Not supported:
`BUILT -> WITNESSED` in the form the build stated, because of the defeats below.

## Undeclared defeats the witness found

| # | Defeat | Closed in the next commit |
| --- | --- | --- |
| 1 | `Kernel.attempt()` + `commit()` forged a `ratify` receipt with no checks; audit was silent | yes: audit requires every `REQUIRED_PASSING` predicate on a committed receipt; a commit over a failed precondition raises |
| 2 | editing `record.input_digests` or `record.scope` in the projection was invisible to audit | yes: audit compares every immutable field of the projected record with its journaled body |
| 3 | `spent()` read the `receipts` dict, so popping one entry re-opened a spent budget | yes: `spent()` and `_last_receipt_for` read the journal |
| 4 | `actor_kind="ROBOT"` and `effect_class="EXTERNAL_WORLD_LATER"` were journaled as contract-invalid records | yes: the kernel raises before opening an attempt; malformed grants are refused at registration |
| 5 | a plan with two addresses and one digest committed with one input silently dropped | yes: `inputs_paired` refuses `INCOMPLETE_PLAN` |
| 6 | observer independence is a string blacklist; prose that admits relying on the report passes | no: the kernel cannot verify prose; named in `kernel/README.md` gaps |
| 7 | `settle_run` input-state check compares a caller declaration to itself on the honest path | no: inherent to an in-memory reference; named in gaps |
| 8 | an exception between open and close leaves no receipt and no audit defect | no: queued as judgement 4 in `decisions/0019` |
| 9 | `TARGET_UNKNOWN` had no fixture case | yes: `KERNEL-ADMIT-DEF-UNKNOWN` and a reason-code coverage test |
| 10 | `REPRODUCED` beside `UNATTESTABLE` over exact inputs becomes effective | no: policy question, queued as judgement 5 |

Residuals the witness named and this build left as they are: founding scenario
010 is `SEED` and not consumed by the oracle; no service imports the kernel;
`kernel/pyproject.toml` carries a `setuptools` build-system line without a
decision record (as does the Asset Service).

## Checks after the closing commit

```text
python scripts/verify.py    PASS, under the 3 s budget; kernel suite 60 tests OK
python scripts/lint.py      PASS; every kernel module under 300 lines
```

Standing after this file: still `BUILT`. The closing commit was written by the
builder, and a build cannot witness itself. The next witness step is the same
command set over the new head, with the ten rows above as the checklist.
