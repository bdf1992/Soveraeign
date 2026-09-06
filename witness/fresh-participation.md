# Witness record: fresh participation vertical slice (P15-X1)

```witness
standing_supported  BUILT
subject  fresh-participation
revision  161d559fc4eba85dab598c3495d0620cbacbf011
pass  2
```

Two passes by the same role, different commits. Pass 2 (commit `161d559`) is current and
owns the declaration above. Pass 1 (commit `d40d61f`) follows it unchanged as history.

No `*_status` field in `STATUS.yaml` names this subject, so `scripts/sov_standing.py` does not
read this file. The subject is the one `ITEM` member under
`custody:phase-1-5/fresh-participation` in `contracts/custodies/phase-1-5.json`:
`scripts/sov_fresh.py`, stage `VERTICAL_SLICE`, standing `BUILT`, `stage_observed_by` null.

## Pass 2: commit 161d559 (2026-09-06)

Verdict: **NOT-YET**.

Claim under observation, as the builder states it: every F1 to F7 defect from pass 1 is
repaired at this commit, and every identity in the P15-Q1.3 observation is read from a node
record (the Console Service's grant and session records and the Gateway's receipts,
`scripts/sovfresh/node.py`, `scripts/sovfresh/probe.py`). Builder's report:
`reports/2026-09-06-fresh-participation-slice.md`, section "Independent witness". It was read
after every command below had run and is the executor's self-report; nothing here is taken from
it.

Commit witnessed: `161d559fc4eba85dab598c3495d0620cbacbf011` on
`claude/phase-2-citizen-mechanics-inrozu`. `git status --porcelain` was empty before and after
every command, `git rev-parse HEAD` read the commit throughout, and `.local/sov-sessions/` does
not exist on this host, so every probe run wrote only to its temporary directories. The commit
changes 11 files (+1000/-373), all inside the concern; `conformance/` is unchanged between
`d40d61f` and `161d559`, so the oracle was not weakened.

Witness: `claude-fable-5-1/sov-witness@2026-09-06`, pass 2 by the same role. This participant
did not build, edit, stage or commit anything under the subject. The only files it wrote are
this section and `witness/observations/2026-09-06-fresh-participation-observation-2.json`, both
after every command under `Verified` had returned. Pass 1 below is carried unchanged: the
pass-1 receipt's 24 digests recompute exactly against the bytes `git show d40d61f:<path>`
returns, and its line citations (`probe.py:127,131-133,146,162-164`, `layers.py:182`) match the
`d40d61f` source. Both witness files first enter history in the builder's commit `161d559`,
which is the landing residual pass 1 named; no independent copy exists, so "unchanged" rests on
the digest recomputation, not on a byte comparison.

### Standing supported

`BUILT`, unchanged. The identity claim is reproduced: with an issuer, `principal_id` comes from
the registry through the resolver, `session_id` and `grant_id` from Console records the node
wrote, `interface_binding_id` from the Node Interface document, and each reads `None` when the
product refused. F2 to F8 and F13 are repaired through the surface; F1 is repaired for two of
its three legs. `BUILT -> WITNESSED` is not supported, for three reasons the builder can repair
inside the concern: the positive live run passes under any non-empty `--issuer` string, because
the Console's genesis makes the first issuer on a fresh node its root and the probe never
consults the registry that names the root seat (F20); the `foreign_session` leg of the Q1.3
mismatch is refused by the binding composer in `scripts/`, never reaches the node, and leaves no
receipt (F19); and the custody's closure command reads `FAIL` under an operator environment it
overrides and cannot be affected by, which `verify.py` inherits (F18).

### Verified

Commands run from the repository root at the commit above. Exit codes are the process's own.

