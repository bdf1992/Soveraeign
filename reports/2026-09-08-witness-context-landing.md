# concern:harness/witness-context — where it stands

Continued from the handoff at `5cee66c` on `claude/witness-context-discovery-runas1`.

Candidate `4653b62` on `claude/witness-context-handoff-n8lk0h`, tree `26f2f22`, base
`64fe985`, thirty-nine paths, every one inside `grant:standing-landing-loop`. `verify`
PASS and `lint` PASS measured at that commit in a clean worktree, not in the working tree
that built it. Twelve readings have been commissioned.

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
which the grant excludes. That generalises: 152 clarity-covered artifacts, **113 of them
inside the grant's scope**, receipt file outside it. Drafted as `decisions/0105`.

## What twelve readings did

The concern's own repair — the witness frame — was straightforward. The **guard** was not.
Twelve independent readings defeated it, and each found the same failure one layer further
out:

| reading | where the defect had moved |
| --- | --- |
| 1–3 | prose matching, then the binding resolver |
| 4–5 | the enumerator, then the classifier |
| 6 | the classifier again, where its own rule had not been applied |
| 7 | the refusals themselves, which lived in docstrings |
| 8 | the landing gate, which read the local `main` ref rather than the remote |
| 9 | the verification, which passed against a working tree and failed against the commit |
| 10 | the checker's own mutants: behaviours no corpus case pinned |
| 11 | the dispatch rule, which graded source text where the frame rule graded rendered text |
| 12 | three prompt shapes the reader still could not follow: a concatenated helper, a decoy `return`, and one `{` |

The seventh changed the shape. It used no part of this package as its oracle — it rendered
prompts by executing all twenty-three workflows in node with a recording `agent()` stub —
and named the cause: eight partial JavaScript scanners with six different rule sets, and
refusals that were sentences. One defect reproduced across three candidates *after being
named*, because nothing executable refused it.

The twelfth is the one worth reading. It constructed three dispatches that hand a witness
agent an earlier agent's output as its oracle, each carrying the corpus's own inverted
sentence in the text the evaluator receives, and every case passed on all three. All three
were the same mistake in three places: the reader answered a structural question by
scanning characters.

- `prompt_of` took the call text up to the first `{` at depth zero, assuming the first
  brace opens the options object. One object literal inside a prompt ended the graded text
  there. It now reads the call's arguments.
- `resolved_prompt` followed a helper only when the prompt was *exactly* a call or exactly
  a name. Twenty-one of the twenty-two repairs concatenate, so every helper body was one
  opaque expression. It now substitutes each resolvable piece in place.
- `blocks` graded the first `return [`, so a guarded decoy array carrying the correct frame
  was what every frame rule read. It now refuses a frame with more than one of its own
  returns.

The same reading found three more, all repaired: a frame declared as anything but
`function witnessFrame(` was graded by neither rule; the corpus's well-formedness test
asserted a floor of twenty-nine against fifty-five cases, so twenty-six could be deleted
silently; and `independence_basis` returned `MEASURED` for something that measures supply
and resolution rather than independence, which is now `observation_basis` returning
`SUPPLIED_AND_RESOLVED`.

`scripts/sovprompts/scan.py` is one mask for the package, consumed by every reader.
`scripts/tests/fixtures/witness-context-defeats.json` carries all fifty-five constructions
with contiguous ids, and `test_witness_context_defeats.py` runs them in both directions:
the live tree must produce no violation, and every case must produce the refusal it names.

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
- **This report's own class of change is the thing `decisions/0105` names.** Queuing A25
  in `STATUS.yaml` staled sixty-three clarity readers on a basis that is the whole file.
  They were re-stamped on one class judgement — a seven-line append to one list changes
  what no covered document must satisfy — which is honest but is the second time this
  concern has met the same erosion. Scoping a clarity basis below whole-file belongs to
  the contracts boundary.
- The observation records carry six top-level keys the landing gate reads and no
  observation schema admits. Nothing grades `reports/observations/` against a schema.
- `.local/landing/` does not exist in this container, so the quarantine record of the 156
  rows lost during an earlier repair is unreachable and cannot be re-derived.
- **The change to the landing gate was absorbed, not declared.** The twelfth reading found
  `scripts/sovkernel/authority.py`, `scripts/sov_land.py` and `scripts/sovland/` in the
  candidate and not in the account, and asked whether that crosses the boundary that mints
  a separate concern. It does not: same directory, same effect class, same authority, and
  the change is what this concern's own observations had to pass through. Not declaring it
  was the defect, and it is declared here and in the commit message.
- **A guard is only ever as good as its last reading.** Twelve readings produced twelve
  dissents. Each repair was at the cause and each was pinned by a case, and the twelfth
  still found three. The honest claim is not that this package cannot be defeated; it is
  that fifty-five named constructions cannot defeat it and that the corpus makes the next
  defeat cheap to add.

## Terminal

Not landed. **Held at an `ACCEPTANCE_SEAM`**, one independent observation short: the
eighth reading is commissioned against `3c9b298` and has not returned. `acceptance/A25.json`
and `decisions/0105` are presented to `seat:root` for the two things this session cannot
settle — the shape of the skill tree, and a grant whose scope cannot express the change it
admits.
