# 0087 · The phase number refuses, and a lesson cannot assert a check it does not have

Status: `OWNER-RULED · BUILT · SELF-TESTED · NOT WITNESSED`

Bdo asked, on 2026-08-27, how many lessons had landed. The answer was one of
seven, and none of the six findings from the Phase-I retro had entered the
lessons loop at all. He then directed that the system enforce what the retro
learned, so future sessions inherit it rather than rediscover it.

This record is that enforcement. It changes no policy any governing document
owns. It makes two existing rules refuse.

## What was wrong

Two readings, both from `reports/2026-08-27-phase-i-retro.md`.

`scripts/sov_f2_gate.py` has read the distance between `SPEC.md` and the
conformance corpus since it was written, and returns non-zero whenever the gate
is open. Nothing ran it. It was in no check table, no landing gate, and no
orientation page, so it read 0 of 44 for six days and 401 commits, and refused
nothing.

`decisions/0029` created the lessons loop and closed with a named residual: it
added no check enforcing the drain. Seventeen days later the page still graded
itself. Its `Standing now` line, its standings, and its landings were prose
nothing read.

## Decision

### 1. A floor on the phase reading, not the gate itself

`contracts/phase-progress.json` records the reading the corpus currently earns
and the grader `scripts/sov_phase_progress.py` refuses a fall below it. The
check is registered as "phase progress floor".

Registering the gate itself was considered and rejected. It would refuse every
run until the phase exit is earned, which is months, and a check that is red for
months teaches a reader to skip it — the same failure this repair is for,
wearing a different colour.

What refuses is regression, by total and by family, because a fall needs an edit
to the corpus or the specification and is attributable to that edit. What does
not refuse is a stall: the participant landing the commit that crosses the
ceiling is not the participant who let the number sit still, and
`decisions/0081` took the wall clock out of the exit code on exactly that
reasoning. The stall prints its commit count and records debt. It is measured in
commits rather than days so it reads the record and not the host clock.

The floor also refuses an id the specification does not state
(`UNKNOWN_PREDICATE`), a predicate uncovered and unexcused
(`UNDECLARED_UNCOVERED`), and an exclusion that has stopped being true
(`STALE_EXCLUSION`). Those three together make the exclusion list
self-maintaining: closing a gap forces its own exclusion to be deleted, and a
new normative predicate in `SPEC.md` cannot arrive uncounted.

### 2. The join the gate was waiting for

All 20 oracle controls now declare a `predicates` array. The gate reads **36 of
44** where it read 0, without a single new fixture: the coverage existed and was
never claimed in machine-readable form.

The join is one predicate per oracle assertion whose failure *is* that
predicate's failure. A generous join was available and refused, because crediting
coverage nobody demonstrated is the defect the retro named. The eight predicates
still uncovered are enumerated with reasons in `uncovered_on_purpose`:
`PRED-I-2.1` because no control rereads a source, `PARITY-1` because no control
discovers operations, and the six run and capture transitions no control models.

### 3. A standing on the lessons page is a claim the tree can defeat

`contracts/lessons-loop.json` and `scripts/sov_lessons.py`, registered as
"lessons loop". `EFFECTIVE` is defined by `decisions/0029` as running inside
`scripts/verify.py` or `scripts/lint.py`, so an entry claiming it while naming no
path either one reaches now refuses. The grader reads what counts as reached out
of the check table it is itself an entry in, so a lesson cannot assert a check
that is not running.

**The drain count does not refuse, and this record does not reverse
`decisions/0029` on that point.** That record declined a check failing on an
eighth lesson, on the reasoning that it makes capture costly at exactly the
moment capture matters. The reasoning holds. The count is printed every run and
recorded as debt past the threshold, which puts it in front of a reader without
charging anyone for writing a lesson down. This closes the half of that residual
that taxes nobody.

### 4. The retro's own findings entered the loop

Four new entries, and two findings dropped rather than recorded.

`L-0008` and `L-0009` stand `EFFECTIVE`, naming the checks this record lands.
`L-0010` (governance outgrew what it governs) and `L-0011` (product ground is
cited and not routed on) stand `RECORDED`. Findings 4 and 5 are dropped with
links to `contracts/custody.schema.json` and `contracts/work-circuit.json`,
because `decisions/0029` drops a lesson that restates a rule an owning document
already holds.

The page now reads 8 `RECORDED` against a threshold of 7. The drain is due, it
is reported as debt, and draining it is not one concern: `L-0003`, `L-0005` and
`L-0006` each land in a different service, and `AGENTS.md` mints a separate
concern when work crosses a service boundary.

## Defaults taken

- **The floor is 36, pinned at `11c3f1a`.** Overturned by a reading of the join
  that finds a control declaring a predicate its oracle does not assert.
- **The stall ceiling is 40 commits.** A guess, and it refuses nothing, so being
  wrong costs a misleading debt line rather than a blocked landing. Overturned by
  the first stall reading that nobody acts on.
- **Three of the four lessons filed as needing Bdo were settleable here.** This
  record does not settle them; it records that `L-0003`, `L-0005` and `L-0006`
  are reachable at the tier that holds each service, which is not this concern.

## Consequences

- `python scripts/verify.py` runs two more checks. Both pass on this branch.
- The eight checks failing here fail identically on the base commit `11c3f1a`
  with none of this applied, verified on a clean worktree. This branch neither
  causes nor repairs them. `docs/documentation.html` is one of them and was left
  stale deliberately: rebuilding it produces an 855KB minified re-render that
  would bury a 60-line change and collide with whoever holds that drift.
- `PRED-I-2.1`, `PARITY-1` and the six run transitions are now visibly open with
  a reason each, where before they were indistinguishable from the 36 that are
  covered.

## Evidence

- `scripts/tests/test_phase_progress.py`: 23 tests. Every one of the five
  declared refusals is fired by a case, the stall is proved non-refusing, and the
  join is checked directly — no control may declare a predicate `SPEC.md` does
  not state, or a requirement predicate belonging to another requirement.
- `scripts/tests/test_lessons_loop.py`: 24 tests over synthetic pages, so a
  lesson being written or drained never breaks them. All seven declared refusals
  fire.
- `python scripts/sov_phase_progress.py check` and `python scripts/sov_lessons.py
  check` run the graders by hand.
- Standing is `BUILT_SELF_TESTED_NOT_WITNESSED`. The participant that built these
  cannot observe them.

## What still waits on Bdo

1. **Ratifying this record and the two contracts.** Both are `PROPOSED`.
2. **`L-0010`**, whether a proportion between records and demonstrated coverage
   is a governed constraint at all. It is a claim about how much governance is
   too much, which is the root seat's to place.
3. **`L-0007`**, unchanged from where `decisions/0029` left it: whether
   "enumerate what the guard touches and mark what has been varied" belongs in
   `AGENTS.md`. He granted the edit on 2026-08-27; it is not made here because it
   is a governing document and this concern does not hold one.

## Source and authority

- Bdo's direction, 2026-08-27: enforce what the retro learned so future sessions
  inherit it
- `reports/2026-08-27-phase-i-retro.md`, findings 1, 2, 3 and 6
- `decisions/0029-lessons-loop.md` — the loop, the four standings, the threshold,
  and the residual this closes half of
- `decisions/0081` — the reasoning that a reading nobody caused does not refuse
  whoever arrived next
- `SPEC.md` Conformance boundary; `ROADMAP.md` F2 exit
- `AGENTS.md` — closure ownership, the absorption test, evidence and standing
