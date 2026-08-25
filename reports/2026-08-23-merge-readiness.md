# Fast-forward merge readiness, tested, 2026-08-23

Status: `TESTED IN AN ISOLATED WORKTREE · NOT APPLIED · NOTHING COMMITTED · NOTHING RATIFIED`

`reports/2026-08-23-harness-reconciliation.md` ends its fast-forward analysis with:
"No textual conflict is expected. That expectation has not been tested and should be,
rather than trusted." This report tests it.

The working tree at `c:` was not modified by this operation. All work happened in a
detached `git worktree` under this session's scratchpad, which has since been removed.

Third operation of the day; the others are `reports/2026-08-23-line-endings.md` and
`reports/2026-08-23-oracle-hardening.md`.

## Method

1. `git worktree add --detach <scratch>/merge-probe origin/main` — a clean checkout of
   `b36c50d`, eight commits ahead of local `main` at `b5819da`, no divergence.
2. `git diff > local-tracked.patch` from the live tree (604 lines across 13 tracked files)
   and `git apply --3way` it onto the probe. Three-way, so a hunk that cannot be placed
   surfaces as a conflict rather than as a silent rejection.
3. Copy all 71 untracked local files into the probe, recording any that already exist.
4. Normalize the probe tree to LF, which `.gitattributes` now requires.
5. Resolve the conflicts and run `python scripts/verify.py`.

## Result: the merged state is green

`python scripts/verify.py` in the probe, exit 0, after resolution:

| Check | Merged probe | Local tree for comparison |
| --- | --- | --- |
| repository hygiene | PASS, 150 text files, 21 Python modules | PASS, 138 text files |
| bootstrap and locked evidence | PASS, 127 checks | PASS, 126 checks |
| conformance oracle controls | `SUITE PASS cases=20 coverage_gaps=0` | same |
| oracle tests / Asset Service / repository tooling | 17 OK / 5 OK / 28 OK | same |
| total | 1.149s of the 3.0s budget | 1.026s |

The extra bootstrap check is upstream's `contracts/issue-metadata.schema.json` entering the
contract-validation loop. Nothing upstream broke anything local, and nothing local broke
anything upstream.

## Two of the four files conflict; two do not

The untested expectation was that all four overlapping files touch different sections.
That holds for two of them and fails for two:

| File | Local added | Upstream added | Three-way result |
| --- | --- | --- | --- |
| `AGENTS.md` | 12 lines | 6 lines | **clean** |
| `CONTRIBUTING.md` | 9 lines | 45 lines | **clean** |
| `CLASSIFICATION.md` | 11 lines | 40 lines | **CONFLICT** |
| `STATUS.yaml` | 8 lines | 7 lines | **CONFLICT** |

Both conflicts are additive collisions in one shared paragraph, not disagreements. Neither
side contradicts the other; each simply extended the same sentence or the same list. Both
resolve as unions.

### CLASSIFICATION.md

One closing paragraph. Upstream appended the operating-loop vocabulary to the list of new
proposed policy; local appended Console to the service split. Union:

```text
The concrete `Service`/`Component` normalization, the initial
Asset/Proofing/Console split, and the operating-loop role and stance vocabulary
are new proposed policy. Bdo's ratification is required before this file becomes
authoritative vocabulary.
```

### STATUS.yaml

The tail of `open_decisions`. Upstream registered `O13` as the SDLC ratification question;
local held `O13` reserved by comment for the harness question and registered `O14` for
Console. Union keeps both registered entries and replaces the now-false reservation
comment, because `O13` is no longer reserved — it is taken:

```yaml
  - id: O13
    question: Does Bdo ratify SDLC.md's tiers, stance dyads, concern-registry derivation, and Red-gated release requirement?
    blocks: sdlc_loop_activation
  - id: O14
    question: Is Console Service the accepted third service boundary under that name, and does Bdo authorize a provisional Human Binding target for it ahead of O10?
    blocks: console_implementation
  # The federation-harness ratification question (decisions/0013-federation-harness.md,
  # reports/2026-08-22-christening.md item 1) has no id: O13 was taken by the SDLC loop
  # on origin/main while it was reserved locally. It is registered only when Bdo rules.
```