| Command | Exit | Reading |
| --- | --- | --- |
| `git rev-parse --short HEAD`; `git status --porcelain`; `git show --stat 161d559`; `git diff --stat d40d61f 161d559 -- conformance/` | 0 | `161d559`; empty; 11 files +1000/-373; empty |
| `python scripts/sov_fresh.py selfcheck` | 0 | `PASS: fresh participation slice closes on the positive variant and 3 defeating variants each fail their own predicates` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5` | 1 | `FAIL`; `registry.resolve as urn:...:instance:fresh-<id>: REFUSED SESSION_IDENTITY_REQUIRED`; only `foreign_session: REFUSED SESSION_IDENTITY_REQUIRED`; Q1.1, Q1.2 `holds`; Q1.3 `missing session_id; missing grant_id; missing interface_binding_id; collapsed; mismatch did not refuse`; `node: no issuer: this node has recorded no grant for any actor` (the builder's claimed honest FAIL, reproduced) |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | 0 | `PASS`; own crossing `COMMITTED`; `foreign_session: REFUSED SESSION_ATTRIBUTION_CONFLICT`; `other_actor_on_this_session: REFUSED ACTOR_ATTRIBUTION_MISMATCH`; `other_actor_without_the_grant: REFUSED AuthorityRefused`; cleanup `release lease:...`, `close console session session_...`; all three `holds` |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo --json` | 0 | `identities` = `principal:claude-fable-5`, `session_c9ad17d6685b40c0`, `grant_ce7bfb68d8dc49c0`, `urn:soveraeign:binding:node-interface:model-json-v1`; `cross_principal_session_mismatch` = `REFUSED`; `oral_history_used` = `false`; `node.own.grant_id` = `null`; `refusals.foreign_session` has `stage: bind` and no `receipt_id`; the other two carry `receipt_id` and stages `check-attribution`, `check-authority` (F8 repaired: `--json` after the subcommand) |
| `run --principal principal:claude-fable-5 --variant unregistered-principal` (no issuer / `--issuer principal:bdo`) | 1 / 1 | `principal UNIDENTIFIED` in both; Q1.1 `fresh context missing principal_id`; Q1.3 fails; with the issuer the node still reads `registry.resolve ...: COMMITTED` (F3 repaired; F25) |
| `run --principal principal:claude-fable-5 --variant work-dies-with-session` (no issuer / `--issuer principal:bdo`) | 1 / 1 | `work ... recorded only on the session`; `work survives False`; Q1.2 `missing custody_or_lease; work does not survive the carrying session`; with the issuer Q1.1 and Q1.3 `holds` |
| `run --principal principal:claude-fable-5 --variant no-grant` (no issuer / `--issuer principal:bdo`) | 1 / 1 | identical readings to the no-issuer positive run in both; `--issuer` is discarded by `probe.py:101-102` |
| `env -u SOV_PRINCIPAL python scripts/sov_fresh.py run` | 2 | `REFUSED PRINCIPAL_REQUIRED: ...` |
| `SOV_PRINCIPAL=principal:somebody python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | 1 | `P15-Q1.1: fresh participation required oral history`; `defect: undeclared environment inputs: SOV_PRINCIPAL` (F4 repaired) |
| `SOV_PRINCIPAL=principal:claude-fable-5 python scripts/sov_fresh.py run --issuer principal:bdo` | 0 | `PASS`; the variable is the declared channel when `--principal` is absent (`sov_fresh.py:60-62`) |
| `SOV_PRINCIPAL_REGISTRY=/nonexistent python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:bdo` | 1 | `principal UNIDENTIFIED`; Q1.1 `missing principal_id; required oral history`; `defect: undeclared environment inputs: SOV_PRINCIPAL_REGISTRY` (F10 traced) |
| `SOV_PRINCIPAL=principal:bdo python scripts/sov_fresh.py selfcheck` | 1 | `FAIL: fresh participation probe does not discriminate`; `positive variant failed: ... undeclared environment inputs: SOV_PRINCIPAL` (F18) |
| `SOV_PRINCIPAL_REGISTRY=/nonexistent python scripts/sov_fresh.py selfcheck` | 1 | `FAIL: no principal registry at /nonexistent` (F18) |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer principal:nobody-at-all` | 0 | `PASS`; Q1.3 `holds` (F20) |
| `python scripts/sov_fresh.py run --principal principal:claude-fable-5 --issuer ""` | 1 | uncaught traceback ending `soveraeign_console_service.refusals.AuthorityRefused: a grant must name who issued it; an empty issuer is not a name` (F21) |
| witness's own drive of `scripts/sovfresh/node.py` functions against a temporary node (`open_node`, `admit(..., "principal:bdo", ...)`, `bind(..., session_id="session_deadbeefdeadbeef")`, `cross`) | 0 | composer verdict `BOUND`; Gateway reading `REFUSED`, stage `check-attribution`, `ACTOR_ATTRIBUTION_MISMATCH`, with `receipt_id` (the node's own foreign-session refusal, reachable and not driven by the probe: F19); the own `COMMITTED` receipt payload carries `detail.resolution` and no grant identifier (F22); `node.console.grants(reader_id=actor)` -> `AuthorityRefused: ... holds no live read:authority grant` |
| `python -m unittest scripts.tests.test_sov_fresh` | 0 | `Ran 15 tests in 2.335s OK` |
| `python scripts/sov_custody.py selfcheck` | 0 | `46 case(s), 27/27 declared refusals reached`; `selfcheck PASS` |
| `python scripts/sov_next.py --strict` | 0 | `scripts/sov_fresh.py [PRESENTED] drawn / custody custody:phase-1-5/fresh-participation`; `PASS: phase/custody precedence is explicit ...` |
| `python scripts/sov_active_phase_progress.py` | 0 | no output (pass-1 residual reproduced) |
| `python scripts/lint.py` | 0 | `PASS: repository hygiene (1186 text files, 553 Python modules, 10 named debt)` |
| `python scripts/verify.py` | 0 | `PASS: 51 checks in 15.862s wall`; `BUDGET DEBT: 9 check(s) over ceiling`, among them `fresh participation slice: 1.570s over its 1.500s ceiling` (F24); the `FAIL` lines in the output are planted tooling self-test output inside `repository tooling tests` |
| `python -c` over `sovverify.checks.CHECKS` after package import | 0 | 51 names, 51 distinct, `fresh participation slice` once (F13 repaired) |
| `python scripts/sov_fresh.py selfcheck` timed alone, three runs | 0; 0; 0 | 0.609s, 0.649s, 0.611s wall |
| `python scripts/sov_witness_layer.py records` (before writing) | 0 | `PASS: 7 witness receipt(s) graded, 0 unusable, 7 stale against their subject` (the pass-1 receipt is now `STALE_SUBJECT`, as expected once the subject moved) |
| recomputation of the pass-1 receipt's 24 `observed_state_digests` against `git show d40d61f:<address>` | 0 | 24/24 match |
| `python scripts/sov_standing.py`; `python scripts/sov_clarity.py check`; `python scripts/sov_docs.py check` (before writing) | 0; 0; 0 | `PASS: 1 standing claim(s)`; `PASS: clarity scope and receipts are well-formed and current`; `PASS: documentation page matches 281 documents` |
| `sha256sum` over 25 addresses | 0 | recorded in the receipt's `observed_state_digests` |

