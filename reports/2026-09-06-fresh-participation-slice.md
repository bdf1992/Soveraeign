# Fresh participation: the first P15-X1 slice

Session `session-651746`, branch `claude/phase-2-citizen-mechanics-inrozu`, 2026-09-06.
Concern: move `custody:phase-1-5/fresh-participation` (exit clause P15-X1) off its opening
point with work whose closure a command demonstrates. Effect class `RECORD_LOCAL`
throughout. No phase state, standing field, or floor moved.

## Terminal

Presented on the branch for acceptance. Not landed on `main`: the change touches
`CLAUDE.md`, which the ratified standing grant excludes, so `scripts/sov_land.py` is not the
path and Bdo's review of the branch is. Independent witness: see the section below.

## What was built, and the command that proves it

| Part | Proof | Reading at the first commit |
| --- | --- | --- |
| A fresh participant enters from the artifact and resolves principal, session, phase, work, capability, authority and a Record projection | `python scripts/sov_fresh.py run --principal principal:claude-fable-5` | `PASS`; P15-Q1.1, Q1.2, Q1.3 hold on a live run |
| The probe can fail | `python scripts/sov_fresh.py selfcheck` | positive variant passes; `unregistered-principal` fails Q1.1 and Q1.3, `work-dies-with-session` fails Q1.2, `borrowed-authority` fails Q1.3, and nothing else fails |
| The layers are the product's own | `scripts/sovfresh/layers.py` | imports `sovsession`, `sovlease`, `sovnode.bindings`, `sovkernel.authority`, `sovcustody`, and the Record Service; the grade comes from `conformance/commissioning.py`, which imports none of them |
| Unit cases | `python -m unittest scripts.tests.test_sov_fresh` | 11 cases |
| Custody board | `python scripts/sov_custody.py board custody:phase-1-5/fresh-participation` | one `ITEM` member at `VERTICAL_SLICE`, standing `BUILT`, `stage_observed_by` null |
| Repository gate | `python scripts/verify.py`; `python scripts/lint.py` | 51 checks PASS; hygiene PASS |

The closed path the member claims: session register, principal resolve, campaign read from
`STATUS.yaml` and `contracts/phases.json` by digest, work read from the custody collection,
lease taken under the work, one reachable operation bound to the session, the standing
grants graded for the session's own actor, the run's facts appended to a Record the probe
opened and projected back as a `RecordProjection`, the session ended, the lease and custody
read again, and the three predicates graded. The last layer is a check whose result is
derived from the run, which is what `contracts/work-circuit.json` asks of a vertical slice.

What the live run shows about the node today:

- a fresh session resolves `UNIDENTIFIED` unless the participant declares a registered
  principal through `SOV_PRINCIPAL` or `--principal`; the registry names, it does not guess;
- the session's own principal holds no standing grant, so the authority gate reads
  `AUTHORITY_REFUSED`, while the same operation binds to the session; capability and
  authority are read apart, which P15-Q1.1 asks for;
- a request carrying another session's id is refused `SESSION_ATTRIBUTION_CONFLICT` by the
  node-interface binding;
- the lease holder is the run's instance principal and the declared durable principal is its
  controller, so the two identities the lease schema separates stay separate.

## Defaults taken

Reversible; each can be overturned in one place.

- The custody's closure check moves from `python scripts/sov_session.py brief` to
  `python scripts/sov_fresh.py selfcheck`. `decisions/0102` recorded the first as "the reader
  that exists today"; the brief cannot detect the clause's defeating condition and the probe
  is built to.
- Member kind `ITEM`, work state `PRESENTED`. The floor in `contracts/phase-progress.json`
  stays `ROOT_POINT`: the opening note raises a floor where a witnessed member exists, and
  this member is a build claim.
- The check joins verify under a new group, `scripts/sovverify/commissioning.py`, because
  `checks.py` was at its 300-line ceiling and the check reads the active phase rather than
  repository hygiene or a participant's own tests. Named ceiling 1.5 seconds against 0.44
  measured alone and 1.17 measured in the pool.
- The authority request grades `repository.commit` with declared `verify` and `lint` PASS
  evidence. Declared, not measured: it exists to grade the actor gate, and it is why the
  `borrowed-authority` variant reads `PERMITTED` for actor `sov`.
- The bound operation is the first reachable operation admitting a `MODEL` actor, sorted by
  id (`asset.ingest-asset`). It is bound, not dispatched.
- Cleanup obligations on the work unit are the custody's own list plus the inventory the
  participant opened: release its lease, end its session.

## Residuals

- The model serving this session is `claude-fable-5-1`. The registry names
  `principal:claude-fable-5`, and the live run declared that. Whether the version drift wants
  a new registry entry is identity naming, so it is recorded rather than done.
- `grant_id` in the identity observation is the standing grant the evaluator considered and
  refused. A fresh principal holds no grant of its own, and the instrument accepts the
  refused grant as the distinct grant identity. Whether that satisfies "grant authority
  remains distinct" is for the witness.
- `python scripts/sov_active_phase_progress.py` prints nothing on a passing read. It refuses
  correctly; a reader running it by hand cannot tell a pass from a no-op.
- Two checks CLAUDE.md counts moved: 50 to 51 verification checks and 30 to 31 reports. The
  page was corrected, not the tolerance, and its clarity receipt re-recorded after a read
  against `AGENTS.md`, `SOV.md`, and `STATUS.yaml`.

## Next bounded operation

Under the same custody: a second vertical that shares the boundary with this one so the
custody can reach `HORIZONTAL_SURFACE`, its declared target. The natural candidate is the
discovery side of P15-X3: a second fresh participant finds this run's lease, projection, and
result from the store and the Record alone. Under P15-X1 itself, the remaining gap is a
lease taken by a session whose principal is verified rather than `UNVERIFIED`, which waits
on the Identity Service challenge lifecycle.
