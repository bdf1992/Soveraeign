# 0061 · Concerns keep their source; execution artifacts do not

Status: `OWNER-DIRECTED`

## Decision

A concern is the durable unit of unfinished work. An issue is its coordination record, a
branch is temporary execution state, and a pull request proposes a durable result. None of
those execution artifacts becomes the semantic source of the concern merely by existing.

Every newly minted meaningful concern must be traceable upward before it justifies new
execution inventory. Prefer the canonical references the ticket already carries:

- `capability` resolves through `contracts/product-canon.json` to journeys, promises, and
  Product Ground;
- `evidence_pointer`, `walker_receipt`, `target_pr`, and `target_head` name the observation
  or exact target that caused or tested the concern;
- `governing_rule` and `authority` name a policy or authority source;
- parent, village, dependency, and held-ticket references connect concern records without
  redefining their meaning.

When none of those can name the source, the issue body may carry an exact `Source` address.
That address points to existing meaning; it does not mint another product taxonomy or a
GitHub-owned source registry.

This is prospective. Historical issues are not made defective solely because they predate
this rule. Do not create cleanup tickets merely to retrofit source metadata. Enrich old
concerns when they are touched for real work, or when doing so directly enables absorption
or closure.

## Settlement vocabulary

Five relations are enough for the current work graph:

- `derived_from` — the concern exists because the named source remains unrealized,
  unproven, unreconciled, or otherwise unsettled;
- `depends_on` — another concern or artifact is required before the next transition;
- `advances` — the landed result reduces the concern but does not settle it;
- `satisfies` — the landed result settles the concern represented by the issue;
- `supersedes` — a named successor concern or durable result now owns the remaining
  meaning.

`advances` is not terminal. A merged pull request that merely advances a concern leaves the
issue open with the next unsatisfied state visible. `satisfies` is terminal once the durable
result and required evidence exist. `supersedes` is terminal only when the successor is
explicit.

GitHub's `Closes #N` syntax is therefore reserved for `satisfies`. A merge by itself never
proves satisfaction.

## Branch and pull-request linking

Do not create a second branch registry. GitHub already records the pull request head ref and
commit graph. The pull request names the concern it carries and whether it advances,
satisfies, or supersedes it; that is enough to derive concern → PR → branch → commits while
the branch exists.

After settlement, the branch is execution residue. Decision 0060 retires an exact merged
head when it is unchanged and no open pull request still depends on it.

## LANDED terminal

For the participant holding the branch, `LANDED` means more than merged and green. All of
the following must be true or explicitly accounted for:

1. the durable result exists on the intended base;
2. the PR records `advances`, `satisfies`, or `supersedes` for the concern it carried;
3. the concern's remaining standing is visible after merge;
4. open dependent PRs and shared branch uses are accounted for;
5. the remote merged head retires when the branch-retirement contract admits it;
6. local contained branch, worktree, and live claim/session state retire when the
   participant controls them;
7. a satisfied issue closes, a superseded issue names its successor before closing, and an
   advanced concern stays open.

Green CI, a merge commit, age, quiet, or behindness are not terminal states by themselves.

## Relationship to product identity and accounting

This decision applies the already accepted identity rule one level lower. Product Ground
and the canon own durable product meaning; GitHub coordinates work against those meanings.
`GROUND-014` requires meaningful expenditure to resolve upward to product intention and
product intention to resolve downward to what was spent realizing it. A concern linked to a
canonical capability can already use the existing attribution projection to reach journeys,
promises, and Ground without duplicating those identities in the ticket.

The work graph is therefore:

`source / product intention → concern → issue → PR → branch/commits → durable result → evidence / receipt`

The middle execution artifacts may disappear. The source, concern disposition, landed
result, and evidence remain recoverable.

## Defeating cases

Demote this decision if it requires a second registry that duplicates canonical product
meaning, if a branch or PR becomes the semantic source of a concern, if merging can close an
issue that was only advanced, if source attribution is treated as authority or proof of
satisfaction, or if adoption creates a new backlog whose only purpose is retrofitting old
metadata.

## Source and authority

Bdo, 2026-08-25 interactive session: connect issue/branch lifecycle to the product identity,
accounting, and recording work; settle the remaining source, relationship, and landing
policy before treating the rest as an experience/tooling problem.
