# Oracle self-test hardening, 2026-08-23

Status: `BUILT · SELF-TESTED · NOT WITNESSED · NOTHING RATIFIED`

Conformance-domain operation CONF-TEST-HARDEN, named as the domain's clean first move in
`reports/2026-08-22-baseline.md`. One session held the controller role and did the work
itself; no independent witness has run. A build report never witnesses itself.

Second operation of the day; the first is `reports/2026-08-23-line-endings.md`.

## Change protocol record

1. **Requested outcome and current state.** The conformance domain exists so that no
   participant is qualified by its own self-report. `conformance/run.py` derived every
   defect from observation records and never read a participant verdict field, which was
   the guarantee it was built for. But the step *before* evaluation, indexing the
   submitted report by `case_id`, was a bare dict comprehension that trusted whatever
   shape arrived.
2. **Affected.** `conformance/run.py` (loader and one new refusal path),
   `conformance/tests/test_oracle.py`, `conformance/README.md`. No requirement predicate,
   no check function, no control observation, no scenario narrative.
3. **Preconditions and expected observable result.** Before: `python scripts/verify.py`
   green, oracle `SUITE PASS cases=20 coverage_gaps=0`, 5 oracle self-tests. Expected
   after: identical suite verdict on honest input, `SUITE INVALID` on an unreadable
   report, and defeating tests for each hole.
4. **Effect class.** `RECORD_LOCAL`.
5. **Rollback.** Revert the three files. No contract, fixture, or standing changed.

## What the probe found

Four holes, probed against the participant-binding path before any change, using an honest
report built from the repository's own positive controls:

| Probe | Before | After |
| --- | --- | --- |
| honest report | `SUITE PASS cases=9`, exit 0 | unchanged |
| failing observation, then a duplicate `case_id` carrying a passing one | **`SUITE PASS cases=9`, exit 0** | `SUITE INVALID`, exit 1, reason names the repeated id |
| entry with no `observed` key | `KeyError: observed`, no report at all | `SUITE INVALID`, exit 1 |
| `observed` is a string, not an object | `AttributeError: str object has no attribute get` | `SUITE INVALID`, exit 1 |
| report is an object carrying its own `"suite": "PASS"` | `TypeError: string indices must be integers` | `SUITE INVALID`, exit 1 |

The second row is the one that mattered. Indexing was last-wins, so a submitter could
send the honest failing observation and a fabricated passing one under the same
`case_id`, and the oracle would silently evaluate the second and report the suite green.
Nothing in the output revealed that ten observations had been supplied for nine cases.
That is the verdict passing from the oracle to the submitter, which is the single thing
this domain exists to prevent.

Rows three through five are contract violations of a different kind: `conformance/README.md`
already reserved `INVALID` for "the case or participant report cannot be evaluated", and
the runner produced a traceback and no report instead. A witness reading a crashed run
cannot tell a broken participant from a broken oracle.

## What changed

| Artifact | Change |
| --- | --- |
| `conformance/run.py` | `observations_by_id` now validates the report envelope and raises the new `ObservationError`: array shape, non-empty string `case_id`, `observed` object, no repeated id. The case file is held to the same reading, so a duplicated control id is refused too |
| `conformance/run.py` | new `refuse()` emits `SUITE INVALID` with the reason in both text and `--json` form and exits non-zero, the verdict README.md already reserved and the runner never produced |
| `conformance/tests/test_oracle.py` | 5 tests to 17. Three new classes: report reading (7 defeating cases), smuggled verdict fields (2, sweeping all nine checks), participant run verdicts (3, end to end through `main()`) |
| `conformance/README.md` | new "How a report is read" section stating the four refusals and why the duplicate rule is load-bearing; the `INVALID` entry extended to name `SUITE INVALID` |

Nothing was weakened. No check got more permissive, no control observation changed, and
the twenty embedded controls still produce the same twenty verdicts.

## Defeating evidence

The new tests bite. Two that are not hypothetical:

- `test_repeated_case_id_is_refused_not_resolved` and
  `test_duplicated_observation_invalidates_the_whole_run` both fail against the old
  loader, since they assert a refusal that did not exist. The end-to-end one additionally
  asserts `SUITE PASS` is absent from the output, so a future regression to last-wins
  cannot pass it quietly.
- `test_no_check_reads_a_submitted_verdict` sweeps all twenty controls, injecting
  `participant_verdict`, `verdict`, `expected_oracle`, `suite`, `defects: []`, and
  `passed: true` into each `observed`, and asserts the defect list is identical to the
  honest one. The previous file tested this for `check_i5` only.

The new duplicate guard also caught a real bug in the first draft of the test helpers
themselves: they keyed synthetic participant case ids on `requirement`, which collides
because PROD-I-5 carries two control pairs (`CONF-I5-*` and `CONF-I5-GRANT-*`). The
helpers now key on the control id. The guard found a duplicate its own author did not
intend within minutes of existing, which is the behaviour it was added for.

## Checks observed

- `python scripts/verify.py` exit 0: hygiene PASS (136 text files, 21 Python modules,
  1 named debt), bootstrap PASS 126 checks, oracle `SUITE PASS cases=20 coverage_gaps=0`,
  oracle tests 17 OK, Asset Service 5 OK, repository tooling tests 28 OK, inside the
  3.0s budget.
- Honest participant run rebuilt from the positive controls: `SUITE PASS`, exit 0, both
  before and after the change. The hardening costs an honest participant nothing.
- All four probe payloads re-run after the change; every one now reports `SUITE INVALID`
  with a reason naming the offending entry.

## Residuals

1. Not witnessed. A `sov-witness` pass over this operation is the next bounded step.
2. `conformance/run.py` is now 332 lines. Lint's 300-line production limit only covers
   `/src/` and `scripts/`, so nothing gates it, but the file now holds nine requirement
   checks, a report loader, and result formatting. It is a split candidate, not yet debt.
3. **`--cases` is submitter-controllable.** A participant can run
   `python conformance/run.py --cases its-own-cases.json --observations its-own.json` and
   produce a green suite that proves nothing, because it supplied both sides. The code
   cannot close this; a witness must run the repository's `conformance/scenarios.json`.
   That procedure is not stated in `conformance/README.md`, in the PRD fresh-witness
   requirement, or in FOUND-007. It is the largest remaining hole in the qualification
   path, and it is a procedure hole rather than a code one.
4. Observations are still not validated against
   `contracts/participant-observation.schema.json`. Held on baseline judgement item 5 (X4).
5. The README addition sits in the document X4 asks about. It is scoped to runner
   mechanics and says so explicitly, but if Bdo rules the schema owns the crossing, this
   text may need to move.

## Judgement queue for Bdo (nothing decided)

1. [conformance, PRD, reconcile with residual 3] Should the fresh-witness contract state
   that a qualifying run must use the repository's `conformance/scenarios.json`, and should
   the runner record the digest of the case file it ran in its report so a witness's output
   is self-describing? This is the remaining way a participant can qualify itself.
2. [conformance] `SUITE INVALID` is a new suite-level verdict. `conformance/README.md`
   already reserved `INVALID` for an unevaluable participant report, so this was treated as
   gap-closure against a stated contract rather than a new result meaning. Confirm, or route
   it through a decision record.
3. [conformance, contracts] Baseline item 5 (X4) still holds `CONF-README-BIND` and schema
   validation of observations. The refusals added here are envelope shape only and do not
   pre-empt that ruling; confirm the read.