### Pass-1 findings, disposition at 161d559

- **F1 - repaired through the surface for two of three legs; the third is F19.**
  `other_actor_on_this_session` is refused by the Gateway at `check-attribution` with
  `ACTOR_ATTRIBUTION_MISMATCH` (`services/gateway/.../attribution.py:32`) and
  `other_actor_without_the_grant` at `check-authority` with `AUTHORITY_REFUSED` /
  `AuthorityRefused` (`services/gateway/.../core.py:247`); both are read from receipts the node
  wrote. `_mismatch` (`probe.py:70-87`) compares exact codes against `reason` or `diagnostic`
  and returns `REFUSED` only when the participant's own crossing `COMMITTED`; nothing but those
  three codes satisfies it. The `borrowed-authority` variant and the `sovkernel.authority`
  request are gone.
- **F2 - repaired.** `grant_id` is `admitted["grant_id"]`, the Console record
  `console.grant(actor, required_authority, SCOPE, granted_by=issuer)` returned
  (`node.py:49-51`); it names a grant the actor holds, and is `None` with no issuer, which the
  instrument fails as `missing grant_id`. Residual F22.
- **F3 - repaired through the surface.** `probe.py:99-100` substitutes
  `principal:unregistered-<session>` whatever the caller declared; the variant fails Q1.1 and
  Q1.3 with and without an issuer.
- **F4 - repaired as derived.** `oral_history_used` is `bool(layers.undeclared_inputs(declared))`
  (`probe.py:96,162`; `layers.py:24-31`) and fires on `SOV_PRINCIPAL` or
  `SOV_PRINCIPAL_REGISTRY` set and undeclared. The same derivation is what F18 trips on.
- **F5 - repaired as derived.** Cleanup is the custody's declared list plus leases the lease
  store reads as orphaned after the host session ended plus a console session the Record
  reads as `OPEN` (`probe.py:142-149`; `node.py:104-111`). The labels are the probe's, the
  facts are the stores'.
- **F6 - repaired.** `interface_binding_id` is `own_binding["interface_binding_id"]`, `None`
  on refusal (`node.py:73-74`; `probe.py:176`); observed as `missing interface_binding_id` on
  every no-issuer run.
