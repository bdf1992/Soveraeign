# Standard draft · `story` ticket kind

Status: `SUPERSEDED · carried into decisions/0022-story-ticket-kind.md on 2026-08-23`

Kept as the working note behind the decision. The shipped fields differ from the
table below: `wants` / `leaves_with` became `expected` / `found` / `asks`, because a
story narrates the participant's expectation over the scenario and asks the substrate
for adjustments; the decision record is the authority on what landed.

A proposal for Bdo. Nothing here edits `contracts/issue-metadata.schema.json`,
`.github/labels.yml`, or `CONTRIBUTING.md`; those move together in one reviewed
change after the owner decides. Drafting is `RECORD_LOCAL`.

## Current state

`soveraeign-ticket/v1` admits five kinds: `epic-of-epics`, `village`, `bit`,
`implementation-stub`, `verification-engagement`. Containment is
`epic -> village -> bit | stub`. There is no story kind, no story label, and no
story field on any kind.

The nearest existing shapes:

| Shape | Where | What it is | What it is not |
| --- | --- | --- | --- |
| Scenario | `conformance/scenarios.json` | One strategy-neutral participant narrative per requirement: given, desired, gap, forced conditions, work item, watched delta | A ticket. It lives in the repository and the oracle reads it. |
| Six-line story | `.claude/epic/NARRATIVE.md` | Who walks in, what they want, counter, leans on, what they leave with, today | A contract. Nothing validates it. |

The proposal joins them: a story is told on a ticket in the six-line shape, and
it is *walked* only through a scenario the oracle can run.

## What a story is

A **story** is one participant from the cast walking up to one front-office
counter wanting one outcome. It names the back-office supports the counter
cannot work without, and what the participant leaves holding.

It is not a bit (it obliges nothing to exist), not a stub (it closes no
repository surface), and not an engagement (it attacks nothing). It is the
reason a counter opens.

## Proposed metadata

New `kind: story`. Required beyond the common fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `story_id` | `^STORY-[A-Z0-9-]+$` | Identity |
| `participant` | enum | One of the cast: `owner`, `human-operator`, `model-operator`, `external-system`, `worker`, `witness`, `neighbor-node` |
| `village` | existing enum | The counter's village |
| `village_issue` | issueRef | Containment edge, as for bits and stubs |
| `parent` | issueRef | The front-office counter (a `bit`) the participant walks up to |
| `wants` | string | One outcome, in the participant's words |
| `leans_on` | issueRef[] | Back-office supports the counter cannot work without. Distinct from `requires`: a story is never dispatched, so it never blocks; it is *walkable* or not. |
| `leaves_with` | string | The receipt, record, or decision in the participant's hand |
| `scenario` | string, optional | The `conformance/scenarios.json` id that walks this story. Required before standing may rise above `PROPOSED`. |

`standing` reuses the existing enum, read for a story as:

| Standing | Means |
| --- | --- |
| `PROPOSED` | Told. The six lines exist; no scenario binds it. |
| `DECLARED_NOT_IMPLEMENTED` | Bound. A scenario exists; some support on `leans_on` is not yet `BUILT`. |
| `BUILT_SELF_TESTED_NOT_WITNESSED` | Walked by its builder. Every support is at least `BUILT` and the scenario passed under the builder's own run. |
| `WITNESSED` | Walked under independent observation (`participant-observation.schema.json`). |
| `RATIFIED` | Bdo. |
| `DEMOTED` | The counter or a support was demoted; the story is told again or withdrawn. |

The walker derives a reading the way it derives `ready / held / unrouted` for
bits: **told** (no scenario), **walkable** (scenario bound, every `leans_on`
at least `BUILT`), **walked** (`WITNESSED` or above). A derived reading is
evidence about the tree; it settles nothing.

## Refusals the contract should declare

- A story with no `participant`, or a `participant` outside the cast.
- A story whose `parent` is not a `bit` listed as a front-office counter in
  `.claude/epic/offices.json`.
- A story whose `leans_on` names a closed issue or anything in `outside_both`.
- A story above `PROPOSED` with no `scenario`.
- A story marked `WITNESSED` by the actor who walked it. A build cannot witness
  itself; neither can a walk.
- A pull request closing a story. Only an observation moves a story; a PR may
  move the stubs it leans on.

## Label projection

`kind_to_type` gains `"story": "type: story"`. One new label in
`.github/labels.yml`:

```yaml
- name: "type: story"
  color: "E16F24"
  description: "One participant, one counter, one outcome; walked only through a conformance scenario."
```

Village, horizon, effect, and standing labels project as they do today.

## Queue policy

Stories do not enter the takeable queue. `contracts/ticket-queue-policy.json`
should exclude `kind: story` from dispatch ordering and instead report them
under the counter they belong to, so a counter's stories are visible beside
its stubs without competing with them.

## Files the reviewed change would touch

1. `CONTRIBUTING.md` — Issue coordination contract: add the kind, the
   containment edge, the closing rule.
2. `contracts/issue-metadata.schema.json` — the `story` branch in `allOf`,
   the `participant` enum, `leans_on`, `wants`, `leaves_with`, `scenario`.
3. `.github/labels.yml` and `contracts/ticket-label-projection.json` — the
   label and its derivation.
4. `contracts/ticket-queue-policy.json` — exclusion from dispatch.
5. `contracts/fixtures/` — one positive story block and the six defeating
   blocks above.
6. `scripts/sovepic/survey.py` — containment accepts `story`; the
   told/walkable/walked reading.
7. `CLASSIFICATION.md` — `owner`, `external system`, and `neighbor node` are
   not in the participation vocabulary today; `operator`, `worker`, and
   `witness` are. The cast either joins the contract or narrows to it.
8. Attended `python scripts/sov_epic.py sync` after the first story is filed.

Size: an afternoon for items 1–6, plus one owner read for item 7.

## Example block

The first story for the Operator Desk, as it would be filed:

```yaml
issue_schema: soveraeign-ticket/v1
tags: [kind:story, scope:counter, horizon:now-to-next, effect:record-local]
kind: story
story_id: STORY-OPERATOR-DESK-HUMAN-JUDGEMENT-REQUEST
participant: human-operator
village: reach-and-motion
village_issue: "#2"
parent: "#30"
wants: "Ask the owner for a call on one thing without deciding it for them."
leans_on: ["#6", "#7", "#11", "#12", "#13"]
leaves_with: "A judgement request on the owner's desk and one attributable event for having raised it."
scenario: null
standing: PROPOSED
horizon: NOW_TO_NEXT
authority: Bdo/product-intent
effect_class: RECORD_LOCAL
evidence_pointer: .claude/epic/NARRATIVE.md#the-operator-desk-30-45
last_observed_at: null
walker_receipt: PENDING
demotion_pointer: "#demotion"
dependency_channels: [trust-control, record-spine]
```

Title form stays `Subject — bounded outcome`:
`Operator Desk — a human raises a judgement request`.

## Decisions this draft queues for the owner

1. Adopt `story` as a sixth kind, or keep stories in the repository beside
   scenarios and out of GitHub entirely.
2. The cast as contract vocabulary (`CLASSIFICATION.md`) or as a narrative
   convention only.
3. Whether a story's `parent` must be a front-office counter, which makes
   `offices.json` load-bearing for validation and moves it out of "plumbing".
4. Whether a story may ever close without a `WITNESSED` walk.
