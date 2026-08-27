---
name: sov-verification
description: Domain know-how for the Soveraeign verification domain - the dependency-free verification harness (scripts/verify.py, scripts/lint.py, scripts/verify_bootstrap.py), the CI gate .github/workflows/verify.yml, and stewardship of the ENGINEERING.md engineering baseline. Load when a task names "sov-verification" or the "verification domain", edits any of those artifacts, touches the graded verify budget, adds or tightens a lint or bootstrap check, or reconciles baseline statements across ENGINEERING.md, AGENTS.md, CONTRIBUTING.md, and .cursorrules. Not for the conformance oracle (conformance domain), service implementations (asset/proofing domains), or governing-document policy at large (governance domain).
---

## Purpose

The verification domain owns the single required repository gate and keeps it
fast, dependency-free, and honest. It enforces the engineering baseline other
domains build against, without ever holding authority itself: a green gate is
evidence, never ratification.

## Owns / Must not

Owns: scripts/verify.py, scripts/lint.py, scripts/verify_bootstrap.py, the CI
gate .github/workflows/verify.yml, and stewardship of ENGINEERING.md baseline
coherence. Per AGENTS.md directory boundaries, /scripts owns verification and
bounded repository maintenance.

Must not: put product business logic in scripts/; add runtime dependencies;
weaken a verification gate, marker, or fixture to make something pass; exceed
the verify budget or loosen a grade band without a decision record; write
another service's state; touch immutable lineage/ evidence.

## Key files

- scripts/verify.py - runs all checks. BUDGET_GRADES holds the bands
  (PLATINUM 3.0, GOLD 6.0, SILVER 15.0) and BUDGET_SECONDS is derived from
  the slowest, so the two cannot drift apart. Every passing run prints its
  grade; only passing 15.0s fails. decisions/0050.
- scripts/sovverify/clocks.py - the two clocks every check is timed on: wall from
  perf_counter, and the CPU spent by the process tree the check waits for (a
  Windows job object, or os.wait4 rusage on POSIX). A CPU that cannot be taken is
  reported as unmeasured; wall is never substituted for it. The gate keys on
  aggregate wall time and on nothing else, so adding a clock changed no verdict.
  Do not read a rise in CPU as proof the repository grew: contention buys real
  cycles, and on ubuntu-latest one commit measured twice read half the CPU on the
  slower runner. decisions/0071 proposes keying the budget on compute, carries
  the measurements, and recommends its own rejection; it is not in force.
- scripts/lint.py - hygiene: UTF-8 decodability, CRLF/trailing-whitespace/final-
  newline, Python syntax and future-annotations, 300-line module limit with
  KNOWN_MODULE_DEBT, duplicate top-level YAML keys, decision-number collisions,
  secret shapes, local absolute user paths. It reads bytes,
  never Path.read_text - universal-newline translation once made the CRLF rule
  unreachable; scripts/tests/test_lint.py holds that defeating case.
- .gitattributes - pins `* text=auto eol=lf` so the working tree is LF on every
  platform, and `lineage/** -text` so evidence digests stay byte-exact. Required
  and marker-checked by scripts/verify_bootstrap.py.
- scripts/verify_bootstrap.py - REQUIRED file list, governing-document markers,
  SOURCES.lock digests, founding scenarios, conformance controls, contract JSON.
- .github/workflows/verify.yml - CI runs `python scripts/verify.py` on Python
  3.11 and 3.12 with `contents: read`.
- ENGINEERING.md - proposed reference baseline (owned document; this domain
  stewards its coherence, Bdo ratifies its content).
- CONTRIBUTING.md, AGENTS.md, .cursorrules - carry markers verified by
  scripts/verify_bootstrap.py; keep them consistent, never delete a marker to
  make a broken document pass.

## Standing and constraints

- STATUS.yaml: `engineering_framework_status:
  OWNER_ACCEPTED_A1_PHASE_I_REFERENCE_BASELINE`, with the graded budget recorded
  in the comment above it (`decisions/0050`).
  Python 3.11+, SQLite, filesystem content-addressed custody, JSON Schema
  Draft 2020-12, dependency-light unittest, and local-process/CLI-first
  operation are accepted (`decisions/0024-open-decision-drain.md`, O2). They are
  mechanisms, not semantic authority, and may be replaced behind proved contracts.
- The harness's own self-tests establish `BUILT` only. A check cannot witness
  itself, and `scripts/verify.py` emitting a green run is never authority.
- Every check must declare how it avoids relying on the thing it checks. That
  relation string is a claim; if it is false, the check is worse than absent.
  Correct it the moment the check changes.

## Named operations

- gap-closure: add a check enforcing an invariant already stated in the
  governing set but not yet enforced, with a positive and a defeating case
  first (RECORD_LOCAL).
- lint-rule: add or tighten one scripts/lint.py hygiene rule with a
  demonstrated defeating example, keeping the current tree passing honestly.
- bootstrap-marker-sync: update REQUIRED files or markers in
  scripts/verify_bootstrap.py when a governing document legitimately changed,
  never weakening a marker to silence a failure.
- budget-report: measure per-check timing against the bands and report which
  grade the run earns and what the next one costs; changing a band or the
  budget itself needs a decision record.
- doc-coherence: reconcile baseline statements across ENGINEERING.md,
  AGENTS.md, CONTRIBUTING.md, and .cursorrules so no document becomes a
  competing authority.
- ci-parity: confirm .github/workflows/verify.yml still runs exactly
  `python scripts/verify.py` with read-only permissions and supported Pythons.
- debt-registry: maintain KNOWN_MODULE_DEBT in scripts/lint.py - name new debt
  with its split plan; remove an entry only when the split actually happened.
- witness-prep: assemble the claim list and check inventory an independent
  witness needs to move engineering_framework_status toward WITNESSED; this
  operation never witnesses its own domain's work.

## Verification

From the repository root:

- `python scripts/verify.py` - the required gate; graded wall time after
  Python starts, failing only past 15.0s.
- `python scripts/lint.py` - hygiene subset.
- `python scripts/verify_bootstrap.py` - structure and evidence subset.
- `python conformance/run.py` and
  `python -m unittest discover -s conformance/tests -v` - oracle checks the
  gate wraps.
- From services/asset: `python -m unittest discover -s tests -v` - reference
  participant tests the gate wraps.

## Vocabulary

- OPEN -> BUILT -> WITNESSED -> RATIFIED - artifact standing lifecycle; a
  passing self-test may establish BUILT, never WITNESSED or RATIFIED.
- RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE - record standing in the
  operational System of Record; do not conflate with the artifact lifecycle.
- ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED - event
  outcomes, recorded separately from standing.
- RECORD_LOCAL / RESOURCE_CONSUMPTION / EXTERNAL_WORLD - effect classes; every
  consequential operation declares exactly one; EXTERNAL_WORLD is refused in
  Phase I.
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
- checks_observed: exact commands, exit codes, timing versus the budget.
- standing_proposals: at most OPEN -> BUILT from self-tested work; never claim
  WITNESSED or RATIFIED.
- judgement_items: questions queued for Bdo, stated as questions.
- next_operation: the next bounded operation, or none.
