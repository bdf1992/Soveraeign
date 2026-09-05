# Thin circuit 1: one Phase 1.5 commissioning circuit, end to end, on a trivial unit of work

Session `session-69de8a`, principal `principal:claude-fable-5`, branch
`claude/skill-loop-closure-identity-iiogql`, 2026-09-05. Concern
`concern:phase-1-5/thin-circuit-1`. Effect class `RECORD_LOCAL` throughout; no grant held,
nothing external touched, no phase state changed.

The frame Bdo asked for: one category, the items dependency-mapped, parallel runs only over what
benefits from them. The category is the Phase 1.5 exit. Its stages are a chain, so the honest
first move was not four parallel lanes but one circuit run thin, so that the stage where it
fizzles names the missing primitive instead of a plan guessing it. This is that run. Every stage
below used a tool the repository already had; nothing was built to run it.

## The unit of work

Residual R13 in `services/observation/KNOWN-GAPS.md`: a regression test that still passed with
its repair reverted. Chosen because it is inside one service, one effect class, one authority, and
its closure is a command with two polarities.

## The circuit, stage by stage

| Stage | What ran | Result |
| --- | --- | --- |
| Identity, session | `sov_session.py register` under `SOV_PRINCIPAL=principal:claude-fable-5`; `principal` | identified, `UNVERIFIED`, 1 hop from `principal:bdo`; concern, two queues, one source bound |
| Discovery of work | `sov_custody.py list`, `sov_next.py`, `KNOWN-GAPS.md` | R13 under `custody:phase-1-5/evidenced-judgement` |
| Capability, authority | `sov_interface.py show`, `sov_grant.py list` | `observation.observe-run` declared; no grant needed for `RECORD_LOCAL` |
| Lease | `sov_lease.py take` with closure and defeat, then `helper` for the worker and `helper --relation WITNESS` | `lease:services-observation-known-gaps-md-r13`, two child leases |
| Record: attempt | `soveraeign-record append-entry` `ATTEMPTED` | journal seq 1 |
| Execution | `sov-worker` agent, one bounded operation | new case `WitnessResidualsOn3087714.test_the_run_address_reported_as_its_own_output_is_still_refused`; fails with the `\| {record.run_id}` union reverted (exit 1), passes with it (33 tests, exit 0); `observe.py` unchanged; presented, uncommitted; held at `AUTHORITY_SEAM` for the docs projection |
| Record: outputs, report | `OUTPUT` per file with sha256, `REPORTED` | seq 2 to 5 |
| Predicates before looking | Observation Service `declare_predicates` | `BYTES_PRESENT` and `DIGEST_EQUALS` per reported address, declared before the observer read anything |
| RecordProjection | `soveraeign-record project-evidence` for the witness | `urn:soveraeign:record-projection:262dac66...`, two included records |
| Independent observation | `sov-witness` agent: tree digests, both polarities re-run, `verify.py`, `observe-run` as its own actor | relation `INDEPENDENT`; observation `urn:soveraeign:observation:37d4ce49...`; all predicates true; one **dissent**: `verify.py` exit 1, the changed gap list is clarity-covered and its receipt was stale |
| Repair inside the concern | controller: clarity review recorded for `KNOWN-GAPS.md`, heading lead under the residuals reworded to admit a later repair, docs page rebuilt; recorded as a second `ATTEMPTED`, three `OUTPUT`, one `REPORTED` | seq 6 to 10 |
| Second observation | same witness, same lease, new declaration over four addresses | `verify.py` 50 of 50 PASS, clarity PASS, lint PASS; relation `INDEPENDENT` over both executors; observation `urn:soveraeign:observation:8fb249ea...`; eight predicates true; supports landing at these digests |
| Findings | witness `WORK` Finding, schema-valid, frozen before the controller read it | `reports/observations/2026-09-05-thin-circuit-1-witness-observation.json` |
| Settlement | `sov_kernel.py check` on a `settle_run` request carrying the second observation | `PERMITTED: settle_run may commit as COMMITTED`; receipt appended, seq 13 |
| Cleanup | `sov_lease.py close` on all three leases against the receipt | all `COMPLETED`; parent `standing_reached: WITNESSED`; `status`: no leases held |
| Record into the artifact | `export-journal`, `verify-export` from an empty store | 13 entries, head `6f59baa1...`, `verified: true`; `reports/observations/2026-09-05-thin-circuit-1-journal.json` |
| Admission | member added to `custody:phase-1-5/evidenced-judgement` | `sov_next.py` now lists the run under active phase work |
| Discovery by a fresh participant | see below | see below |

