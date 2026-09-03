# Witness record: Observation Service thin slice

```witness
standing_supported  none
```

Verdict: **NOT-YET**.

Subject: `observation_service_status` in `STATUS.yaml`, value
`BUILT_THIN_SLICE_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED`, together with the
conformance and derived-standing changes the same commit carries.

Commit witnessed: `169182fe4c7b928d12d98d3ee228d82dd58ec2db` on
`claude/phase-1-5-to-2-hbsv79`. `git status --short` was empty before and after every
command below. Nothing in this record was taken from the builder's report; every claim was
re-derived from the tree at that commit.

Witness: `claude-fable-5-1/sov-witness@2026-09-03`. This participant did not build, edit,
stage, or commit anything under the subject. The only files it created are this record and
`witness/observations/2026-09-03-observation-service-observation.json`. Its probe was run from
a scratch directory outside the repository and is quoted in full under `Probe` below, because
the invocation did not permit a file under `witness/probes/`.

## Standing supported

None. The observation supports no transition. The thin slice is built and its own tests pass,
but three of the sub-claims the standing rests on were defeated through the declared surface
(findings F1, F3, F4), so `BUILT -> WITNESSED` is not supported yet. The conditions below name
the exact repairs after which a re-witness could support it.

## Verified

Commands run from the repository root at the commit above, with exit codes and bounded output.

