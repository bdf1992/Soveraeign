# Witness record: Observation Service thin slice

```witness
standing_supported  WITNESSED
subject  observation-service
revision  f8a755f73a815ce15bea6af486bb924c7cb2970f
pass  4
```

Four passes by the same role, different commits. Pass 4 (commit `f8a755f`) is current and
owns the declaration above. Pass 3 (commit `3087714`), pass 2 (commit `540bc01`) and pass 1
(commit `169182f`) follow it unchanged as history.

## Pass 4: commit f8a755f (2026-09-05)

Verdict: **RATIFIABLE-WITH-CONDITIONS**.

Subject: `observation_service_status` in `STATUS.yaml`, value
`BUILT_THIN_SLICE_WITNESSED_REMAINDER_DECLARED`. The value moved from
`BUILT_THIN_SLICE_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED` at `900326e` on the three passes
below; its comment (`STATUS.yaml:46-50`) and `contracts/status-claims.json:160-166` bind it to
commit `3087714`. This pass is scoped to the residuals R10-R13 pass 3 recorded, to whether pass
3's conclusions still hold on the new bytes, and to what the record supports for the value on
these bytes.

Commit witnessed: `f8a755f73a815ce15bea6af486bb924c7cb2970f` on
`claude/astra-gtp-scalability-6eus65`. `git log --oneline 3087714..f8a755f` lists `900326e` (the
standing move), `84a5491` (Phase 1.5 opened), `84dfe1f`, `e2ebb2a`, `9e4fdea`, `4b0bc1d` (two
merges and a harness change), then `f8a755f`, the only one of the seven that touches the subject.
`git rev-parse HEAD` read this commit and `git status --short` was empty before and after every
command below.

Witness: `claude-fable-5-1/sov-witness@2026-09-05`, fourth invocation. This participant did not
build, edit, stage, or commit anything under the subject. The only files it changed are this
record and `witness/observations/2026-09-05-observation-service-observation-4.json`. The commit
message of `f8a755f` was displayed by `git show --stat` at the start of the pass, before any
probe; it is the builder's report and nothing below is taken from it. The residual wording
re-derived here is pass 3's as recorded in this file, not the builder's transcription in
`services/observation/KNOWN-GAPS.md`; the two differ on R12, and the difference matters below.
Probes ran from a scratch directory outside the repository and are quoted in full under `Probe`;
the invocation permitted no file under `witness/probes/`.

### Standing supported

`BUILT -> WITNESSED` for `observation_service_status` at `f8a755f`, **re-supported** on these
bytes. It does not carry forward from `3087714`: the pass-3 receipt reads `STALE_SUBJECT`
against this tree (`sov_witness_layer.py records` recomputes 27 digests and finds `record.py`,
`observe.py`, `test_thin_slice.py`, `KNOWN-GAPS.md`, `test_kernel_predicates.py` and seven
governing files moved), so the bytes it observed are no longer the bytes in the tree, and a
`WITNESSED` value over bytes no receipt covers rests on history. This pass re-derived the claim on
the current bytes: every pass-3 conclusion re-run holds; the three code repairs (R10, R11, R13)
each go red when their guard is reverted in a scratch copy; R12 is repaired for one of the three
rules pass 3 named and still open for two; the oracle, the kernel transitions, and the service
facade are byte-identical to pass 3. The record binds to the subject `observation-service`, the
field `observation_service_status`, the revision above, and the same claim pass 3 bound: the five
operations `request-observation`, `declare-predicates`, `infer-relation`, `observe-run`, and
`read-observation` are built, self-tested, and independently observed through
`ObservationService` and `RunRecord.from_entries`; `list-pending-observations`,
`counter-observation`, and `attest-observation` are declared and unbuilt; no binding routes any
of the eight. The value's comment and the status-claims row name `3087714`; whoever moves them to
rest on this pass names `f8a755f`. This is an observation. It supports the transition and
ratifies nothing.

### Verified

Commands run from the repository root at the commit above, before either witness file was
written.