## Witness disposition

Observer `urn:soveraeign:principal:instance:sov-witness-thin-1`, a participant that did not build
or edit anything under observation. Two passes, one file written, the frozen Finding byte-identical
across both. First pass: every claim `HOLDS` except `verify.py` green (`DISSENT`, clarity receipt
stale) and the `pre_tree` claim (`UNATTESTABLE`, the index was measured, not the tree). Second
pass: the dissent resolved, every repair `HOLDS`. Standing supported: `OPEN -> BUILT` for R13; the
three evidence conditions of `grant:standing-landing-loop` met at these digests. Judgement items
for Bdo: none. The witness's full record is the file named above; this report is not it.

## Where it fizzled, in order met

Each is a missing primitive or a wrong shape, found by running rather than by planning. None
stopped the circuit; each was worked around by a reachable route and recorded.

1. **Two vocabularies for one principal.** The registry names `principal:claude-fable-5`; the lease
   schema refuses anything but `urn:soveraeign:principal:<kind>:<id>`. The lease was taken under the
   URN form. One principal, two spellings, no mapping owned anywhere.
2. **The run-scoped RecordProjection omits the run's outputs and says `omissions: []`.** Scoping by
   subject collects the entries on the run subject and none of the `OUTPUT` entries whose subject
   is the output address, though their payload names the run. The Finding could cite only two
   addresses. The commissioning instrument then reads the empty list as "omissions missing"
   (Q2.2), so it cannot tell "nothing omitted" from "omissions undeclared".
3. **The observer has no write path to the journal.** Both observations were appended by the
   controller; the first under the observer's actor id, which the witness flagged, the second under
   the controller's with the observer in the payload. Which is right is the Record owner's.
4. **`settle_run` is judged but performed by nobody.** The kernel check returned `PERMITTED`; the
   receipt was appended by the controller by hand. The transition has an evaluator and no
   participant.
5. **`ATTEMPTED` cannot fingerprint the working tree.** `git write-tree` reads the index, so
   `pre_tree` equalled the post-change tree. A run has no honest pre-state address.
6. **A second attempt reuses the first's fence and expiry.** The controller's repair attempt was
   recorded under fence 1 with the worker's expiry; the record has no word for a second executor
   on one run, and `relation.py` names one `executor_id` over a two-executor record.
7. **The clarity receipt records a digest and a flag, not a reading.** "Read the changed row
   against the case it names" is the controller's word (the witness's residual S-d; the
   commissioning report of 2026-09-03 raised the same, J3).
8. **No participant-in-work Finding, no comparison.** The circuit's judgement half ran on one
   subject. Q2.3 and Q2.4 fail for that reason and no other.
9. **A "fresh session" cannot be simulated in-process.** `sov_session.py --name` re-bound to this
   session's concern and refused `SESSION_CONCERN_IMMUTABLE`, which is correct; a fresh
   participant had to be a separate agent.
10. **The host withheld the helper tool from the worker.** Reported by name, not as a rule.
11. **One clone, one session registry.** A second participant in the same clone reads the
    first's registration as its own (fresh-participant friction below). Isolation of a fresh
    participant is a property of the process, not of the repository, and the brief cannot say
    whose context it is showing.
12. **The Observation Service has no command line.** The observation was reproducible only
    through a scratchpad driver, so a later participant can verify the export but not repeat the
    observation from the artifact.

## Commissioning grade

`conformance/commissioning.py`, the twelve P15 predicates, over an observed record holding only
what this run actually did (`observed.json` in the session scratchpad; the grade is reproduced in
the table). Pass: Q2.1 (history in Record, reconstructable, private state not authoritative),
Q3.1 (independent observation, settled against current state, receipt, no inventory left),
Q3.2, Q4.1, Q4.2 (the candidate below cites its sources and holds no standing). Fail: Q1.1 (no
projection at entry), Q1.2 (no cleanup obligations declared on the lease), Q1.3 (no grant, so
identity separation could not be shown; cross-principal refusal not exercised), Q2.2 (fizzle 2),
Q2.3 and Q2.4 (fizzle 8), Q4.3 (no alternate institution attempted). Q3.2 passes on the
discovery below. Five of twelve on the first circuit. That number is the density reading for
this pass.

