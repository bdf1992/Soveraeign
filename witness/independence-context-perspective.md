# Witness · the seven-edge independence walk

Subject: commit `7be1323c91951f2404abe4394d04bc7c7dc39292` on
`claude/agent-independence-definition-z4crlv`, the build of
`decisions/0104-independence-is-context-and-perspective.md`.

Pass 1, 2026-09-07. Verdict **FINDING**, dissenting. The pass supported no standing.

## Filing note

Everything below this note is pass 1's, quoted, and nothing else is.

The witness could not file it: `scripts/sovdocs/facets.py` classifies `witness/*.md` into the
documentation corpus, so a new file here turns `verify.py` red and repairing that needs a file
a witness may not edit. The builder filed these bytes. That is weaker custody than a witness
writing its own record, and it is a `KNOWN-GAPS` row rather than a thing smoothed over.

Two earlier versions of this note were themselves the defect. The first carried a
`Builder's disposition` section below the witness's closing line; the second moved that out and
put two paragraphs of builder prose about pass 2 *above* the line certifying the file as quoted
witness bytes. Pass 3 found the second. Everything the builder has to say about these passes is
in `reports/2026-09-08-independence-repairs.md`, which cites this record.

## Independence of this pass

Launched by the builder, which `decisions/0100` requires and `decisions/0104` Ruling 4 admits.
Context handed over was the objective in the owner's own words, the frozen commit, and the
file list; the builder's reasoning, plan and conclusions were withheld, and the pass was told
to derive its criteria from the repository's contracts rather than from the decision record's
account of itself. Frame differs: `sov-witness`, not the building profile.

One limit, recorded because the definition this pass grades is the one it was run under: the
deliverable is partly a decision record, so the artifact under review *is* the builder's
reasoning. The context axis cannot be clean on a rationale-shaped subject, and the perspective
axis carried this pass.

## Observed

Working tree clean at start, after every probe, and at the end; `verify.py` run twice with
identical verdicts (trap T6 discipline).

| Command | Exit | Result |
| --- | --- | --- |
| `python3 scripts/verify.py` (twice) | 0 | `PASS: 52 checks in 15.744s / 15.790s wall` |
| `python3 scripts/lint.py` | 0 | `PASS: repository hygiene (1225 text files, 562 Python modules, 10 named debt)` |
| service tests, `services/observation/tests` | 0 | `Ran 55 tests ... OK` |
| `python3 scripts/sov_standing.py` | 0 | `PASS: no status field claims WITNESSED or RATIFIED` |
| `python3 scripts/sov_docs.py check` | 0 | `PASS: documentation page matches 287 documents` |

Criteria taken from `services/observation/contracts/service.json` (unchanged by the commit),
`CONTRACT.md` C7, `SPEC.md` `Observation`/`observe_run`, and `AGENTS.md`. The manifest's
`forbids` list was the sharpest instrument: `reading-an-incomplete-record-as-independence`,
`accepting-a-declared-relation-in-place-of-an-inferred-one`,
`accepting-an-executor-report-as-an-observation`.

Trap T2 holds: none of the findings below is visible to any of those commands.

## Reproduced

The seven-edge walk exists and fires; each new edge produces `DIRECT` on a record carrying its
datum. The retired edge is gone from the enum and a record still written in it is refused.
`edges_examined.minItems` is coupled to the enum length, and `CHARTER.md`'s edge list is
coupled to the enum in both directions — genuine structural guards, not declarations.

The `unanswerable_edges: maxItems 0` guard is load-bearing: deleting it turns the fixture
`OBS-RELATION-SEM-UNDECLARED-CONTEXT-READS-INDEPENDENT` from refused to accepted.

## Findings

**F1 — five records the manifest forbids reached `INDEPENDENT`.** Adversarial journal slices,
each returning `INDEPENDENT` / `COMPLETE` / no unanswerable edges and validating clean:

| Probe | Record | Result |
| --- | --- | --- |
| P1a | a prior arrow's actor with no launch entry; candidate loads that actor's profile under another id | `INDEPENDENT` |
| P2 | `payload.lease` a string rather than an object | `INDEPENDENT` |
| P3b | the executor's `ATTEMPTED` names a decoy `subject_id`; the candidate moved the real subject | `INDEPENDENT` |
| P4 | `predicates_source_actor` names an alias of the executor carrying no profile | `INDEPENDENT` |
| P5 | launcher declares thin context while having handed over the transcript | `INDEPENDENT` |

P1a defeats Ruling 3 directly: `_walk_perspective` treated a missing profile as unanswerable
and `_walk_lifecycle` treated the same absence as "different", so the edge degraded to id
equality and a rename defeated it. `CHARTER.md` claimed the property the implementation had
only for executors. P5 was disclosed in `KNOWN-GAPS.md` and `decisions/0104`; P1a, P3b and P4
were not. P2 is pre-existing at `b1448ee`.

**F2 — the runtime gate did not enforce the invariant the schema was strengthened to hold.**
The `maxItems` constraint lived only in schema validation, which nothing on the runtime path
runs. `require_independent` read `outcome`, never `record_completeness` or
`unanswerable_edges`. An inference reading `INDEPENDENT` over an `INCOMPLETE` record naming
two unanswerable edges was admitted, and the emitted `observer_relation` — the field
`SPEC.md` requires to state how the observer avoided the executor's report — asserted the
record was `COMPLETE`. Also pre-existing: no `run_id` check.

**F3 — the control the grant-edge retirement leans on was defeated by a version of the
executor.** The relay refusal compared ids where the rest of the change compared profiles, so
`infer_relation` read `worker-a-2` as `DIRECT` while `observe_run` admitted it as a submitter.
Two opposite answers about one actor on one record.

**F4 — two mutations survived the 55-test suite**, both on the "silence is not a pass" side:
deleting the `cannot_answer` calls in `_walk_context`'s no-launch branch, and deleting the
refusal for a subject with zero arrows.

**F5 — the demotion was honest but incomplete.** Eight current artifacts still asserted the
old standing, two of them contracts nothing grades: `services/README.md` (the table `AGENTS.md`
points to, and a declared source of `diagrams/service-map.md`, whose prose the commit updated
to the opposite), `CLAUDE.md`, `contracts/custodies/phase-1-5.json`, `contracts/phases.json`
(whose recorded reading of `sov_standing.py` the command falsified), `services/host/SERVICE-SPEC.md`,
`PRD.md`, `ROADMAP.md`, `.claude/epic/NARRATIVE.md`. `services/observation/contracts/service.json`
still described the per-run scope.

**F6 — the standing-test edit was not a weakened oracle**, and the stated reason for it is
true: the removed line graded the record rather than the reader. But one added assertion
compared `read_claims()` to `read_claims(STATUS)` — the same call twice, a vacuous assertion
in the one test whose job is refusing vacuity.

**F7 — `conformance/oracle-controls.json` carried the retired edge name `SAME_ACTOR`**, which
the oracle's predicates never grade. The oracle also does not read `unanswerable_edges`, so
the silence-as-pass closed in the service schema stays reachable at the kernel boundary.

## Standing supported

**None.** The demotion to `BUILT_THIN_SLICE_REMAINDER_DECLARED_NOT_WITNESSED` is the correct
reading and is supported as stated. F1 through F4 are reasons a fresh pass over the seven-edge
walk should not yet conclude. The change is `BUILT` and self-tested; the enforcement surface
had holes its own charter denied.

This is an observation. It settles nothing and ratifies nothing.

## Judgement items raised for Bdo

1. This commit edits `AGENTS.md` and adds a decision record, both excluded from
   `grant:standing-landing-loop`. Does it land under the standing grant or need acceptance?
2. `decisions/0104` question 2 is open and the grant-edge retirement is a builder's default.
   Given F3, does a builder's power over the observer's *authority* stay its own question?
3. Both context edges read a declaration where they could measure. Is a declared context axis
   admissible in the interim, or should `CONSTRUCTION_CONTEXT_INHERITED` refuse until
   something computes the cross-check Ruling 8 describes?
