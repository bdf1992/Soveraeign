---
name: sov-verification
description: Domain know-how for the Soveraeign verification domain - the dependency-free verification harness (scripts/verify.py, scripts/lint.py, scripts/verify_bootstrap.py), CI verification surfaces, evidence correlation, gate justification, and stewardship of the ENGINEERING.md engineering baseline. Load when a task names "sov-verification" or the "verification domain", edits those artifacts, touches the graded verify budget, adds or tightens a lint/bootstrap check, analyzes repeated CI failures, audits blocking gates, or reconciles baseline statements across ENGINEERING.md, AGENTS.md, CONTRIBUTING.md, and .cursorrules. Not for the conformance oracle (conformance domain), service implementations (asset/proofing domains), or governing-document policy at large (governance domain).
---

## Purpose

The verification domain owns the canonical repository verifier and keeps its
engineering evidence fast, dependency-free, attributable, and honest. It
enforces the engineering baseline other domains build against without ever
holding semantic authority itself: a green gate is evidence, never
ratification.

Verification follows one compression invariant:

> one authoritative producer per engineering fact; independent observers may
> reproduce evidence; projections and compatibility runs do not become new
> owners of the fact merely because they execute separately.

Several checks may legitimately observe the same defect. Correlate them before
turning each red observation into a separate concern.

## Owns / Must not

Owns: scripts/verify.py, scripts/lint.py, scripts/verify_bootstrap.py, CI
verification mechanics under .github/workflows/, engineering-evidence
correlation, gate-card analysis, and stewardship of ENGINEERING.md baseline
coherence. Per AGENTS.md directory boundaries, /scripts owns verification and
bounded repository maintenance.

Must not: put product business logic in scripts/; add runtime dependencies;
weaken a verification gate, marker, or fixture to make something pass; loosen a
grade band without the decision path that owns it; write another service's
state; treat repeated observations as repeated defects without evidence; turn
an advisory signal into a blocker merely because its workflow exists; or touch
immutable lineage/evidence.

## Key files

- scripts/verify.py - runs the canonical repository check surface and reports
  attributed per-check evidence.
- scripts/sovverify/clocks.py - the two clocks every check is timed on: wall from
  perf_counter, and the CPU spent by the process tree the check waits for (a
  Windows job object, or os.wait4 rusage on POSIX). A CPU that cannot be taken is
  reported as unmeasured; wall is never substituted for it. A rise in CPU is
  not by itself proof the repository grew: contention can buy real cycles.
- scripts/lint.py - hygiene: UTF-8 decodability, CRLF/trailing-whitespace/final-
  newline, Python syntax and future-annotations, 300-line module limit with
  KNOWN_MODULE_DEBT, secret shapes, local absolute user paths. It reads bytes,
  never Path.read_text - universal-newline translation once made the CRLF rule
  unreachable; scripts/tests/test_lint.py holds that defeating case.
- .gitattributes - pins `* text=auto eol=lf` so the working tree is LF on every
  platform, and `lineage/** -text` so evidence digests stay byte-exact. Required
  and marker-checked by scripts/verify_bootstrap.py.
- scripts/verify_bootstrap.py - REQUIRED file list, governing-document markers,
  SOURCES.lock digests, founding scenarios, conformance controls, contract JSON.
- .github/workflows/ - transports and presentations of verification evidence.
  A workflow name or matrix cell does not create a second semantic owner for the
  repository-validity fact. Compatibility dimensions remain useful evidence
  when they test a genuinely different environment.
- ENGINEERING.md - proposed reference baseline (owned document; this domain
  stewards its coherence, Bdo ratifies its content).
- CONTRIBUTING.md, AGENTS.md, .cursorrules - carry markers verified by
  scripts/verify_bootstrap.py; keep them consistent, never delete a marker to
  make a broken document pass.

## Standing and constraints

Phase I is terminal `CLOSED_INCOMPLETE`; `phase:1-5`, Operational Commissioning,
has been open since 2026-09-03 (`decisions/0102`). Verification remains cross-phase engineering
substrate and does not infer current authority from historical phase rules.

The harness's own self-tests establish `BUILT` only. A check cannot witness
itself, and `scripts/verify.py` emitting a green run is never authority.

Every check must declare how it avoids relying on the thing it checks. That
relation string is a claim; if it is false, the check is worse than absent.
Correct it the moment the check changes.

## Observation correlation

Before escalating a red observation, derive a correlation key from the most
stable available referent:

`subject revision × failing predicate/check × normalized failure signature`

The key is diagnostic, not identity law. If a failure contains a stronger exact
subject such as an operation id, fixture id, or invariant id, prefer that over
prose text.

Classify repeated observations as:

- **new defect** — the evidence demonstrates a materially different violated
  predicate or subject;
- **useful corroboration** — a different environment, independent observer, or
  deliberately different attack reproduces the same defect and adds evidence;
