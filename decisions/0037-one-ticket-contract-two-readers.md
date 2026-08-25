# 0037 · One ticket contract, two readers, one parity check

Status: `OWNER-ACCEPTED 2026-08-23 · BUILT AND SELF-TESTED · NOT WITNESSED`

Bdo accepted this record on 2026-08-23 over the evidence below
(`decisions/0023-acceptance-not-approval.md`: acceptance follows inspectable
evidence and is not permission to begin). Acceptance settles the ruling. It does
not make the changed readers `WITNESSED`: the checks that support this record are
the builder's own, and `AGENTS.md` holds that a build cannot witness itself. An
independent pass over `scripts/sovticket/yamlblock.py`,
`scripts/sovepic/metadata.py`, and the eight issue-body cases is still owed.

## Context

`soveraeign-ticket/v1` is read by two independent parsers:

- `scripts/sovticket/yamlblock.py`, serving the ticket contract commands
  (`validate`, `labels`, `queue`, `selfcheck`);
- `scripts/sovepic/metadata.py`, serving the epic walk (`sov_epic`, `sovepic/walk.py`).

`decisions/0022` extended the admitted YAML subset to block sequences of flat mappings
so a story could carry `asks`. Only the epic reader was extended; its own Residuals
section names the file it changed. The ticket reader was left as it was.

The consequence reached the live board. Issue `#67`, the first story, walks correctly in
the epic tree and fails `python scripts/sov_ticket.py validate` with
`line 19: nested key outside a nested mapping`. The schema declared a shape one reader
could not parse, and 28 metadata fixtures all passed, because every one of them feeds an
already-parsed instance to the validator and none crosses a parser.

Comparing the readers against the same corpus then found the divergence running the other
way as well. The epic reader silently admitted four shapes the ticket reader refuses. One
of them loses data: a repeated key inside a sequence item overwrites the first, so

```yaml
asks:
  - of: "#11"
    of: "#30"
```

read as a single ask `{"of": "#30"}`. The first ask disappeared with no error.

## Decision

Three changes, none of which widens what a ticket may say.

**1 · The ticket reader gains the construct the schema already declared.**
`yamlblock.parse_block` admits a block sequence whose items are one-level mappings, which
is what `contracts/issue-metadata.schema.json` has always required of `asks`. The schema
is unchanged. A sequence carries one item shape throughout: mixing a mapping item and a
scalar item in one sequence is refused, because it would let a routable ask and an
unroutable sentence be read as the same kind of thing.

**2 · The epic reader stops admitting what the contract refuses.** Four tightenings:

| Shape | Was | Now |
| --- | --- | --- |
| A repeated key inside one sequence item | last value silently won | refused, `duplicate key` |
| A key indented deeper than the sequence item | folded into the item above it | refused as outside the subset |
| A sequence mixing scalar and mapping items | both admitted into one list | refused |
| An issue body that leads with prose | a later fenced block was read as the ticket's | refused |

The last one matters beyond tidiness: `extract_block` searched the whole body, so a yaml
code sample anywhere in an issue could be read as that issue's own declaration.

**3 · Reader parity becomes a standing check rather than a coincidence.**
`conformance/fixtures/tickets/body-cases.json` holds eight cases that begin as bytes a
person could paste into GitHub and end as either declared metadata or a named refusal.
`scripts/sov_ticket.py selfcheck` runs them, so they sit inside `scripts/verify.py` and
the `ticket-contract` CI workflow. `scripts/tests/test_ticket_readers.py` asserts both
readers agree on every case: identical output on a positive case, a refusal from each on
a defeating one. Refusal wording may differ; admitting the body may not.

## Why not one reader

One reader is the better end state and this decision does not reach it. The two modules
have different callers, different error types, and different scalar typing —
`sovepic.metadata` coerces `123` and `true` to `int` and `bool`, `sovticket.yamlblock`
keeps every scalar a string. No live ticket carries such a value, so the readers agree
today, but that is luck rather than design.

Merging them is a refactor with its own risk, and this session found the defect while
doing something else. The parity check is the smaller move that makes the divergence
fail in the repository instead of on the board, and it is the precondition for merging
them later with evidence that nothing changed.

## Consequences

- `#67` validates. `python scripts/sov_ticket.py validate` now fails on `#51` and `#52`
  only, both free-form issues predating the contract.
- `python scripts/sov_ticket.py labels` reports zero drift across 49 typed tickets, after
  the declared label projection was applied to eight issues at Bdo's direction.
- `scripts/verify.py` renames the check to `ticket contract corpora` and declares the new
  corpus among what it observes.
- `scripts/tests/test_sov_ticket.py` split: the reader tests and the parity cases moved to
  `scripts/tests/test_ticket_readers.py`, keeping both modules inside the 300-line limit.
- Verification: 282 tooling tests, 54 ticket fixture cases (18 transition, 28 metadata,
  8 issue-body), `python scripts/verify.py` PASS in 2.299 s against the 3 s budget,
  `python scripts/lint.py` PASS.

## What would defeat this ruling

- A ticket body that both readers admit and read differently. The parity check covers the
  declared corpus, not every possible body.
- A live ticket needing a construct outside the admitted subset, which would mean the
  subset is under-declared rather than the readers wrong.
- Evidence that the prose-first refusal breaks an issue the epic tree depends on. Only
  `#51` (closed) and `#52` (open, untyped) lead with prose today.

## Residuals

- The two readers still disagree on scalar typing. No live ticket exposes it; nothing
  guards it.
- `#52` remains open with no metadata block. Its text says it is blocked by `#47`, which
  under `AGENTS.md` is a dependency edge rather than a block, so it wants a
  `requires: ["#47"]` and a ticket kind. Not written here: choosing its kind is backlog
  judgement, not a parser defect.
- The parity check reads the checked-in corpus, not the live board. A body that reaches
  GitHub without passing through a fixture is still unguarded until `validate` runs.