## Discovery by a fresh participant

A separate agent with no context, told only to enter through the repository's own signposts
(`CLAUDE.md`, `AGENTS.md`, `sov_session.py brief`, `sov_next.py`, `sov_custody.py list` and
`board`), found the run from `sov_next.py`'s active-phase-work block, boarded
`custody:phase-1-5/evidenced-judgement`, read both evidence files, verified the journal export
against an empty store (13 entries, `verified: true`), and answered correctly what the work was,
who executed it (two actors), who observed it, the inferred relation, and that the run settled on
a kernel-permitted `settle_run` with the settler disclosed as the second executor. It named the
capability it could now use: a portable self-verifying journal export, and an observe-run whose
own-report guard is pinned by a defeating test. That is the Q3.2 read: the accepted result was
discovered and used without oral history, so the predicate passes.

Its friction, which is evidence:

- `sov_session.py brief` showed it this session's registration, intent and concern as though they
  were its own, while calling it the only live session with an unidentified principal. The
  session registry is per clone, so a second participant in the same clone inherits the first's
  context and cannot tell. A fresh participant is a separate process, and a shared clone cannot
  isolate one.
- The observe-run it read about was performed by a session-scratchpad driver, not a repository
  command, so from the bytes alone it could reproduce the export verification but not the
  observation. The Observation Service has no command line.
- `verify-export` creates an empty store at whatever `--root` it is given, so "touch no live
  store" held only because the root named was empty.
- The receipt's `input_state_digest` is not reconstructable from the two evidence files; it took
  the kernel verdict as recorded.
- `sov_custody.py list` alone could not say which of six open custodies held the recent work;
  `sov_next.py` could. The board was the one signpost that named both evidence files.

## Candidate next Definition

`proposal:phase-1-5/thin-circuit-1-next-definition`, standing `RECORDED`, authority `NONE`,
sources: the thirteen journal entries and the witness observation named above. It proposes no
policy. It says what the next circuit needs before it can score higher, each item one primitive:

- a run-scoped projection rule that includes entries whose payload names the run, and an
  `omissions` field that distinguishes none from undeclared;
- one spelling of a principal, or a declared mapping between the two;
- a journal write path for an observer, or a rule that the appender is the actor;
- a participant that performs `settle_run` from a permitted check and writes the receipt;
- a working-tree fingerprint for `ATTEMPTED`, and a fence per attempt;
- a participant-in-work Finding and a comparison record, so Q2.3 and Q2.4 can be tried;
- a command line for the Observation Service, so an observation is repeatable from the artifact;
- cleanup obligations on the lease at `take`.

Nothing here is required to be adopted. It is the settled experience of one run, cited.

## Defaults taken

- The circuit ran in the shared working tree, not a worktree: one live session, and a worktree
  would have split the journal from the bytes it describes.
- The controller repaired the witness's dissent itself rather than re-leasing the worker: same
  service, same effect class, same authority.
- Two `KNOWN-GAPS.md` rows are now stale and were **not** edited: "Settlement: nothing settles a
  run anywhere" and "no run of this service, or of any service, has been observed". Editing them
  after settlement would move the observed bytes. That is the next bounded operation in the
  same service, and the exact stale sentences are named here so it is not lost.
- The journal export is committed as evidence; the live store under `.local/record` is
  gitignored runtime state and is not.

## Standing

`observation_service_status` unchanged. R13 `OPEN -> BUILT`, supported by an independent
observation. Custody `phase-1-5/evidenced-judgement` gains one member at `WITNESSED`,
`PRESENTED`. No phase clause is claimed earned. Nothing here is ratified.

## Terminal

Presented on the branch. Not landed on `main`: the change edits `contracts/custodies/phase-1-5.json`
and this report, and the ratified standing grant excludes neither, but the session was asked to
run the circuit and collect the disposition, not to land. The landing gate is the next step if
Bdo wants it, and the witness's second pass says the tree meets its three evidence conditions.