| Command | Exit | Excerpt |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --short` | 0; 0 | `f8a755f73a815ce15bea6af486bb924c7cb2970f`; empty, before and after every command |
| `python scripts/verify.py` | 0 | `PASS: 50 checks in 17.351s wall`; `DEBT: no wall-clock grade at 17.351s; SILVER needs 15.000s or less`; `BUDGET DEBT: 9 check(s) over ceiling, 26.801s above budget` (attributed, non-refusing). The verdict is the `PASS: 50 checks` line and the exit code, not the `FAIL` lines the tooling self-tests print over planted trees |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1176 text files, 546 Python modules, 10 named debt)` |
| `python -m unittest discover -s tests` in `services/observation` | 0 | `Ran 51 tests OK` (49 at pass 3; two new in `WitnessResidualsOn3087714`) |
| `python -m unittest discover -s conformance/tests` | 0 | `Ran 83 tests OK` (79 at pass 3; four new in `EveryRuleNamesItsDefect`) |
| `python conformance/run.py` | 0 | `SUITE PASS cases=33 coverage_gaps=0`; every `*-DEF` control `FAIL`, every `*-POS` `PASS` |
| `python scripts/sov_f2_gate.py` | 1 | `requirement 25/25`, `transition 14/14`, `parity 5/5`; `participants 1/2 bound`; `OPEN` on the second participant only, as at pass 3 |
| `python scripts/sov_baseline.py` | 0 | `PASS: participant matches its recorded baseline (9 requirements, 8 failing as recorded)` |
| `python scripts/sov_standing.py` | 0 | `SUPPORTED observation_service_status claims WITNESSED`; `PASS: 1 standing claim(s), each with a witness record`. Read against pass 3's declaration; see `Finding on the check itself` |
| `python scripts/sov_witness_layer.py records` | 0 | `PASS: 6 witness receipt(s) graded, 0 unusable, 6 stale against their subject`; the pass-3 receipt `STALE_SUBJECT (27 digest(s) recomputed)`, twelve addresses moved |
| `python scripts/sov_clarity.py status` / `check` | 0 / 0 | `CURRENT 142, STALE 0, UNCHECKED 3, EXEMPT 90`; `PASS`. The three `UNCHECKED`: this file (R9), `.claude/skills/can-it-run-doom/SKILL.md`, `.claude/skills/draw-the-owl/SKILL.md`; the last two arrived in `9e4fdea`, not in the subject's commit |
| `python scripts/sov_traps.py` | 0 | `PASS: 2 trap(s) still hold, 3 recorded for attended checking` |
| guard reverts (scratch copies of `services/observation`, test bootstrap `ROOT` pointed at the repository) | n/a | R10 guard removed (`record.py:97-98`): `test_an_output_with_no_producer_is_unreadable` `FAIL: Unreadable not raised`. R11 guard removed (`observe.py:108-110`): `test_observe_run_reads_the_record_it_is_handed` `FAIL: Unreadable not raised`. R13 guard reverted (`observe.py:121` to `record.run_entry_ids()`): `test_the_run_id_itself_is_not_a_predicate_address` `FAIL: PredicatesUndeclared not raised`. Unmodified copy: `Ran 36 tests`, `FAILED (errors=2)` from two loader errors that need the real root; each revert adds exactly `failures=1` |
| mutation sweep (scratch copy of `conformance/`; every `defects.append(...)` statement in `kernel_predicates.py` and `requirements.py`, 97 in all, located by AST span and replaced with `pass` one at a time; `unittest discover -s tests` read against the copy's baseline `FAILED (errors=2)`, loader errors in `test_lineage_fixtures` and `test_principled_deviation`, neither of which reads an oracle rule) | n/a | `kernel_predicates.py`: 34 of 44 seen, 10 unseen (`:46`, `:53`, `:89`, `:91`, `:93`, `:112`, `:114`, `:214`, `:219`, `:223`). `requirements.py`: 12 of 53 seen. Of the three pass 3 named, `:168` is now seen (`failures=1`), `:214` and `:219` are not. `run.py --cases oracle-controls.json` alone reads `SUITE PASS` for each of the eleven re-checked deletions, as at passes 2 and 3 |
| pass-3 probe re-run (quoted under pass 3, `sys.path` made absolute) | 0 | every line as pass 3 recorded it, except P1d and P7d, which now refuse: `P1d REFUSED UNREADABLE: entry out1 records an output with no producer receipts=1`; `P7d REFUSED UNREADABLE: entry urn:soveraeign:run:probe has no entry_id`. Happy path `UNRESOLVED`, `INDEPENDENT`, `{'p': True}`, receipts `RECORDED, COMMITTED, COMMITTED, COMMITTED` |
| pass-4 probe (quoted below) | 0 | outputs under `Residuals re-derived` |
| `sha256sum` | 0 | byte-identical to pass 3: `conformance/kernel_predicates.py` `f1d81c80...`, `conformance/requirements.py` `4b2fe7b3...`, `conformance/run.py` `c049f9e6...`, `conformance/oracle-controls.json` `75b4cf02...`, `scripts/sovverify/checks.py` `a5316c26...`, `scripts/sovkernel/transitions.py` `478fe0a0...`, `scripts/sovkernel/capability_map.py` `56230a9a...`, `scripts/sovnode/composition.py` `e7320557...`, `contracts/fixtures/capability-map.reference.json` `84e296ce...`, `relation.py` `7591b945...`, `service.py` `e20b03b9...`, `errors.py` `8ce373e7...`, `service.json` `621397d4...`, `observation-request.schema.json` `fd5cb97d...`. Changed under the subject: `record.py`, `observe.py`, `test_thin_slice.py`, `KNOWN-GAPS.md`, `test_kernel_predicates.py`, `.clarity/coverage.json` (one receipt), `docs/documentation.html` |

### Residuals re-derived (R10-R13 as pass 3 worded them)

A repair whose named case stays green with its guard reverted is not a repair; each verdict
below rests on the revert, the probe through `ObservationService` and `RunRecord.from_entries`,
or the sweep. The builder's list of repairs was not consulted for any of them.

| Residual | Verdict | Evidence |
| --- | --- | --- |
| R10 `malformed()` requires an actor only on the run's entries; an anonymous `OUTPUT` reads `INDEPENDENT []` | **REPAIRED** | `record.py:97-98` refuses an `OUTPUT` event with no actor. P1d (empty actor), P1g (`actor` key absent), P1h (`None`), P1i (`kind` `RECEIPT`, actor empty): each `REFUSED UNREADABLE: entry out1 records an output with no producer`, one receipt. The guard is the one R1 applies to the run's entries, applied to outputs. Revert goes red |
| R11 `observe_run` never calls `record.malformed()`; a substituted malformed record rides in on an earlier inference | **REPAIRED as worded; its description overclaims (R14)** | `observe.py:108-110` reads `malformed()` before `require_independent`. P7d (pass 3's case: `REPORTED` lost its id) `REFUSED UNREADABLE`; P7f (`OUTPUT` lost its producer) and P7g (`GRANT` lost its digest) `REFUSED UNREADABLE`, `observations=0`, the refusal receipt written by `service.py:_attempt`. Revert goes red. P7e and P7h: a **well-formed** substituted record in which the observer attempted the run, or produced the output, after an inference over a record in which it did neither, is `OBSERVED {'p': True}` with three `COMMITTED` receipts, while direct inference over the same record reads `DIRECT [SAME_ACTOR@attempt2, HOLDS_RUN_LEASE@attempt2, GRANT_DESCENDS_FROM_RUN@g-z]` and `DIRECT [PRODUCED_THE_OUTPUT@out1]`. `observe.py:105-106` and the R11 line of `KNOWN-GAPS.md` say "a substituted record cannot ride in on an earlier inference"; a malformed one cannot, a well-formed one still does. That is F8, open since pass 1 and carried; the new wording claims it closed |
| R12 `kernel_predicates.py:168,214,219` can be replaced with `pass` without `conformance/tests` noticing | **REPAIRED 1 of 3** | `:168` ("observation entered with a standing other than OBSERVATION") is now pinned by `test_observation_with_other_standing` (sweep: `failures=1`). `:214` ("discovery names no interface") and `:219` ("<name> binding missing <field>") are still unseen: `FAILED (errors=2)` baseline and `SUITE PASS` for each. The builder's transcription of R12 at `3087714` (`KNOWN-GAPS.md`, `git show 3087714:services/observation/KNOWN-GAPS.md`) named "report standing, discovery id/inputs shape, and settlement receipt", a different set from pass 3's, and the four new tests pin that set plus `:168`. The repair followed the transcription, not the record |
| R13 the R6 regression test passes with `observe.py:116` reverted | **REPAIRED** | the test now reports the run id as an output and stands an `OUTPUT` entry on it, so the "not a recorded durable output" guard no longer fires first, and asserts `run's own entry` in the refusal. Revert of `observe.py:121` goes red (it stayed green at pass 3). P7b unchanged |

### Pass-3 conclusions, re-run on the new bytes

| Conclusion | Holds | Evidence |
| --- | --- | --- |
| F1 reporter is an executor edge | yes | P1: `DIRECT [SAME_ACTOR@report]` |
| F2 second attempt's actor is an edge | yes | P2: `DIRECT`, three edges at `attempt2` |
| F3 malformed record refuses `UNREADABLE` with one receipt | yes, widened | P3, P3b, P4, P4b, P4b', P4c, P4d, P4e, P4f, P4g as at pass 3; P1d, P1g, P1h, P1i added |
| F4 reported unsettled run is not named `COMMITTED` | yes | P8 `UNRESOLVED`; P8c `REFUSED`; P8d `COMMITTED`, `INDEPENDENT`; J1 carried |
| F5 malformed declared digest refuses | yes | P6: `REFUSED UNREADABLE: the record declares no sha256 digest for out/1` |
| F6 run's grant absent reads `INDEPENDENT` | still open, note | P5: `INDEPENDENT []`, unchanged |
| F7 report entry is not a predicate address | yes | P7: `PREDICATES_UNDECLARED ... run's own entry` |
| F8 inference not bound to the record it was inferred over | still open; now misdescribed | P9 refuses; P10 `False`; P10b `True`; P7e, P7h observe over a substituted well-formed record (R14) |
| R1-R2, R4-R8 | hold | R1 now also refuses off the run (R10 repaired); R2 P2b, P2d, P2e unchanged; R4 P4b, P4b' unchanged; R7 join grader unchanged (`test_kernel_predicates.py` byte-adds only); R8 `CLAUDE.md` still consistent (`sov_snapshot` inside `verify.py`) |
| R3 refused run refuses `INCOMPLETE_PROPOSAL`; default undocumented | **closed**: P8b unchanged; `KNOWN-GAPS.md:57` now records the default | the half pass 3 left open is repaired; J4 remains the manifest owner's |
| R5 settled run may still be observed | yes | `record.py:21-25`; P8d |
| R9 this record has no clarity receipt | still open | `UNCHECKED` includes this file |
| C1 capability map `ACTIVE` at an unrouted address | carried | `capability_map.py`, `composition.py`, `capability-map.reference.json` byte-identical to pass 3; `node-interface.reference.json` changed only in regenerated digests (273 lines, all `digest`/`input_state_digest`/`record_digest` values) |
| C2 `CONF-RUN-DEF` declares only what it defeats | yes | `oracle-controls.json` unchanged (`75b4cf02...`) |
| C3 rules can be seen to disappear | yes for 46 of 97; see R12 | whole-corpus sweep above; pass 3's 11 named still seen |
| C4 participant mode scoped to declared requirements | carries by byte-identity | `run.py`, `requirements.py` unchanged; not re-run this pass (`Uncovered`) |
| S3 no current document quotes the retired value | yes | `grep` finds the old value only in history rows and STATUS comments |

### What the builder did not report, and hygiene

- `git show --stat f8a755f`: seven files, each named in the message. `.clarity/coverage.json`
  changed one receipt (`services/observation/KNOWN-GAPS.md`, `artifact_digest` `56683e1d...`,
  which is the file's current digest; `sov_clarity.py check` `PASS`). `docs/documentation.html`
  changed one line, regenerated; accepted on the `documentation reader` check and not read.
- Oracles not weakened: `kernel_predicates.py`, `requirements.py`, `run.py`, `oracle-controls.json`
  byte-identical to pass 3; `test_kernel_predicates.py` adds 24 lines and deletes none.
- Module sizes: `record.py` 192, `observe.py` 167, `relation.py` 198, `service.py` 176, all under
  300; `test_thin_slice.py` 474 (a test module; `lint.py` passes with 10 named debt, none here).
- Vocabulary: no new reason code, standing, event, edge, or role term. `UNREADABLE` and
  `PREDICATES_UNDECLARED` are the manifest's (`service.json`). The new detail strings ("records an
  output with no producer") are prose, not enum values.
- Secrets: the diff carries no key, token, credential, private-key, or absolute-path shape.
- Not the builder's: clarity `UNCHECKED` rose from 1 to 3 on two skill pages from `9e4fdea`.

### Finding on the check itself

- **`scripts/sov_standing.py` reads a declaration where a measurement is one module away.** The
  check "standing claims carry a witness" (`scripts/sovverify/checks.py:49`) reads the
  `standing_supported` field of the first ```witness block in `witness/observation-service.md`
  and stops (`scripts/sovstanding/records.py`, `declared_block`); it reads neither the block's
  `revision` nor the tree. Before this pass it read `SUPPORTED` on a tree where every receipt for
  the subject was `STALE_SUBJECT`. The measured half exists: `sov_witness_layer.py records`
  recomputes every receipt digest and, by design (`witness/observations/README.md`), grades
  staleness as debt. Consequence: a subject may be rewritten wholesale after `WITNESSED` and the
  gate that carries the claim never turns; only a debt line does, and `verify.py` exits 0. The
  builder's `KNOWN-GAPS.md` says plainly that the bytes owe a fresh pass, which is the right
  repair from the builder's side and is not what the gate reads. Currently correct on its own
  terms; recorded because the dominant defect in this repository's history is a check that
  cannot see what it grades. Not the builder's defect; J5 below.

### Residuals (the builder's to absorb; none holds the transition)

- **R12, carried in part - LOW, `conformance/kernel_predicates.py:214,219`.** Two of the three
  rules pass 3 named can still be deleted unseen. The whole-corpus count (46 of 97 appends
  pinned; `requirements.py` 12 of 53) is the size of the remaining pin, stated so the next pass
  can measure against it rather than sample.
- **R14 - LOW, `observe.py:105-106` and `KNOWN-GAPS.md` R11 line.** The claim is wider than the
  guard: "a substituted record cannot ride in on an earlier inference" holds for a malformed
  substitute and fails for a well-formed one (P7e, P7h). Either bind the inference to the
  record's entry digests (which closes F8) or narrow the sentence to what the guard does.
- **R9 - carried.** This record has no clarity receipt; the receipt lives in
  `.clarity/coverage.json`, which this invocation does not permit the witness to write.
- **The `3087714` citations.** `STATUS.yaml:46-50` and `contracts/status-claims.json:164` name the
  commit pass 3 observed. Accurate as history; a reader of the field learns nothing about the
  current bytes from them. Whoever holds the branch decides whether they move to `f8a755f`.

### Conditions

- **C1 (passes 1-3), carried unchanged.** The five observation operations still read
  `activation: ACTIVE`, `address: observation:in-process` from `capability_map.py:76-78` while
  `composition.py:187-190` routes no such address. Every file the condition names is
  byte-identical to pass 3. Discharge as pass 3 stated it.

### Judgement items (questions, not the witness's to answer)

- **J1-J4.** Carried from passes 2 and 3 unchanged.
- **J5.** Should the standing gate read the current witness receipt's `artifact_revision` and
  digests against the tree, so that a `*_status` value reading `WITNESSED` over moved bytes is at
  least named, or is `STALE_SUBJECT` as debt the intended reading for a value whose comment binds
  it to a commit?

### Uncovered

- Participant mode (`services/asset/scripts/conformance_observations.py` then `run.py --cases
  conformance/scenarios.json --observations ...`) was not re-run; the oracle files it exercises
  are byte-identical to pass 3, `conformance/scenarios.json` and the asset script were not
  digested.
- `docs/documentation.html` was accepted on `verify.py`'s regeneration check; its one changed
  line was not read.
- The five commits between `3087714` and `f8a755f` other than `900326e`'s `STATUS.yaml` and
  `status-claims.json` lines were read only as `git show --stat` lists them.
- `list-pending-observations`, `counter-observation`, and `attest-observation` remain `PROPOSED`
  and were not examined.
- No network, no `gh`, no ruleset query.

### Landing residual

As at pass 3: writing this record makes `docs/documentation.html` stale
(`scripts/sovdocs/facets.py` indexes `witness/*.md`), so `python scripts/verify.py` is expected to
return 1 on `documentation reader` and on `repository tooling tests`
(`scripts/tests/test_sov_docs.py`, `test_the_built_page_is_current`). The witness may not
rebuild the page; whoever lands this record runs `python scripts/sov_docs.py build`. Every check
under `Verified` ran before either file was written and `verify.py` read 0 then. Post-write
readings are recorded in the receipt's `telemetry.post_write`.

### Probe

Two probes, both run from a scratch directory against `services/observation/src` at the commit
above; neither is a file in this repository.

The first is pass 3's probe, quoted in full under `Pass 3 / Probe`, with its `sys.path` line made
absolute. Every output line matched pass 3's record except P1d and P7d, recorded above.

The second adds the cases the new guards and the R11 wording invite:

```python
import hashlib, sys
sys.path.insert(0, 'services/observation/src')  # relative to the repository root
from soveraeign_observation_service import ObservationService, RunRecord, ObservationRefused
RUN = "urn:soveraeign:run:probe"; OUT = b'{"standing": "RECORDED"}'; OUTD = hashlib.sha256(OUT).hexdigest()
def e(eid, kind, subject, actor, payload):
    return {"entry_id": eid, "kind": kind, "subject": subject, "actor": actor,
            "payload": payload, "entry_digest": hashlib.sha256(eid.encode()).hexdigest()}
class Clock:
    t = 0
    def __call__(self):
        Clock.t += 1; return f"2026-09-05T{Clock.t//60:02d}:{Clock.t%60:02d}:00+00:00"
def base(out_actor="worker-a"):
    return [
        e("g-root","EVENT","grant-root","seat:root",{"event":"GRANT","holder_id":"orch","parent_grant_id":None}),
        e("g-run","EVENT","grant-run","orch",{"event":"GRANT","holder_id":"worker-a","parent_grant_id":"grant-root"}),
        e("g-z","EVENT","grant-z","orch",{"event":"GRANT","holder_id":"witness-z","parent_grant_id":"grant-root"}),
        e("attempt","EVENT",RUN,"worker-a",{"event":"ATTEMPTED","lease":{"holder_id":"worker-a"},"grant_id":"grant-run"}),
        e("out1","EVENT","out/1",out_actor,{"event":"OUTPUT","digest":OUTD}),
        e("report","EVENT",RUN,"worker-a",{"event":"REPORTED","output_record_addresses":["out/1"]}),
    ]
def infer(name, ents, cand="witness-z"):
    svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, ents)
    try:
        inf = svc.infer_relation(rec, cand, "MODEL"); print(name, inf["outcome"], [x["edge"]+"@"+x["evidence_address"] for x in inf["edges_found"]], "receipts=%d" % len(svc.receipts))
    except ObservationRefused as r: print(name, "REFUSED", svc.receipts[-1]["reason_code"], "|", r, "receipts=%d" % len(svc.receipts))
    return svc, rec
print("== R10 edges ==")
ents = base(); del ents[4]["actor"]; infer("P1g OUTPUT actor key absent", ents)
ents = base(); ents[4]["actor"] = None; infer("P1h OUTPUT actor None", ents)
ents = base(); ents[4]["kind"] = "RECEIPT"; infer("P1i OUTPUT-event entry kind RECEIPT, actor empty", [*ents[:4], dict(ents[4], actor=""), ents[5]])
print("== R11 edges: observe_run over a substituted record after a good inference ==")
def observe_sub(name, substituted, pred_addr="out/1"):
    svc = ObservationService(Clock()); svc.infer_relation(RunRecord.from_entries(RUN, base()), "witness-z", "MODEL")
    svc.declare_predicates(RUN, [{"predicate_id":"p","kind":"BYTES_PRESENT","address":pred_addr}])
    try:
        o = svc.observe_run(RunRecord.from_entries(RUN, substituted), "witness-z", lambda a: OUT)
        print(name, "OBSERVED", o["predicate_results"], "observations=%d" % len(svc.observations), [r["outcome"] for r in svc.receipts])
    except ObservationRefused as r: print(name, "REFUSED", svc.receipts[-1]["reason_code"], "|", r, "observations=%d" % len(svc.observations))
sub = base(); sub[4]["actor"] = ""; observe_sub("P7f substituted: OUTPUT lost its producer", sub)
sub = base(); del sub[0]["entry_digest"]; observe_sub("P7g substituted: GRANT lost its digest", sub)
sub = base(); sub[5]["entry_id"] = None; observe_sub("P7d substituted: REPORTED lost entry_id (pass 3)", sub)
sub = base(); sub.insert(4, e("attempt2","EVENT",RUN,"witness-z",{"event":"ATTEMPTED","lease":{"holder_id":"witness-z"},"grant_id":"grant-z"})); observe_sub("P7e substituted, well-formed: observer now an executor", sub)
sub = base(out_actor="witness-z"); observe_sub("P7h substituted, well-formed: observer now the producer", sub)
print("== direct inference over the same P7e/P7h records, for contrast ==")
ents = base(); ents.insert(4, e("attempt2","EVENT",RUN,"witness-z",{"event":"ATTEMPTED","lease":{"holder_id":"witness-z"},"grant_id":"grant-z"})); infer("P7e' inferred directly", ents)
infer("P7h' inferred directly", base(out_actor="witness-z"))
```

Guard reverts: copy `services/observation` to a scratch directory, point the test bootstrap's
`ROOT` at the repository, delete `record.py:97-98` (R10), delete `observe.py:108-110` (R11), or
set `observe.py:121` to `own_entries = record.run_entry_ids()` (R13), and run the named test
class. Mutation sweep: copy `conformance/` to a scratch directory; for every
`Expr(Call(Attribute(Name('defects'), 'append')))` node in `kernel_predicates.py` and
`requirements.py`, replace the node's line span with `pass` at the same indentation, run
`python -m unittest discover -s tests` and `python run.py --cases oracle-controls.json` from the
copy, read `failures=` against the copy's baseline `FAILED (errors=2)` and the `SUITE` line,
restore.

## Pass 3: commit 3087714 (2026-09-03)

Verdict: **RATIFIABLE-WITH-CONDITIONS**.

Subject: `observation_service_status` in `STATUS.yaml`, value
`BUILT_THIN_SLICE_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED`, scoped this pass to the
residuals R1-R9 pass 2 recorded and to whether pass 2's conclusions still hold on the new bytes.

Commit witnessed: `308771445a669dba6810848d99586e16d732e02f` on `claude/phase-1-5-to-2-hbsv79`,
one commit past `540bc01` (`git log --oneline 540bc01..3087714` lists exactly it).
`git status --short` was empty before and after every command below and `git rev-parse HEAD`
read the same commit throughout. The builder's report
(`reports/2026-09-03-phase-1-5-commissioning-pass.md`) came up as a diff in the same batch as
the probe, after the probe had run; nothing below is taken from it, and where it is named it is
named as a claim.

Witness: `claude-fable-5-1/sov-witness@2026-09-03`, third invocation. This participant did not
build, edit, stage, or commit anything under the subject. The only files it changed are this
record and `witness/observations/2026-09-03-observation-service-observation-3.json`. The probe
ran from a scratch directory and is quoted in full under `Probe`; the invocation permitted no
file under `witness/probes/`.

### Standing supported

`BUILT -> WITNESSED` for `observation_service_status` at `3087714`. Six of the nine residuals
are repaired through the declared surface with a refusing or direct-edge case each (R1, R2, R4,
R6, R7, R8); two are carried as documented defaults (R3 in part, R5); one is outside the
witness's files (R9). Every pass-1 and pass-2 conclusion re-run on the new bytes holds. The
record binds to the subject `observation-service`, the field `observation_service_status`,
the revision above, and this claim: the five operations `request-observation`,
`declare-predicates`, `infer-relation`, `observe-run`, and `read-observation` are built,
self-tested, and independently observed through `ObservationService` and
`RunRecord.from_entries`; `list-pending-observations`, `counter-observation`, and
`attest-observation` are declared and unbuilt; no binding routes any of the eight. A moved
value must assert `WITNESSED` as a whole token for the thin slice only and assert neither
reachability nor ratification; `contracts/status-claims.json:160-163` still reads "no
independent observation exists" and moves with it. This is an observation. It supports the
transition and ratifies nothing.

### Verified

Commands run from the repository root at the commit above.

| Command | Exit | Excerpt |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --short` | 0; 0 | `308771445a669dba6810848d99586e16d732e02f`; empty |
| `python scripts/verify.py` | 0 | `PASS: 50 checks in 14.754s wall`; `GRADE: SILVER`; `BUDGET DEBT: 9 check(s) over ceiling` (attributed, non-refusing). The `FAIL` lines in its output are emitted by the tooling self-tests over planted trees inside `repository tooling tests`; the verdict line is the `PASS: 50 checks` line and the exit code |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1169 text files, 546 Python modules, 10 named debt)` |
| `python -m unittest discover -s tests` in `services/observation` | 0 | `Ran 49 tests OK` (43 at pass 2; six new in `WitnessResidualsOn540bc01`) |
| `python conformance/run.py` | 0 | `SUITE PASS cases=33 coverage_gaps=0`; every `*-DEF` control `FAIL`, every `*-POS` `PASS` |
| `python -m unittest discover -s conformance/tests` | 0 | `Ran 79 tests OK` |
| `python scripts/sov_f2_gate.py` | 1 | `requirement 25/25`, `transition 14/14`, `parity 5/5`; `participants 1/2 bound`; `OPEN` on the second participant only |
| `python scripts/sov_phase_progress.py check` | 0 | `PASS: the gate reading meets its floor and every gap below it is declared`; `NONE_ACTIVE` |
| `python scripts/sov_baseline.py` | 0 | `PASS: participant matches its recorded baseline (9 requirements, 8 failing as recorded)` |
| `python scripts/sov_clarity.py status` / `check` | 0 / 0 | `STALE 0, UNCHECKED 1, EXEMPT 88`; `PASS`. The one `UNCHECKED` is this file (R9) |
| participant mode: `services/asset/scripts/conformance_observations.py`, then `run.py --cases conformance/scenarios.json --observations ... --json` | 0 / 1 | `suite FAIL`, 9 cases, `missing_positive_and_defeating_coverage []`; `PROD-I-2 PASS`, eight `FAIL` on requirement defects (C4 holds) |
| mutation probe, targeted (scratch copy of `conformance/`, one `defects.append` replaced with `pass`, `unittest discover -s tests`; scratch baseline `FAILED (errors=2)` from two loader errors) | n/a | 11 of 11 rules pass 2 named still noticed (`kernel_predicates.py:44,80,126,150,153,160,164,181,183,233`, `requirements.py:109`: `failures>=1`). Three rules a random sample reached are not: `:168`, `:214`, `:219` read the baseline `errors=2` only (R12). `run.py` alone reads `SUITE PASS` for every deletion but `:105`, as before |
| join-grader defeat (scratch copy; `CONF-RUN-SETTLE-DEF` additionally declares `TRANS-observe_run`) | n/a | `test_defeating_controls_defeat_what_they_claim` fails: `CONF-RUN-SETTLE-DEF claims TRANS-observe_run; defects: settlement cites no observation of this run run settled against a stale state`; `run.py` alone still `SUITE PASS` (R7) |
| R6 regression strength (scratch copy of `services/observation` with `observe.py:116` `\| {record.run_id}` reverted; `WitnessResidualsOn540bc01` only) | n/a | `Ran 6 tests OK`: the R6 test passes without the R6 repair (R13) |
| relation/receipt probe (quoted below) | 0 | outputs recorded per residual under `Residuals re-derived`; the happy path reads `UNRESOLVED`, `INDEPENDENT`, `{'p': True}`, four receipts `RECORDED, COMMITTED, COMMITTED, COMMITTED` |
| `sha256sum` | 0 | `scripts/sovkernel/transitions.py` `478fe0a0...`, `conformance/kernel_predicates.py` `f1d81c80...`, `conformance/requirements.py` `4b2fe7b3...`, `conformance/run.py` `c049f9e6...`, `conformance/oracle-controls.json` `75b4cf02...`, `scripts/sovverify/checks.py` `a5316c26...`, `service.py` `e20b03b9...`, `errors.py` `8ce373e7...`: byte-identical to pass 2, so pass 2's readings of the kernel parity, the oracle, the verify harness, and the service façade carry. Changed under the subject: `record.py`, `relation.py`, `observe.py`, `test_thin_slice.py`, `KNOWN-GAPS.md`, `test_kernel_predicates.py`, `CLAUDE.md`, `.clarity/coverage.json` (two receipts) |

### Residuals re-derived

Each verdict comes from a probe through `ObservationService` and `RunRecord.from_entries`, from
a scratch mutation, or from a repository gate. The builder's list of repairs was not consulted
for any of them.

| Residual | Verdict | Evidence |
| --- | --- | --- |
| R1 anonymous entry dropped | **REPAIRED** for entries on the run; **changed shape** off the run (R10) | `record.py:78-95` `malformed()` requires an actor on every entry whose subject is the run; `relation.py:123-125` refuses `UNREADABLE` before anything else is read. P1b (anonymous `REPORTED`), P2c (anonymous second `ATTEMPTED`), P1c (`actor` key absent): each `REFUSED UNREADABLE`, one receipt, detail `entry <address> on the run names no actor`. P1d: an `OUTPUT` entry with an empty actor is off the run, so it is not refused; the candidate reads `INDEPENDENT []` |
| R2 first attempt's lease and grant only | **REPAIRED** | `relation.py:137-150` reads every attempt. P2b: lease holder `lessee-c` of a second attempt reads `DIRECT [HOLDS_RUN_LEASE@attempt2, GRANT_DESCENDS_FROM_RUN@g-c]`. P2d: `helper-b`, whose grant descends from the second attempt's grant, reads `DIRECT [GRANT_DESCENDS_FROM_RUN@g-b2]`. P2e: a second attempt whose payload omits `grant_id` reads `RELATION_UNDETERMINED`, the absent-key rule applied per attempt. P2 now reads three edges for the second attempt's actor |
| R3 refused run refuses `INCOMPLETE_PROPOSAL`; surface untested | **changed shape**: tested, not renamed, not in `KNOWN-GAPS.md` | `test_thin_slice.py` `test_a_refused_run_with_nothing_to_read_is_refused_through_the_surface` drives `request_observation` on a refused run and asserts the refusal's detail, which closes the untested half. P8b: `is_terminal() True`, `terminal_outcome() REFUSED`, request `REFUSED INCOMPLETE_PROPOSAL: the run reported no durable output to observe`, unchanged. `observation-request.schema.json:33-36` requires `durable_output_addresses` with `minItems: 1`, so the reason has a defensible reading: a request the schema cannot carry. `grep INCOMPLETE_PROPOSAL services/observation/KNOWN-GAPS.md` finds nothing; the default is stated in the builder's report only |
| R4 `OUTPUT` without subject refuses under the wrong name | **REPAIRED** | P4b (`subject` absent) and P4b' (`subject` empty): `REFUSED UNREADABLE: entry out1 has no subject`, one receipt. P4 (`GRANT` without subject) moved from `RELATION_UNDETERMINED` to `UNREADABLE` by the same guard |
| R5 docstring says a settled run could never be observed | **REPAIRED** as documentation | `record.py:21-25` and `KNOWN-GAPS.md` "Terminal means no longer in flight" now say a settled run may still be observed and name `counter-observation` as the reason. P8d unchanged: `COMMITTED`, `INDEPENDENT`. `test_a_settled_run_may_still_be_observed` covers it through the surface |
| R6 own-entry guard keys on `entry_id` | **REPAIRED** at the surface, with two notes (R11, R13) | `observe.py:116` adds the run id to the guarded set. P7b: the run id reported as an output and recorded by an `OUTPUT` entry refuses `PREDICATES_UNDECLARED: reads-run reads urn:soveraeign:run:probe, which is the run's own entry`. P4e: a `REPORTED` entry without `entry_id` now refuses `UNREADABLE` at inference. P4f (`kind` empty), P4g (bad `entry_digest`): `UNREADABLE` |
| R7 join grader matches substrings | **REPAIRED** | `test_kernel_predicates.py:224-246` `WORDS` holds rule-specific defect prefixes; each listed phrase is the opening of one `defects.append` string in `kernel_predicates.py` or `requirements.py` (44 strings listed and compared). Defeat run above: an over-declaring control now fails the test while `run.py` alone still passes. It remains a text classifier over the joined defect text, but the phrases no longer cross rule families, and a rule whose text matches no phrase credits nothing, which fails in the safe direction |
| R8 `CLAUDE.md` contradicts itself on Gateway | **REPAIRED** | `CLAUDE.md:118-119`: "Proofing and Asset Projection are boundaries with no implementation; Gateway has the one in-process route named above and nothing more", consistent with `:85` and `services/README.md:15`; `sov_snapshot` passes inside `verify.py`. The page's clarity receipt was re-recorded (`.clarity/coverage.json`, `changed: true`) |
| R9 this record has no clarity receipt | **STILL OPEN** | `sov_clarity.py status` reads `UNCHECKED 1`, this file. The receipt lives in `.clarity/coverage.json`, which this invocation does not permit the witness to write. A reviewer who is not this witness may record it; it is not a build claim |

### Pass-2 conclusions, re-run on the new bytes

| Conclusion | Holds | Evidence |
| --- | --- | --- |
| F1 reporter is an executor edge | yes | P1: `DIRECT [SAME_ACTOR@report]` |
| F2 second attempt's actor is an edge | yes | P2: `DIRECT [SAME_ACTOR@attempt2, HOLDS_RUN_LEASE@attempt2, GRANT_DESCENDS_FROM_RUN@g-b]` |
| F3 malformed record refuses `UNREADABLE` with one receipt | yes, widened | P3, P3b, P4c, P4d as at pass 2; P4, P4b, P4e, P4f, P4g now also `UNREADABLE`, one receipt each |
| F4 reported unsettled run is not named `COMMITTED` | yes | P8: `UNRESOLVED`; P8c: `REFUSED`; the default is now written in `KNOWN-GAPS.md`; J1 stands |
| F5 malformed declared digest refuses | yes | P6: `REFUSED UNREADABLE: the record declares no sha256 digest for out/1` |
| F6 run's grant absent reads `INDEPENDENT` | still open, note | P5: `INDEPENDENT []`, unchanged |
| F7 report entry is not a predicate address | yes | P7: `PREDICATES_UNDECLARED ... run's own entry` |
| F8 notes | unchanged, plus R11 | P9: thin record refuses `PREDICATES_UNDECLARED`; P10 `False`; P10b `True` |
| C2 `CONF-RUN-DEF` declares only what it defeats | yes | `oracle-controls.json` unchanged (`75b4cf02...`); control declares `TRANS-observe_run`, `TRANS-settle_run`, `defects=4` |
| C3 rules can be seen to disappear | yes for the 11 named; see R12 | targeted mutation round above |
| C4 participant mode scoped to declared requirements | yes | `missing_positive_and_defeating_coverage []` |
| S3 no current document quotes the retired value | yes | `grep` at pass 2; `SERVICE-SPEC.md` unchanged since |

### New residuals (the builder's to absorb; none holds the transition)

- **R10 - LOW, `record.py:92-94` against `relation.py:101`.** `malformed()` requires an actor
  only on entries whose subject is the run. P1d: an `OUTPUT` entry with an empty actor is kept,
  and `PRODUCED_THE_OUTPUT` compares that empty actor to the candidate, so an output nobody
  signed is nobody's and the candidate reads `INDEPENDENT []`. Consequence if left: a projection
  that loses an output's producer admits the producer as observer. The same rule R1 applied
  to the run's entries applies here.
- **R11 - LOW, `observe.py:97-137`.** `observe_run` never calls `record.malformed()`; only
  `infer_relation` does. P7d: infer over a well-formed record, then observe over a record whose
  `REPORTED` entry has lost its `entry_id`, with a predicate over the report's address: it
  evaluates `True` with three `COMMITTED` receipts. Reachable only by handing `observe_run` a
  different record than the one inferred over (`service.py:143-145`, pass 1's F8), so it is
  F8's note widened, not R6 reopened.
- **R12 - LOW, `conformance/kernel_predicates.py:168,214,219`.** Three rules ("observation
  entered with a standing other than OBSERVATION", "discovery names no interface", "binding
  missing <field>") can be replaced with `pass` without `conformance/tests` noticing. C3 was
  repaired over the sample pass 2 named and holds for it; the corpus pin is still partial.
- **R13 - LOW, `test_thin_slice.py` `test_the_run_id_itself_is_not_a_predicate_address`.**
  The test declares a predicate over the run id, which is also unreported, so the older
  "not a recorded durable output" guard raises the same `PredicatesUndeclared` and the test
  passes with `observe.py:116` reverted. It is a positive case for R6, not its defeating
  fixture; P7b above is.

### Conditions

- **C1 (pass-1 S1, pass-2 C1), carried and re-attributed.** The five observation operations
  still read `activation: ACTIVE`, `address: observation:in-process` in
  `contracts/fixtures/capability-map.reference.json` while `scripts/sovnode/composition.py:187-190`
  routes no such address and the Node Interface shows `reachability: []` beside them. This
  pass read the source of that row: `scripts/sovkernel/capability_map.py:76-78` sets `ACTIVE`
  at `<service>:in-process` for every built operation on the `IN_PROCESS` transport, and
  `scripts/sov_capability.py` rebuilds the fixture from that rule. The row is the map policy's
  output, not a hand edit inside this concern; pass 2's "repair the row" framing was wrong, and
  the Record Service reads the same way. What would discharge it: either the rule activates
  `IN_PROCESS` only when the composition routes the address, or the map's owner writes what
  `ACTIVE` at an in-process address means and where a reader learns that. Until then a derived
  artifact declares a door the composition does not open. It does not falsify the standing
  value, which claims no reachability.
- **C2 (pass 2), discharged.** Regression cases through the surface now exist for the
  anonymous entry, the second attempt's lease and grant, and the refused run.

### Judgement items (questions, not the witness's to answer)

- **J1.** Carried: may `run_outcome` carry `UNRESOLVED`, a `settle_run` outcome, for a run the
  kernel has not settled? `KNOWN-GAPS.md` now records the default and asks the same question.
- **J2.** Carried: is a false declaration in a derived artifact admissible under
  `REMAINDER_DECLARED` when it is the output of the map's own rule rather than an edit?
- **J3.** Carried: should a clarity receipt carry the reading's scope?
- **J4.** Does `INCOMPLETE_PROPOSAL` ("a request or declaration omits a field the contract
  requires") cover a run that is terminal but reported nothing durable, because the request
  schema cannot carry it, or does that run need its own reason code? The code and the schema
  agree today; the manifest's owner has not said so.

### Uncovered

- `docs/documentation.html` was accepted on `verify.py`'s regeneration check; the 107 changed
  lines were not read.
- The builder's report was read only as the diff `540bc01..3087714` shows it, after the probe.
- `list-pending-observations`, `counter-observation`, and `attest-observation` remain
  `PROPOSED` and were not examined.
- The clarity rewrites of pass 2 were not re-reviewed; only the two receipts this commit
  changed (`CLAUDE.md`, `KNOWN-GAPS.md`) were checked against their bytes.
- No network, no `gh`, no ruleset query.

### Landing residual

With this record and its receipt present, `python scripts/verify.py` returned 1 on two checks
with one cause: `documentation reader` (`docs/documentation.html is stale`;
`scripts/sovdocs/facets.py` indexes `witness/*.md`) and `repository tooling tests`, whose
`scripts/tests/test_sov_docs.py:204-206` `test_the_built_page_is_current` calls the same
`sov_docs.cmd_check` and read `1 != 0`. Pass 2 predicted the first only; the second is the
same staleness reaching `verify.py` through a second check. The witness may not rebuild the
page; whoever lands this record runs `python scripts/sov_docs.py build`. Every check under
`Verified` was run before either file was written, and `verify.py` read 0 then. After
writing: `python scripts/sov_standing.py` 0 (`PASS: no status field claims WITNESSED or
RATIFIED (1 record(s) on file)`), `python scripts/lint.py` 0 (`1170 text files`),
`python scripts/sov_witness_layer.py records` 0 (this pass's receipt `CURRENT`, 27 digests
recomputed; passes 1 and 2 `STALE_SUBJECT`, as expected of receipts naming an earlier
commit). R9 remains after landing unless a reviewer records the receipt.

### Probe

Run from a scratch directory against `services/observation/src` at the commit above; not a
file in this repository. Each case reaches the service only through `ObservationService` and
`RunRecord.from_entries`.

```python
import hashlib, sys
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
        Clock.t += 1; return f"2026-09-03T{Clock.t//60:02d}:{Clock.t%60:02d}:00+00:00"
def base(lease_holder="worker-a", grant="grant-run", out_actor="worker-a", report_actor="worker-a"):
    return [
        e("g-root","EVENT","grant-root","seat:root",{"event":"GRANT","holder_id":"orch","parent_grant_id":None}),
        e("g-run","EVENT","grant-run","orch",{"event":"GRANT","holder_id":"worker-a","parent_grant_id":"grant-root"}),
        e("g-b","EVENT","grant-b","orch",{"event":"GRANT","holder_id":"worker-b","parent_grant_id":"grant-root"}),
        e("g-c","EVENT","grant-c","orch",{"event":"GRANT","holder_id":"lessee-c","parent_grant_id":"grant-root"}),
        e("g-z","EVENT","grant-z","orch",{"event":"GRANT","holder_id":"witness-z","parent_grant_id":"grant-root"}),
        e("attempt","EVENT",RUN,"worker-a",{"event":"ATTEMPTED","lease":{"holder_id":lease_holder},"grant_id":grant}),
        e("out1","EVENT","out/1",out_actor,{"event":"OUTPUT","digest":OUTD}),
        e("report","EVENT",RUN,report_actor,{"event":"REPORTED","output_record_addresses":["out/1"]}),
    ]
def run(name, entries, candidate, kind="WORKER"):
    svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, entries)
    try:
        inf = svc.infer_relation(rec, candidate, kind)
        print(name, inf["outcome"], [x["edge"]+"@"+x["evidence_address"] for x in inf["edges_found"]], "receipts=%d" % len(svc.receipts))
    except ObservationRefused as r: print(name, "REFUSED", svc.receipts[-1]["reason_code"] if svc.receipts else "NO-RECEIPT", "|", r, "receipts=%d" % len(svc.receipts))
    except Exception as r: print(name, "ESCAPED", type(r).__name__, r, "receipts=%d" % len(svc.receipts))
    return svc, rec
print("== F1/F2 (pass-2 conclusions) ==")
run("P1  reporter-as-candidate", base(report_actor="worker-b"), "worker-b")
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"worker-b",{"event":"ATTEMPTED","lease":{"holder_id":"worker-b"},"grant_id":"grant-b"}))
run("P2  second-attempt actor", ents, "worker-b")
print("== R2 ==")
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"worker-b",{"event":"ATTEMPTED","lease":{"holder_id":"lessee-c"},"grant_id":"grant-c"}))
run("P2b second-attempt lease holder", ents, "lessee-c")
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"worker-b",{"event":"ATTEMPTED","lease":{"holder_id":"worker-b"},"grant_id":"grant-b"}))
ents.append(e("g-b2","EVENT","grant-b2","worker-b",{"event":"GRANT","holder_id":"helper-b","parent_grant_id":"grant-b"}))
run("P2d second-attempt grant descendant", ents, "helper-b")
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"worker-b",{"event":"ATTEMPTED","lease":None}))  # no grant_id key
run("P2e second attempt omits grant_id key", ents, "witness-z")
print("== R1 ==")
run("P1b anonymous REPORTED", base(report_actor=""), "witness-z")
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"",{"event":"ATTEMPTED","lease":None,"grant_id":None}))
run("P2c anonymous second ATTEMPTED", ents, "witness-z")
ents = base(); del ents[7]["actor"]; run("P1c REPORTED lacks actor key", ents, "witness-z")
run("P1d anonymous OUTPUT (off-run entry)", base(out_actor=""), "witness-z")
ents = base(); ents[4]["actor"] = ""; run("P1e anonymous GRANT entry", ents, "witness-z")
ents = base(); ents[4]["payload"].pop("holder_id"); run("P1f GRANT without holder_id", ents, "witness-z")
print("== F3 / R4 / R6 (malformed record) ==")
ents = base(); [x.pop("entry_digest") for x in ents]; run("P3  no digests", ents, "witness-z")
ents = base(); del ents[5]["entry_digest"]; run("P3b attempt no digest", ents, "witness-z")
ents = base(); del ents[4]["subject"]; run("P4  GRANT no subject", ents, "witness-z")
ents = base(); del ents[6]["subject"]; run("P4b OUTPUT no subject", ents, "witness-z")
ents = base(); ents[6]["subject"] = ""; run("P4b' OUTPUT empty subject", ents, "witness-z")
ents = base(); ents[5]["payload"] = None; run("P4c payload None", ents, "witness-z")
ents = base(); ents[5]["payload"] = "junk"; run("P4d payload str", ents, "witness-z")
ents = base(); ents[7]["entry_id"] = None; run("P4e REPORTED no entry_id", ents, "witness-z")
ents = base(); ents[6]["kind"] = ""; run("P4f OUTPUT kind empty", ents, "witness-z")
ents = base(); ents[6]["entry_digest"] = "sha256:zz"; run("P4g OUTPUT bad entry_digest", ents, "witness-z")
print("== F6 ==")
run("P5  run grant absent", base(grant="grant-unknown"), "witness-z")
print("== F5 ==")
ents = base(); ents[6]["payload"]["digest"] = "not-a-digest"
svc, rec = run("P6a", ents, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"p","kind":"BYTES_PRESENT","address":"out/1"}])
try: print("P6  malformed OUTPUT digest", svc.observe_run(rec, "witness-z", lambda a: b"anything")["predicate_results"])
except ObservationRefused as r: print("P6  malformed OUTPUT digest REFUSED", svc.receipts[-1]["reason_code"], "|", r, "receipts=%d" % len(svc.receipts))
print("== F7 / R6 ==")
ents = base(); ents[7]["payload"]["output_record_addresses"] = ["out/1", "report"]
ents.append(e("out-report","EVENT","report","worker-a",{"event":"OUTPUT","digest":hashlib.sha256(b'{"claim":"done"}').hexdigest()}))
svc, rec = run("P7a", ents, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"reads-report","kind":"JSON_FIELD_EQUALS","address":"report","field":"claim","expected":"done"}])
try: print("P7  report entry as address", svc.observe_run(rec, "witness-z", lambda a: b'{"claim":"done"}' if a == "report" else OUT)["predicate_results"])
except ObservationRefused as r: print("P7  report entry as address REFUSED", svc.receipts[-1]["reason_code"], "|", r)
ents = base(); ents[7]["payload"]["output_record_addresses"] = ["out/1", RUN]
ents.append(e("out-run","EVENT",RUN,"worker-a",{"event":"OUTPUT","digest":hashlib.sha256(b'{"claim":"done"}').hexdigest()}))
svc, rec = run("P7b run id as OUTPUT subject (ids intact)", ents, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"reads-run","kind":"JSON_FIELD_EQUALS","address":RUN,"field":"claim","expected":"done"}])
try: print("P7b run id as predicate address", svc.observe_run(rec, "witness-z", lambda a: b'{"claim":"done"}' if a == RUN else OUT)["predicate_results"])
except ObservationRefused as r: print("P7b run id as predicate address REFUSED", svc.receipts[-1]["reason_code"], "|", r)
# P7d: infer over a well-formed record, then observe over one whose REPORTED entry lost its id (F8 reuse; observe.py has no malformed() call)
svc = ObservationService(Clock()); good = base(); good[7]["payload"]["output_record_addresses"] = ["out/1", "report"]
good.append(e("out-report","EVENT","report","worker-a",{"event":"OUTPUT","digest":hashlib.sha256(b'{"claim":"done"}').hexdigest()}))
svc.infer_relation(RunRecord.from_entries(RUN, good), "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"reads-report","kind":"JSON_FIELD_EQUALS","address":"report","field":"claim","expected":"done"}])
bad = [dict(x) for x in good]; bad[7] = dict(bad[7]); bad[7]["entry_id"] = None
try: print("P7d observe over record whose REPORTED lost entry_id (F8 reuse)", svc.observe_run(RunRecord.from_entries(RUN, bad), "witness-z", lambda a: b'{"claim":"done"}' if a == "report" else OUT)["predicate_results"], "receipts=%d" % len(svc.receipts))
except ObservationRefused as r: print("P7d REFUSED", svc.receipts[-1]["reason_code"], "|", r)
print("== F4 / R3 / R5 ==")
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, base())
print("P8  reported unsettled ->", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"])
refused = base()[:6] + [e("rcpt","RECEIPT",RUN,"kernel",{"outcome":"REFUSED","event":"begin_run"})]
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, refused)
print("P8b refused-before-report is_terminal/outcome:", rec.is_terminal(), rec.terminal_outcome())
try: print("P8b", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"])
except ObservationRefused as r: print("P8b request on refused run REFUSED", svc.receipts[-1]["reason_code"], "|", r)
refused2 = base() + [e("rcpt","RECEIPT",RUN,"kernel",{"outcome":"REFUSED","event":"report_run"})]
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, refused2)
print("P8c refused after report ->", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"])
settled = base() + [e("rcpt","RECEIPT",RUN,"kernel",{"outcome":"COMMITTED","event":"settle_run"})]
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, settled)
print("P8d settled ->", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"], svc.infer_relation(rec, "witness-z", "MODEL")["outcome"])
print("== F8 ==")
svc = ObservationService(Clock()); full = RunRecord.from_entries(RUN, base())
svc.infer_relation(full, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"p","kind":"BYTES_PRESENT","address":"out/1"}])
thin = RunRecord.from_entries(RUN, [x for x in base() if x["entry_id"] != "out1"])
try: print("P9 ", svc.observe_run(thin, "witness-z", lambda a: OUT)["observation_id"])
except ObservationRefused as r: print("P9  thin record REFUSED", svc.receipts[-1]["reason_code"], "|", r)
obs = svc.observe_run(full, "witness-z", lambda a: OUT)
d2 = svc.declare_predicates(RUN, [{"predicate_id":"q","kind":"BYTES_PRESENT","address":"out/1"}])
print("P10 read_observation returns judged declaration:", svc.read_observation(obs["observation_id"])["declaration"]["declaration_id"] != d2["declaration_id"])
obs2 = svc.observe_run(full, "witness-z", lambda a: OUT)
print("P10b same id for different predicates:", obs2["observation_id"] == obs["observation_id"])
print("== happy path ==")
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, base())
print("PH", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"], svc.infer_relation(rec, "witness-z", "MODEL")["outcome"])
svc.declare_predicates(RUN, [{"predicate_id":"p","kind":"DIGEST_EQUALS","address":"out/1","expected":"sha256:"+OUTD}])
o = svc.observe_run(rec, "witness-z", lambda a: OUT); print("PH", o["predicate_results"], "receipts=%d" % len(svc.receipts), [r["outcome"] for r in svc.receipts])
```

Targeted mutation round: copy `conformance/` to a scratch directory, replace the
`defects.append(...)` statement at one line with `pass`, run
`python -m unittest discover -s tests` from the copy, read `FAILED (failures=N, errors=2)`
against the copy's baseline of `FAILED (errors=2)`, restore. Join-grader defeat: in a copy,
add `TRANS-observe_run` to `CONF-RUN-SETTLE-DEF`'s `predicates` in `oracle-controls.json`,
run `python -m unittest tests.test_kernel_predicates`. R13: in a copy of
`services/observation`, revert `observe.py:116` to `own_entries = record.run_entry_ids()`,
point the test bootstrap's `ROOT` at the repository, run `WitnessResidualsOn540bc01`.

## Pass 2: commit 540bc01 (2026-09-03)

Verdict: **RATIFIABLE-WITH-CONDITIONS**.

Subject: `observation_service_status` in `STATUS.yaml`, value
`BUILT_THIN_SLICE_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED`, together with the conformance
and derived-standing changes the same branch carries.

Commit witnessed: `540bc01f094320588749d2ba3c123aec53b71396` on `claude/phase-1-5-to-2-hbsv79`.
`git status --short` was empty before and after every command below and `git rev-parse HEAD`
read the same commit throughout. The builder's session report
(`reports/2026-09-03-phase-1-5-commissioning-pass.md`) and the two commit messages were read
only after every probe below had run; nothing in this section is taken from them.

Witness: `claude-fable-5-1/sov-witness@2026-09-03`, second invocation. This participant did not
build, edit, stage, or commit anything under the subject. The only files it changed are this
record and `witness/observations/2026-09-03-observation-service-observation-2.json`. Its probe
was run from a scratch directory outside the repository and is quoted in full under `Probe`,
because the invocation permitted no file under `witness/probes/`.

### Standing supported

`BUILT -> WITNESSED` for `observation_service_status`. The claim the value makes - five
operations built and self-tested, three declared and unbuilt, nothing yet witnessed - was
reproduced through the declared surface and the repository's own gates, and every defeat pass 1
found through that surface now refuses. One pass-1 condition (S1, the capability map) is not
repaired; it is documented instead. It does not falsify the standing value, which claims no
reachability, so it is carried here as a condition on ratification rather than a hold on the
observation. The residuals below are the builder's to absorb; none re-opens a route pass 1
closed. This is an observation. It supports the transition and ratifies nothing.

### Verified

Commands run from the repository root at the commit above.

| Command | Exit | Excerpt |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --short` | 0; 0 | `540bc01f094320588749d2ba3c123aec53b71396`; empty |
| `python scripts/verify.py` | 0 | `PASS: 50 checks in 14.764s wall`; `GRADE: SILVER`; `BUDGET DEBT: 9 check(s) over ceiling` (attributed, non-refusing) |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1168 text files, 546 Python modules, 10 named debt)`; the `STATUS.yaml` duplicate-key `WARN`s predate the branch |
| `python -m unittest discover -s tests` in `services/observation` | 0 | `Ran 43 tests OK` (37 at pass 1; six new in `WitnessFindingsOn169182f`) |
| `python conformance/run.py` | 0 | `SUITE PASS cases=33 coverage_gaps=0` |
| `python -m unittest discover -s conformance/tests` | 0 | `Ran 79 tests OK` (includes `test_kernel_predicates.py`, 41 cases) |
| `python scripts/sov_f2_gate.py` | 1 | `requirement 25/25`, `transition 14/14`, `parity 5/5`; `participants 1/2 bound`; `OPEN` on the second participant only |
| `python scripts/sov_phase_progress.py check` | 0 | `PASS`, floor 44 met, `NONE_ACTIVE` |
| `python scripts/sov_baseline.py` | 0 | `PASS: participant matches its recorded baseline (9 requirements, 8 failing as recorded)` |
| `python scripts/sov_clarity.py status` / `check` | 0 / 0 | `CURRENT 142, STALE 0, UNCHECKED 1, EXEMPT 88`; `PASS`. The one `UNCHECKED` is `witness/observation-service.md` itself (pass 1's file, committed in `162ffaf` without a clarity receipt) |
| `python conformance/run.py --json` (defects) | 0 | `CONF-RUN-DEF`: `executor observed its own run`, `observation admitted without an INDEPENDENT inference (DIRECT)`, `observation admitted with a direct edge to the run`, `a participant in the run settled it` - every defect names `observe_run` or `settle_run`, the two predicates it now declares |
| participant mode: `services/asset/scripts/conformance_observations.py` then `run.py --cases conformance/scenarios.json --observations ...` | 0 / 1 | `SUITE FAIL cases=9 coverage_gaps=0`; `PROD-I-2 PASS`; eight `FAIL` on requirement defects only. No `SPEC-*` gap |
| mutation probe (scratch copy of `conformance/`, one rule at a time) | n/a | 13 of 13 sampled deletions fail `conformance/tests` (`failures>=1` above the scratch baseline of two loader errors from tests that need the real root); `run.py` alone still reads `SUITE PASS` for 11 of them, as at pass 1. The pin is the test, and `scripts/sovverify/checks.py:116` runs `conformance/tests` inside `verify.py`, graded on the subprocess exit code (`scripts/sovverify/clocks.py:124`) |
| relation/receipt probe (quoted below) | 0 | P1 `DIRECT [SAME_ACTOR@report]`; P2 `DIRECT [SAME_ACTOR@attempt2]`; P3/P3b `REFUSED UNREADABLE receipts=1`; P4 `RELATION_UNDETERMINED receipts=1`; P4c/P4d `UNREADABLE receipts=1`; P6 `REFUSED UNREADABLE`; P7 `REFUSED PREDICATES_UNDECLARED ... run's own entry`; P8 `UNRESOLVED`; P8c `REFUSED`; P2b, P1b, P2c, P5, P8b, P8d, P9, P10, P10b as recorded under the findings |
| `sha256sum scripts/sovkernel/transitions.py` | 0 | `478fe0a065c8da6d...`, byte-identical to pass 1, so pass 1's kernel-parity reading (the kernel refuses the reporter by `reporter_id`, `transitions.py:116`) carries |

### Pass-1 findings, re-derived

Each verdict below comes from a probe through `ObservationService` and
`RunRecord.from_entries`, or from a repository gate; the builder's list of repairs was not
consulted until afterwards.

| Finding | Verdict | Evidence |
| --- | --- | --- |
| F1 reporter not an edge | **REPAIRED** | `record.py:86-98` `executors()` reads every `ATTEMPTED` and `REPORTED` actor; `relation.py:136-137`. P1: reporter `worker-b` reads `DIRECT`, `SAME_ACTOR` cited at the `REPORTED` entry |
| F2 only first attempt read | **REPAIRED for the actor; changed shape for the lease and grant** | P2: second attempt's actor reads `DIRECT`. P2b: `relation.py:139-149` still reads `lease` and `grant_id` from the first attempt only, so the lease holder of a second attempt who is not its actor reads `INDEPENDENT []` (residual R2) |
| F3 malformed entry escapes | **REPAIRED** | `service.py:77-80` turns `KeyError`, `TypeError`, `ValueError`, `AttributeError` into `UNREADABLE` with a receipt; `relation.py:103-108`. P3 (no `entry_digest` anywhere), P3b (attempt only), P4c/P4d (payload `None`/string): each refuses with exactly one receipt naming `UNREADABLE`. P4 (grant without `subject`) and P4b (output without `subject`) refuse `RELATION_UNDETERMINED` and `DIRECT ONLY_EXECUTOR_REPORT` with one receipt each; see R4 |
| F4 reported run named `COMMITTED` | **REPAIRED within condition 3; one question remains** | `record.py:138-148`. P8: reported, unsettled run yields `UNRESOLVED`; P8c: refused after report yields `REFUSED`. `UNRESOLVED` is in the request schema's enum and in `SPEC.md:393,446`. It is also the word `settle_run` issues (`SPEC.md:512`), and here no receipt carries it; see J1 |
| F5 malformed digest disables byte check | **REPAIRED** | `observe.py:134-137`. P6: `OUTPUT` digest `not-a-digest` refuses `UNREADABLE`, receipt written |
| F6 run's grant absent reads `INDEPENDENT` | **STILL OPEN**, note | P5 unchanged: `INDEPENDENT []`. Not a pass-1 condition; `KNOWN-GAPS.md` records the candidate-side default, not this run-side one |
| F7 report readable as a predicate address | **REPAIRED** | `observe.py:116-122`, `record.py:100-103`. P7: the report entry's id named as an address refuses `PREDICATES_UNDECLARED ... run's own entry`. The regression test now proves what its name says. See R6 for the guard's shape |
| F8 notes | **STILL OPEN**, notes | P9 changed: the reuse of an inference over a thinner record now refuses because `observe.py:123` also requires the `OUTPUT` entry, which closes the specific defeat pass 1 recorded while leaving the reuse itself (`service.py:143-145`). P10 `False` and P10b (two observations over the same addresses share an id; `read_observation` returns the first) unchanged |
| C2 `CONF-RUN-DEF` over-declares | **REPAIRED** | `oracle-controls.json` control `CONF-RUN-DEF` declares `TRANS-observe_run`, `TRANS-settle_run`; its four defects name both. `test_kernel_predicates.py:220-246` grades every defeating control's declared predicates against its defect text; see R7 for that grader's shape |
| C3 rules cannot be seen to disappear | **REPAIRED** | mutation probe: 13 of 13 sampled rules (the nine pass 1 named, the `DISSENTED` attestation rule mutated by hand, and three more) fail `conformance/tests` alone. The test loads `kernel_predicates.py` and `requirements.py` by file path; it imports no participant code |
| C4 participant runs carry `SPEC-*` gaps | **REPAIRED** | `run.py:96-101` scopes a participant run to `PRD_REQUIREMENTS` plus the rows its case file declares (`requirements.py:28`); participant probe reads `coverage_gaps=0`. `run.py:5-13` states the two-set rule; `conformance/README.md:9-16` restates it |
| S1 capability map `ACTIVE` at an unrouted address | **STILL OPEN**, changed shape | `contracts/fixtures/capability-map.reference.json` still carries five `activation: ACTIVE`, `address: observation:in-process`; `scripts/sovnode/composition.py:187-190` binds four addresses, none of them; `contracts/fixtures/node-interface.reference.json` shows each of the five with `standing: BUILT`, `reachability: []` beside that `ACTIVE`. Neither repair condition 4 offered was taken; a row in `services/observation/KNOWN-GAPS.md:20` now documents it. Condition C1 below |
| S2 receipts re-recorded on a grep | **changed shape; the review itself is not derivable from the record** | `.clarity/coverage.json` trajectory by `STATUS.yaml` basis digest: `169182f` 63 on `dae8e4f4`; `162ffaf` 61 restored to `96d9e073`, 2 on `dae8e4f4`; `540bc01` 63 on `dae8e4f4`, 65 receipts changed. A receipt carries `artifact_digest`, `basis`, `changed` and nothing about who read, when, or how (`schema: soveraeign-clarity-coverage/v1`), so whether 65 artifacts were read in full is the builder's word. What the tree can answer: the four rewrites are accurate (below), and no artifact in `sov_clarity.py scope` states the old standing or the old counts as present-tense fact (grep for `CHARTERED_BOUNDARY_NOT_IMPLEMENTED` with `observation`, `20 controlled cases`, `40 checks`, `chartered and unbuilt`; only `STATUS.yaml`, the corrected `services/host/SERVICE-SPEC.md:121-123`, the history row in `contracts/status-claims.json:145`, and status-claims fixtures match). See R8 |
| S3 host `SERVICE-SPEC.md` quotes retired value | **REPAIRED** | `services/host/SERVICE-SPEC.md:121-123` now quotes `BUILT_THIN_SLICE_SELF_TESTED_REMAINDER_DECLARED_NOT_WITNESSED` |

The four clarity rewrites checked against the tree: `.claude/epic/NARRATIVE.md:271-279`
(33 controls: `run.py` reads 33; three operations declared only: manifest reads 5 `BUILT`,
3 `PROPOSED`; gate covered in both polarities: 44/44); `.claude/skills/sov-conformance/SKILL.md:17-20,35-43`
(thirteen checks: `len(CHECKS)` is 13; 33 controls); `ROADMAP.md:293-298` (135 declared, 5
reachable: `sov_interface.py show` reads `declared 135`, `reachable 5`; five of eight
operations); `conformance/README.md:9-16` (two-set coverage rule matches `run.py:96-101`).
All four are accurate as of this commit.

### Residuals (the builder's to absorb; none holds the transition)

- **R1 - LOW, `record.py:93-97`, `relation.py:128-130`.** An anonymous entry is dropped, not
  refused. P1b: a `REPORTED` entry whose `actor` is empty leaves the reporter unknown and the
  candidate reads `INDEPENDENT []`. P2c: a second `ATTEMPTED` entry attributed to nobody is
  skipped the same way. Only the first attempt's actor is required (`relation.py:129`).
  `CHARTER.md` says a record too thin to answer refuses; here it answers. Consequence if left:
  a projection that loses the reporter's actor admits the reporter as observer. No journal
  entry contract requiring `actor` was found under `services/record/contracts/`, so the shape
  is reachable from a projection.
- **R2 - LOW, `relation.py:139-149`.** `HOLDS_RUN_LEASE` and `GRANT_DESCENDS_FROM_RUN` read
  the first attempt's `lease` and `grant_id` only. P2b: a second attempt whose lease holder is
  `lessee-c` (not its actor) lets `lessee-c` read `INDEPENDENT []`. F2 is repaired for the
  actor edge and not for the other two edges a re-attempt carries.
- **R3 - LOW, `service.py:95-99`, `errors.py:63-66`.** P8b: a run refused before any report
  (a `RECEIPT` with `outcome: REFUSED`, no outputs) is terminal (`is_terminal() True`,
  `terminal_outcome() REFUSED`) but `request_observation` refuses it `INCOMPLETE_PROPOSAL`,
  whose declared meaning is "a request or declaration omits a field the contract requires".
  The requester omitted nothing. The regression test
  (`test_thin_slice.py`, `test_a_reported_run_without_a_receipt_is_requested_as_unresolved`)
  asserts the refused half through `record.terminal_outcome()` directly, not through the
  operation, so the declared surface's behaviour on a refused run is untested.
- **R4 - LOW, `relation.py:95-100`.** P4b: an `OUTPUT` entry without a `subject` is
  invisible to `outputs()`, so the walk reads the output as absent and refuses with
  `ONLY_EXECUTOR_REPORT`. It refuses, and one receipt is written; the reason names the wrong
  defect (a malformed record, not a report-only run).
- **R5 - LOW, `record.py:21-24` against `record.py:150-152`.** P8d: a run that already carries
  a `COMMITTED` receipt is requestable (`run_outcome: COMMITTED`) and inferable
  (`INDEPENDENT`), while the module docstring says a settled run "could never be observed".
  Pre-existing at pass 1; recorded because `TERMINAL_OUTCOMES` now includes `COMMITTED`.
- **R6 - LOW, `record.py:100-103`.** The own-entry guard keys on `entry_id`. A `REPORTED`
  entry with no `entry_id` has no address to refuse, and an `OUTPUT` entry whose subject is the
  run id itself is not guarded (P7b evaluated `True`). Contrived from a journal that always
  assigns ids; recorded so a projection without ids is not assumed safe.
- **R7 - LOW, `conformance/tests/test_kernel_predicates.py:224-246`.** The predicate-join
  grader matches substrings (`observ`, `settle`, `report`) in the defect text. `settlement
  cites no observation of this run` contains `observ`, so a settle-only control that declared
  `TRANS-observe_run` would pass it. Correct today; a classifier, not a measurement of which
  rule fired.
- **R8 - LOW, `CLAUDE.md:85` against `CLAUDE.md:118`.** One page says "Gateway has one
  in-process Asset route" and "Gateway [is a] boundar[y] with no implementation". Both
  sentences predate the branch (`c8eedd9:CLAUDE.md:85,114-115`); the second was edited in
  `169182f` to remove Observation and Registry and kept Gateway; the page's receipt was
  re-recorded in `540bc01` on a full reading. Not the observation delta, and not the builder's
  contradiction to start with; it is what a full reading of that page would have met.
  `ROADMAP.md:294-295`, rewritten in the same commit, says the opposite of `CLAUDE.md:118`.
- **R9 - note.** `witness/observation-service.md` was committed in `162ffaf` into the clarity
  population's `operations` campaign without a receipt and is the one `UNCHECKED` artifact.
  It is this witness's file, so the review is not the witness's to record.

### Conditions

- **C1 (S1).** Either `contracts/fixtures/capability-map.reference.json` reads
  `DECLARED_NOT_ACTIVATED` for the five observation operations until `composition.py` routes
  `observation:in-process`, or the map's owner rules that `ACTIVE` may describe an unrouted
  address and says where a reader learns that. The builder's report assigns this to "the map
  policy"; the row was changed by the same builder in `169182f`, so repairing it is inside the
  concern (`AGENTS.md`, Closure ownership). Pass 1's condition 4 stands unrepaired.
- **C2 (R1, R2, R3).** Regression cases through the declared surface for an anonymous
  `REPORTED`/`ATTEMPTED` entry, a second attempt's lease and grant, and
  `request_observation` on a refused run.

### Judgement items (questions for the owner, not the witness)

- **J1.** May `run_outcome` carry `UNRESOLVED`, a `settle_run` outcome (`SPEC.md:512`), for a
  run the kernel has not settled? The schema enum and `SPEC.md` admit the word; the schema's
  description still says "the run's terminal receipt outcome", and here there is no receipt.
  The alternative pass 1 named was to refuse when no terminal receipt exists.
- **J2.** Is a false declaration in a derived artifact, documented in `KNOWN-GAPS.md` rather
  than corrected, admissible under `REMAINDER_DECLARED`?
- **J3.** Should the clarity receipt carry a field for the reading's scope (full read versus
  basis-delta), so that pass 1's S2 becomes checkable rather than a matter of the builder's
  word? Carried from pass 1.

### Uncovered

- `docs/documentation.html`, `docs/surface.html`, the diagram pins and the node-interface
  projection were accepted on `verify.py`'s regeneration checks; their text was not read
  beyond the observation rows quoted above.
- `list-pending-observations`, `counter-observation` and `attest-observation` remain
  `PROPOSED` and were not examined.
- The kernel `settle_run` parity was taken from `test_kernel_parity.py` (run, 43 OK) and the
  unchanged bytes of `transitions.py`; the witness did not drive `evaluate()` by hand this
  pass.
- Whether two helper agents read 65 artifacts cannot be established from any artifact; only
  the consequences of such a reading were checked.
- No network, no `gh`, no ruleset query.

### Landing residual

With this record and its receipt present, `python scripts/verify.py` is expected to return 1
on `documentation reader` only (`scripts/sovdocs/facets.py` indexes `witness/*.md`), exactly
as at pass 1; the witness may not rebuild the page. The checks recorded under `Verified` were
run before either file was written. The admissibility reads taken after writing are in the
completion report and the receipt's `telemetry`.

### Probe

Run from a scratch directory against `services/observation/src` at the commit above; not a file
in this repository. Each case reaches the service only through `ObservationService` and
`RunRecord.from_entries`.

```python
import hashlib, sys
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
        Clock.t += 1; return f"2026-09-03T{Clock.t//60:02d}:{Clock.t%60:02d}:00+00:00"
def base(lease_holder="worker-a", grant="grant-run", out_actor="worker-a", report_actor="worker-a"):
    return [
        e("g-root","EVENT","grant-root","seat:root",{"event":"GRANT","holder_id":"orch","parent_grant_id":None}),
        e("g-run","EVENT","grant-run","orch",{"event":"GRANT","holder_id":"worker-a","parent_grant_id":"grant-root"}),
        e("g-b","EVENT","grant-b","orch",{"event":"GRANT","holder_id":"worker-b","parent_grant_id":"grant-root"}),
        e("g-c","EVENT","grant-c","orch",{"event":"GRANT","holder_id":"lessee-c","parent_grant_id":"grant-root"}),
        e("g-z","EVENT","grant-z","orch",{"event":"GRANT","holder_id":"witness-z","parent_grant_id":"grant-root"}),
        e("attempt","EVENT",RUN,"worker-a",{"event":"ATTEMPTED","lease":{"holder_id":lease_holder},"grant_id":grant}),
        e("out1","EVENT","out/1",out_actor,{"event":"OUTPUT","digest":OUTD}),
        e("report","EVENT",RUN,report_actor,{"event":"REPORTED","output_record_addresses":["out/1"]}),
    ]
def run(name, entries, candidate, kind="WORKER"):
    svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, entries)
    try:
        inf = svc.infer_relation(rec, candidate, kind)
        print(name, inf["outcome"], [x["edge"]+"@"+x["evidence_address"] for x in inf["edges_found"]], len(svc.receipts))
    except ObservationRefused as r: print(name, "REFUSED", r, len(svc.receipts), svc.receipts[-1]["reason_code"])
    except Exception as r: print(name, "ESCAPED", type(r).__name__, r, len(svc.receipts))
    return svc, rec
run("P1", base(report_actor="worker-b"), "worker-b")                 # DIRECT [SAME_ACTOR@report] 1
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"worker-b",
    {"event":"ATTEMPTED","lease":{"holder_id":"worker-b"},"grant_id":"grant-b"}))
run("P2", ents, "worker-b")                                          # DIRECT [SAME_ACTOR@attempt2] 1
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"worker-b",
    {"event":"ATTEMPTED","lease":{"holder_id":"lessee-c"},"grant_id":"grant-c"}))
run("P2b", ents, "lessee-c")                                         # INDEPENDENT [] 1   (R2)
run("P1b", base(report_actor=""), "witness-z")                       # INDEPENDENT [] 1   (R1)
ents = base(); ents.insert(6, e("attempt2","EVENT",RUN,"",{"event":"ATTEMPTED","lease":None,"grant_id":None}))
run("P2c", ents, "witness-z")                                        # INDEPENDENT [] 1   (R1)
ents = base(); [x.pop("entry_digest") for x in ents]; run("P3", ents, "witness-z")   # REFUSED UNREADABLE 1
ents = base(); del ents[5]["entry_digest"]; run("P3b", ents, "witness-z")            # REFUSED UNREADABLE 1
ents = base(); del ents[4]["subject"]; run("P4", ents, "witness-z")  # REFUSED RELATION_UNDETERMINED 1
ents = base(); del ents[6]["subject"]; run("P4b", ents, "witness-z") # DIRECT [ONLY_EXECUTOR_REPORT@report] 1 (R4)
ents = base(); ents[5]["payload"] = None; run("P4c", ents, "witness-z")   # REFUSED UNREADABLE 1
ents = base(); ents[5]["payload"] = "junk"; run("P4d", ents, "witness-z") # REFUSED UNREADABLE 1
run("P5", base(grant="grant-unknown"), "witness-z")                  # INDEPENDENT [] 1   (F6 open)
ents = base(); ents[6]["payload"]["digest"] = "not-a-digest"
svc, rec = run("P6a", ents, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"p","kind":"BYTES_PRESENT","address":"out/1"}])
try: print("P6", svc.observe_run(rec, "witness-z", lambda a: b"anything")["predicate_results"])
except ObservationRefused as r: print("P6 REFUSED", r, len(svc.receipts))   # REFUSED UNREADABLE 3
ents = base(); ents[7]["payload"]["output_record_addresses"] = ["out/1", "report"]
ents.append(e("out-report","EVENT","report","worker-a",
    {"event":"OUTPUT","digest":hashlib.sha256(b'{"claim":"done"}').hexdigest()}))
svc, rec = run("P7a", ents, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"reads-report","kind":"JSON_FIELD_EQUALS",
                              "address":"report","field":"claim","expected":"done"}])
try: print("P7", svc.observe_run(rec, "witness-z",
      lambda a: b'{"claim":"done"}' if a == "report" else OUT)["predicate_results"])
except ObservationRefused as r: print("P7 REFUSED", r)               # PREDICATES_UNDECLARED ... run's own entry
ents = base(); ents[7]["entry_id"] = None; ents[7]["payload"]["output_record_addresses"] = ["out/1", RUN]
ents.append(e("out-run","EVENT",RUN,"worker-a",{"event":"OUTPUT","digest":hashlib.sha256(b'{"claim":"done"}').hexdigest()}))
svc, rec = run("P7b", ents, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"reads-run","kind":"JSON_FIELD_EQUALS","address":RUN,"field":"claim","expected":"done"}])
print("P7b", svc.observe_run(rec, "witness-z", lambda a: b'{"claim":"done"}' if a == RUN else OUT)["predicate_results"])  # {'reads-run': True} (R6)
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, base())
print("P8", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"])   # UNRESOLVED
refused = base()[:6] + [e("rcpt","RECEIPT",RUN,"kernel",{"outcome":"REFUSED","event":"begin_run"})]
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, refused)
print("P8b", rec.is_terminal(), rec.terminal_outcome())              # True REFUSED
try: print("P8b", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"])
except ObservationRefused as r: print("P8b REFUSED", r)              # INCOMPLETE_PROPOSAL (R3)
refused2 = base() + [e("rcpt","RECEIPT",RUN,"kernel",{"outcome":"REFUSED","event":"report_run"})]
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, refused2)
print("P8c", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"])  # REFUSED
settled = base() + [e("rcpt","RECEIPT",RUN,"kernel",{"outcome":"COMMITTED","event":"settle_run"})]
svc = ObservationService(Clock()); rec = RunRecord.from_entries(RUN, settled)
print("P8d", svc.request_observation(rec, "requester-q", "HUMAN", RUN)["run_outcome"],
      svc.infer_relation(rec, "witness-z", "MODEL")["outcome"])      # COMMITTED INDEPENDENT (R5)
svc = ObservationService(Clock()); full = RunRecord.from_entries(RUN, base())
svc.infer_relation(full, "witness-z", "MODEL")
svc.declare_predicates(RUN, [{"predicate_id":"p","kind":"BYTES_PRESENT","address":"out/1"}])
thin = RunRecord.from_entries(RUN, [x for x in base() if x["entry_id"] != "out1"])
try: print("P9", svc.observe_run(thin, "witness-z", lambda a: OUT)["observation_id"])
except ObservationRefused as r: print("P9 REFUSED", r)               # PREDICATES_UNDECLARED (not a recorded output)
obs = svc.observe_run(full, "witness-z", lambda a: OUT)
d2 = svc.declare_predicates(RUN, [{"predicate_id":"q","kind":"BYTES_PRESENT","address":"out/1"}])
print("P10", svc.read_observation(obs["observation_id"])["declaration"]["declaration_id"] != d2["declaration_id"])  # False
obs2 = svc.observe_run(full, "witness-z", lambda a: OUT)
print("P10b", obs2["observation_id"] == obs["observation_id"])     # True
```

Mutation probe for C3: copy `conformance/` to a scratch directory, replace one
`defects.append(...)` (or the `DISSENTED` membership test at `kernel_predicates.py:71`) with
`pass` / `False`, run `python run.py --cases oracle-controls.json` and
`python -m unittest discover -s tests` from the copy, read the `SUITE` line and the unittest
verdict, restore. Baseline of the unmodified copy: `Ran 70 tests`, `FAILED (errors=2)`, both
errors being loader errors from tests that resolve paths against the real repository root.

## Pass 1: commit 169182f (2026-09-03) - historical

This section is the first pass, kept as written. Its own declaration block is quoted below
and is not the record's declaration: `scripts/sov_standing.py` reads only the first block
under the title, which pass 2 owns.

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
