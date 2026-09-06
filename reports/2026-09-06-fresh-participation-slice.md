# Fresh participation: the first P15-X1 slice

Session `session-651746`, branch `claude/phase-2-citizen-mechanics-inrozu`, 2026-09-06.
Concern: move `custody:phase-1-5/fresh-participation` (exit clause P15-X1) off its opening
point with work whose closure a command demonstrates. Effect class `RECORD_LOCAL`
throughout. No phase state, standing field, or floor moved.

## Terminal

Presented on the branch for acceptance, in two commits: the slice, then the repairs the
first witness pass asked for. Not landed on `main`: the change touches `CLAUDE.md`, which
the ratified standing grant excludes, so `scripts/sov_land.py` is not the path and Bdo's
review of the branch is.

## What was built, and the command that proves it

| Part | Proof | Reading at the second commit |
| --- | --- | --- |
| A fresh participant enters from the artifact and resolves principal, host session, phase, work, node session, grant, one admitted crossing and a Record projection | `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | `PASS`; P15-Q1.1, Q1.2, Q1.3 hold |
| The same run in a node nobody has granted anything in | `python scripts/sov_fresh.py run --principal principal:claude-fable-5` | `FAIL`; Q1.1 and Q1.2 hold, Q1.3 reads `identity separation missing grant_id` and the crossing is refused `SESSION_IDENTITY_REQUIRED` |
| The probe can fail | `python scripts/sov_fresh.py selfcheck` | positive variant passes; `unregistered-principal` fails Q1.1 and Q1.3, `work-dies-with-session` fails Q1.2, `no-grant` fails Q1.3, nothing else fails |
| The layers are the product's own | `scripts/sovfresh/layers.py`, `scripts/sovfresh/node.py` | session registry, lease store, custody model, Node Interface, `LocalActionPath` (Console, Gateway, Record, Registry services); the grade comes from `conformance/commissioning.py`, which imports none of them |
| Unit cases | `python -m unittest scripts.tests.test_sov_fresh` | 15 cases |
| Custody board | `python scripts/sov_custody.py board custody:phase-1-5/fresh-participation` | one `ITEM` member at `VERTICAL_SLICE`, standing `BUILT`, `stage_observed_by` null |
| Repository gate | `python scripts/verify.py`; `python scripts/lint.py` | 51 checks PASS; hygiene PASS |

The closed path: host session registered; principal resolved from the registry as the
participant declares it; campaign read from `STATUS.yaml` and `contracts/phases.json` by
digest; work read from the custody collection; a lease taken under it, held by the run's
instance principal with the declared principal as controller; a node opened with empty
stores; when an issuer exists, the Console Service records `open:session` and the
operation's required authority for the actor and opens the actor's session; `registry.resolve`
bound to that session and dispatched through the Gateway; three more crossings the node must
refuse; the run's facts appended to the node's Record and projected back; the host session
ended; the lease read back as orphaned inventory and the console session as still open; the
three predicates graded. The last layer is a check whose result is derived from the run.

What the node refuses, each read from a Gateway receipt or the binding:

- a request carrying another session's id: `SESSION_ATTRIBUTION_CONFLICT` at the binding;
- another actor presenting this actor's session: `ACTOR_ATTRIBUTION_MISMATCH` at the
  Gateway's attribution stage;
- another actor on its own session without the grant: `AuthorityRefused` at the Gateway's
  authority stage.

`cross_principal_session_mismatch` reads `REFUSED` only when all three refuse for the reason
named and the owner's own crossing committed. A refusal for another reason is reported as
`REFUSED_FOR_ANOTHER_REASON` and fails the predicate.

## Independent witness

Pass 1 observed commit `d40d61f` through the declared surfaces. Verdict `NOT-YET`; standing
supported `BUILT`, unchanged. Record: `witness/fresh-participation.md`, receipt under
`witness/observations/`. Seven defects, each repaired in the second commit:

1. The Q1.3 mismatch was derived from `AUTHORITY_REFUSED` for an actor no grant names, which
   is absence of a grant, not a refused mismatch; the `borrowed-authority` variant defeated the
   probe's own derivation, not the product. Now every identity and refusal is read from the
   node's Console and Gateway records, and the Q1.3 defeating variant is `no-grant`, a state
   this node is actually in.
2. `grant_id` was the standing grant that had refused the participant. Now it is the grant the
   issuer recorded for the actor, or `None`, which fails the predicate.
3. `unregistered-principal` was not implemented inside the probe; through the CLI it passed.
   Now the variant substitutes an unregistered principal itself, whatever was declared.
4. `oral_history_used` was a constant. Now it is true when a resolver input the caller did not
   declare is set in the environment, and the input is named.
5. Cleanup obligations were composed by the probe. Now they are the custody's own list plus
   what the stores read back: the lease the store reports orphaned, and the console session
   still `OPEN`.
6. `interface_binding_id` fell back to a probe constant on refusal. Now it is `None`.
7. The cross-session reading compared verdicts, not codes. Now each refusal must carry the
   reason it declares.

Witness residuals recorded rather than changed: `--json` now works after the subcommand (F8);
the declared verify/lint evidence in the old authority request is gone with that request
(F9); `SOV_PRINCIPAL_REGISTRY` is now an explicit argument and, when set undeclared, is
reported as oral history (F10); `survives_session` now requires the store to read the lease as
orphaned after the session ended (F11); the custody schema has no evidence field and
`sovcustody/model.py` never calls `judge_advance`, so a member stage is a declaration
nothing measures (F12, pre-existing); `COMMISSIONING_CHECKS` is now spliced in one place,
the package `__init__` (F13); the custody closure command and the verify `Check` are two
declarations nothing ties together (F14, same as every other custody); the work the
participant accepts is the custody that lists the probe (F16); an `UNIDENTIFIED` principal can
still take a lease with `controller_principal: null` (F17, a lease-contract question).

## Defaults taken

Reversible; each can be overturned in one place.

- The custody's closure check moves from `python scripts/sov_session.py brief` to
  `python scripts/sov_fresh.py selfcheck`. `decisions/0102` recorded the first as "the reader
  that exists today"; the brief cannot detect the clause's defeating condition and the probe
  is built to.
- Member kind `ITEM`, work state `PRESENTED`. The floor in `contracts/phase-progress.json`
  stays `ROOT_POINT`: the opening note raises a floor where a witnessed member exists, and
  this member is a build claim.
- The check joins verify under a new group, `scripts/sovverify/commissioning.py`, spliced in
  by the package `__init__` beside the integrity checks. Named ceiling 1.5 seconds against
  0.62 measured alone.
- `selfcheck` uses a fixture issuer, `principal:fixture-root`, to open the temporary node's
  permits office, and a fixture principal in a temporary registry copy. Neither exists
  outside the run. The live reading uses no fixture: `run` without `--issuer` reports what
  a fresh node holds, and `--issuer` names the seat that opens the office for that run.
- The crossing is `registry.resolve` on `sov://asset/ingest-asset`, scope `registry:any`:
  reachable, `RECORD_LOCAL`, deterministic.

