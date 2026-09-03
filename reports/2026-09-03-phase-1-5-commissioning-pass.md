# Phase 1.5 commissioning pass: two circles, then the owl

Session `session-bf50c8`, branch `claude/phase-1-5-to-2-hbsv79`, 2026-09-03. Concern:
move toward the prepared Phase 1.5 horizon through work whose closure a command can
demonstrate, and surface the problems found on the way. Effect class `RECORD_LOCAL`
throughout. No phase opened; `STATUS.yaml` stays `NONE_ACTIVE` and the next gate stays
`SUCCESSOR_PHASE_OPENING`, which only the root seat performs.

## Terminal

Presented on the branch for acceptance. Not landed on `main`: the changes touch
`STATUS.yaml`, `PRD.md`, `CLAUDE.md`, and `.claude/agents/sov.md`, which the ratified
standing grant excludes, so the landing gate is not the path for this change and Bdo's
review of the branch is.

## What was built, and the command that proves each part

| Part | Proof | Reading at the second commit |
| --- | --- | --- |
| Every normative predicate `SPEC.md` states carries a positive and a defeating fixture | `python scripts/sov_f2_gate.py` | 44/44; the gate stays `OPEN` on its second bound participant only |
| The phase-progress floor is the ceiling | `python scripts/sov_phase_progress.py check` | floor 44, `uncovered_on_purpose` empty, PASS |
| Twelve kernel controls judged through one table | `python conformance/run.py` | 33 controls, `SUITE PASS`, every defeating control fails for its predicate's own reason |
| Every oracle rule guarded one at a time | `python -m unittest discover -s conformance/tests` | `test_kernel_predicates.py` pins each rule to the exact defect it names |
| Observation Service thin slice | `cd services/observation && python -m unittest discover -s tests` | 43 tests: five operations, every declared refusal, schema-valid inference and observation, kernel `settle_run` parity |
| The Asset participant rereads its source for `PRED-I-2.1` | `python scripts/sov_baseline.py` | matches its recorded baseline |
| Repository gate | `python scripts/verify.py`; `python scripts/lint.py` | 50 checks PASS; hygiene PASS |

The eight predicates that were open: `capture_source`, `make_effective`, `begin_run`,
`report_run`, `observe_run`, `settle_run`, `PRED-I-2.1`, and `PARITY-1`. These are exactly
the minimal kernel closure set issue #173 names.

The Observation Service infers independence from the run's own journal entries over the five
direct edges the charter names, returns `UNDETERMINED` and refuses when the record cannot
answer, reads outputs itself against the digests the record declares, evaluates predicates
declared before the looking, and leaves one receipt per attempt. `KNOWN-GAPS.md` lists the
defaults taken so each can be overturned in one place.

## Witness

A separate `sov-witness` agent observed commit `169182f`, the first frozen subject, through
the declared surfaces only. Its record is `witness/observation-service.md` with a receipt under
`witness/observations/`. Verdict: `NOT-YET`; standing supported: none. It reproduced every
gate reading and dissented on these points, each repaired in the second commit:

- `SAME_ACTOR` read only the `ATTEMPTED` actor, so the actor who wrote `REPORTED` inferred
  `INDEPENDENT` while the kernel refuses that observer. The reporter is now an executor.
- Only the first `ATTEMPTED` entry was read; a second attempt's executor now reads `DIRECT`.
- A malformed record (missing digest or subject) escaped as a Python error with no receipt.
  Every such failure now refuses `UNREADABLE` and leaves the receipt.
- `request-observation` wrote `run_outcome: COMMITTED` from the presence of a report, which is
  the executor's word standing in for settlement. It now reads the run's terminal receipt and
  writes `UNRESOLVED` when none exists.
- A malformed `OUTPUT` digest silently disabled the byte check; it now refuses `UNREADABLE`.
- A report listed as its own durable output was a readable predicate address; the run's own
  entries are never predicate addresses now.
