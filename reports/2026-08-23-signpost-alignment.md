# Signpost alignment and the first kernel move, 2026-08-23

Status: `BUILT · SELF-TESTED · NOT WITNESSED · NOTHING RATIFIED`

Bdo directed two operations in order: align the signposts that disagree about what happens
next, then work the foundation. Both landed. One session did the work and wrote this report,
so it is `BUILT` evidence and not a witness (`AGENTS.md` Authority).

## Change protocol record

1. **Requested outcome and current state.** Four signposts named a different next action.
   `README.md` step 5 pointed at the `ROADMAP.md` gate and its objective list put the shared
   kernel last; `STATUS.yaml` declared `F0_FOUNDING_CLOSURE`; the epic projection made `#6`
   the only reachable ticket; `ENGINEERING.md` named the same job "split `core.py`". One job
   carried five names and no document connected them.
2. **Affected.** `ROADMAP.md` (new crosswalk section), `README.md` (step 5, immediate
   objective, repository-state list), `scripts/sov_next.py` and its tests,
   `scripts/sov_kernel.py` and its tests, `contracts/kernel-transitions.json`,
   `scripts/verify.py` (two checks added). No governing rule moved owner.
3. **Preconditions and expected observable result.** Before: `verify.py` green at 1.185s,
   no reconciliation check, transition contract prose-only. Expected after: one command
   naming the reachable job with every alias, a gate that refuses when a crosswalk row stops
   resolving, and a machine-checkable projection of the `SPEC.md` transition table.
4. **Effect class.** `RECORD_LOCAL`.
5. **Rollback.** Revert the six files and remove the two `verify.py` entries. No contract
   semantics, standing, or open decision changed.

## Alignment

`ROADMAP.md` gained a Name crosswalk. It is the only place the identity of a job across
vocabularies is asserted, because that assertion is judgement and belongs in the document
owning phase vocabulary — not in a script that would appear to derive it.

`scripts/sov_next.py` reads `STATUS.yaml`, `ROADMAP.md`, the epic projection,
`ENGINEERING.md`, and the `diagrams/` provenance headers, and prints one answer:

```text
== reachable work ==
  #6 [NOW] Shared Kernel — govern legal transitions
      phase   `F3` Minimal local kernel
      debt    `SPEC.md` transition contract, projected to
              `contracts/kernel-transitions.json`
      drawn   `K` in `diagrams/crossing-topology.md`
```

It deliberately does not resolve the declared-gate disagreement. `STATUS.yaml` names a
document gate and the projection names a code ticket; both lanes may be legitimate and
ranking them is owner judgement. The tool reports the conflict and exits zero.

The gate refuses only on a crosswalk row that stops resolving — a renamed phase, a missing
diagram, a dropped ticket reference. A stale view and a gate disagreement are reported and
never fail the build, because neither is a defect and an alarm that fires on non-defects is
one operators learn to clear unread.

`README.md` now points at the command instead of asserting an order, and its immediate
objective states two lanes rather than one ranked list.

## The first kernel move

`SPEC.md` fixes fourteen legal transitions in a prose table. Prose cannot be checked, so
`scripts/sov_kernel.py` derives `contracts/kernel-transitions.json` from it — fourteen
transitions, seventeen named refusal codes, three admitting an open reasoned refusal.

The projection holds no standing. `selfcheck` re-derives from `SPEC.md` and refuses when the
two disagree, naming the exact field and the repair. Observed against a deliberate edit:

```text
FAIL: SPEC.md moved: projection records ef6264c4b5734e59, SPEC.md is now b7dd174be02736ad
FAIL: read_source.preconditions: projection disagrees with SPEC.md
```

One invariant is worth naming: a transition declaring neither a refusal code nor an open
reasoned refusal is a defect. A transition that cannot refuse cannot gate.

## Checks observed

`python scripts/verify.py` from a clean root, all checks passing in 2.189s against the
3.000s budget. 141 repository tooling tests, of which 41 are new here — 19 for the
reconciler and 22 for the kernel projection, each with its defeating case.

The budget is worth watching: it was 1.185s earlier today and is now 2.189s, 73% consumed.

## Residuals

- **The kernel is contracts, not a module — corrected after this report's first draft.** The
  first draft recorded "the kernel has no home" and queued a directory decision. The priors
  answer it: `CLASSIFICATION.md` files the shared kernel under cross-cutting foundations
  rather than the System/Node/Service/Component ladder; the epic tree already assigns bit
  `#6` the stub `#25` at `contracts/`; `ENGINEERING.md` places kernel *contracts* in the
  dependency chain; `contracts/README.md` disclaims programming-language classes; and
  `PRD.md` PROD-I-9 forces it — two materially different model bindings cannot share a
  Python package. No directory decision is owed. The kernel is implemented once per service
  and its sameness is proven behaviourally.
- **Every diagram view is stale.** Eight of eight, including the two crossing views authored
  today, because `SPEC.md`, `PRD.md`, `CLASSIFICATION.md`, and `STATUS.yaml` all moved. Most
  are flagged and correct — the reproduction-versus-applicability split registered as O4.
- The projection covers the transition *table*. `SPEC.md` requirement predicates and object
  field lists remain prose.

## Judgement queue for Bdo (nothing decided)

1. **Which lane leads — `F0` or `F3`?** `STATUS.yaml` declares the document gate; the epic
   projection makes `#6` the only reachable ticket. The reconciler reports the disagreement
   and refuses to rank it. Ranking is owner judgement and no document currently holds it.
2. **O4 still gates the staleness half.** Reproduction-only drift detection now runs in the
   gate as a report. Whether a drifted view is *wrong* remains unanswerable, so all eight
   views read stale while most are correct.

## Corrected in this report

An earlier revision queued a third item claiming nothing enforced kernel sameness, because
the conformance oracle had never been bound to a participant. That was wrong. The oracle has
been bound since 2026-08-22: `services/asset/conformance/README.md` documents the command and
`BASELINE.md` records the result — all nine requirements `FAIL`, which that file calls the
implementation work surface, not a defect in the binding. The error came from invoking the
oracle without `--cases conformance/scenarios.json`, which graded participant observations
against the control fixtures; `INVALID` correctly meant "cannot grade", and was misread as
"unbound".

`scripts/sov_baseline.py` now runs the documented comparison inside the verification gate and
refuses on divergence from the record in either direction, so the same misreading cannot
recur silently. What remains open is the participant's repair, not the binding.

## Next bounded operation

- **asset** — repair the participant against its nine recorded failures. The oracle proves
  kernel sameness and is already bound; the failures are the work surface.
- **asset** — split `core.py` by owned responsibility. This aligns one service to the kernel
  contracts; it is not itself kernel construction.
- **diagrams** — refresh the eight stale digests, and the `O14` reference in `service-map.md`
  that the renumber to O18 invalidated.
