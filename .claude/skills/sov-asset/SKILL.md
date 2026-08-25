---
name: sov-asset
description: Bounded work in the Soveraeign asset domain (Asset Service) under services/asset. Load when the task mentions "sov-asset", "asset domain", "asset service", or its concrete artifacts - services/asset/CHARTER.md, KNOWN-GAPS.md, contracts/service.json, soveraeign_asset_service (core.py, cli.py), test_walking_skeleton.py, conformance_observations.py, or the asset conformance BASELINE.md. Covers gap closure, fixture authoring, module splits, conformance observation, and doc coherence for this domain only - not the Proofing Service, kernel contracts, or the root conformance oracle.
---

## Purpose

Advance the Asset Service reference participant - custody, description,
transformation, relationship, discovery, and governed use of enterprise
assets - by one bounded operation at a time. The participant is
`BUILT_SELF_TESTED_NOT_WITNESSED`: its work surface is repairing observed gaps
against frozen contracts, never weakening the oracle to pass.

## Owns / Must not

Owns: the `services/asset` bounded lifecycle - charter, service contracts,
implementation under `src/soveraeign_asset_service/`, tests, `KNOWN-GAPS.md`,
and the domain conformance baseline record.

Must not: witness its own build claims (independent witnessing comes from
`sov-witness` or the conformance oracle, never asset builders); own or touch
another service's state; bypass kernel transitions to write authoritative state
(projections, adapters, and workers never become authoritative by convenience);
weaken `conformance/` scenarios or the oracle; add a runtime dependency without
a named boundary and decision record; import participant code into the oracle.

## Key files

- `services/asset/CHARTER.md` - role, boundary, first proving operation
- `services/asset/README.md` - status and run commands
- `services/asset/KNOWN-GAPS.md` - observed gaps vs proposed SPEC (work surface)
- `services/asset/contracts/service.json` - service contract (owns/operations/forbids)
- `services/asset/contracts/ai-native-asset-service.yaml` - narrative contract
- `services/asset/src/soveraeign_asset_service/core.py` - participant (over 300 lines; named gap)
- `services/asset/src/soveraeign_asset_service/cli.py` - CLI binding
- `services/asset/tests/test_walking_skeleton.py` - self-tests (BUILT evidence only)
- `services/asset/scripts/conformance_observations.py` - observation adapter
- `services/asset/scripts/demo.py` - local demo walk
- `services/asset/conformance/BASELINE.md` - observed FAIL baseline vs PROD-I-1..9
- `conformance/run.py`, `conformance/scenarios.json` - frozen root oracle (read-only here)

## Standing and blockers

`STATUS.yaml`: `asset_service_status: BUILT_SELF_TESTED_NOT_WITNESSED`. The
next standing transition is independent witnessing (`BUILT -> WITNESSED`) by a
non-builder; ratification is Bdo-only.

- The `ENGINEERING.md` baseline, `SPEC.md`, `CLASSIFICATION.md`, and the BYOM
  contract are all accepted (`decisions/0024-open-decision-drain.md`). Build on
  them. Follow the vocabulary exactly; do not fork it, and do not invent binding
  fields the model-binding contract does not declare.
- A gap fix is never Phase-I qualification. Qualification needs independent
  observation, which a builder cannot supply for its own build.
- Nothing in this domain waits on Bdo. Settle what evidence can settle and
  record what would defeat the ruling (`decisions/0033-close-the-founding-docket.md`,
  Ruling 1); the only owner hold is `PUBLIC-CLEARANCE`, which blocks public
  release and no engineering.

## Named operations (available now)

1. Gap closure: pick one `KNOWN-GAPS.md` row (e.g. visible `admit` transition,
   receipt completeness, observer independence) and repair the participant with
   fixtures first, oracle frozen.
2. Defeating-fixture authoring: add a positive and defeating unittest case
   under `services/asset/tests/` for an existing contract predicate.
3. Module-boundary split: split `core.py` by owned responsibility below 300
   lines while preserving the public participant contract (itself a named gap).
4. Conformance observation refresh: re-run the observation adapter against the
   frozen oracle and record the newly observed verdicts in
   `services/asset/conformance/BASELINE.md`.
5. Doc coherence: reconcile CHARTER/README/KNOWN-GAPS wording with
   `CLASSIFICATION.md` and `SPEC.md` vocabulary without changing semantics.
6. Acceptance packet: when a result is built and independently observed,
   assemble the six-part packet of `decisions/0023-acceptance-not-approval.md`
   over it. Never over work not yet done.

## Verification

- `python scripts/verify.py` (repo root; required gate, graded budget (PLATINUM 3 s, GOLD 6 s, SILVER 15 s))
- `python scripts/lint.py` (repo root; text, syntax, module size, secrets)
- `python -m unittest discover -s tests -v` (from `services/asset/`)
- `PYTHONPATH=src python scripts/demo.py` (from `services/asset/`)
- Conformance binding (from repo root):
  `PYTHONPATH=services/asset/src python services/asset/scripts/conformance_observations.py > <scratch>/asset-observations.json`
  then `python conformance/run.py --cases conformance/scenarios.json --observations <scratch>/asset-observations.json`

## Vocabulary (exact terms)

Asset; Asset version; Payload; Source; Recording; Proposal; Receipt;
Observation; Retraction; Projection; Worker (report is not observation);
Witness. Record standing: `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`.
Artifact standing lifecycle: `OPEN -> BUILT -> WITNESSED -> RATIFIED`. Event
outcomes: `ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED | UNRESOLVED`.
Attestation outcomes: `REPRODUCED`, `DISSENTED`, `UNATTESTABLE`. Effect
classes: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD` (no external
effects in Phase I). Do not invent synonyms for any of these.

## Report format

Files changed (repo-relative paths); checks observed (exact commands and exit
codes); standing proposals (at most `OPEN -> BUILT`; witnessing belongs to an
independent witness, ratification to Bdo); judgement items queued for Bdo; next
bounded operation.
