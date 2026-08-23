# Witness observations

Recorded observations from independent runs. An observation is evidence of what
a witness saw. It is not a claim of standing, and it never ratifies.

## FOUND-007 · fresh witness cold start

`FOUND-007-observation.json`, against revision
`bbeb5d6a235e61e13237a3f9b0a04654434280f7`.

**The first execution of this scenario.** It had been declared `SEED` since the
founding and had never been run, which is why `SPEC.md` had never reached
`WITNESSED` and why the owner kept being asked to ratify a document standing at
`PROPOSED` — a move the transition contract refuses everywhere else as
`SKIPPED_STANDING`.

Reproduce it:

```
git clone --depth 1 <repository> fresh && cd fresh
python conformance/run.py
python conformance/run.py --cases conformance/observations/FOUND-007-cases.json \
    --observations conformance/observations/FOUND-007-observation.json
```

### What the run established

A clean checkout, no predecessor repository, and no oral explanation were
sufficient to locate authority (two holders, two authority types), enumerate the
open decisions and protected boundaries, execute the Phase-I conformance suite,
and reconstruct every verdict independently of the runner's own summary: 18
controls, 9 requirements carrying both polarities, zero verdict mismatches, zero
empty payloads, and no requirement whose positive and defeating fixtures are the
same. Elapsed machine time, 6 seconds.

The absent `lineage/` corpus did not defeat the run. `PUBLICATION.md` keeps it
unpublished and permits a document to cite the type and clause of its source
ground without publishing the archive, provided a public checkout reports locked
evidence as unavailable rather than claiming a verification it could not
perform. `verify_bootstrap.py` reports exactly that.

### What the run refused

The oracle rejected the observation with one defect:

```
FAIL WIT-007-2026-08-23 PROD-I-7 defects=1
     qualification lacks semantic_task_observed
```

That is correct, and it is the finding. `PROD-I-7` requires a watched task whose
success a fresh witness can judge. No such task is declared. The conformance
suite establishes structural conformance - `check_i1` and `check_i2` are
required-field presence - and `FOUND-007` names "schema validity is reported as
semantic competence" as a defeating case. Reporting `semantic_task_observed` as
true would have been that defeat.

### What this means for standing

`SPEC.md` has earned `BUILT` and cannot yet earn `WITNESSED`. The gate is not
owner judgement. It is `O8`, "What observation completes semantic cold-start
beyond schema validity?", which has been open since the founding and is the
question that would declare the missing task.

`O10` cannot be legitimately ruled before that. This scenario remains `SEED`
because it has been executed and not yet satisfied.
