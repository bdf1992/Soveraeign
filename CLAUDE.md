# Claude Code Host Binding

@AGENTS.md
@SOV.md

Operate as Sov when working in this repository. The imported files own Sov's
semantics, authority boundaries, governing context, and completion protocol.

Claude Code is one host binding, not Sov's semantic owner. Host capabilities do
not imply authority. Use only the model, tools, permissions, and live grants
visible in the current invocation; never infer them from this file or silently
substitute another model.

## Known traps

Facts about this repository that answer confidently and wrongly. Each cost a
session a false claim or a wasted hour. `python scripts/sov_traps.py` asserts
the checkable ones and **fails when a trap stops being true** — a failure there
means the hazard is gone and the entry below must be deleted, so this list
cannot outlive what it warns about.

- **T1 · `lineage/` is not in the tree.** Every traceability claim in `SPEC.md`
  and `CLASSIFICATION.md` grounds in it. `verify_bootstrap.py` reports the
  missing evidence as `SKIP`, and `verify.py` records that skip as `PASS`.
- **T2 · `verify.py` exit 0 does not mean conformance.** The participant's
  recorded baseline registers failing requirements as expected, so the suite is
  green while all nine Phase-I requirements fail. Green here means "unchanged",
  not "correct".
- **T3 · `NOT_WITNESSED` contains the token `WITNESSED`.** Any standing check
  written with a substring match reports every unwitnessed subject in the
  repository as witnessed. Compare whole tokens and treat a preceding `NOT` as
  denial; `scripts/sov_standing.py` is the worked example.
- **T4 · `gh api .../branches/main/protection` returns `404` while a ruleset is
  active.** Protection on `main` comes from ruleset `Gate`, not classic branch
  protection. Query `.../rulesets`. The 404 has already produced a false claim
  in a governed document.
- **T5 · A skipped required check satisfies the ruleset.** Skipped is not
  blocked. A job gated off by a repository variable still reports as satisfying
  the check that requires it.
- **T6 · Several sessions write this tree at once.** Files appear and change
  mid-read. Freeze a commit before witnessing, measuring, or ratifying, and
  work in a worktree rather than racing the shared branch.

T4 through T6 need network or live observation, which Phase I refuses, so they
are recorded rather than asserted. Silence about them is not confirmation.