| Command | Exit | Excerpt |
| --- | --- | --- |
| `git rev-parse HEAD` | 0 | `169182fe4c7b928d12d98d3ee228d82dd58ec2db` |
| `git status --short` | 0 | empty |
| `python scripts/verify.py` | 0 | `PASS: 50 checks in 14.833s wall`; `GRADE: SILVER`; `BUDGET DEBT: 9 check(s) over ceiling` (attributed, non-refusing) |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1164 text files, 545 Python modules, 10 named debt)`; the duplicate-key `WARN`s on `STATUS.yaml` predate this commit (`byom_status` declared twice at `HEAD~1` too) |
| `python -m unittest discover -s tests -v` in `services/observation` | 0 | `Ran 37 tests in 0.029s OK` |
| `python conformance/run.py` | 0 | `SUITE PASS cases=33 coverage_gaps=0`; every `*-DEF` control `FAIL`, every `*-POS` control `PASS` |
| `python scripts/sov_f2_gate.py` | 1 | `44/44 normative predicates carry both fixtures`; `participants 1/2 bound`; `OPEN: F2 milestone gate` |
| `python scripts/sov_phase_progress.py check` | 0 | `44/44 predicates, floor 44`; `PASS` |
| `python scripts/sov_baseline.py` | 0 | `PASS: participant matches its recorded baseline (9 requirements, 8 failing as recorded)` |
| `python scripts/sov_clarity.py status` / `check` | 0 | `CURRENT 142, STALE 0, UNCHECKED 0, EXEMPT 88`; `PASS` |
| `python conformance/run.py --json` (defect strings) | 0 | each new defeating control lists only defects naming its predicate's reason; no "missing field" defect appears (see C1) |
| mutation probe (scratch copy of `conformance/`) | n/a | deleting 9 of 10 sampled oracle rules left `SUITE PASS cases=33`; only the `begin_run` failed-gate rule was noticed (see C3) |
| participant mode: `conformance_observations.py` then `run.py --cases conformance/scenarios.json --observations ...` | 0 / 1 | `suite FAIL coverage_gaps ['SPEC-CAPTURE','SPEC-DISCOVERY','SPEC-EFFECTIVE','SPEC-RUN']`; `PROD-I-2 PASS []`; reread block `{'digest': '97a7ba4b...', 'reread_count': 2}` (see C4) |
| relation/receipt probe (quoted below) | 0 | P1 `INDEPENDENT`, P2 `INDEPENDENT`, P3 `ESCAPED ValueError receipts=0`, P4 `ESCAPED KeyError receipts=0`, P5 `INDEPENDENT`, P6 observation emitted, P7 `{'reads-report': True}`, P8 `COMMITTED`, P9 observation emitted, P10 `False` |

## Claim 1: conformance closure

- 33 controls in `conformance/oracle-controls.json`: **observed**.
- `conformance/kernel_predicates.py` adds `SPEC-CAPTURE`, `SPEC-EFFECTIVE`, `SPEC-RUN`,
  `SPEC-DISCOVERY` and `conformance/requirements.py` merges them into `CHECKS`: **observed**.
  The module is loaded by file path through `importlib`; it imports no participant code.
- F2 gate 44/44, open only on the second participant; `contracts/phase-progress.json` floor
  44, `uncovered_on_purpose` empty: **observed**.
- PRED-I-2.1 credited by a reread rule in `check_i2` (`conformance/requirements.py:107-111`)
  and a real reread in `services/asset/scripts/conformance_observations.py:84-90`:
  **observed**. `verified_address` (`services/asset/src/.../store.py:157`) reads the blob at
  the digest path and refuses on disagreement, so the reported digest is of bytes that came
  back, not of the table row.
- New defeating controls fail for the reason their predicate names: **observed** (C1).
- No oracle rule was removed: **observed**. The diff of `conformance/` removes only the fixed
  nine-member `REQUIREMENTS` set and one docstring line.
- Every new control exercises every predicate it declares: **dissented** (C2).

### C1 (observed, no finding)

Defect strings per defeating control, read from `run.py --json`: `CONF-CAPTURE-DEF` "source
captured under a digest its bytes do not carry"; `CONF-EFFECTIVE-DEF` "attestation policy unmet
yet claim made effective", "claim made effective over a DISSENTED attestation"; `CONF-RUN-DEF`
"executor observed its own run", "observation admitted without an INDEPENDENT inference
(DIRECT)", "observation admitted with a direct edge to the run", "a participant in the run
settled it"; `CONF-RUN-BEGIN-DEF` "run began past a failed gate: budget"; `CONF-RUN-REPORT-DEF`
"report accepted under a stale lease", "executor report settled the run";
`CONF-RUN-SETTLE-DEF` "settlement cites no observation of this run", "run settled against a
stale state"; `CONF-DISCOVERY-DEF` two parity defects; `CONF-I2-DEF` includes "source did not
reread byte-identical by digest". None fails on an incidental missing field.

### C2 — finding, MEDIUM: `CONF-RUN-DEF` declares two predicates it does not exercise

`conformance/oracle-controls.json`, control `CONF-RUN-DEF`, `predicates` lists
`TRANS-begin_run` and `TRANS-report_run`, but every defect it produces is an `observe_run` or
`settle_run` defect (C1). Its `begin` and `report` blocks are byte-identical to the positive
control's. That is the exact defeat `contracts/custodies.json:426`
(`custody:oracle-predicate-join`) names: "a control declaring a predicate it does not actually
exercise, which would credit coverage that no case proves." The F2 count does not depend on it
today because `CONF-RUN-BEGIN-DEF` and `CONF-RUN-REPORT-DEF` exist; the over-declaration is
still a false join in the corpus. Consequence if ratified as-is: the join stops being a
measurement for those two predicates, and deleting either dedicated control would leave the
gate reading closed.

### C3 — finding, MEDIUM: the corpus cannot see most of its own rules disappear

Mutation probe on a scratch copy of `conformance/` (original controls, one rule deleted at a
time): deleting the reread rule (`requirements.py:107-111`), "executor observed its own run"
(`kernel_predicates.py:150`), "report accepted under a stale lease" (`:128`), "settlement cites
no observation of this run" (`:187`), "run settled against a stale state" (`:189`), the
PARITY-1 same-operations rule (`:224`), the INDEPENDENT-inference rule (`:152`), the DISSENTED
attestation rule (`:78`), and the capture digest-mismatch rule (`:37`) each left
`SUITE PASS cases=33 coverage_gaps=0`. Only the `begin_run` failed-gate rule was noticed. The
cause is that most defeating fixtures fail for two or more independent reasons at once, and
`CONF-CAPTURE-DEF` and `CONF-I2-DEF` share their case with sibling checks. This is the class
the witness procedure names in 6a: the check grades a verdict it cannot attribute. It is not a
weakening, and it was true of the pre-existing corpus too; but the commit's claim that
"PRED-I-2.1 is credited by a reread rule" is credited by a rule nothing guards. Consequence if
ratified: any of those rules can be removed or broken without the suite noticing.

### C4 — finding, MEDIUM, unreported: participant runs now carry four permanent coverage gaps

`conformance/requirements.py:297` derives `REQUIREMENTS = set(CHECKS)`, so it now holds the
four `SPEC-*` keys. `conformance/run.py:89,113-117` seeds `seen` from `REQUIREMENTS` and
reports a coverage gap for any key with no case of the required polarity. In participant mode
against `conformance/scenarios.json` (which carries only `PROD-I-*` cases) the run therefore
reports `coverage_gaps ['SPEC-CAPTURE','SPEC-DISCOVERY','SPEC-EFFECTIVE','SPEC-RUN']`, and a
participant that met all nine requirements could never read `SUITE PASS`. `sov_baseline.py`
still passes because it compares per-requirement verdicts. The builder's report does not
mention this change to what a participant run means. `conformance/run.py:5` still says "The
nine requirement predicates".

## Claim 2: Observation Service thin slice

- Five operations under `services/observation/src/soveraeign_observation_service/`, tests in
  `test_thin_slice.py` and `test_kernel_parity.py` pass, manifest marks five `BUILT`, the
  emitted inference validates against `relation-inference.schema.json` and the observation
  against `contracts/observation.schema.json`: **observed**. Module sizes 61-186 lines.
- The service never writes the journal: **observed** in `src/`. `record.py` imports nothing
  from the Record Service; state is five in-memory lists in `service.py:40-44`. Note the
  test `test_thin_slice.py:285-297` imports `soveraeign_record_service` directly and appends
  entries; that is the test crossing the service boundary, not the service.
- Independence inferred over the five charter edges with `UNDETERMINED` refusing:
  **observed as implemented, with two ways past the check** (F1, F2).
- Every attempt leaves exactly one receipt: **dissented** (F3).
- `evaluate()` permits `settle_run` on the emitted observation and refuses the forged
  self-observation: **observed**, with a note. The refusal comes from
  `scripts/sovkernel/transitions.py:116` comparing `observer_id` to `current.reporter_id`; the
  kernel reads nothing else from the observation, and `satisfactory` is computed by the test
  at `test_kernel_parity.py:45`, not by the kernel or the service.
- A record shape that reads absence as independence: **partly** (F5, F6).
- A predicate kind that reads the executor's report: **the guard is the executor's own list**
  (F7).

### F1 — finding, HIGH: the actor who wrote `REPORTED` is not an edge

`relation.py:127-128` reads `SAME_ACTOR` from the `ATTEMPTED` entry's actor only. The actor of
the `REPORTED` entry (`record.py:82-85`) is cited but never compared to the candidate. Probe P1:
a journal whose `ATTEMPTED` actor is `worker-a` and whose `REPORTED` actor is `worker-b`, with
lease and outputs belonging to `worker-a`, infers `worker-b` as `INDEPENDENT` with
`edges=[]`. `SPEC.md:412` ("Executor completion is a report, not settlement") and
`SPEC.md:510` make the reporter the executor's voice, and the kernel refuses exactly this
observer (`transitions.py:116-119`, "produced the report it offers as observation"). The service
is therefore weaker than the kernel it feeds. Consequence if ratified: a participant that
reports a run it did not begin can be admitted as its own observer.

### F2 — finding, MEDIUM: only the first `ATTEMPTED` entry is read

`record.py:77-80` returns the first `ATTEMPTED` entry; `relation.py:117-135` reads executor and
lease from it alone. Probe P2: a second `ATTEMPTED` entry on the same run by `worker-b` with
its own lease and grant; `worker-b` infers `INDEPENDENT`. A re-attempt is a plausible journal
shape and the record does not refuse it. Consequence: the executor of the attempt that actually
produced the report can be admitted as observer.

### F3 — finding, MEDIUM: the one-receipt invariant is defeated by a malformed entry

`service.py:64-71` catches only `ObservationRefused`. `record.py:122-127` raises `ValueError`
when an entry has no sha256 `entry_digest`; `record.py:89,94` and `relation.py:66` raise
`KeyError` when a `GRANT` or `OUTPUT` entry has no `subject`. Probes P3 and P4: both escape
`infer_relation` with `receipts=0`. `KNOWN-GAPS.md` ("Every attempt leaves exactly one receipt")
and `service.py:11-12` state the invariant the builder claims, and `errors.py:45-48` declares
`UNREADABLE` for "the run's record could not be read", which is the reason these should carry.
`test_every_attempt_leaves_exactly_one_receipt` (`test_thin_slice.py:259`) only drives declared
refusals, so it cannot see this. Consequence: an attempt over a damaged record leaves no trace.

### F4 — finding, MEDIUM: `request-observation` names a reported run `COMMITTED`

`service.py:97`: `"run_outcome": "COMMITTED" if record.report() is not None else "REFUSED"`.
`observation-request.schema.json:29-31` defines `run_outcome` as "the run's terminal receipt
outcome"; `SPEC.md:512` makes `COMMITTED` the outcome `settle_run` issues after a satisfactory
observation, and `record.py:21-24` itself says a run is observed before it is settled. Probe
P8: a reported, unsettled run yields `run_outcome: COMMITTED`. The service that exists to keep
an executor's report from standing in for settlement records the report as settlement. This is
vocabulary drift against `SPEC.md` and `CLASSIFICATION.md`, not a schema failure.

### F5 — finding, LOW: a malformed declared digest silently disables the byte check

`observe.py:128-130` compares bytes to the record's digest only `if declared is not None`;
`digest_address` returns `None` for any non-sha256 string. Probe P6: an `OUTPUT` entry whose
`payload.digest` is `not-a-digest` lets `observe_run` emit an observation over arbitrary bytes
with no `DIGEST_MISMATCH` and no `UNREADABLE`. The observation does record its own digest of
what it read, so it is honest about the bytes; it is silent about the record being unreadable.

### F6 — note, LOW: a run whose own grant is absent from the record reads `INDEPENDENT`

Probe P5: `grant_id: grant-unknown` on the attempt, no `GRANT` entry for it, candidate holds a
rooted grant; `_walk_grants` (`relation.py:53-80`) walks the candidate's chain to root, finds
no match, and records no unanswerable edge. The reading is logically defensible (a complete
chain that does not contain the run's grant does not descend from it) but the record is
incomplete about the run itself, and `CHARTER.md:42` says a record too thin to infer from
refuses. Recorded so the next reader can overturn it rather than inherit it.

### F7 — finding, LOW: the "reads the report" refusal is really an "unreported address" refusal

`observe.py:116-120` refuses a predicate whose address is not in the executor's
`output_record_addresses`. That is the whole enforcement of the manifest precondition
`predicates_evaluable_without_executor_report`. Probe P7: an executor that lists its own report
address among its outputs, with an `OUTPUT` entry for it, has a `JSON_FIELD_EQUALS` predicate
evaluated over that report and `True` returned. `test_a_predicate_that_reads_the_report_refuses`
(`test_thin_slice.py:219`) uses the address `e-report`, which is refused because it is
unreported, so the test name claims more than the test proves.

### F8 — notes, LOW

- `service.py:132-138` reuses the latest inference by `run_id` and observer over whatever
  `RunRecord` the caller passes to `observe_run`; probe P9 emitted an observation over a record
  with no `OUTPUT` entry after inferring over a complete one. Caller-controlled; recorded.
- `service.py:155-156` returns the latest declaration for the run, not the one the observation
  was judged through; probe P10 returned `False`. The docstring at `service.py:146` promises
  the latter.
- `observe.py:136-139` derives `observation_id` from run, observer and addresses only, so two
  observations with different predicates over the same addresses share an id and
  `read_observation` returns the first.

## Claim 3: standing and derived artifacts

- `STATUS.yaml` value, `contracts/status-claims.json`, manifest standing, docs pages, diagram
  pins, node-interface projection: **observed** consistent; `verify.py` regenerates and checks
  them and passed. `sov_standing.py` reads the value as a denial (`NOT_WITNESSED`).
- Capability map refresh: **finding** (S1).
- Clarity receipts: **finding** (S2).
- One stale claim the builder's method could not reach: **finding** (S3).

### S1 — finding, MEDIUM, unreported: five observation operations declared `ACTIVE` at an unrouted address

`contracts/fixtures/capability-map.reference.json` moves five observation operations from
`activation: DECLARED_NOT_ACTIVATED` to `activation: ACTIVE`, `address: observation:in-process`.
`scripts/sovnode/composition.py:187-190` binds `asset`, `registry`, `console` and
`host:in-process` only; `route_census()` (`:72-123`) enumerates no observation route, and
`services/observation/KNOWN-GAPS.md` says "No binding drives this service; the tests call it
in-process". `ACTIVE` here is a declaration nothing measures. `CLAUDE.md` states the rule:
"declarations are not reachability". (`record:in-process` shares the pattern and predates this
commit; that does not make the new instance correct.) Consequence: the Node Interface projection
derived from the map presents five operations as activated that no binding can reach.

### S2 — finding, LOW: sixty receipts re-recorded on a token grep

`.clarity/coverage.json`: 67 receipts changed; 60 changed only in the `STATUS.yaml` basis digest
(`96d9e073... -> dae8e4f4...`), 7 in artifact digest as well. The builder states the 60 were
re-recorded after grepping each for mentions of the observation standing. Under
`.claude/skills/clarity/SKILL.md`, `record` "records a completed clarity review" and a review is
steps 1-15, including unslop and the two closing questions; "'No edit needed' is a valid result
only after the artifact has been actively reviewed." A token grep discharges the delta half of
step 12 and nothing else, and the receipt carries no field that says so, so the record now
asserts sixty reviews that were basis-delta checks. It is a finding, not a review. Its weight is
bounded: the artifact bytes were unchanged and previously reviewed under the same digest, and
the only basis change was thirteen lines of `STATUS.yaml`. The skill has no delta-review mode;
whether one should exist is a skill-owner choice and is listed under judgement items. What
would discharge it now: re-read the 60, or state the delta scope in the receipt if the skill is
extended to allow it.

### S3 — finding, LOW, unreported: `services/host/SERVICE-SPEC.md:121-122`

Still reads "that service is chartered but not implemented (`observation_service_status:
CHARTERED_BOUNDARY_NOT_IMPLEMENTED`, `STATUS.yaml`)". The file is not in the clarity population
(`.clarity/coverage.json` lists `services/host/CHARTER.md` and `JOURNEYS.md` only), so a method
that reads only stale receipts could not find it. It is a current document quoting a
`STATUS.yaml` value that no longer exists.

## Conditions

A re-witness could support `BUILT -> WITNESSED` for the thin slice after:

1. F1: `relation.py` treats the `REPORTED` entry's actor as an executor edge (or the charter
   is amended to say why not), with a defeating test in `test_thin_slice.py`.
2. F3: `service.py` writes an `UNREADABLE` receipt for a record it cannot read, and the
   one-receipt test drives a malformed entry.
3. F4: `service.py:97` stops naming a reported run `COMMITTED`; use a value the schema and
   `SPEC.md` agree is the run's receipt outcome, or refuse when no terminal receipt exists.
4. S1: the capability map declares `DECLARED_NOT_ACTIVATED` for observation until a route
   exists, or `composition.py` binds `observation:in-process`.
5. C2: `CONF-RUN-DEF` declares only the predicates its defects exercise.
6. C4: participant mode either scopes coverage to the case file's requirements or
   `scenarios.json` carries the `SPEC-*` cases; the builder's report states the change.

F2, F5, F6, F7, F8, C3, S2 and S3 are the builder's to absorb inside the concern; they do not
by themselves hold the transition.

## Uncovered

- `docs/documentation.html`, `docs/surface.html`, the diagram pins and
  `contracts/fixtures/node-interface.reference.json` were accepted on `verify.py`'s
  regeneration checks; their text was not read.
- `scripts/tests/test_phase_progress.py` and `test_node_interface.py` changes were read for
  intent (planting synthetic gaps because the live corpus now covers PARITY-1) and not
  executed in isolation.
- The `list-pending-observations`, `counter-observation` and `attest-observation` operations
  were not examined; the manifest leaves them `PROPOSED`.
- The clarity edits to `PRD.md`, `.claude/agents/sov.md`, `CLAUDE.md` and
  `services/observation/CHARTER.md` were read as diffs, not re-reviewed for clarity.
- No network, no `gh`, no ruleset query.

## Landing residual

With this record and its receipt added to the tree, `python scripts/verify.py` returns 1 on
one check only, `documentation reader`: `docs/documentation.html is stale; run python
scripts/sov_docs.py build`. `scripts/sovdocs/facets.py:66` indexes `witness/*.md`, so any new
witness record ages that derived page. At the witnessed commit itself, with neither file present,
verify returned 0 as recorded above. The witness may not write the page; whoever lands this
record rebuilds it. `python scripts/sov_standing.py` and `python scripts/lint.py` both return 0
with the two files present, and `python scripts/sov_witness_layer.py records` grades the
receipt `CURRENT` (21 digests recomputed).

## Probe

Run from a scratch directory against `services/observation/src` at the commit above; not a
file in this repository. Each case reaches the service only through `ObservationService` and
`RunRecord.from_entries`, the declared surface.

```python
import hashlib, sys
from pathlib import Path
sys.path.insert(0, 'services/observation/src')  # relative to the repository root
from soveraeign_observation_service import ObservationService, RunRecord, ObservationRefused
RUN = "urn:soveraeign:run:probe"; OUT = b'{"standing": "RECORDED"}'
OUTD = hashlib.sha256(OUT).hexdigest()
def e(eid, kind, subject, actor, payload):
    return {"entry_id": eid, "kind": kind, "subject": subject, "actor": actor,
            "payload": payload, "entry_digest": hashlib.sha256(eid.encode()).hexdigest()}
class Clock:
    t = 0
    def __call__(self):
        Clock.t += 1; return f"2026-09-03T00:{Clock.t:02d}:00+00:00"
def base(lease_holder="worker-a", grant="grant-run", out_actor="worker-a", report_actor="worker-a"):
    return [
        e("g-root","EVENT","grant-root","seat:root",{"event":"GRANT","holder_id":"orch","parent_grant_id":None}),
        e("g-run","EVENT","grant-run","orch",{"event":"GRANT","holder_id":"worker-a","parent_grant_id":"grant-root"}),
        e("g-b","EVENT","grant-b","orch",{"event":"GRANT","holder_id":"worker-b","parent_grant_id":"grant-root"}),
        e("g-z","EVENT","grant-z","orch",{"event":"GRANT","holder_id":"witness-z","parent_grant_id":"grant-root"}),
        e("attempt","EVENT",RUN,"worker-a",{"event":"ATTEMPTED","lease":{"holder_id":lease_holder},"grant_id":grant}),
        e("out1","EVENT","out/1",out_actor,{"event":"OUTPUT","digest":OUTD}),
        e("report","EVENT",RUN,report_actor,{"event":"REPORTED","output_record_addresses":["out/1"]}),
    ]
def run(name, entries, candidate):
    svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, entries)
    try:
        inf = svc.infer_relation(rec, candidate, "WORKER")
        print(name, inf["outcome"], [x["edge"] for x in inf["edges_found"]], len(svc.receipts))
    except ObservationRefused as r: print(name, "REFUSED", r, len(svc.receipts))
    except Exception as r: print(name, "ESCAPED", type(r).__name__, r, len(svc.receipts))
run("P1", base(report_actor="worker-b"), "worker-b")                      # INDEPENDENT [] 1
ents = base(); ents.insert(5, e("attempt2","EVENT",RUN,"worker-b",
    {"event":"ATTEMPTED","lease":{"holder_id":"worker-b"},"grant_id":"grant-b"}))
run("P2", ents, "worker-b")                                               # INDEPENDENT [] 1
ents = base(); del ents[4]["entry_digest"]; run("P3", ents, "witness-z")  # ESCAPED ValueError 0
ents = base(); del ents[3]["subject"];      run("P4", ents, "witness-z")  # ESCAPED KeyError 0
run("P5", base(grant="grant-unknown"), "witness-z")                       # INDEPENDENT [] 1
ents = base(); ents[5]["payload"]["digest"] = "not-a-digest"
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, ents)
svc.infer_relation(rec, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"p","kind":"BYTES_PRESENT","address":"out/1"}])
print("P6", svc.observe_run(rec, "witness-z", lambda a: b"anything")["predicate_results"])  # {'p': True}
ents = base(); ents[6]["payload"]["output_record_addresses"] = ["out/1", "report"]
ents.append(e("out-report","EVENT","report","worker-a",
    {"event":"OUTPUT","digest":hashlib.sha256(b'{"claim":"done"}').hexdigest()}))
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, ents)
svc.infer_relation(rec, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"reads-report","kind":"JSON_FIELD_EQUALS",
                              "address":"report","field":"claim","expected":"done"}])
print("P7", svc.observe_run(rec, "witness-z",
      lambda a: b'{"claim":"done"}' if a == "report" else OUT)["predicate_results"])  # True
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, base())
print("P8", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"])  # COMMITTED
```

Mutation probe for C3: copy `conformance/run.py`, `requirements.py`, `kernel_predicates.py`
and `oracle-controls.json` to a scratch directory, replace one `defects.append(...)` with
`pass`, run `python run.py --cases oracle-controls.json`, read the `SUITE` line, restore.