- `CONF-RUN-DEF` declared `begin_run` and `report_run` while defeating only observation and
  settlement, the exact defeat `custody:oracle-predicate-join` names. It now declares what it
  defeats.
- Nine of ten sampled oracle rules could be deleted without a control failing.
  `conformance/tests/test_kernel_predicates.py` holds each rule alone.
- `REQUIREMENTS = set(CHECKS)` gave every participant run four permanent coverage gaps. The
  runner now holds participants to the nine PRD requirements plus the kernel rows their own
  case file declares.
- `services/host/SERVICE-SPEC.md` still quoted the old observation status; corrected.
- The capability map marks the five built operations `ACTIVE` at an address the composition
  does not route. Recorded in `KNOWN-GAPS.md`; the Record Service shares the pattern and it is
  the map policy's to settle.
- Sixty-odd clarity receipts had been re-recorded after a review that grepped each stale
  artifact for the moved fact. The witness called that a finding, not a review under the
  clarity skill. Those receipts are restored to their pre-commit state, so
  `python scripts/sov_clarity.py check` now reads them `STALE` on the `STATUS.yaml` basis. That
  is the truthful state: the basis moved and the artifacts were not re-read. Re-reading them is
  owed work, and whether a delta-scoped basis re-check should be a recordable review state is
  a question for the skill's owner.

A second witness pass over the repaired commit is recorded in the same witness file when it
completes; the standing field does not move until a record supports it.

## Problems discovered and carried

- `STATUS.yaml` declares `sov_operating_agent_status` and `ticket_kind_vocabulary_status`
  twice with different values. A YAML reader keeps the last; the first is dead text. Owner's
  document, reported rather than edited.
- `custody:phase-i/receipt-reconstruction` and `custody:independent-observation` close on
  `python scripts/sov_ainative.py --check 3`, which the script does not accept. Both records
  are terminal, so they are left as evidence.
- Twenty-nine owner-routed questions carry `product_intent`, `acceptance_standing`, or
  `external_commitment`; `contracts/acceptance-policy.json` admits seven hold reasons and
  declares the list exhaustive. This is the residue that held Phase I clause X4 at
  `SUBSTANTIALLY_EARNED`, and it is a conflict between settled constraints: `CLAUDE.md` lists
  owner-held product intent among what waits on Bdo, and the policy has no word for it. A
  policy seam; `python scripts/sov_docket.py holds` lists the questions.
- `python scripts/sov_clarity.py --help` crashed on an unescaped percent sign. Fixed.
- `python scripts/sov_phase_progress.py raise-floor` prints that exclusions still need
  removing but cannot remove them; the edit was made by hand.

## Standing changes

- `observation_service_status`: `CHARTERED_BOUNDARY_NOT_IMPLEMENTED` to
  `BUILT_THIN_SLICE_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED`, with the matching row in
  `contracts/status-claims.json`, the service manifest, `services/README.md`, the charter,
  the orientation page, and the status remarks in `PRD.md` and `.claude/agents/sov.md`.
- `contracts/phase-progress.json` floor: 36 to 44, exclusions cleared.
- Nothing is `WITNESSED`. Nothing is `RATIFIED`. No phase is open.

## Defaults taken

Recorded in `services/observation/KNOWN-GAPS.md`: terminal means reported or refused; the
record is four payload events; a found edge outranks an unanswerable one; a candidate whose
grant is absent from the record is undetermined; three predicate kinds; declared-before by
injected clock; one receipt per attempt; `UNRESOLVED` as the outcome of a reported, unsettled
run.

## What waits on Bdo

Acceptance of this branch. Nothing else here asks for judgement: the discovered problems are
listed so they are visible, and each names the seat that owns it.

## Next bounded operation

The F2 gate's last open condition is a second bound participant: a materially different
binding running the same fixtures and supplying an observation set under
`conformance/observations/`. That is Phase I clause X2 territory and the smallest parity
slice issue #173 asks for.