- **redundant recomputation** — the same subject and predicate are rediscovered
  without adding material evidence after sufficient detection already exists.

Never optimize toward literal one-observation-per-defect. Independent witness
and compatibility evidence intentionally amplify some facts. Optimize away
unexplained redundant amplification.

Useful non-authoritative readings include:

- total red observations / unique defect signatures;
- useful corroborations / repeated observations;
- runner time after sufficient detection / total verification runner time.

These become gates only through a separately justified policy.

## Gate cards

A blocking gate should be explainable by one compact card:

`subject | risk | scope | test | pass criterion | evidence class | expected cost | owner`

The card is an analysis shape, not a new authority registry. Reuse an existing
owning contract/decision when it already carries these facts.

Rules:

1. No explicit pass criterion means the signal is advisory or telemetry; merely
   completing a procedure is not a quality threshold.
2. Scope must be proportional to the risk being guarded; whole-repository work
   is not justified by a narrow concern without evidence.
3. Expected cost is part of the gate's design. A useful check can still be the
   wrong synchronous blocker.
4. Evidence class must say what the result proves and what it cannot prove.
   Mutation testing, for example, is Blue test-quality evidence, never an
   independent witness by itself.
5. A gate that has earned blocking authority may still be optimized, correlated,
   or moved earlier; compression must not silently weaken its criterion.

## Named operations

- gap-closure: add a check enforcing an invariant already stated in the
  governing set but not yet enforced, with a positive and a defeating case
  first (RECORD_LOCAL).
- lint-rule: add or tighten one scripts/lint.py hygiene rule with a demonstrated
  defeating example, keeping the current tree passing honestly.
- bootstrap-marker-sync: update REQUIRED files or markers in
  scripts/verify_bootstrap.py when a governing document legitimately changed,
  never weakening a marker to silence a failure.
- budget-report: measure per-check timing and report attributed cost; changing a
  governing band/ceiling follows the decision path that owns that policy.
- doc-coherence: reconcile baseline statements across ENGINEERING.md,
  AGENTS.md, CONTRIBUTING.md, and .cursorrules so no document becomes a
  competing authority.
- ci-parity: confirm CI still invokes the intended repository verifier and
  supported compatibility dimensions with least permissions; report duplicate
  whole-verifier execution rather than assuming every workflow is a unique
  quality fact.
- observation-correlation: group red observations by stable subject/predicate
  signature and distinguish new defects, useful corroboration, and redundant
  recomputation before creating work.
- gate-card-audit: state subject, risk, scope, test, pass criterion, evidence
  class, expected cost, and owner for a blocking check; if criterion or risk is
  absent, recommend advisory standing rather than inventing a threshold.
- debt-registry: maintain KNOWN_MODULE_DEBT in scripts/lint.py - name new debt
  with its split plan; remove an entry only when the split actually happened.
- witness-prep: assemble the claim list and check inventory an independent
  witness needs; this operation never witnesses its own domain's work.

## Verification

From the repository root:

- `python scripts/verify.py` - canonical repository verification.
- `python scripts/lint.py` - hygiene subset.
- `python scripts/verify_bootstrap.py` - structure and evidence subset.
- `python conformance/run.py` and
  `python -m unittest discover -s conformance/tests -v` - oracle checks the
  gate wraps.
- From services/asset: `python -m unittest discover -s tests -v` - reference
  participant tests the gate wraps.

Record exact commands, exit codes, subject revisions, and the check/fixture that
actually failed. Do not report a second workflow name as a second defect without
that analysis.

## Vocabulary

- OPEN -> BUILT -> WITNESSED -> RATIFIED - artifact standing lifecycle; a
  passing self-test may establish BUILT, never WITNESSED or RATIFIED.
- RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE - record standing in the
  operational System of Record; do not conflate with the artifact lifecycle.
- ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED - event
  outcomes, recorded separately from standing.
- RECORD_LOCAL / RESOURCE_CONSUMPTION / EXTERNAL_WORLD - effect classes. The
  current authority/gate path decides what is admitted; historical Phase-I
  phase-wide refusal wording is not current policy.
- Worker - an executor assigned a scoped, leased operation; its report is not
  observation.
- Witness - an independent verifier depositing evidence.
- Observation - independent evidence of what occurred; executor output alone
  cannot establish success.
- Receipt - the record returned by an attempted crossing or operation.
- Proposal - an attributed claim without ratified standing.
- Projection - a rebuildable derived view that never becomes authoritative by
  convenience.

## Report format

- files_changed: paths with a one-line reason each.
- checks_observed: exact commands, exit codes, revision, and correlation key
  where failures repeat.
- gate_cards: only for gates touched/audited in the operation.
- standing_proposals: at most OPEN -> BUILT from self-tested work; never claim
  WITNESSED or RATIFIED.
- judgement_items: questions queued for Bdo, stated as questions.
- next_operation: the next bounded operation, or none.
