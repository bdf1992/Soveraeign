# concern:harness/witness-context — where it stands

Continued from the handoff at `5cee66c` on `claude/witness-context-discovery-runas1`.

Candidate `fa37fc7` on `claude/witness-context-handoff-n8lk0h`, tree read from that
commit, base `64fe985`, forty-one paths, every one inside `grant:standing-landing-loop`.
`verify` PASS and `lint` PASS measured at that commit in a clean worktree, not in the
working tree that built it. Fifteen readings have been commissioned.

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

## What fifteen readings did

The concern's own repair — the witness frame — was straightforward. The **guard** was not.
Fifteen independent readings defeated it seventy-one times, and each found the same failure one
layer further out:

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
| 12 | three prompt shapes the reader could not follow: a concatenated helper, a decoy `return`, and one `{` |
| 13 | the provenance reader, which matched `agent(` while the enumerator two modules away resolved aliases |
| 14 | the frame reader, which bound the first textual declaration and never asked which binding runs |
| 15 | the frame's own edges: text after the join, a shadowed binding, and a register asserting gates that did not exist |

The seventh changed the shape. It used no part of this package as its oracle — it rendered
prompts by executing all twenty-three workflows in node with a recording `agent()` stub —
and named the cause: eight partial JavaScript scanners with six different rule sets, and
refusals that were sentences. One defect reproduced across three candidates *after being
named*, because nothing executable refused it.

The twelfth and thirteenth are the ones worth reading, and they found the same thing twice
in different clothes: **the reader answered a structural question by matching text.**

- `prompt_of` stopped at the first `{`, so an object literal in a prompt hid everything
  after it. It reads the call's arguments now.
- `resolved_prompt` followed a helper only when the prompt was *exactly* a call or a name,
  and twenty-one of twenty-two repairs concatenate. It substitutes each piece in place now.
- `blocks` graded the first `return [`, so a decoy array carrying the correct frame was
  what every frame rule read.
- `derives_from_agent_result` matched the literal `agent(`, so `const spawn = agent`
  produced a dispatch the enumerator found and the provenance reader did not — two modules
  apart, because only one of them resolved aliases.
- The same binding map read a JSON Schema's `properties: { summary: ... }` keys as
  bindings, so three schema constants in `sov-asset.js` resolved to "derives from an agent
  result" on the *pristine* tree. That is the failure in the other direction, and it is the
  one this package holds itself to avoiding.
- A helper returning `[a, b].join(sep)` rendered as one opaque expression, so a
  frame-shaped decoy spliced where the frame belongs delivered text no rule read.

The last of those was only half closed by rendering it: the thirteenth reading left the
real frame in place as dead code and put `/* witnessFrame( */` ahead of the decoy, which
one grader read on raw source and the other on the mask. Both read the mask now, and the
rule changed from presence to identity: **a file that declares a frame must deliver it**,
with the frame's own rendering as the opening bytes of every witness dispatch in that file.
There is nowhere ahead of it to put anything.

The fourteenth found the identity rule was not enforced at all. `render._body` bound the
first textual `function witnessFrame(` and never asked which binding JavaScript resolves,
so a reassignment placed after the declaration — or a second declaration that hoisting
prefers — left the real frame in the file as dead code for every rule to grade while the
evaluator received another. The fifteenth then defeated the repair twice more: a
block-scoped `const { witnessFrame } = ...` shadow, which the binding count did not see;
and a countermand concatenated *after* `].join('\n\n')`, which was missing from the
delivered text and from the frame's rendering at once, so the two matched byte for byte
and the evaluator read it anyway. A frame now refuses a name bound more than once by any
route, and refuses to deliver anything outside a graded block.

The fifteenth also read the register the fourteenth's repair introduced, and found five of
its eight entries wrong — each a case nobody wrote, recorded as a gate that did not exist.
The register claimed the lexer refuses an unbalanced brace before any rule reads the
function; it does not, because the lexer masks strings while the frame reader scanned raw
source. That is now three separate repairs: the frame reader balances on the mask, the
register fails the build when it names a refusal the package no longer states, and the
three entries that survive say which gate beats them and why.

The same reading measured the resolver in the direction that convicts correct code and
found integer loop counters flagged as carrying an agent's output: `for (var i = 0; i <
plan.operations.length; i++)` returned its whole init clause as what is written into `i`,
so every name in the condition polluted it. A statement now ends at its own semicolon.

`scripts/tests/fixtures/witness-context-defeats.json` carries all seventy-one constructions
with contiguous ids. Which refusals are demonstrated is not prose: a case reads every
refusal message out of the package's own syntax tree, runs the corpus, and fails the build
on any refusal no case fires — and on any register entry naming a refusal that no longer
exists.

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
- **A guard is only ever as good as its last reading.** Fourteen readings produced
  fourteen dissents. Each repair was at the cause and each was pinned by a case, and the
  fourteenth still found the strong rule unenforced on the one file it was written for.
  The honest claim is not that this package cannot be defeated; it is that sixty-five
  named constructions cannot defeat it, that every refusal it states is now either fired
  by a case or recorded as unreachable with its reason, and that the corpus makes the next
  defeat cheap to add.
- **Presence is graded, meaning is not, and only identity escapes that.** Twenty-two of
  the twenty-three workflows are held to a demotion sentence plus the position of what
  they splice. Two independent readings showed what that cannot catch: a prompt may open
  on the demotion and then, in its own prose, tell the evaluator to take the builder's
  scope as given and not to pin a subject. No presence or position rule reaches it.
  Identity does — the frame's rendering compared against the bytes the dispatch delivers —
  and `sov-loop.js` is held to that. Extending it to the other twenty-two means each
  declaring its own frame, because a workflow is a standalone file with no way to import
  one, so the same forty lines of frame prose would be copied eighteen times. That is a
  `DEPENDENCY_SEAM`, not a rule: the workflow runtime exposes no shared-code mechanism.
  Named here rather than worked around, and it is the next bounded operation on this
  concern.
- **A splice-free witness prompt carries no demotion, and that is the rule rather than a
  hole.** Three shipped dispatches deliver no interpolation at all — one returns a
  command's stdout, one is a fresh-participant probe told not to read the scan outputs,
  one reconciles the issue tree against its contracts. A splice is the only channel an
  earlier agent's output has into a prompt, so a prompt with none has nothing to demote.
  What that argument does not cover is an account arriving by reference — a literal prompt
  naming a file the builder just wrote — which is the same meaning-not-presence limit and
  is not separately checked.

## Terminal

Not landed. **Held at an `ACCEPTANCE_SEAM`**, one independent observation short: the
eighth reading is commissioned against `3c9b298` and has not returned. `acceptance/A25.json`
and `decisions/0105` are presented to `seat:root` for the two things this session cannot
settle — the shape of the skill tree, and a grant whose scope cannot express the change it
admits.