## Residuals

- The model serving this session is `claude-fable-5-1`. The registry names
  `principal:claude-fable-5`, and the live run declared that. Whether the version drift wants
  a new registry entry is identity naming, so it is recorded rather than done (witness J3).
- A fresh node has recorded no grant for any actor, so P15-Q1.3 is unmet there until an
  issuer opens the permits office. Whether the clause may be observed with the root seat
  issuing for the run, or wants a standing grant to a fresh principal, is the witness's J1.
- Re-pointing an exit custody's closure check is taken as a reversible default; whether it
  wants a decision-record note is the witness's J2.
- `python scripts/sov_active_phase_progress.py` prints nothing on a passing read.
- Two counts on `CLAUDE.md` moved: 50 to 51 verification checks and 30 to 31 reports. The page
  was corrected, not the tolerance, and its clarity receipt re-recorded after a read against
  `AGENTS.md`, `SOV.md`, and `STATUS.yaml`.

## Next bounded operation

Under the same custody: a second vertical that shares the boundary with this one so the
custody can reach `HORIZONTAL_SURFACE`, its declared target. The natural candidate is the
discovery side of P15-X3: a second fresh participant finds this run's lease, console session,
and projection from the stores alone. Under P15-X1 itself, the remaining gap is a session
whose principal is verified rather than `UNVERIFIED`, which waits on the Identity Service
challenge lifecycle.
