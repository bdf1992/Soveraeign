# Independent observation of the origin/main merge, 2026-08-23

Status: `OBSERVED BY A NON-BUILDER · NOT A WITNESS-SEAT DEPOSIT · NOTHING RATIFIED`

Three Claude sessions built concurrently in one working tree today and reconciled
`feat/federation-harness-and-hardening` with `origin/main`. This records what an
independent path shows, so the merge carries something other than three self-reports.

The observer built none of the work below except where named. It does not occupy the
Witness seat (`CLAUDE.md`, Who Claude is here), so this proposes no standing change; a
seated witness pass is still owed.

## What landed

`bb85ddc`, parents `cf587d5` and `f461889`. Forty-six commits on the branch and
nineteen on main reconciled across six conflicted paths.

| Session | Built |
| --- | --- |
| `soveraeign-fb` | four conflict resolutions, decision renumber `0021/0023/0024` to `0030/0031/0032`, `decisions/0033` closing the founding docket, `decisions/0034` widening two SPEC refusal cells, `scripts/sovkernel/derivation.py` and the `drift` gate |
| `soveraeign-88` | `scripts/verify.py` and `contracts/README.md` resolutions, the `sovticket` to `sovkernel` import repair in three files, `adapters/ollama/invoke.py` and nineteen cases |
| `soveraeign-54` | `contracts/seat-message.schema.json`, its fixtures, `decisions/0035` |
| this observer | `72bf9e5`, `5c58cd7`, `cf587d5` pre-merge, and `ecba440` — **not observed here** |

## Observations

`python scripts/verify.py` passes: 17 checks, 1.188s wall against the 3.000s budget,
13 skips each carrying a stated reason. `python scripts/lint.py` passes with one named
debt. `python scripts/sov_kernel.py drift` passes: 14 transitions and 18 refusal codes
agree between `SPEC.md` and `contracts/kernel-transitions.json`.

Beyond re-running the builders' own suites:

- **The `SPEC.md` edit is additive.** Diffed against both merge parents. It adds
  `STALE_STATE` to `admit` and `OBSERVATION_MISSING` to `settle_run` and changes no
  other cell. No commit path widened, no precondition relaxed. Both codes are carried
  in `contracts/kernel-transitions.json`, both have cases in
  `conformance/fixtures/kernel/transition-cases.json`, and `decisions/0034` records the
  edit as made at Control resolution.
- **`invoke_model` refuses before the crossing, not after.** The claim is structural,
  not asserted: `BoundaryRefusalsPrecedeTheCrossing.assert_refused_without_sending`
  checks `transport.posts == []` on an injected transport, so a case cannot pass while
  the input has left. Six refusals are covered that way, including a cloud-served model
  declared local under `LOCAL_ONLY`.
- **`services/record/` is in the merge commit.** Issue #7 runs on this branch: eight
  cases including the witness walk the issue declares.
- **No decision number is duplicated**, and `open_decisions` is `[]`.

## Residuals

- `ecba440` is built and self-tested by this observer and therefore unobserved. It
  changes what `apply`, `verify` and `activate` do on a host without POSIX ownership,
  and it changes how every custody path in every manifest is validated. Someone else
  should look at it.
- `scripts/witness_infrastructure.py` sits at exactly 300 lines against the 300-line
  limit. The next line added there fails the gate.
- Three writers shared one working tree with no lease. Nothing in the repository
  prevented it, detected it, or would have recorded it; it was resolved by the sessions
  messaging each other after the collision was already underway. That is a gap in the
  operating loop, not in any of the work above.
- Everything named here is `BUILT` or self-tested. No standing changed.
