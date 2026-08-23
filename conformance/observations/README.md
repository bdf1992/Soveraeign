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

## FOUND-007 · second run, after the semantic task existed

`FOUND-007-rerun-observation.json`, against revision
`ec0427ad08b0` on a clean clone of `main`.

The first run was refused for the right reason. Decision 0021 declared the
semantic cold-start task, `FOUND-010`, and `custody.py` implemented the
`read-version` operation the service contract had always claimed. With a task to
observe, the same procedure was performed again from a fresh clone: authority
located, conformance suite executed, every verdict reconstructed, and the
semantic task run and held.

```
PASS  WIT-007-2026-08-23-B  PROD-I-7  defects=0
```

`PROD-I-7`, independent qualification, is satisfied. `SPEC.md` is therefore
proposed at `WITNESSED`, which is a proposal supported by this observation and
not a ratification: a witness can support a standing proposal and can never
ratify one.

Read the suite line on that run carefully. `SUITE FAIL cases=1 coverage_gaps=8`
is not a failure of this case. Submitting one participant observation leaves the
other eight requirements without one, and the runner reports that absence as
missing coverage. The case itself passed with zero defects.

**O10 is now legitimately askable.** It was not before, and that was the whole
problem: the owner was being asked to ratify a document that had skipped two
standings, which this repository refuses everywhere else as `SKIPPED_STANDING`.
