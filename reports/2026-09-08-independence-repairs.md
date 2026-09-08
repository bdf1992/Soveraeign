# Independence: three witness passes and what they changed

Concern: define what "independent" means for an observer, then build it. Branch
`claude/agent-independence-definition-z4crlv`, owner-directed in session 2026-09-07.
`decisions/0104-independence-is-context-and-perspective.md` is the ruling; this report is the
builder's account of carrying it and settles nothing.

**This file was cited before it existed.** The script that should have written it aborted on
its first statement, and the retry re-ran only the other half. Three artifacts — a governing
decision record, `services/observation/CHARTER.md`, and the pass 1 witness record — cited it
for a day while it was in no commit on any branch. Pass 3 found that and could not grade pass
2's conditions, because the conditions were unreadable. It is the same defect the passes kept
finding in the code, made by the same participant one layer up: a citation nobody resolved.
No repository check resolves a cited path in prose; `verify.py`'s citation check reads journal
exports only. That is now a row in `services/observation/KNOWN-GAPS.md`.

The witness records: `witness/independence-context-perspective.md` (pass 1, quoted), and
passes 2 and 3 below. Pass 2's probes are at `witness/probes/probe_independence_walk.py`;
pass 3's at `witness/probes/probe_independence_declared.py`.

## Pass 1, commit `7be1323`

Dissented; supported no standing. It reached `INDEPENDENT` on five records the manifest
forbids, every one a datum the record did not carry answered "no" instead of "cannot say".
The deepest defeated Ruling 3 by rename: `_walk_perspective` refused on a missing profile and
`_walk_lifecycle` read the same absence as a clean "different". It also found the runtime gate
reading `outcome` alone, admitting an `INDEPENDENT`-over-`INCOMPLETE` inference whose
observation then asserted `COMPLETE`; and the relay refusal comparing ids where the walk
compared profiles.

Repaired at `f28e43b`, pinned by `WitnessFindingsOn7be1323`. One pre-existing defect (a
non-object lease reading "no holder") absorbed: same file, same effect class, same authority.

## Pass 2, commit `f28e43b`

Dissented; supported no standing. Its envelope was `UNATTESTABLE` for a contract-typed
`Finding`, because `contracts/finding.schema.json` requires a `record_projection_id` and none
has been exercised on a real run (`contracts/phases.json`, P15-X2). It said plainly the
standing answer was no either way.

- **D1** — `decisions/0104` claimed one module with one reading while `HOLDS_RUN_LEASE` and
  `PRODUCED_THE_OUTPUT` still compared raw ids. Neither actor need be the attempter, which is
  why those edges exist at all.
- **D2** — `context_passed` had no closed vocabulary, so a launcher truthfully declaring
  `transcript` in lower case was read as subject-side.
- **D3** — `admission.py` graded a verdict and never the record it described.
- **D4** — the pass 1 decoy repair made admission *decrease* as the record grew.
- **D5** — four surviving mutations, including a test that could not fail.
- **D6** — two more artifacts asserting the old standing.
- **D7** — the builder's own prose sat inside the pass 1 witness record.
- **D8** — no oracle weakened; the retired edge name in `oracle-controls.json` was cosmetic.

Repaired at `3c24420`, pinned by `WitnessFindingsOnF28e43b`. Residuals R1 and R2 routed as
`KNOWN-GAPS` rows rather than absorbed.

## Pass 3, commit `3c24420`

Dissented; supported no standing; `UNATTESTABLE` for the same Record reason, plus this file's
absence.

- **F1** — the decoy is back. `_corroborated` asks only that an actor of the run appear on the
  named subject, and the executor writes the name, so it is satisfied by any subject the
  executor has itself moved. The subject's own builder was admitted as its independent
  observer, with the candidate's arrow on the real subject sitting unread in the same record.
