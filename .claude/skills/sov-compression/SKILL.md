---
name: sov-compression
description: Cross-cutting gap-phase learning/compression competence for Soveraeign. Use for the daily compression ritual, weekly super-compression, repeated-defect analysis, representation/drift reduction, lesson routing, gate review, and the GAP_OPERATIONALLY_INVISIBLE readiness reading. This skill owns no policy and creates no new ledger.
---

# sov-compression

## Purpose

Make learning cheaper than repetition. Read one bounded window of repository
activity, correlate repeated observations to the same subjects, expose where
representations or checks are multiplying, and route the result into mechanisms
that already own it.

This is gap-phase harness competence. It does not open a successor phase, mint a
standing, create authority, or create another System of Record. `STATUS.yaml`
and `contracts/phases.json` remain authoritative for phase state; `LESSONS.md`
and `contracts/lessons-loop.json` own lessons; existing concerns/custodies own
work; governing documents and decisions own policy.

This skill composes, rather than replaces, the existing owners:

- `sdlc-feedback` owns how learning returns to the SDLC loop;
- `sov-governance` owns governing meaning, phase boundaries, and owner routing;
- `sov-verification` owns repository verification evidence and gate mechanics.

Compression supplies the cadence and correlation procedure. It must not copy
those owners into a fourth policy surface.

## Core distinctions

- **One authoritative producer per fact.** Independent observers may reproduce
  evidence; projections may render it. Neither becomes a competing producer.
- **Corroboration is not duplication.** Independent evidence can be valuable.
  Re-running the same observation after the defect is already sufficiently
  established is the waste to expose.
- **A report observes. A lesson generalizes. A decision changes policy. A
  concern creates work.** Do not promote one into another merely because it is
  interesting.
- **Repetition is a skill-extraction signal, not a prerequisite for learning.**
  One demonstrated authority, identity, security, or record-integrity defect can
  establish an invariant immediately. A reusable skill is extracted only after
  a stable procedure repeats.
- **Gap work is temporary by definition.** Once the historical-to-current seam
  is no longer observable to an independent fresh reader, stop manufacturing
  gap work to preserve the ritual.

## Mechanical reader

Use the same deterministic reader for both cadences:

```bash
python scripts/sov_compression.py daily --json
python scripts/sov_compression.py weekly --json
```

It reads only:

- current `STATUS.yaml` phase/gate projection;
- `LESSONS.md` through the existing `sov_lessons` grader;
- the exact local Git revision and bounded commit/path churn;
- local and remote-tracking refs already present in this checkout.

It writes nothing. Scheduled executions already have `.local/schedules/` capture
and ledger semantics; do not add a compression ledger beside them.

The deterministic reader is necessary but insufficient for the gap terminal. A
fresh-reader pass must separately test whether current entry documents are
actually usable without conversational or oral history.

## Daily ritual

The daily pass is a small 24-hour feedback loop:

1. Pin the exact subject revision and confirm whether the repository still reads
   `phase: NONE_ACTIVE` while the gap is open.
2. Read the lessons loop. Surface any false `EFFECTIVE`/`ADMITTED` claim and
   whether the non-refusing drain is due.
3. Read the last 24 hours of commits as observations over paths. Name high-churn
   subjects without interpreting churn itself as a defect.
4. Ask whether a red/finding is a new defect, useful corroboration, or another
   observation of an already-known defect.
5. Route only what was learned:
   - report-only observation;
   - lesson candidate or stronger existing lesson;
   - decision candidate only when policy/authority/boundary changes;
   - concern candidate only when concrete work remains.
6. Run or consume an independent fresh-reader reading of the current entry path.
7. Prefer one small compression/closure action over new surface. If no action is
   justified, say so; the ritual is allowed to produce no work.

The daily ritual should feel almost invisible: short, bounded, and biased toward
removing future reconciliation cost.

## Weekly super-compression

The weekly pass uses the same instrument over seven days, then goes deeper:

1. Compare repeated high-churn subjects and repeated defect shapes across the
   week.
2. Identify where one fact has multiple producers or where a projection/check is
   recomputing a fact already owned elsewhere.