- **F7 - repaired.** Codes, not verdicts (`probe.py:76-86`).
- **F8 - repaired.** `--json` is accepted after `run` (`sov_fresh.py:130-134`).
- **F9 - superseded.** The declared-evidence authority request no longer exists.
- **F10 - traced, partly.** An undeclared `SOV_PRINCIPAL_REGISTRY` now fails Q1.1 and is
  named. The observation still does not record which registry the principal resolved from,
  and `run` has no `--registry` argument: the builder's report says the registry "is now an
  explicit argument", which is true of `probe.run` and not of the CLI.
- **F11 - open, residual.** `survives` (`probe.py:145-146`) is true whenever a lease was taken
  and the store reads it orphaned; only declining the lease defeats it.
- **F12 - open, unchanged.** The stage is a declaration nothing measures.
- **F13 - repaired.** `checks.py:298` no longer imports `COMMISSIONING_CHECKS`;
  `sovverify/__init__.py:15` is the one splice; 51 distinct checks measured.
- **F14 - open, unchanged.**
- **F15 - repaired.** The report carries an "Independent witness" section.
- **F16 - open, unchanged** (`layers.py:22,80-93`).
- **F17 - open, residual (product), extended by F25.**

### New findings

- **F18 - MEDIUM, defect. `scripts/sovfresh/probe.py:96`; `scripts/sov_fresh.py:80,103-109`;
  `scripts/sovverify/clocks.py:135`.** `selfcheck` reads `FAIL` when the operator's
  environment carries `SOV_PRINCIPAL` (measured: exit 1, `positive variant failed ...
  undeclared environment inputs: SOV_PRINCIPAL`), although `layers.speaking_as` overrides both
  resolver variables for every selfcheck run, so the environment cannot change what selfcheck
  resolves. `cmd_selfcheck` passes no `declared` set and `probe.run` grades the operator's
  environment anyway. `fixture_registry` builds its copy from `principals.load(ROOT)`, which
  honours `SOV_PRINCIPAL_REGISTRY`, so the fixture's base is itself an undeclared environment
  input (`SOV_PRINCIPAL_REGISTRY=/nonexistent selfcheck` -> `FAIL: no principal registry`).
  `verify.py` launches every check through `Popen` without `env=`, so the custody's closure
  command and the `fresh participation slice` check go red on an input they do not read.
  Consequence: the closure check's verdict varies with the operator's shell; a check that
  fails on what it cannot see is the defect class this repository's history names.
- **F19 - MEDIUM, defect. `scripts/sovfresh/probe.py:56-58,76`; `scripts/sovfresh/node.py:1-6,64,88-90`;
  `scripts/sovnode/bindings.py:107-108`.** The `foreign_session` leg of `_mismatch` is
  satisfied by `SESSION_ATTRIBUTION_CONFLICT`, raised by the Node Interface binding composer in
  `scripts/sovnode/bindings.py` when the probe's own argument `session_id: "another-session"`
  disagrees with the binding's session id. The request never reaches the node, `cross` returns
  at stage `bind`, and no receipt exists (`--json` shows no `receipt_id` for that leg). The
  node's own refusal of a session it never opened was reachable through the `session_id`
  override on `node.bind` (`node.py:64`), which the probe never uses; driven directly, the
  Gateway refuses it at `check-attribution` with `ACTOR_ATTRIBUTION_MISMATCH` and a receipt.
  Consequence: the module docstring "the Gateway refuses or admits the crossing, and the
  receipt carries the reason" and the report's "every identity and refusal is read from the
  node's Console and Gateway records" are untrue of one of the three legs Q1.3 rests on.
