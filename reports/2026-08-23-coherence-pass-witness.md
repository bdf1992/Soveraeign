# Coherence pass witness, 2026-08-23

Status: `WITNESSED BY A SEPARATE AGENT · NOTHING RATIFIED`

Bdo supplied a zip of twenty edited governing, harness, and CI files
(`CLAUDE(20260823-171454).zip`, stamped 12:35). The interactive session diffed
it against the branch, adopted the reconciliations, held back three policy
questions, and committed `a518afd`. A `sov-witness` agent then observed that
commit in a detached worktree with a clean tree, through its own path. This
report holds the observation. Bdo's wording on who Claude is ("a sovereign user
of Soveraeign") was applied as ruled, not as a proposal.

## What was witnessed

| Check | Result |
| --- | --- |
| `git diff 50b802c a518afd --stat` | 20 files, +200/-129; exactly the claimed set, nothing outside it |
| `python scripts/verify.py` | exit 0, `PASS: repository checks completed in 1.536s`; 20 conformance cases, 0 coverage gaps |
| `python scripts/lint.py` | exit 0, 207 text files, 39 modules, 1 named debt |
| CRLF bytes in changed blobs | none |
| `CLASSIFICATION.md` names `OPEN → BUILT → WITNESSED → RATIFIED` beside record standing | reproduced |
| `SPEC.md` receipt text agrees with its own `report_run` row | reproduced |
| `PRD.md` PROD-I-6 agrees with `SPEC.md` and `conformance/run.py` `check_i6` | reproduced |
| `AI-NATIVE.md` template lists all nine Soveraeign checks | reproduced |
| `AI-NATIVE.md` in the `AGENTS.md` Design System of Record and `CODEOWNERS` | reproduced |
| `## Two-binding proof` heading unchanged; 20 cross-references resolve | reproduced |
| Held-back items (retraction=`FULL`, Red-lane inputs, CODEOWNERS-as-ratification) absent from the diff | reproduced |
| Workflow `name:` fields unchanged | reproduced |

Verdict: `OPEN -> BUILT` supported. `BUILT -> WITNESSED` supported for the
governing-document, CODEOWNERS, and workflow portions; for `CLAUDE.md` only
with residuals 1 and 2 below named as defects.

## Residuals the builder did not report

1. `CLAUDE.md` history sentence lost the word "proofing" and fused two lines.
   Fixed in the follow-up commit.
2. `CLAUDE.md` enumerated open decisions as O1-O13, O17, O18 while
   `STATUS.yaml` also holds O16 and O19. Replaced with a pointer to
   `STATUS.yaml`.
3. `O1-O12` survived in `sov-governance/SKILL.md`, `sov-governance.js`, and
   `sov-baseline.js`. Replaced with "the open decisions in `STATUS.yaml`".
4. `CLASSIFICATION.md` coined "evidence lifecycle" as a synonym for the
   section's own "artifact lifecycle". Collapsed to one term.
5. `diagrams/requirement-lifecycle.md:53` still says "two bindings" against the
   revised PRD Phase-I exit. Left alone pending judgement item 2.
6. The three held-back contradictions were in a commit message, not in
   `OPEN-SEAMS.md`. Recorded as S11, S12, S13.
7. `AI-NATIVE.md`'s claim to preserve `lineage/evidence/core/SUBSTRATE.md` T2 is
   unattestable in this checkout: `lineage/` is absent and `verify.py` skips the
   archive. Pre-existing; bears on judgement item 1.

## Judgement items for Bdo

1. Is `unreachable with no structural axis present → DECORATION`
   (`AI-NATIVE.md`) a gap-fill or a change to the minimum arithmetic that
   `decisions/0006` says must not change? It cannot be checked against
   SUBSTRATE.md T2 here.
2. The PRD Phase-I exit now names one human and two model bindings (three).
   Keeping "two" was the other harmonization. Is the stricter exit intended?
3. The orchestrator and controller now plan the smallest ungated precursor of
   a gated objective instead of returning an empty plan. `decisions/0018` is
   silent. Admissible without amending 0018?
4. S11, S12, S13 in `OPEN-SEAMS.md`: each is a direction only the owner picks.
5. `CLASSIFICATION.md` says "An operational record may be ratified under a
   matching live grant." Does "matching" carry that a judgement-typed record
   still needs Bdo (PROD-I-5, `SPEC.md` authority rule)?
6. From `scripts/sov_next.py --strict` (another session's work, uncommitted at
   the time): `STATUS.yaml` declares `F0_FOUNDING_CLOSURE` while reachable work
   sits at `F3` (#6 Shared Kernel). The script refuses to choose. Owner's call.

## Left unread

The witness did not read `CONTRACT.md`, decisions 0001-0015 and 0017, or the
founding scenarios beyond search, and could not read `lineage/`. The
interactive session did not inspect the other session's concurrent
uncommitted work (`scripts/sov_kernel.py`, `contracts/kernel-transitions.json`,
`ROADMAP.md` crosswalk) beyond running `sov_next.py`.