3. Separate useful independent corroboration from redundant recomputation.
4. Review lessons that stayed `RECORDED`: drain, strengthen, supersede, or leave
   them recorded with an explicit reason. Never promote by summary.
5. Review candidate skills. Promote only procedures that repeated with stable
   inputs, outputs, refusal boundary, and owner documents.
6. Review gate pressure using the existing #187 rule: blocking authority needs
   an explicit risk, scope, pass criterion, evidence class, expected cost, and
   owner. No criterion means advisory evidence, not a blocking verdict.
7. Re-run the fresh-reader test independently rather than inheriting the daily
   reports' claim that orientation is clear.
8. End with a **subtraction plan**: facts/projections/checks/process steps that can
   now be derived, correlated, retired, or made unnecessary.

The weekly result is not a new architecture plan. Its job is to make the next
week inherit less ambiguity than the previous one.

## Shape audit

When a repair appears correct but repeated Red work keeps finding another hole,
check the axes separately before widening the implementation:

`subject · identity · session · binding · scope · authority · provenance ·
referent · revision · topology · time · host/repository boundary`

The purpose is not to force every concern through every axis. It is to avoid
fixing the obvious noun while the real invariant lives one relation deeper.

## Gap terminal

The ritual may report the literal readiness reading:

`GAP_OPERATIONALLY_INVISIBLE`

only when an independent fresh reader can, from the current repository alone:

1. identify historical Phase I as terminal `CLOSED_INCOMPLETE` rather than live
   authority;
2. identify that no successor phase is active and locate the current next gate;
3. enter the current progressive participant path without oral history;
4. reach the relevant principal/session -> grant -> operation -> record/projection
   path and the concern -> custody -> lease -> closure -> landing -> settlement
   lifecycle where applicable;
5. find no `EFFECTIVE` lesson whose claimed carrier is absent or stale;
6. find material owner decisions attached only to the exact transition they gate,
   rather than an undifferentiated owner backlog blocking all work; and
7. encounter surviving work as ordinary current readiness, not unexplained
   Phase-I archaeology, duplicate truth, or reconciliation debris.

`GAP_OPERATIONALLY_INVISIBLE` is **not** phase opening, acceptance, ratification,
or permission to mutate `contracts/phases.json` or `STATUS.yaml`. It means the
pre-opening gap has stopped imposing a special operational tax. Once this reading
is independently supported, stop minting gap-specific work unless a regression
makes the gap visible again. Daily compression may continue as regression
detection and weekly compression may continue as ordinary system compression.

If the fresh-reader result cannot be established, report `GAP_VISIBLE` or
`UNATTESTABLE`; never infer invisibility from green CI or from the compression
synthesizer's own confidence.

## Output contract

Return these sections, omitting empty ones rather than inventing content:

- subject revision and window;
- gap reading: `GAP_VISIBLE`, `GAP_OPERATIONALLY_INVISIBLE`, or `UNATTESTABLE`;
- fresh-reader evidence/friction;
- new defects;
- useful corroboration;
- duplicate/redundant observations;
- representation or gate pressure;
- lesson routing;
- skill candidates (weekly especially);
- decision candidates that genuinely require owner/root judgement;
- concrete concern candidates;
- subtraction/compression candidates;
- next smallest action.

## Refusals

Refuse to:

- open/name a successor phase or change `phase: NONE_ACTIVE`;
- convert `GAP_OPERATIONALLY_INVISIBLE` into a phase transition;
- create a new learning/weekly ledger when schedule capture and existing records
  already hold the observation;
- turn churn, failure count, repetition, model consensus, or recency into
  authority or standing;
- treat executor/self-report as independent evidence;
- create a concern merely so an observation has somewhere to go;
- create a new skill from one clever procedure or from repeated prose alone;
- silently delete historical evidence or owner decisions in the name of
  compression;
- merge independent observation into the authoritative producer it is meant to
  check;
- keep the gap alive after its observable terminal has been independently reached.

## Verification

For mechanical changes to this capability:

```bash
python -m unittest scripts.tests.test_sov_compression -v
python scripts/sov_compression.py daily --json
python scripts/sov_compression.py weekly --json
python scripts/sov_schedule.py validate
python scripts/verify.py
python scripts/lint.py
```

Record exact exit codes. A green run is engineering evidence only.
