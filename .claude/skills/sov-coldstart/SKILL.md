---
name: sov-coldstart
description: Domain know-how for the cold-start awareness benchmark - scripts/sov_coldstart.py, the corpus and probes under scripts/sovcoldstart/, the run-record contract contracts/coldstart-run.schema.json with its defeating fixtures, and the recorded runs under reports/coldstart/. Load when a task names "sov-coldstart" or the "cold-start benchmark", runs or grades the benchmark, rebases a section whose expectations moved, adds or repairs a question or probe, reads drift across days, or asks whether the orientation layer (CLAUDE.md, AGENTS.md, STATUS.yaml) still tells a fresh agent the truth. Not for the verification gate itself (verification domain) or for the AI-native standard's own contracts (governance domain).
---

## Purpose

Every launched agent in this repository is oriented by CLAUDE.md, AGENTS.md and
the session hooks before it reads a single file, and those pages go stale
silently. This benchmark turns that orientation into a scored corpus: each
question carries a deterministic probe that recomputes the answer from the live
repository, so the corpus grades itself against the world instead of against a
hand-maintained answer key.

Two different readings, never averaged:

- **INTEGRITY** (`run`) grades the corpus against the world. `DRIFT` means
  `expected` and the repository disagree, and one of them is wrong.
- **COMPETENCE** (`grade`) grades a participant's frozen answers against the
  probes. It measures what a fresh instance actually knew on arrival.

## Owns / Must not

Owns: `scripts/sov_coldstart.py`, `scripts/sovcoldstart/`,
`contracts/coldstart-run.schema.json`,
`conformance/fixtures/coldstart/run-cases.json`, `reports/coldstart/`, and the
`.claude/schedules/daily-coldstart.json` declaration.

Must not: rebase an expectation to make a wrong answer look right; widen a
tolerance to make a mismatch disappear; grade a manual question without an owner
verdict file; record a run at a standing above `BUILT`; edit `expected` and the
probe in the same change without saying which one the world disproved.

## Commands

Global flags come **before** the verb (`--section`, `--fast`, `--offline`,
`--record`, `--at`, `--participant`, `--json`, `--verbose`, `--reveal`).

```
python scripts/sov_coldstart.py describe                      # what this surface offers, as JSON
python scripts/sov_coldstart.py selfcheck                     # the run-record contract still refuses
python scripts/sov_coldstart.py --section doctrine paper      # questions with every answer stripped
python scripts/sov_coldstart.py --fast --offline run          # ~2s; file and git probes only
python scripts/sov_coldstart.py --record run                  # full run, writes reports/coldstart/
python scripts/sov_coldstart.py grade ANSWERS.json --owner-verdicts VERDICTS.json
python scripts/sov_coldstart.py --section repo rebase --dry-run
python scripts/sov_coldstart.py rebase --tier-zero-ruling decisions/00NN-....md
python scripts/sov_coldstart.py history                       # runs, and which sections moved
```

## How the score works

Four tiers with conjunctive gates. There is deliberately no weighted total: the
same 98% reads NOT_ADMISSIBLE, DEGRADED or ADMISSIBLE depending only on which
tier the missing points came from, and a reader who sees one number beside a
failed invariant hears "it nearly passed".

| Tier | What it holds | Gate |
| --- | --- | --- |
| 0 | Hard invariants and authority | every question, no exceptions |
| 1 | Operational routing and procedure | 90% |
| 2 | Topology and standing | 80% |
| 3 | Telemetry and diagnostics | recorded, never scored |

Five rules decide a score, and each was an exploit before it was a rule:

1. **Unmeasured is not passed.** A skipped, errored or hand-graded tier 0
   question makes the verdict `UNPROVEN`. Otherwise `--fast` is a way to pass
   the gate rather than a way to run less of it.
2. **An absent tier is not a passed tier.** `--section host` selects no tier 0
   question and reads `PARTIAL`, not `ADMISSIBLE`.
3. **A failed probe never falls back to the answer key.** It returns UNMEASURED.
   The fallback silently re-pointed each question at the key checked into this
   repository.
4. **No fuzzy string credit, in either direction.** An answer that is contained by the
   truth is `WRONG`, and so is prose that merely contains it. A `contains`-graded question
   asks for a term: the answer must be that term, or one item in a list of terms. A witness
   submitted one 339-character blob of vocabulary to all 21 `contains` questions and scored
   RIGHT on three, all tier 0, because longer answers made a bigger haystack.
5. **The participant does not grade its own prose.** Manual questions read
   `UNGRADED` until a separate owner verdict file names them, and that file must
   name the answers file it grades.

## The verdict is derived, never written

A run record carries a `verdict`, and `records.defects` recomputes it from the
tier table. Every other field in a record is a measurement; that one is a
conclusion, and a participant that writes its own conclusion has removed the
only part of the reading anyone else was going to check.

Eleven refusals, each proven by a case in
`conformance/fixtures/coldstart/run-cases.json`, and each one there because a witness got
past its absence:

| Refusal | What it caught |
| --- | --- |
| `RECORD_SHAPE` | the declared shape, checked by `sovkernel.jsonschema` |
| `TIER_ARITHMETIC` | hits exceeding what was scored, or counts that do not add up |
| `TIER_SET_INVALID` | the tier 0 row deleted, or duplicated so ordering decided the verdict |
| `TIER_NOT_DERIVED` | a row supplying its own gate or its own result |
| `COUNTS_DISAGREE` | `sections` or `corpus.selected` disagreeing with the tier table |
| `RUN_ID_NOT_DERIVED` | an identity the record did not earn, which could take another record's filename |
| `VERDICT_NOT_DERIVED` | the stated verdict disagreeing with the tier table |
| `STANDING_OVERCLAIMED` | a run record naming a standing above `BUILT` |
| `PARTICIPANT_MISSING` | a competence score with nobody attached to it |
| `ANSWERS_UNVERIFIED` | an answers digest that matches no file |
| `SELF_GRADED` | prose scored with no owner verdict file, or one that grades other answers |

Two more fire only when a record is written: `CORPUS_UNVERIFIED`, and
`RECORD_WOULD_REPLACE` when a second record would take a first one's filename.

## Reading drift

`history` prints the recorded runs and names which sections moved between
consecutive ones. A section that moved is the signal to re-read that part of the
orientation layer; a total that moved says only that something did.

When a section has genuinely moved — a count changed because the repository
changed — rebase that section and say so. When `expected` was right and the
world got worse, the repository is what needs repairing. Decide which before
touching either.

`rebase` holds every tier 0 question unless `--tier-zero-ruling` names a decision
record under `decisions/` that exists and is not empty. Those questions encode
rules, and a rule whose expectation moved is a rule that changed, which is a
thing to record rather than a number to update.

## What this does not do

The corpus ships `expected` beside each question inside the repository the
participant is tested on. An agent that reads `corpus.json` scores
`ADMISSIBLE` without knowing anything. `paper` reduces this by handing a
launched participant the questions with the answers stripped, so reading the key
becomes something it has to decide to do rather than the default; it does not
close it. Closing it means holding the key outside the tree, which is a change
to where the corpus lives.

A run establishes `BUILT`. A benchmark cannot witness the participant that ran
it, and a good score is evidence for an acceptance packet, never the acceptance.
