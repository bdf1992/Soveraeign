# 0029 · The lessons loop: an inbox that drains into evidence

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Depends on `0028-history-as-lineage.md` for the evidence addresses a lesson
cites.

## Decision

`LESSONS.md` at the repository root is an inbox of `Proposal` records
(`SPEC.md`, Information objects), not a rulebook. It exists so the project stops
relearning the same thing across sessions, and so that what was learned becomes
something the system can check rather than something a model must remember.

1. **An entry is a proposal.** It begins `RECORDED` and claims no authority.
   It names: the claim, evidence addresses drawn from `lineage/SOURCES.lock`,
   the intended landing, and its standing.
2. **Standing climbs the four values that do not collapse** (`SPEC.md`,
   Historical standing and current effectiveness): `RECORDED` when written,
   `ADMITTED` when a fixture or check passes for it, `RATIFIED` only by Bdo
   through a decision record, `EFFECTIVE` when it runs in `scripts/verify.py` or
   `scripts/lint.py`. A lesson awaiting Bdo is a PROD-I-6 pending-right record
   and blocks nothing.
3. **Capture trigger: memory consolidation** — when an interactive session merges
   or retires its memory files. Not host context compaction; wiring that is a
   later `update-config` operation.
4. **Drain trigger: seven entries standing `RECORDED`.** At seven, each entry is
   drained into its landing or dropped. The rule is *drain*, not *review*.
5. **Landing:** a defeating fixture when the claim is mechanically checkable, a
   decision draft when it is a judgement; also `lint`, `known-gap`, `seam`, or
   `drop`. The lesson declares which at write time.
6. **A lesson that restates a rule an owning document already holds is dropped**
   with a link to that owner, and stays listed as dropped so it is not
   relearned. This is what keeps the file from becoming a competing authority
   (`AGENTS.md`, Design System of Record).

The drain is the `Feedback Skill` already named in `SDLC.md`: standing review,
residual and seam capture, correction proposals routed into `OPEN-SEAMS.md`,
`decisions/`, and `STATUS.yaml`. This record gives that skill a queue to work
from.

## Change protocol record

1. **Requested outcome and current state.** Bdo, 2026-08-23: from the retroactive
   memory, make a Lessons file; whenever memory is consolidated, update lessons;
   when lessons pass a threshold, check them in — carrying evidence through the
   services and updating the evidence by what is evident and by ways to test it.
   Before: lessons lived only in an interactive session's memory directory, which
   launched agents never read, and in transcripts nobody re-opened.
2. **Affected contracts, fixtures, sources.** `LESSONS.md` (new). No schema
   change. Evidence addresses resolve against `lineage/SOURCES.lock` under 0028.
3. **Preconditions and expected observable result.** `lineage/` exists and is
   clean. Expected: a lesson can be traced from claim to evidence address to a
   named landing, and the file's length is bounded by the drain rather than
   growing without limit.
4. **Effect class.** `RECORD_LOCAL`.
5. **Rollback.** Delete `LESSONS.md`. Nothing depends on it; no standing derives
   from it.

## Evidence

`LESSONS.md` opens with five entries, four of them defects found in the very run
that built 0028 — which is the honest first test of whether the inbox earns its
place:

- L-0001 the orientation snapshot in `CLAUDE.md` drifted from the record inside
  one day (26 commits claimed, 65 actual);
- L-0002 six of twenty-five session sources are locked but never recorded, and
  they are the six largest;
- L-0003 `sanitize-v1` never appears on a manifest because `pii-v1` consumes host
  paths first;
- L-0004 one session transcript is recorded `EXACT`;
- L-0005 federation run `wf_a2d4eb5e-df2` ran verification and witness last and
  exhausted its budget at agent 20 of 25, so the five agents that died were
  exactly the ones whose job was to check the work.

Three land as fixtures, one as a lint check, two as decisions. Standing: five
`RECORDED`, threshold seven, so the loop is not yet at its first drain.

L-0005 is the entry that could not have come from git or GitHub. It is only
visible in the run record, which is the argument for treating sessions as
sources at all.

## Defaults taken

- Put the inbox at the repository root as `LESSONS.md` rather than under
  `decisions/`, so launched agents — which do not carry an interactive session's
  memory — can find it without being told where to look.
- Set the threshold at seven. It is a round number chosen to be small enough that
  a drain stays cheap and large enough that a drain is not constant. Change it by
  editing this record; nothing computes against it.
- Read "whenever memory is compacted" as memory consolidation rather than host
  context compaction. The latter is a host event needing a hook, and can be added
  without disturbing this loop.
- Made the default landing a defeating fixture when checkable and a decision when
  judgemental, with the lesson declaring which. Bdo did not settle this when
  asked; it is the most likely default to be countered.
- Kept the two records separate: a lesson governing launched agents belongs in the
  repository, a lesson about how Bdo and an interactive session work together
  stays in that session's memory. Merging them would put host-local material
  under version control.
- Did not add a check enforcing the drain threshold. An unenforced rule is weaker,
  but a `verify.py` check that fails on an eighth lesson would make capture
  costly at exactly the moment capture matters.

These defaults remain proposals. Work continues unless a governing constraint is
violated; Bdo may counter any of them in review.

## Gate names

`lessons.ratify_loop` — ratification of the capture trigger, threshold, and
landing rule as policy. Writing lessons, draining them into fixtures, and citing
them are all reachable without that ruling; only their standing as a governing
loop waits on it.
