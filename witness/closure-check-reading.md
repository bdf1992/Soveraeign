# Witness record: the closure check every custody declares

```witness
standing_supported  WITNESSED
subject  closure-check-reading
revision  3f7f09c47c0f59be17bfb50f04ae8551667a664b
pass  5
```

Five passes by the same witness participant, each against a different frozen commit on
`claude/phase-1-5-exit-custody-x7fsi0`. Pass 5 (`3f7f09c`) owns the declaration above.
Passes 1 through 4 (`e981d64`, `06efb59`, `99647c7`, `f296d2a`) follow as history.

Witness: `sov-witness`, five invocations. It did not build, edit, stage, or commit anything
under the subject. Every defeat attempt ran in a `git worktree` copy, removed afterwards;
`git status --short` was empty and `git rev-parse HEAD` unchanged before and after each pass.

## Subject

Two of the six Phase 1.5 exit custodies opened declaring a `COMMAND` closure check that
produced no reading. `python scripts/sov_active_phase_progress.py` and
`python conformance/commissioning.py` each named a real module with real grading functions and
no entry point, so the declared check printed nothing and exited 0. A participant running its
own custody's declared closure would read silence as a pass. `contracts/phases.json` already
asserted in prose that the first of those commands read the exit custodies at their floors.

Custodies served: `custody:phase-1-5/commissioning-circuit` (P15-X5), whose own closure check
was one of the two and whose opening basis names this reader as its first piece of work; and
`custody:phase-1-5/definition-recurrence` (P15-X4), whose closure check was the other.

## Standing supported

`OPEN -> BUILT` for `scripts/sovcustody/closures.py`, and `BUILT -> WITNESSED` for the closure-
check reading, covering `scripts/sov_active_phase_progress.py`, `conformance/commissioning.py`,
and `scripts/sovcustody/closures.py`. Supported at `f296d2a` by pass 4 and carried to `3f7f09c`
by pass 5, which read the absorption below. Pass 4 verified through the declared surface:
`verify.py` PASS at 51 checks, `lint.py` PASS, `sov_custody.py selfcheck` 54 cases and 36 of 36
declared refusals reached, `test_custody_boards` 70 tests; at pass 4 no member claimed standing
above `BUILT`, and the three that now read `WITNESSED` were set on the strength of this record
after pass 5 carried it.

## What each pass defeated

**Pass 1 (`e981d64`)** reproduced both silence claims against the parent `4b0bc1d` and
confirmed the new readings refuse a constructed stage regression and a neutered fixture. It
withheld `WITNESSED`: the static `__main__`-guard grade read a *declaration* where the claim was
about *reporting*, and `if __name__ == "__main__": pass` satisfied it — demonstrated end to
end, with the declared closure exiting 0 in silence while every check stayed green. It also
found `--run` exiting 0 over the commands it had just printed as producing no reading, four
parsing defects in `script_of` (`-X utf8`, `-W ignore`, a `PYTHONPATH=` prefix, and the `py -3`
launcher) with `-m` named as a declared limitation rather than a defect, eight shapes
`has_entry_point` graded wrongly, and one lost defect string in the refactored
`commissioning_instrument`.

Its count of those commands was four. The artifact holds seven. The witness read `--run` through
`tail -40`, which cut the top three, and said so itself in pass 3; the builder took the four into
a docstring and a commit message from there. Recording that as a docstring defect alone would let
this record repair the witness, which is the shape the whole concern refuses.

**Pass 2 (`06efb59`)** closed all of those and found three more. The live reading was scoped to
the active phase, which reads as history-versus-now and is not: two live custodies carry no
phase, so the filter dropped `custody:session-as-node` while appearing to have skipped only
closed history. `run` captured stderr and discarded it, so a reader that printed one line and
then died was indistinguishable from one refusing loudly. And the inherited count of four had
reached a committed docstring, where the artifact holds seven.

**Pass 3 (`99647c7`)** confirmed the terminal scope, the counts, and every earlier repair, and
found the module split had left `python scripts/sov_custody.py closures` raising `NameError` on
every path without `--run`. The repository gate runs `--live --run`, so the broken branch stayed
green behind 51 passing checks — the subject's own defect one level up. It also showed the
traceback discriminator both over- and under-fires: it admitted five kinds of wholly silent
non-zero exit that the previous rule caught, and refused a failing `-m unittest` suite for being
a failing suite. It measured the predicate the evidence actually supports: all seven declared
commands that exit non-zero write 135 to 195 characters of reason.

**Pass 4 (`f296d2a`)** reconstructed the `NameError` in a scratch copy and watched four of the
five new subcommand tests and `verify.py` go red, then confirmed the corrected predicate against
its own battery: silent exit 0, silent exit 3, `os._exit(1)`, whitespace-only, a segfault, a
shell `exit 4`, and a nonexistent binary all refused; stderr-only at exit 0, a stderr reason at
exit 1, a traceback after a reading, a traceback alone, and a normal report all admitted, with
the verdict on all seven real commands unchanged.

It also settled a governance question against itself: both judgement items it had routed to the
root seat in earlier passes are `routine_decisions` under `contracts/closure-ownership.json`,
escalating them was the witness's own defect rather than caution, and nothing the builder settled
in those four passes belonged to the owner.

It found one laundering route that needed no code. Under an inherited `PYTHONDEVMODE=1` or
`PYTHONWARNINGS=always`, a leaked file handle makes the interpreter write a `ResourceWarning`
the module never chose to emit, and the exact Phase 1.5 shape — a `main()` that runs, reports
nothing, returns 0 — is admitted for output it never produced. Latent rather than live: neither
variable is set in `.github/`, in `scripts/`, or in the environment, and the verdict on every
real subject was correct. The witness named it a one-line absorption inside the concern and not
a reason for another round.

## Absorbed after pass 4

`run` now pins the child's diagnostic environment (`scripts/sovcustody/closures.py`,
`_child_env`), so what the interpreter says about a command cannot become what the command said.
Two coverage gaps pass 4 recorded as gaps rather than defects are also closed: the
`run`-plus-JSON path, and the branch where the command never starts.

**Pass 5 (`3f7f09c`)** confirmed the absorption against all three environments, verified the
environment is filtered rather than replaced so `PATH` and the resolution variables survive, and
proved each new test goes red when its own subject is reverted. It found the denylist was two
names against a class of at least six — `PYTHONVERBOSE`, `PYTHONPROFILEIMPORTTIME`,
`PYTHONMALLOCSTATS` and `PYTHONINSPECT` each laundered the same silent subject — and that pinning
warnings off would refuse a check whose whole reading is a deliberate `warnings.warn`. All six are
now denied and both costs are stated in `_child_env`. It read this record against its own four
passes and corrected four things in it, including the attribution above. Its `WITNESSED` support
carries to `3f7f09c`.

## What this record does not support

Nothing here says a Phase 1.5 exit clause is met. `custody:phase-1-5/commissioning-circuit`
moves from `ROOT_POINT` to `VERTICAL_SLICE` on two members and
`custody:phase-1-5/definition-recurrence` on one; a stage is how far the thing has been drawn,
not how well it is proven, and no circuit has been run. The static screen grades a declaration
and cannot see an entry point that reports nothing; only the live reading measures that, and it
is scoped to custodies still carrying work. Seven declared commands reject their own arguments
and are admitted as unbuilt capabilities their holders own — six on terminal Phase-I custodies,
one on `custody:session-as-node`.

This is an observation, not a settlement and not a ratification.
