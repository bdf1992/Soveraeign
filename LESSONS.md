# Lessons

An inbox, not a rulebook. Every entry here is a `Proposal` under `SPEC.md`
(Information objects): it begins `RECORDED` and claims no authority. Nothing in
this file governs anything. A lesson that should govern leaves this file for the
document that owns the rule; a lesson that restates a rule an owning document
already holds is dropped with a link to that owner (`AGENTS.md`, Design System
of Record: do not duplicate a rule as a competing authority).

Proposed standing: `decisions/0029-lessons-loop.md`.

## How an entry moves

`RECORDED` when written here. `ADMITTED` when a fixture or check passes for it.
`RATIFIED` only by Bdo, through a decision record. `EFFECTIVE` when it actually
runs in `scripts/verify.py` or `scripts/lint.py`. The four do not collapse
(`SPEC.md`, Historical standing and current effectiveness).

A lesson awaiting Bdo is a PROD-I-6 pending-right record. It blocks nothing.

## Capture and drain

- **Capture trigger:** memory consolidation — when an interactive session merges
  or retires its memory files. Not host context compaction; wiring that is a
  later `update-config` operation.
- **Drain trigger:** seven entries standing `RECORDED`. At seven, each is drained
  into its landing or dropped. The rule is *drain*, not *review*: a file that only
  grows becomes policy by accident.
- **Landing:** `fixture` when the claim is mechanically checkable, `decision` when
  it is a judgement. Also `lint`, `known-gap`, `seam`, `drop`. The lesson declares
  its landing when written.

Standing now: **6 `RECORDED`**, threshold 7.

## Entries

### L-0001 · The orientation snapshot drifted from the record inside one day

`CLAUDE.md`'s repository snapshot claimed 26 commits and 17 decision records.
The record at the time of writing held 65 commits, 18 PRs, 51 issues, and
decision records through 0027. A snapshot that is stale within a day is worse
than no snapshot: it is read as current by every launched agent, which does not
carry the interactive session's context.

- Evidence: `lineage/SOURCES.lock`, all 65 `git-commit:*` and 18 `github-pr:*`
  sources; `CLAUDE.md` "Repository snapshot (informational)".
- Landing: `lint` — a check comparing the snapshot's claimed counts against
  `git rev-list --count` and `decisions/`, failing when they diverge past a
  declared tolerance.
- Standing: `RECORDED`.

### L-0002 · Six of twenty-five sessions are locked but never recorded

`SOURCES.lock` carries 25 `session-file` sources; `lineage/recordings/` holds 19
session recordings. The six without a recording are the six largest transcripts
on the host — the ones holding the most abandoned paths and corrections, which is
exactly the material a session source exists to preserve. No size cap in
`services/asset/scripts/` explains the gap; the cause is not established.

- Evidence: `session-file:0e5f4b24-fe64-4e61-8f83-b0957e4e7eae`,
  `session-file:0fde28fd-48b2-4b45-aa42-ad6bfc72a631`,
  `session-file:146efe7e-d200-42f2-bc46-03163e48b76d`,
  `session-file:8fcfa24b-4ac0-42ac-9c91-62f4f9c950c5`,
  `session-file:99dc7434-460a-4a54-846c-cf775a777acd`,
  `session-file:a4d1c9a7-4f15-42ec-ae79-685452d4eeda`.
- Landing: `fixture` — ingestion reconciles locked sources against produced
  recordings and refuses silently to skip one; a declared skip carries a reason.
- Standing: `RECORDED`.

### L-0003 · Two omission definitions overlap, and only one gets the credit

`history_reader.py` declares `sanitize-v1` (absolute host paths, oversized tool
results, secret shapes) and `pii-v1` (owner email, host username). All 18 lossy
recordings carry `pii-v1` only. Reading the code, an omission is recorded when it
removes something, and `pii-v1` consumes the host username inside a path before
`sanitize-v1` sees it as a path. No content leaked. But a `Recording` that
declares which definitions *fired* is a weaker claim than one declaring which
were *applied*, and `SPEC.md` (`Reader`) asks for omissions deterministically
recoverable from the definition — which reads as configuration, not effect.

- Evidence: `services/asset/scripts/history_reader.py` (`definition_record`,
  the `if removed:` guard); all 18 lossy manifests in `lineage/recordings/`.
- Landing: `decision` — which of declaration-by-configuration or
  declaration-by-effect the `Recording` contract means, and which definition owns
  host paths when both match.
- Standing: `RECORDED`.

### L-0004 · One session transcript is recorded `EXACT`

`rec-6437c0f22043d43e` records a `session-file` source with `fidelity: EXACT` and
`omissions: []`. Under `SPEC.md` (`Reader`), `EXACT` asserts the reader declares
no omissions at all. For a Claude Code transcript that assertion should be rare
and should be justified, not reached by a transform finding nothing to strip.

- Evidence: `lineage/recordings/rec-6437c0f22043d43e.json`.
- Landing: `fixture` — a `session-file` source recorded `EXACT` is refused unless
  the recording carries a declared justification.
- Standing: `RECORDED`.

### L-0005 · Putting the checks last meant the budget took out exactly the checks

Federation run `wf_a2d4eb5e-df2` dispatched five domains sequentially in
implementation order, verification fourth and governance fifth. It exhausted the
host account's monthly spend at agent 20 of 25. The five agents that died were
the three verification builders, the witness, and a governance scoping agent —
that is, every agent whose job was to check the work, plus the operation that
would have surfaced the result for judgement. The build survived; its verification
did not. Ordering checks after construction is correct for dependency and wrong
for budget exhaustion, because a budget runs out at the end.

- Evidence: run `wf_a2d4eb5e-df2` (25 agents, 20 done, 5 failed, 1,792,065
  subagent tokens, 555 tool uses, 5,013s); its journal at
  `subagents/workflows/wf_a2d4eb5e-df2/journal.jsonl`;
  `.claude/drafts/history-lineage-and-lessons-brief.md` operations 1-5.
- Landing: `decision` — whether a federation run reserves budget for its witness
  before dispatching builders, or interleaves verification per domain rather than
  running it as a terminal phase.
- Standing: `RECORDED`.

### L-0006 · A GitHub source's digest covers its title, not its content

`history_sources.py` says plainly that "digests for git and GitHub sources cover
the captured representation recorded here; session digests cover raw bytes". For
a commit that is sound — the payload is `<sha>\t<subject>\n`, and the sha is
itself a content address, so the commit cannot change without the address
changing. For a pull request or issue it is not: the payload is number, title,
and state, so a body can be rewritten entirely and the digest will not move.
PROD-I-2 asks that "a source rereads byte-identical by digest"; 69 of the 159
locked sources currently satisfy a weaker claim than that.

- Evidence: `services/asset/scripts/history_sources.py` (`build_lock`,
  `enumerate_github`); the 51 `github-issue:*` and 18 `github-pr:*` entries in
  `lineage/SOURCES.lock`. Found by witness check W3, which reproduced all 65
  git-commit digests independently and could not do the same for GitHub bodies.
- Landing: `decision` — whether a GitHub source's digest must cover its body,
  which makes the lock depend on an `EXTERNAL_WORLD` read to verify, or whether
  the lock declares metadata-only fidelity for those kinds and says so in
  `lineage/README.md`.
- Standing: `RECORDED`.

## Dropped

None yet. A dropped entry stays listed here with its reason and the owning
document it duplicated, so the same lesson is not relearned and re-proposed.
