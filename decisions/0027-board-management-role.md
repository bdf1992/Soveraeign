# 0027 · Board management role and the GitHub write crossing

Status: `PROPOSED · OWNER RATIFICATION PENDING`

Numbering note: `0022` through `0026` are reserved by records that exist on
`feat/federation-harness-and-hardening` and are not yet on `main`.

## Problem

Decision 0016 made the coordination surface machine-checkable and deliberately
stopped there: it captures, it judges, and it writes nothing. Two days on, the
consequence is visible. The `board drift` job reports into a CI step summary
that nobody opens; the drift it reports has grown rather than cleared; and it
counts closed issues, so the report can never come back clean even in principle.

The deeper defect is not the missing write path. It is that every finding
arrives as a question. A drift report says eight issues are mislabelled and
stops, which leaves the owner to re-derive the projection, decide each case, and
issue the commands. That is the expensive half of the work, handed over while
the cheap half is kept. Bdo named it directly on 2026-08-23: too much must be
decided by him without a surface that carries the evidence and a recommended
action.

## Decision

Add a board management role: one loop that surveys, recommends with evidence
attached, and executes only what was approved.

**Recommendation, not a question.** `scripts/sov_board.py review` captures the
board through the existing read registrar and judges it offline into a batch of
typed actions. Each action carries what was observed, the declared rule that
turns the observation into a recommendation, the recommended move, and a stable
id. The surface it prints is the interface: approving is choosing ids, not
reconstructing the survey.

**Two dispositions, and the difference is enforced.** An action is `PROPOSE`
only if it is mechanically derived from a declared contract and reversible:
`LABEL_ADD`, `LABEL_REMOVE`, `LABEL_CREATE`, `BRANCH_DELETE`. Everything else
is `REPORT`: `CONTRACT_DEFECT`, `CONTRACT_BEHIND`, `LABEL_UNMAPPED`,
`CATALOGUE_UNDECLARED`, `PR_STALE`. A report appears on the same surface, is
rendered `OBSERVE_ONLY`, and is refused by name if an approval names it. Repairing a metadata block needs authorship and closing
a pull request needs judgement; a batch approval is the wrong instrument for
either, and silently dropping such an approval would let a reviewer believe
something happened.

**One write crossing, admitting four verbs.** `adapters/github/apply.py` is the
only module permitted to write to GitHub, as `export.py` is the only one
permitted to read. It admits exactly the four proposable kinds and refuses any
other by name rather than falling through to a generic API call. It is
deliberately self-contained and does not import its sibling: the module holding
write authority should be readable in one file. `sov_board apply` holds no
GitHub knowledge at all and invokes the crossing as a separate process.

**Approval is per action and is not a grant.** The crossing refuses to run
without an approved action list, writes a receipt for every attempt including
refusals and failures, and never stops at the first failure. `--approve all`
approves each action in the batch individually; it establishes no standing
authority for the next batch.

**The catalogue is reconciled before the tickets are.** Nothing syncs
`.github/labels.yml` to GitHub, so a label can be declared, implied by the
projection, and still absent from the repository. The first live run found that
the hard way: `type: engagement` was declared, projected onto #57, and rejected
by the write because the repository had no such label. The survey now captures
the live catalogue and proposes `LABEL_CREATE` before any `LABEL_ADD` that needs
it. A governed label the repository has and the catalogue omits is reported, not
deleted; deleting a label in use is a judgement.

**The judge stops counting the dead.** Closed issues are surveyed for nothing.
A closed ticket cannot drift, and including it produced the report that could
never clear.

**A checkout behind the board is the checkout's defect.** When ticket metadata
carries a value this checkout's projection does not map, the survey emits
`CONTRACT_BEHIND` and recommends extending the contract or merging the branch
that already did. It never recommends cutting the board down to fit.

## Effect class and the protected boundary

Every applied action is `EXTERNAL_WORLD`. `STATUS.yaml` lists
`no_external_effects_in_phase_i` as a protected boundary, and this capability
stands in tension with it as that line is currently written.

Bdo granted the narrower form on 2026-08-23: write, with a confirm on each
batch. This record proposes the boundary be restated to match the grant rather
than left in silent contradiction with it:

> `no_unapproved_external_effects_in_phase_i` — an external-world effect
> requires one owner approval per action at the moment of the effect. No
> standing grant, schedule, or unattended run may supply it.

That restatement is Bdo's to make. Until he makes it, the capability exists,
refuses without approval, and is exercised only when he approves a specific
batch. The seam is recorded under `OPEN-SEAMS.md` S9.

## Consequences

- The board becomes maintainable in one pass instead of accumulating. The first
  live run applied 33 of 34 approved actions: 22 missing labels across seven
  issues and 11 merged branches whose refs still existed. It also reported three
  pull requests quiet for over twelve hours and two issues invisible to the work
  queue for want of a valid metadata block.
- A scheduled or unattended board run is refused by construction, not by policy.
  The crossing has no approval to supply itself, and this record does not grant
  one.
- The role never closes an issue or a pull request. Both are judgements, both
  are how the board records that something ended, and neither is reversible in
  the way a label is.
- `PR_STALE` uses a twelve-hour default because this repository lands a feature
  in an afternoon. It is a reversible default that changes only what is
  reported; `review --stale-hours` moves it without an edit.
- The registrar's declared input projection widens: pull requests now carry
  `isDraft` and `updatedAt`, and branch names and the repository label catalogue
  are captured. All are read-only additions to an existing crossing and are
  recorded in `adapters/github/README.md`.
- The read path stays the read path. `sov_ticket.py` is unchanged, the
  `board drift` CI job is unchanged, and neither gains a write.

## Evidence

- `conformance/fixtures/board/survey-cases.json`: 17 cases, 9 positive and 8
  defeating, run offline by `python scripts/sov_board.py selfcheck` and wired
  into `scripts/verify.py`.
- `scripts/tests/test_sov_board.py`: 31 unit tests over action dispositions,
  approval refusals, the exact commands the crossing builds, and the inputs it
  refuses.
- Standing is `BUILT_SELF_TESTED_NOT_WITNESSED`. No independent witness has run,
  and self-tests establish `BUILT` evidence only.

## Source and authority

- `AGENTS.md` authority, self-direction is not delegation, change protocol,
  directory boundaries, and the effect-class vocabulary
- `decisions/0016-github-coordination-registrar.md` the read registrar, the
  labels-as-projection rule, and the deliberate absence of a write path
- `CONTRIBUTING.md` the issue coordination contract
- `STATUS.yaml` protected boundary `no_external_effects_in_phase_i`
- `OPEN-SEAMS.md` S9, external effects
- Bdo's 2026-08-23 grant: write, with a confirm on each batch; and his
  correction that a decision handed over without evidence and a recommended
  action is the defect being fixed
