# Handoff: witness context, harness grading, and what waits on Bdo

Concern: `concern:harness/witness-context`. Candidate `8183667` on
`claude/witness-context-discovery-runas1`, tree `32935b8`, base `d00f46a`, ten commits,
linear, no merge commits. `verify` exit 0 on 56 checks at the commit; `lint`, `clarity`,
`sov_counts` and `sov_accept audit` all pass.

This is a handoff, not a settlement. It records what stands, what is escalated and to
whom, and what the next participant does. It changes no standing.

## What was wrong, in one paragraph

`SDLC.md`, Release gate item 6, has said since day two that an independent evaluator
receives the contract, the claimed invariants and the built artifact, and that the
builder's tests and plan sit inside that artifact — readable, attackable, never the oracle.
`.claude/workflows/sov-loop.js` opened both of its witness prompts with the Orchestrator's
operation sentence, which is the oracle position. Eleven sibling workflows did the same,
four of them asserting the opposite in the sentence immediately before. The rule was
stated, restated in two unreachable skills, and enforced nowhere.

## What changed

- **One frame builds every witness prompt** (`.claude/workflows/sov-loop.js`). It opens
  with the subject, makes the evaluator derive its own scope from git, resolves the
  owning contract from the paths that actually changed, and puts the builder's account
  last, labelled artifact rather than oracle. Eleven sibling workflows carry the same
  labelling and scope derivation.
- **`scripts/tests/test_witness_context_provenance.py`** renders the prompt rather than
  grading its source, and sweeps all thirty witness dispatches across twenty-two files.
- **`scripts/sov_workflows.py`** and **`scripts/sovprompts/`** grade the twenty-three
  workflow files that `lint.py` never covered: a lexer that reads them as JavaScript, plus
  a node grammar reading where an engine exists. It found two unparseable files —
  `sov-trust.js` and `sov-coldstart.js`, both documented launch paths — and both are
  repaired.
- **`scripts/sovkernel/authority.py`** measures three things about an observer it used to
  take on the observer's word, and records `independence_basis` so a declared reading is
  not filed as a measured one.
- **`scripts/sov_land.py`** reads the repository root at call time. It bound a copy at
  import, so a test pointing the root at a temporary repository moved the git operations
  there and left the accounting write in the real checkout.
- **`scripts/sov_context.py`** measures the orientation surface a participant traverses,
  with a pinned baseline so a compression pass is graded on the tree.

## Escalations

### E1 — Nine skills now cover the ground eight used to. Bdo's ruling. `acceptance/A25.json`

`.claude/skills/sov-lifecycle/` is one path through the loop, an instance of the portable
core `see-it-through` in the bdos repository, pinned by digest. It covers the same ground
as the eight `sdlc-*` skills, and those cannot be retired here:

- `SDLC.md`, Skill axes, declares all eight by name and states that an operator holds
  exactly one tier skill plus its domain skills. A tree without them contradicts it.
- `SDLC.md` is in the standing grant's `excluded_paths`.
- `charting/derive.py` derives its chart from those eight; removing them fails four
  charting tests, measured in a throwaway copy.
- `.claude/workflows/sov-compression.js` routes to `sdlc-feedback`.

So the directory holds more duplication than before, not less, and that is the cost of
presenting a replacement rather than assuming one. **The question is whether one instance
plus domain competences replaces one tier skill plus domain skills.** If yes, retiring the
eight is one concern that also repairs `charting/derive.py` and `sov-compression.js`.

### E2 — Five paths outside the standing grant ride this branch

`STATUS.yaml`, `ROADMAP.md`, `acceptance/A25.json`, `.clarity/coverage.json`,
`reports/context/baseline.json`. `STATUS.yaml` carries the A25 queue entry; `ROADMAP.md` a
skills count `sov_counts.py` refused; the rest are records this work produced. None can
land under `grant:standing-landing-loop`. `CLAUDE.md` is no longer among them: `main`
deleted the hardcoded counts this branch was correcting, which removes the drift rather
than resetting it, and both corrections are withdrawn.

### E3 — 156 rows of the operational landing ledger were destroyed during this work

Not by the defect. By the repair. The first form of
`scripts/tests/test_landing_ledger_isolation.py` computed the ledger path from the
effective root and wrote a row to it; under the defect it was written to detect, that path
is the operational ledger, and its first defeating run truncated the file. A test written
to catch writes to that ledger performed one.

`.local/landing/ledger.quarantined.ndjson` records the loss, how it happened, and that
every row carried `grant:test` or no grant and no observation — so nothing operational was
in them. That is read from a prior count and from rows examined before the loss, and
cannot now be re-derived from the file. The ledger is gitignored with no committed history
and the rows are **not recoverable**. The test now asserts the path and writes nothing.

**Open beyond this concern:** whether verification should reach `.local/landing/` at all.
The root binding is repaired and the suite is asserted to leave the ledger byte-identical,
but a verification run that can address operational accounting at all is a broader
question than one stale binding. That belongs to the verification boundary.

### E4 — PR #233 is a different session's concern

`claude/machine-readable-export-2dmlax`, head `99b7942`, session
`session_011oiMEBGnq7pV91MnputTcR`. None of this work is on it and none should be. Its
`CANDIDATE_HISTORY_NONLINEAR` refusal over merge commit `a4ec194` belongs to that branch;
this one has zero merge commits.

It did surface a real collision: both branches declared `scripts/sovharness/` for
different purposes. Neither is on `main`; that PR is open and based on current `main`, so
this branch yielded and its package is `scripts/sovprompts/`, named for what it reads.

### E5 — The bdos half is a separate repository and unlanded

`bdf1992/bdos`, branch `claude/witness-context-discovery-runas1`. It adds the
`see-it-through` core and the `instantiates` edge with its gate — the rule that lets a
place bind a core without redefining it, and refuses a binding that drops the exit to an
independent judge. Seventeen cores pass every gate; eighty-three tests pass. It stands on
its own and does not wait on E1.

## Residuals

- **No independent observation yet for this candidate.** A witness runs in its own session
  (`session-858bac`) against `8183667`. Three earlier readings dissented and their findings
  are repaired here, but each shared this session's identifier and could not certify its
  own independence. The landing gate requires the observation; until it returns this
  candidate is `BUILT`, not `WITNESSED`.
- **The workflow reader is lexical plus a grammar pass.** A file whose tokens and grammar
  both hold and whose meaning is wrong passes. Stated in the module rather than implied,
  because the previous statement of a limit there was wrong.
- **`independence_basis` reports `MEASURED` only for what the request can show.** The real
  measurement — joining the observer against the session registry's path claims — is not
  done, because that store is per-machine and gitignored and a check reading it would pass
  wherever it is absent.
- **Nothing in this repository runs `python -m bdos instance`.** `sov-lifecycle` pins the
  core's digest and the drift reading happens where bdos is, or not at all.

## Next bounded operation

Read the observation when it lands under `reports/observations/`. Repair anything it
finds, inside this concern. Then `python scripts/sov_land.py` for the in-scope paths, and
present the five in E2 with A25 for Bdo.
