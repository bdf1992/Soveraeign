# 0104 · The landing grant admits prose it cannot land

Status: `PROPOSED · BDO HAS NOT RULED`

Drafted while landing `concern:harness/witness-context`. The change it proposes
widens a `RATIFIED` grant, which the drafting participant may not do, so it is
measured, written, and left for Bdo rather than applied. It follows the shape of
`decisions/0076-witness-outside-the-landing-grant.md`, which left the mirror-image
question — a narrowing — in the same place.

## The finding

`grant:standing-landing-loop` admits ten path prefixes. `contracts/clarity.json`
declares `.clarity/coverage.json` as its `coverage_file`: the receipt store for
every artifact under clarity review. That file is under no admitted prefix, so
`scripts/sovkernel/scope.py` refuses it, exactly as it refuses `witness/`.

Measured against the checked-in grant and the checked-in coverage file:

```
clarity-covered artifacts:                142
of those, inside the grant's scope:       109
  .claude 40 · services 53 · bindings 5 · adapters 4 · contracts 3 ·
  conformance 2 · scripts 1 · workers 1
.clarity/coverage.json inside the scope:  False
```

Changing a covered artifact moves its digest, which makes its receipt stale,
which fails `python scripts/sov_clarity.py check` and the
`test_recorded_reviews_are_well_formed_and_current` case inside
`python scripts/verify.py`. Clearing the staleness means writing
`.clarity/coverage.json`, which the grant refuses.

So for those 109 artifacts the grant is in a deadlock of its own making: land the
prose and `verify` fails, which the grant requires to pass; land the receipt too
and the scope check refuses it. Neither ordering, branch split, nor commit
arrangement escapes it, because both halves are required at the same commit.

## How it was met

`concern:harness/witness-context` repaired the witness frame across thirteen
workflows. The repair itself is untouched by this. What could not cross were:

- `.claude/agents/sov-witness.md`, which restates the `SDLC.md` Release gate 6
  rule the repair enforces, and the three sibling agent files;
- `scripts/README.md`, whose stated `sov_*.py` entrypoint count moves whenever
  the concern adds an entrypoint — so the three new entrypoints
  (`sov_workflows.py`, `sov_context.py`, `sov_ledger_quarantine.py`) were
  withdrawn with it, and with them the workflow grader and the context surface.

The candidate that remained is `3c9b298`, forty paths, all in scope. The
withdrawn work is presented in `acceptance/A25.json`. Nothing was lost and
nothing was smuggled: the split and its reasons are in the candidate's own
commit message.

## The decision this asks for

Not a fix to apply. Two designs that are both coherent and incompatible, and the
choice is the root seat's:

1. **Add `.clarity/` to `scope.paths`.** The loop can then land covered prose
   with its receipt. The cost is precisely the warrant problem
   `decisions/0076` names about `witness/`: a builder that can write the receipt
   store can stamp a clarity review over prose it just wrote, and the receipt
   still reads as a completed review. Clarity is a review, not a derivation, so
   this is not the harmless case that argument has for a generated projection.

2. **Leave the grant as it is** and accept that changes to those 109 artifacts
   are presented for acceptance rather than landed. The cost is that the loop
   cannot carry an ordinary documentation repair inside its own scope, and that
   every such change queues on the owner.

A third shape exists and is not proposed here because it is a contract change
rather than a grant change: scope a clarity receipt below the whole file, so a
mechanical count correction is not the same act as a prose review. `A25` already
records a related residual — a basis that stales sixty readers on one queue
movement — and both point at `contracts/clarity.json` rather than at the grant.

## What would defeat this ruling

- A demonstration that a covered artifact inside the grant's scope can be landed
  under it today. That would make the whole record void; the measurement above
  is the thing to attack.
- A ruling that `verify` need not pass for a landing, which would dissolve the
  deadlock from the other side. It would also dissolve the grant's only
  evidential precondition, so it is named for completeness rather than proposed.
- Evidence that the 109 figure is an artifact of the current coverage file
  rather than of the design, for instance if clarity coverage is meant to shrink
  to the root governing documents, which sit outside the grant already.

## What still waits on Bdo

1. Which of the two designs above holds. Both are consistent with the record;
   the drafting participant does not have a view worth recording, because the
   trade is between two things only the root seat prices.
2. Whether the deadlock is urgent. It has existed since the grant was ratified
   on 2026-08-25 and was met for the first time here, which is evidence it binds
   rarely rather than evidence it is harmless.
3. Neither question gates the landed candidate, which carries no covered
   artifact.