This resolution deliberately does not assign the harness question a number. That is the
renumbering ruling the reconciliation report queues as its item 5, and it is Bdo's.

## A sequencing constraint the earlier analysis does not carry

`origin/main` has no `.gitattributes`. With `core.autocrlf=true` on this host, the probe
checked out **CRLF**, and the byte-reading `scripts/lint.py` from the local line-endings
operation fails hard on it. The probe needed **92 files** normalized before hygiene passed.

So the two halves of that operation cannot be separated across commits:

- `.gitattributes` and the LF normalization of the tree must land in the **same commit**;
- anyone who already holds a checkout must renormalize after pulling it, because
  `.gitattributes` changes future checkouts and not files already on disk.

Committing the hardened lint without `.gitattributes` and the normalization would turn
every Windows checkout red on the first `verify.py`. This is the one ordering error in the
sequence that would actually hurt.

## `.claude/README.md` is the only file that exists on both sides

Of 71 untracked local files, exactly one already exists upstream. The two describe
different things:

- upstream's is the **SDLC loop binding**: `sdlc-` prefixed tier and domain skills, no
  executable orchestration.
- local's is the **federation harness**: `sov-` prefixed domain skills, four role agents,
  twelve executable `.js` workflows.

Merged, `.claude/skills/` holds eight `sdlc-*` and nine `sov-*` skills with **no name
collisions**. The families coexist mechanically. Only the single README has to describe
both, which supports the reconciliation report's reading that these are a loop and a
binding rather than two competing harnesses.

One substantive tension that reading does not dissolve: upstream's README states that
"executable orchestration scripts are not admitted before their logical specification and
defeating fixtures exist," and the local harness ships twelve of them. Either the local
workflows are outside that rule because they orchestrate harness agents rather than kernel
operations, or they are inside it and are currently inadmissible. That is a judgement, not
a merge mechanic.

## Residuals

1. Not witnessed. This is a build-side probe of a merge that has not happened.
2. The probe applied the local diff onto upstream. A real fast-forward runs the other way:
   commit local work first, then fast-forward, then re-apply nothing. The resulting tree is
   the same content, but the commit graph and attribution differ, and only the content was
   tested here.
3. The probe copied untracked files with the filesystem, not with git. File modes and any
   `.gitignore` interaction at commit time are untested.
4. The `.claude/README.md` collision was recorded, not resolved. The probe kept upstream's
   copy, so the merged tree it verified describes only the `sdlc-` family. A merged README
   naming both still has to be written, and its content depends on judgement item 1 of the
   reconciliation report.
5. Upstream is a moving target. `b36c50d` was current when this ran; four pull requests are
   open (#36, #38, #43 draft, #44). A later upstream changes nothing about the conflicts
   found here but may add new ones.

## Judgement queue for Bdo (nothing decided)

1. [governance] Accept the two union resolutions above as written, or rule differently on
   either? They are the smallest resolutions that lose no statement from either side.
2. [governance, verification] Confirm the sequencing constraint: `.gitattributes` plus the
   whole-tree LF normalization in one commit, ahead of or together with the hardened
   `scripts/lint.py`. Splitting them turns every Windows checkout red.
3. [governance, harness] The reconciliation report's five items stand unanswered, and its
   item 5 (renumber `0013-federation-harness` to `0017`) should be ruled **before** the
   fast-forward so no commit ever holds two `0013` records. This probe did not renumber.
4. [harness] Are twelve executable `.claude/workflows/*.js` admissible under upstream's
   stated rule that executable orchestration is not admitted before a logical specification
   and defeating fixtures exist?
