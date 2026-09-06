# Witness record: fresh participation vertical slice (P15-X1)

```witness
standing_supported  BUILT
subject  fresh-participation
revision  d40d61fe83e10d6eca235ee2cfff5dc8e5ae2a27
pass  1
```

No `*_status` field in `STATUS.yaml` names this subject, so `scripts/sov_standing.py` does not
read this file. The subject is the one `ITEM` member under
`custody:phase-1-5/fresh-participation` in `contracts/custodies/phase-1-5.json`:
`scripts/sov_fresh.py`, stage `VERTICAL_SLICE`, standing `BUILT`, `stage_observed_by` null.

## Pass 1: commit d40d61f (2026-09-06)

Verdict: **NOT-YET**.

Claim under observation, as the builder states it: a closed path session -> principal ->
campaign -> work -> lease -> capability -> authority -> Record projection -> session end ->
survival -> instrument, with P15-Q1.1 to Q1.3 graded by `conformance/commissioning.py` on a
live run and three defeating variants each failing their own predicate. Builder's report:
`reports/2026-09-06-fresh-participation-slice.md`. It was read after every command below had
run and is treated as the executor's self-report; nothing in this record is taken from it, and
where it is named it is named as a claim.

Commit witnessed: `d40d61fe83e10d6eca235ee2cfff5dc8e5ae2a27` on
`claude/phase-2-citizen-mechanics-inrozu`. `git status --short` was empty before and after every
command, `git rev-parse HEAD` read the commit throughout, and `.local/sov-sessions/` did not
change, so the probe wrote only to its temporary directories.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`. This participant did not build, edit, stage
or commit anything under the subject. The only files it wrote are this record and
`witness/observations/2026-09-06-fresh-participation-observation.json`, both after every
command under `Verified` had returned.

### Standing supported

`BUILT`, unchanged. The build claim stands: the probe exists, runs through its declared
surface, its self-tests pass, and the repository gates read `PASS` at this commit. The
transition `BUILT -> WITNESSED` is not supported, because three of the fields the instrument
grades are written by the probe rather than derived from a product layer (F2, F4, F5), one
declared defeating variant passes through the declared surface (F3), and the cross-principal
half of P15-Q1.3 was never put to the product (F1). Each of those is the builder's to repair
inside the concern; none is a new ticket.

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse HEAD`; `git status --short`; `git show d40d61f --stat` | 0; 0; 0 | `d40d61fe...`; empty; 14 files, +803/-17 |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant and 3 defeating variants each fail their own predicate` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5` | 0 | `PASS`; `principal principal:claude-fable-5`; `phase phase:1-5 from STATUS.yaml@sha256:9ddb4c4f... + contracts/phases.json@sha256:05a27e13...`; `lease lease:custody-phase-1-5-fresh-participation-fresh-<id> held`; `capability asset.ingest-asset: own session BOUND, foreign session SESSION_ATTRIBUTION_CONFLICT`; `authority for 'principal:claude-fable-5': REFUSED AUTHORITY_REFUSED`; `work survives: True`; Q1.1, Q1.2, Q1.3 `holds` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --json` | 2 | `error: unrecognized arguments: --json` (F8) |
| `python scripts/sov_fresh.py --json run --principal principal:claude-fable-5` | 0 | JSON; `identities.grant_id` = `grant:standing-landing-loop`; `interface_binding_id` = `urn:soveraeign:binding:node-interface:model-json-v1`; `cross_principal_session_mismatch` = `REFUSED`; `cleanup_obligations` = `["release lease:...", "end session fresh-..."]`; `oral_history_used` = `false`; `required_authority` = `ingest:asset`; `effect_envelope` = `RECORD_LOCAL` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --variant unregistered-principal` | 0 | `fresh participation [unregistered-principal]: PASS`; all three predicates `holds` (F3) |
| `python scripts/sov_fresh.py run --principal principal:nobody --variant unregistered-principal` | 1 | `principal UNIDENTIFIED`; `lease ... held`; `own session REFUSED, foreign session SESSION_IDENTITY_REQUIRED`; `authority for '': REFUSED`; Q1.1 `fresh context missing principal_id`; Q1.2 `holds`; Q1.3 `identity separation missing principal_id; principal, session, grant, and interface binding collapsed` |
| `python scripts/sov_fresh.py run --principal principal:nobody` (positive variant) | 1 | identical readings to the row above: the variant name changes nothing in `probe.run` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --variant work-dies-with-session` | 1 | `work recorded only on the session`; `work survives: False`; Q1.2 `durable work missing custody_or_lease; work does not survive the carrying session`; Q1.1, Q1.3 `holds` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --variant borrowed-authority` | 1 | `authority for 'sov': PERMITTED grant:standing-landing-loop`; Q1.3 `cross-principal/session mismatch did not refuse`; Q1.1, Q1.2 `holds` |
| `env -u SOV_PRINCIPAL python scripts/sov_fresh.py run` | 2 | `REFUSED PRINCIPAL_REQUIRED: declare the registered principal ... the registry names, it does not guess` |
| `python -m unittest scripts.tests.test_sov_fresh` | 0 | `Ran 11 tests in 1.199s OK` |
| `python scripts/sov_custody.py board custody:phase-1-5/fresh-participation` | 0 | `VERTICAL_SLICE 1`, `ITEM scripts/sov_fresh.py [build claim]`; `closes when COMMAND python scripts/sov_fresh.py selfcheck`; estimate `grants 0..1 PENDING`, `judgement_units 1..1 PENDING` |
| `python scripts/sov_custody.py selfcheck` | 0 | `46 case(s), 27/27 declared refusals reached`; `selfcheck PASS` |
| `python scripts/sov_active_phase_progress.py` | 0 | no output (the builder's residual about a silent pass is reproduced) |
| `python scripts/sov_next.py --strict` | 0 | `scripts/sov_fresh.py [PRESENTED] drawn / custody custody:phase-1-5/fresh-participation`; `PASS: phase/custody precedence is explicit ...` |
| `python scripts/verify.py` | 0 | `PASS: 51 checks in 14.098s wall`; `GRADE: SILVER`; `BUDGET DEBT: 8 check(s) over ceiling` (attributed, non-refusing); `TIME: fresh participation slice: 1.107s wall, 0.483s cpu`. The `FAIL` lines in the output are planted tooling self-test output inside `repository tooling tests`; the verdict is the `PASS: 51 checks` line and the exit code |
| `python -c` over `sovverify.checks.CHECKS` after package import | 0 | 51 names, 51 distinct; `REPOSITORY_CHECKS` 41, `PARTICIPANT_CHECKS` 7 |
| `python scripts/sov_fresh.py selfcheck` timed alone, three runs | 0; 0; 0 | 0.463s, 0.462s, 0.456s wall |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1183 text files, 552 Python modules, 10 named debt)` |
| `python scripts/sov_snapshot.py` | 0 | `PASS: 9 of 10 snapshot claim(s) match the record` (commits not checked here: shallow clone) |
| `python scripts/sov_clarity.py check` | 0 | `PASS: clarity scope and receipts are well-formed and current` |
| `python scripts/sov_traps.py` | 0 | `PASS: 2 trap(s) still hold, 3 recorded for attended checking` |
| `python scripts/sov_standing.py`; `python scripts/sov_witness_layer.py records` (before writing) | 0; 0 | `PASS: 1 standing claim(s)`; `PASS: 6 witness receipt(s) graded, 0 unusable, 6 stale against their subject` |
| `sha256sum` over 24 addresses | 0 | recorded in the receipt's `observed_state_digests` |

### Findings

Severity names the consequence if the member were ratified at `VERTICAL_SLICE` as-is. Defects
are the builder's to repair inside the concern; residuals are recorded and hold nothing.

- **F1 - HIGH, defect. `scripts/sovfresh/probe.py:101,127-130`; `scripts/sovfresh/layers.py:160-184`.**
  `cross_principal = graded["verdict"] == "REFUSED"` reads the participant's own authority
  request, made as its own actor, for a capability no grant gives it. `AUTHORITY_REFUSED` there
  is the ordinary absence of a grant, not a refused cross-principal mismatch. No product layer
  was handed a session principal together with another actor's grant and asked to refuse. The
  `borrowed-authority` variant swaps the request's actor for `sov`, and `sovkernel.authority`
  correctly reads `PERMITTED` for `sov`; nothing in what the probe drives could have refused it,
  so the variant defeats the probe's own derivation, not the product. A product seam that does
  bind a session to a grant exists (`bindings/mcp/gateway.py:173-215`, `SESSION_NOT_LIVE`,
  `GRANT_NOT_HELD`) and was not driven. Consequence: the second clause of P15-Q1.3 reads as
  observed when it was never exercised against the product.
- **F2 - HIGH, defect. `scripts/sovfresh/layers.py:182`; `scripts/sovfresh/probe.py:162`;
  `scripts/tests/test_sov_fresh.py:72`.** `grant_id` is `result.get("grant_id") or considered[0]`:
  when the participant is refused, the identity slot is filled with the grant that refused it.
  The honest reading of a principal no grant names is `None`, which the instrument
  (`conformance/commissioning.py:49-51`) would fail as `identity separation missing grant_id`.
  The probe supplies a value the participant does not hold, and the unit test pins
  `grant:standing-landing-loop` as the fresh participant's grant identity. "Grant authority
  remains distinct" is satisfied here only by string inequality; the grant named is somebody
  else's authority. Consequence: a ratified Q1.3 would rest on an identity the participant
  never held.
- **F3 - HIGH, defect. `scripts/sov_fresh.py:91-93`; `scripts/sovfresh/probe.py:37-43,68-71`.**
  The `unregistered-principal` variant is not implemented in `probe.run`; the self-check harness
  substitutes `principal:nobody` as caller input. Through the declared surface,
  `run --principal principal:claude-fable-5 --variant unregistered-principal` reads `PASS`,
  exit 0, labelled `[unregistered-principal]`. A declared defeating variant that passes is a
  defeating fixture that does not defeat, and a reader of the `run` output cannot tell.
- **F4 - MEDIUM, defect. `scripts/sovfresh/probe.py:146`.** `"oral_history_used": False` is a
  constant. The instrument's oral-history check (`conformance/commissioning.py:31-32`) can never
  fire from this probe. Nothing derives the flag from where each field came from; the principal
  id itself is supplied by the operator and written into the resolver's environment by
  `layers.speaking_as` (`layers.py:33-47`). Asserted, not earned.
- **F5 - MEDIUM, defect. `scripts/sovfresh/probe.py:131-133`.** The custody declares
  `cleanup_obligations: []`, `contracts/work-lease.schema.json` carries no cleanup field, and the
  two strings the observation reports are composed by the probe. `durable work missing
  cleanup_obligations` cannot fire on the positive path. The strings name the participant's own
  inventory; P15-Q1.2 asks for the work's obligations that survive the session. Written by the
  participant that ran it, which is what `contracts/work-circuit.json` VERTICAL_SLICE evidence
  forbids.
- **F6 - MEDIUM, defect. `scripts/sovfresh/probe.py:163-164`.** `interface_binding_id` falls
  back to `layers.SESSION_BINDING`, a probe constant, when the product refused the binding. In
  the unidentified path the binding was `REFUSED SESSION_IDENTITY_REQUIRED` and the observation
  still carries a non-empty interface binding. Q1.3 fails there for another reason, so the
  fallback is masked today; it hides a product refusal behind a probe-written identity.
- **F7 - LOW, defect. `scripts/sovfresh/probe.py:127`.** `cross_session` is any `REFUSED`
  verdict, not `SESSION_ATTRIBUTION_CONFLICT`. In the unidentified path a
  `SESSION_IDENTITY_REQUIRED` refusal counts as the cross-session refusal.
- **F8 - LOW, residual. `scripts/sov_fresh.py:126`.** `--json` is on the root parser;
  `run --principal X --json` exits 2. `--json run ...` works. The report's command table does
  not claim the failing form, so no false claim; the surface is awkward.
- **F9 - LOW, residual. `scripts/sovfresh/layers.py:166-176`.** The authority request declares
  `evidence.checks verify/lint PASS`, `branch main` and a path; declared, not measured. It is
  what makes `borrowed-authority` read `PERMITTED`, so that variant's reading rests on a
  declaration.
- **F10 - LOW, residual. `scripts/sovsession/principals.py:46-49`; `scripts/sovfresh/layers.py:52-59`.**
  `run` reads `SOV_PRINCIPAL_REGISTRY` from the operator's environment through the resolver and
  the observation drops `claim["registry"]`, so an environment that swaps the registry leaves
  no trace in the grade. This is the one input read from the environment other than the
  declared principal.
- **F11 - LOW, residual. `scripts/sovfresh/probe.py:117-120`.** `survives_session` is true
  whenever a lease was taken: the session end is a raw `end` event, the product's
  `sov_session.py end` does not release leases either, and `lease_store.leases` projects `HELD`
  regardless of session events. Derived, but only the probe declining to take a lease can
  defeat it.
- **F12 - MEDIUM, judgement on the stage claim.** Against `contracts/work-circuit.json`
  VERTICAL_SLICE: both admission predicates are met (an ordered path is named; the path closes on
  a re-runnable check). The evidence predicate, "its result is derived from the run, never
  written by the participant that ran it", is met in part: F2, F4, F5 and F6 are written. Also,
  `contracts/custody.schema.json` `$defs/member` carries no evidence field and
  `scripts/sovcustody/model.py` never calls `circuit.judge_advance` on a member, so the stage is a
  declaration nothing measures. That is the custody model's design, not this builder's; it is
  why this record, not the board, is where the stage claim gets read.
- **F13 - LOW, residual. `scripts/sovverify/__init__.py:11-15`; `scripts/sovverify/checks.py:19,301`.**
  `COMMISSIONING_CHECKS` is spliced in twice, in two orders (the package init also includes
  `INTEGRITY_CHECKS`; `checks.py` does not). `verify.py` imports after the package init, so the
  run reads 51 distinct checks (measured). Sound today; a drift hazard. The named ceiling of
  1.5s is set from evidence: 0.456-0.463s alone, 1.107s pooled.
- **F14 - LOW, residual. `contracts/custodies/phase-1-5.json` closure; `scripts/sovverify/commissioning.py:17`.**
  No reader executes a custody's closure command (`sovcustody/board.py` prints it; its
  subprocess at `:35` is `sov_worklist.py derive`). `verify.py` runs the same command through a
  separately declared `Check`. Two declarations of one command string, nothing ties them. The
  command does run today (exit 0), so `decisions/0102`'s defeating case does not fire.
- **F15 - LOW, residual. `reports/2026-09-06-fresh-participation-slice.md:12`.** "Independent
  witness: see the section below" names a section that does not exist in the report.
- **F16 - LOW, residual. `scripts/sovfresh/layers.py:27,74-86`.** The work the fresh participant
  accepts is the custody whose member is the probe itself. The slice resolves no work other than
  its own custody.
- **F17 - LOW, residual (product, not probe). `scripts/sovfresh/layers.py:101-118`.** With an
  `UNIDENTIFIED` principal the lease is still taken with `controller_principal: null` and
  validates against `contracts/work-lease.schema.json`; Q1.2 holds for a participant nobody
  named. Whether a lease may be held under no controller is the lease contract's question.

### Conditions for a later pass to support `BUILT -> WITNESSED`

- C1 (F1, F7): derive `cross_principal_session_mismatch` from a product refusal of a request
  that carries this session's principal together with a grant or actor it does not hold, and
  compare refusal codes, not verdicts.
- C2 (F2): report `grant_id` as the grant the participant holds, `None` when it holds none, and
  let the instrument or its fixture say what shape "no grant held" takes.
- C3 (F3): make every declared variant change what `probe.run` does, so `run --variant` cannot
  pass for a variant that is declared to fail.
- C4 (F4, F5, F6): replace the three constants with values derived from a layer, or report the
  layer's honest value and let the predicate fail.

### Judgement items (questions, not the witness's to answer)

- J1. May the P15-Q1.3 instrument admit "no grant held" as a distinct identity, or must a fresh
  participant hold a grant before the clause can be observed?
- J2. Is re-pointing an exit custody's closure check away from the reader `decisions/0102`
  named an ordinary reversible default, or does it want a note in the decision record?
- J3. The model serving the builder's session is `claude-fable-5-1`; the registry names
  `principal:claude-fable-5`. Does the version drift want a registry entry? (Builder's
  residual; identity naming is owner-held.)

### Uncovered

- `docs/documentation.html` was accepted on `verify.py`'s `documentation reader` check; the 12
  changed lines were not read.
- The clarity receipt for `CLAUDE.md` was accepted on `sov_clarity.py check`; the prose was not
  re-reviewed.
- The Record Service's `evidence_projection` was not exercised beyond the probe's own call.
- No network, no `gh`, no ruleset query.

### Landing residual

`scripts/sovdocs/facets.py:66` indexes `witness/*.md`, so with this record present
`documentation reader` and `repository tooling tests` are expected to read the built page as
stale, as pass 3 of `witness/observation-service.md` recorded. The witness may not rebuild the
page; whoever lands this record runs `python scripts/sov_docs.py build`. The exact readings
after writing are recorded in the receipt's `telemetry.after_writing`.
