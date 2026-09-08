# concern:harness/witness-context — where it stands

Continued from the handoff at `5cee66c` on `claude/witness-context-discovery-runas1`.

Candidate `3c9b298` on `claude/witness-context-handoff-n8lk0h`, tree `b7212a8`, base
`d00f46a`, one commit, linear, no merge commits, forty paths, every one inside
`grant:standing-landing-loop`. `verify` PASS, `lint` PASS, `clarity` PASS at the commit.
Standing is `BUILT`. Eight readings have been commissioned; seven have returned and every
one dissented, so nothing has landed.

## The first decision, and its reason

The handoff asked whether the observation from witness session `session-858bac`,
commissioned against `8183667`, is evidence for `5cee66c`. **No such observation exists.**
Searched: the working tree, `.local/`, `python scripts/sov_session.py brief`, the
account's session list, and all twenty-six remote refs with `git grep` for `8183667`,
`32935b8` and `858bac`. One file matches and it is the handoff's own prose describing the
witness it commissioned.

The reasoning matters more than the outcome. **Even had it existed it could not have been
evidence for anything landing here.** `scripts/sovland/candidates.py` binds an observation
to its subject by `candidate_commit` and `candidate_tree`, and `scripts/sov_candidate.py`
refuses a mismatch with `EVIDENCE_SUBJECT_MISMATCH`.

That overturns the ordering the handoff proposed. It said to split the branch only after
the witness, because replaying first creates a candidate nobody observed. But the split
changes the tree, so witnessing before it produces evidence the gate refuses — the same
failure by the other road. The candidate must exist before it can be observed: split,
freeze, witness, land.

## What the split found

The handoff named five paths outside the grant. Measured with `scripts/sovkernel/scope.py`
there are six: `reports/` is in none of the grant's ten admitted prefixes, so the handoff
report describing the split was itself outside the grant it described.

Replaying then failed `verify` four ways, three of them one defect: **the grant admits
prose whose receipts and counts live outside it.** Adding a skill moves a count in
`ROADMAP.md`; regenerating a diagram re-pins `STATUS.yaml`; adding an entrypoint moves a
count in `scripts/README.md`, which is clarity-covered, whose receipt is `.clarity/coverage.json`,
which the grant excludes. That generalises: 142 clarity-covered artifacts, **109 of them
inside the grant's scope**, receipt file outside it. Drafted as `decisions/0104`.

## What seven readings did

The concern's own repair — the witness frame — was straightforward. The **guard** was not.
Seven independent readings defeated it twenty-nine times, and each found the same failure
one layer further out:

| reading | where the defect had moved |
| --- | --- |
| 1–3 | prose matching, then the binding resolver |
| 4–5 | the enumerator, then the classifier |
| 6 | the classifier again, where its own rule had not been applied |
| 7 | the refusals themselves, which lived in docstrings |

The seventh is the one that changed the shape. It used no part of this package as its
oracle — it rendered prompts by executing all twenty-three workflows in node with a
recording `agent()` stub — and named the cause: eight partial JavaScript scanners with six
different rule sets, and refusals that were sentences. One defect reproduced across three
candidates *after being named*, because nothing executable refused it.

Both are repaired. `scripts/sovprompts/scan.py` is one mask for the package, consumed by
every reader. `scripts/tests/fixtures/witness-context-defeats.json` carries all twenty-nine
constructions and `test_witness_context_defeats.py` runs them in both directions: the live
tree must produce no violation, every case must produce at least one.

## Withdrawn rather than landed

Each preserved unedited on `claude/witness-context-discovery-runas1`:

- `.claude/skills/sov-lifecycle/` and the three agent sentences naming it — the subject of
  the judgement `acceptance/A25.json` puts to Bdo. A `VERIFICATION` grant should not land
  a change whose purpose is to be ruled on.
- `scripts/sov_workflows.py`, `sov_context.py`, `sov_ledger_quarantine.py` with their
  packages and tests — each adds a `sov_*.py` entrypoint, moving a clarity-covered count.
- The four role agents and `scripts/README.md` — clarity-covered.
- `STATUS.yaml`, `ROADMAP.md`, `.clarity/coverage.json`, `reports/context/baseline.json`,
  and the handoff report.

## Residuals

- **Independence proved consumable.** Two observers retired themselves — one after repairs
  were made on prescriptions it wrote, one after it prescribed against the concern.
  Neither was asked to. The repository's model treats independent observation as
  renewable; this concern spent two of them, and a long concern needs a rotation rather
  than a witness.
- **Presence is graded, meaning is not.** A label followed by a correction inverting it
  passes. The sixth reading judged the repair — making the frame the only way to build a
  witness prompt — not owed by this concern; the seventh disagreed. Unsettled, and the
  disagreement is on the record rather than resolved by whoever wrote last.
- **This report's own class of change is the thing `decisions/0104` names.** Queuing A25
  in `STATUS.yaml` staled sixty-three clarity readers on a basis that is the whole file.
  They were re-stamped on one class judgement — a seven-line append to one list changes
  what no covered document must satisfy — which is honest but is the second time this
  concern has met the same erosion. Scoping a clarity basis below whole-file belongs to
  the contracts boundary.
- The observation records carry six top-level keys the landing gate reads and no
  observation schema admits. Nothing grades `reports/observations/` against a schema.
- `.local/landing/` does not exist in this container, so the quarantine record of the 156
  rows lost during an earlier repair is unreachable and cannot be re-derived.

## Terminal

Not landed. **Held at an `ACCEPTANCE_SEAM`**, one independent observation short: the
eighth reading is commissioned against `3c9b298` and has not returned. `acceptance/A25.json`
and `decisions/0104` are presented to `seat:root` for the two things this session cannot
settle — the shape of the skill tree, and a grant whose scope cannot express the change it
admits.
