# Line-ending enforcement, 2026-08-23

Status: `BUILT · SELF-TESTED · NOT WITNESSED · NOTHING RATIFIED`

Verification-domain operation closing judgement-queue item 8 of
`reports/2026-08-22-console.md` (residual 4 there; christening item 6). One session
held the controller role and did the work itself; no independent witness has run.
Everything below is a build report, never Bdo's judgement and never a witness.

## Change protocol record

1. **Requested outcome and current state.** `AGENTS.md` requires UTF-8, LF endings,
   and a final newline for repository text. `scripts/lint.py` claimed to enforce the
   CRLF half of that rule and did not: it read files with `Path.read_text`, whose
   universal-newline translation rewrites CR and CRLF to LF before the rule ever
   sees them. The rule was unreachable on every platform, not just Windows.
2. **Affected.** `scripts/lint.py`, `scripts/verify.py`, `scripts/verify_bootstrap.py`,
   new `.gitattributes`, new `scripts/tests/test_lint.py`, `CONTRIBUTING.md`,
   `.claude/skills/sov-verification/SKILL.md`, and the on-disk bytes of 73 tracked
   text files. No contract, schema, fixture, or service state.
3. **Preconditions and expected observable result.** Before: index already LF for all
   79 tracked files (`git ls-files --eol` reported `i/lf w/crlf`); working tree CRLF
   purely from a global `core.autocrlf=true`. Expected after: `i/lf w/lf` for all 79,
   lint failing on any CR byte, `python scripts/verify.py` still green inside budget.
4. **Effect class.** `RECORD_LOCAL`.
5. **Rollback.** Delete `.gitattributes`, revert the four scripts and two documents,
   `git checkout -- .` restores the working tree. No committed content changed: every
   normalized file hashes identically to its existing index blob.

## What changed

| Artifact | Change |
| --- | --- |
| `.gitattributes` (new) | `* text=auto eol=lf` pins LF checkout on every platform regardless of a contributor's `core.autocrlf`; `lineage/** -text` exempts evidence whose sha256 digests `scripts/verify_bootstrap.py` checks byte-for-byte |
| `scripts/lint.py` | reads `path.read_bytes()` and decodes explicitly, so the CRLF rule fires; undecodable bytes are now a named defect instead of a traceback; `.gitattributes` added to `TEXT_NAMES` |
| `scripts/tests/test_lint.py` (new) | 7 cases, five of them defeating; drives the real `main()` reader over a throwaway tree |
| `scripts/verify_bootstrap.py` | `.gitattributes` added to `REQUIRED` and marker-checked for both rules (123 -> 126 checks) |
| `scripts/verify.py` | `scripts/tests` check relabelled `repository tooling tests`; it stopped being scheduled-run-only when `test_lint.py` landed there |
| working tree | 73 files normalized CRLF -> LF; index stat cache renormalized for the 70 that carried no pending edit, so `git status` shows the 9 real modifications again instead of 79 |
| `CONTRIBUTING.md`, `sov-verification` skill | state where the LF rule is now enforced and why lint must not go back to `read_text` |

## Defeating evidence

The bug lived in the reader, not the rule, so a test against `check_text` would have
passed before the fix. These drive `lint.main()` over real files. Run against the old
`read_text` reader, restored on purpose to check the cases bite:

- `test_crlf_file_is_a_defect` — FAIL (`0 != 1`): a CRLF file was reported clean.
- `test_lone_cr_file_is_a_defect` — FAIL (`0 != 1`): a lone-CR file was reported clean.
- `test_non_utf8_file_is_a_defect_not_a_traceback` — ERROR: `UnicodeDecodeError`
  escaped `main()` instead of being reported.

Against the fixed reader all seven pass. The fixed reader was restored immediately;
the old reader exists nowhere in the tree.

## Checks observed

- `python scripts/verify.py` exit 0: hygiene PASS (135 text files, 21 Python modules,
  1 named debt), bootstrap PASS 126 checks, oracle `SUITE PASS cases=20 coverage_gaps=0`,
  oracle tests 5 OK, Asset Service 5 OK, repository tooling tests 28 OK. 1.067s of the
  3.0s budget.
- `git ls-files --eol` reports `i/lf w/lf` for all 79 tracked files; no class remains.
- `git diff --name-only` lists exactly the 9 files that were already modified before
  this operation. `git diff --cached` is empty; nothing was staged or committed.
- Independent byte scan (`test_no_repository_text_file_carries_a_cr_byte`) finds zero
  CR bytes across the linted population, checked by counting bytes rather than by the
  lint rule it protects.

## Residuals

1. Not witnessed. A `sov-witness` pass over this operation is the next bounded step;
   this session wrote the fix and cannot witness it.
2. `.claude/` files are outside `TEXT_SUFFIXES` for `.js`, so the eight workflow
   scripts get no hygiene check at all. `.gitattributes` still normalizes their
   endings; lint does not read them.
3. `scripts/verify_bootstrap.py` still uses `read_text` for marker matching. Harmless
   for substring checks, but it is the same call the lint fix removed, so it will read
   as an inconsistency to the next person.
4. `lineage/` does not exist in this checkout, so the `-text` exemption is untested
   against a real `SOURCES.lock`. It is a guard placed ahead of the hazard, not an
   observed pass.
5. The renormalization touched the index stat cache for 70 tracked files. Content is
   provably unchanged (blob hashes match), but the operation did write the index.

## Judgement queue for Bdo (nothing decided)

1. [verification, governance] `.gitattributes` enforces a rule `AGENTS.md` already
   states, so this was treated as gap-closure rather than new policy and no
   `decisions/` record was drafted. If a repository-wide checkout rule counts as
   policy in its own right, it needs decision 0016 and this report is the input.
2. [verification] Should `.js` join `TEXT_SUFFIXES` so `.claude/` workflow scripts get
   hygiene checks (residual 2)? They are harness, not product, and lint's population
   currently draws the line at product text.
3. [verification] Item 8 of the console queue is answered as built, not as ratified.
   Confirm it can be struck once a witness runs.
