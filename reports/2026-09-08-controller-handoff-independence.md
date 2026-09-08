# Controller handoff · the independence definition and its walk

For a controller picking this up cold. Read this, then check the suggestions yourself — every
claim below names the command that settles it. Nothing here is authority and nothing here is
witnessed.

**Read-in cost: this file, plus `decisions/0104` if you are ruling on it. Nothing else is
required to verify what follows.**

## What happened, in five lines

Bdo asked what "independent" means for an observer. It now has an answer: an observer is
independent when it holds nothing the subject's construction produced *and* is not a version of
an actor that produced it — context and perspective, two axes, neither substituting for the
other. That is `decisions/0104`, `PROPOSED`. The Observation Service's five-edge walk became
seven across those axes, scoped to the subject's standing lifecycle rather than one run. Three
independent witness passes read it. All three dissented.

## Standing, so nobody reads this as progress

| Subject | Standing | Where |
| --- | --- | --- |
| `decisions/0104` | `PROPOSED` | its own header |
| The seven-edge walk | `BUILT`, self-tested, **not witnessed** | `STATUS.yaml` |
| The Observation Service | demoted this session, from `WITNESSED` | `contracts/status-claims.json` |

The demotion is the honest part: the passes that earned the old `WITNESSED` had read a walk
that no longer exists. `python scripts/sov_standing.py` now reads zero witnessed claims
repository-wide, which is correct and was previously not so.

## The three passes, and why the third matters most

Each pass defeated the previous repair, in a new place, in the same shape: a datum the record
did not carry, or could not read, answered "no" instead of "cannot say".

- **Pass 1** (`witness/independence-context-perspective.md`) — five records the manifest
  forbids reached `INDEPENDENT`.
- **Pass 2** — the decision record claimed one module with one reading while two edges compared
  raw ids; the decoy repair made admission *fall* as the record grew.
- **Pass 3** — the executor can corroborate a decoy it moved itself; the id re-derivation
  proved nothing; and the structural finding below.

Pass 2 and 3's records, and both dispositions, are in
`reports/2026-09-08-independence-repairs.md`. Their probes are checked in at
`witness/probes/probe_independence_walk.py` and `probe_independence_declared.py` — run them.

## The finding a controller should not let get buried

`decisions/0100` has a builder launch its own witness. So the builder writes the `LAUNCH`
entry. So **the executor authors every field the walk reads to establish the observer's
independence**: `context_passed`, `predicates_source_kind`, `predicates_source_actor`,
`subject_id`, `lease`, and the profile digest that carries the frame. `RunRecord.profile_of`
resolves that digest against nothing.

Ruling 3 says a rename cannot defeat a frame. It cannot. The executor typing a different digest
does. Ruling 3's safeguard — "the launcher is not the observer" — stops the observer vouching
for itself and leaves the executor vouching for the observer.

`CHARTER.md` now states the property the walk has rather than the one it asserted: **it detects
carelessly recorded dependence; it does not detect declared independence.**

## The four suggestions to check, and how

Each is the builder's judgement, not a ruling. Check them; do not inherit them.

**S1 — the fix is that a `LAUNCH` entry must not be authored by the executor.**
Check: read `services/observation/src/soveraeign_observation_service/record.py`, `profile_of`
and `launches`. Ask what a third-party-authored entry would have to carry, and whether the
Record Service can even express "written by someone other than the subject's executor" today.
Falsified if a cheaper fix exists inside this boundary — if it does, the builder missed it.

**S2 — the walk now refuses too much, and that is close to disqualifying.**
`_walk_lifecycle` in `lifecycle.py` refuses any candidate the record shows moving another
subject, and on a real journal most actors carry no profile, so the refusal fires broadly.
Check: build a journal slice resembling a real one and count admissions. A check that refuses
nearly everything carries almost no information. The builder chose fail-closed over admitting a
subject's own builder as its witness; that trade is reversible and is `KNOWN-GAPS.md` row 3.

**S3 — two of the nine queued judgement items matter and seven are bookkeeping.**
The two: whether Ruling 3 conflicts with `decisions/0100`, and whether showing the walk more
record may ever reduce admission (which changes what `record_completeness` means, and that term
is `SPEC.md`-adjacent). Check the full queue at the foot of `decisions/0104` and disagree freely
— this ranking is the builder's.

**S4 — this should not have landed to `main` under the standing grant, and did not.**
`python scripts/sov_land.py plan` refuses `AUTHORITY_REFUSED`: the change carries
`decisions/`, `STATUS.yaml`, `AGENTS.md`, `CLAUDE.md` and `.clarity/coverage.json`, all outside
`grant:standing-landing-loop`. Bdo directed the landing in session on 2026-09-08 as the owner
act that path requires. Check: re-run `plan` and read the refusal yourself.

## What a controller should distrust about this handoff

The builder wrote it, and the builder made four false claims in governing documents during this
concern — including citing a report that existed in no commit, and asserting a repair complete
while two edges still had the defect. Every one was caught by a witness and none by a gate.
Treat the "how to check" column as the load-bearing part of this file and the prose as a lead.

## Commands

```
python scripts/verify.py                      # 52 checks, PASS at the landed commit
python scripts/lint.py                        # PASS
python scripts/sov_standing.py                # zero witnessed claims, which is correct
python conformance/run.py                     # 34 cases, PASS
python witness/probes/probe_independence_walk.py
python witness/probes/probe_independence_declared.py
cd services/observation/tests && python -m unittest test_thin_slice test_contract_shapes test_kernel_parity
```

Verify's exit 0 does not mean conformance (`CLAUDE.md`, trap T2). None of the three passes'
findings was ever visible to it.

## Next bounded operation

Not another repair pass. Either Bdo rules on the Ruling 3 / `decisions/0100` conflict, or a
controller opens a concern against the Record Service for a `LAUNCH` entry whose author is not
the subject's executor. Repairing further inside `services/observation` moves where a
declaration is read, which is what the last three rounds did.