- **F20 - MEDIUM, defect. `scripts/sov_fresh.py:6-7,137`; `scripts/sovfresh/node.py:38-51`;
  `services/console/src/soveraeign_console_service/permits.py:100-103`.** `--issuer` is
  described as "the seat that holds that authority" and "the seat opening this node's permits
  office". Nothing checks it. On a fresh node `permits.issue` runs `_genesis(console,
  granted_by)` for whoever grants first, so `--issuer principal:nobody-at-all` reads `PASS`,
  exit 0, Q1.3 `holds`. The registry that could have measured the name
  (`contracts/principals.json`, `root_principal: principal:bdo`) is loaded by the same run and
  not consulted; the observation's `issuer` field records the typed string as a seat.
  Consequence for P15-X1: the positive live run is a controlled fixture (temporary node, genesis
  seeded under a typed name), which is admissible as a demonstration that the mechanism
  separates identities and refuses borrowed ones, and is not evidence that any seat issued
  anything. The repair is the builder's: refuse an issuer the registry does not name as root,
  or name the flag for what it does and record it as a fixture in the observation.
- **F21 - LOW, defect. `scripts/sovfresh/node.py:48`.** `--issuer ""` escapes as an uncaught
  `AuthorityRefused` traceback from the Console; the node layer's own contract is that a
  refusal is returned, not raised.
- **F22 - LOW, residual (product receipt shape). `scripts/sovfresh/node.py:99`;
  `services/gateway/src/soveraeign_gateway_service/core.py`.** The `COMMITTED` receipt
  carries no grant identifier (`own.grant_id` is `null`), so "this crossing was admitted under
  `grant_id`" is inferred from the `check-authority` stage having passed, not read from the
  receipt. The actor cannot read its grants back (`console.grants` refuses without
  `read:authority`); the probe reads the grant from the write's return, which is the record as
  appended.
- **F23 - LOW, residual. `scripts/sovfresh/probe.py:155,174`.** Two sessions are reported under
  one label: Q1.1 `session_id` is the host session (`fresh-<id>`), Q1.3 `session_id` is the
  console session (`session_<id>`). The instrument does not relate them and a reader of the
  observation would take them for one.
- **F24 - LOW, residual. `contracts/verification-budget.json` (`fresh participation slice`:
  1.5); `contracts/custodies/phase-1-5.json:57`.** The check read 1.570s pooled at this
  commit, over the ceiling pass 1 saw set from 0.46s evidence before the repair added a node
  and three more crossings per variant; alone it reads 0.61-0.65s. Attributed debt, not a
  refusal. The same custody member's `note` now carries "findings repaired in the second
  commit", the builder's own repair claim inside a contract fixture before any witness read
  it; `stage_observed_by` is correctly `null`.
- **F25 - LOW, residual (product, not probe).** With an issuer and an `UNIDENTIFIED`
  principal (`--variant unregistered-principal --issuer principal:bdo`) the Console opens a
  session with `principal_id: null` and the Gateway `COMMITTED` the crossing; the probe's Q1.1
  and Q1.3 fail for the missing principal, so the product's admission is masked. Whether a
  crossing may commit for an actor whose durable principal nobody named is the Console and
  Gateway contracts' question, alongside F17's lease under a null controller.

### Conditions for a later pass to support `BUILT -> WITNESSED`

- C5 (F18): make `selfcheck` independent of the operator's environment: declare or scrub the
  two resolver variables it overrides, and read the fixture's base registry from the repository
  path, not the override.
- C6 (F19): drive the foreign-session leg through the Gateway (a session the node never opened,
  consistent in binding and arguments) and read the node's receipt; keep the composer's
  conflict as an additional reading if wanted, but not as the leg that satisfies Q1.3.
- C7 (F20, F21): either refuse an `--issuer` the registry does not name as `root_principal`,
  returning the refusal, or rename and document the flag as seeding a temporary node's genesis
  and carry that into the observation; return the empty-issuer refusal rather than raising it.
- C1 to C4 from pass 1 are discharged except as F19 narrows C1.

### Judgement items (questions, not the witness's to answer)

- J1 to J3 carried from pass 1. J1 is narrowed by the builder's choice: the instrument requires
  a grant, and a node with no issuer reads Q1.3 unmet.
- J4. May P15-X1 be observed against a temporary node whose root grant the probe itself seeded
  under a declared issuer name, once the name is checked against the registry, or does the
  clause want a node whose permits office the root seat opened and whose grant to this
  participant persists beyond the run?

### Uncovered

- `docs/documentation.html` was accepted on `verify.py`'s `documentation reader` and
  `sov_docs.py check`; the 15 changed lines were skimmed for shape only.
- The Console and Gateway services' own test suites were not rerun; their behaviour was read
  through the probe's node layer and one direct drive of the same functions.
- The Record Service's `evidence_projection` was not exercised beyond the probe's own call.
- No network, no `gh`, no ruleset query.

### Landing residual

As in pass 1: `scripts/sovdocs/facets.py:66` indexes `witness/*.md`, so after this section is
written `documentation reader`, `repository tooling tests` and `sov_docs.py check` are expected
to read the built page as stale. The witness may not rebuild the page; whoever lands this record
runs `python scripts/sov_docs.py build`. The exact readings after writing are in the receipt's
`telemetry.after_writing`.

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