- **F2** — `_rederive_id` proved nothing. The id hashes three caller-supplied fields, so it is
  identical for every verdict the walk could reach about one subject; an honest `DIRECT` and a
  forged `INDEPENDENT` carry the same id. The executor drove its own run through the gate on a
  correctly hashed forgery, and the emitted `observer_relation` read `record read at ;` — a
  sentence with a hole where its evidence goes.
- **F3, the definitional one** — see below.
- **F4** — `_corroborated` had no test that held it: its own declared defeating case passed
  with the guard deleted, killed by the `UNKNOWN` arm instead. The oracle predicate added for
  pass 1's F7 has no fixture in either direction, so deleting it changes no result.
- **F5** — the checked-in probe contains its own defeater unconnected: two slices use a
  literally invalid id and print `refused`, and a third slice proves those refusals meaningless.
- **F6** — `decisions/0104` states two repairs as complete, two paragraphs after the sentence
  naming that exact defect.

### F3 and why three repairs failed in the same shape

Ruling 3 makes perspective the axis that cannot be removed by declaration, read from the
operating profile because a rename defeats an id and does not defeat a frame. Its stated
safeguard is that the launcher is not the observer.

`decisions/0100` has the builder launch its own witness. So the launcher **is** the executor,
and every field the walk reads to establish either axis — `context_passed`,
`predicates_source_*`, `subject_id`, `lease`, and the profile digest itself — is written by
the party being graded. `RunRecord.profile_of` resolves that digest against nothing. A rename
does not defeat the frame; the executor typing a different digest does.

Ruling 3's safeguard names the wrong adversary. It stops the observer vouching for itself and
leaves the executor vouching for the observer. That is why each pass finds the same class
returning somewhere new: the repairs move where a declaration is read, not that one is read.

## Disposition of pass 3

Repaired at the commit carrying this file, pinned by `WitnessFindingsOn3c24420`, and every
guard mutation-tested rather than assumed:

- **F2** — `admission.py` no longer re-hashes anything. It re-runs `infer_relation` over the
  record it was handed and refuses unless the handed verdict is the one the walk reaches,
  field by field. A verdict is a convenience for the caller and never a credential. The empty
  evidence list can no longer print as a hole.
- **F1** — both guards, together. The subject is corroborated *and* the candidate is read
  across every subject. Pass 2 objected that the second refuses an experienced observer, and
  it does; that cost is taken deliberately, because the alternative pass 3 defeated admits a
  subject's own builder as its witness. Disclosed as a `KNOWN-GAPS` row.
- **F4** — `_corroborated`, the candidate-elsewhere guard, and the re-walk each have a case
  that fails when the guard is deleted (verified: all three mutations killed). The oracle
  predicate gets a fixture carrying `unanswerable_edges`.
- **F6** — the two claims are corrected in `decisions/0104` rather than restated.
- The pass 1 witness record carries no builder prose at all, above or below its certifying
  line. Pass 3 found the previous repair had moved the defect above that line rather than out.

**F3 is not repaired and is not repairable here.** It is a property of the definition under
the launch model `decisions/0100` requires, and it is now stated as such: `CHARTER.md` says
what this walk detects rather than what it was asserted to detect, and `KNOWN-GAPS.md` carries
the perspective axis as declared, beside the context axis that was already disclosed.

## Standing

`observation_service_status` stays `BUILT_THIN_SLICE_REMAINDER_DECLARED_NOT_WITNESSED`. Three
passes dissented and none supported `BUILT -> WITNESSED`. Nothing here is witnessed, and pass
3's own probes are now inside the repair loop, so a fourth reading needs a fourth participant.

## Held for Bdo

Nine items across three passes, none answered by the builder. The new one is the largest:
under `decisions/0100` the executor launches the witness and therefore authors the fields that
establish the witness's independence, which makes Ruling 3's non-declarable axis declarable.
Whether that is a conflict to settle or a gap to disclose is the owner's, not the builder's.
`decisions/0104`'s judgement queue carries all nine.
