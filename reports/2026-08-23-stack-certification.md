# Phase-I stack certification, 2026-08-23

Status: `OBSERVED · NOT WITNESSED · NOTHING RATIFIED`

Bdo asked for a Tech Spec derived from `PRD.md` and `SPEC.md`, a certified stack, and the
crossings diagrammed. This report holds the stack evidence. The Tech Spec landed as the
`ENGINEERING.md` Realization map and Crossing realization sections; the crossings landed as
`diagrams/crossing-typology.md` and `diagrams/crossing-topology.md`.

One session did the reading, the running, and the writing. That is enough for `BUILT`
evidence about code it did not author, and it is not a witness. `AGENTS.md` Authority: a
build report never witnesses itself, and only Bdo ratifies. Nothing here answers O2.

## Goal

`ENGINEERING.md` names ten stack rows. Each is a claim. This operation asks one question per
row — *is this exercised by something that runs today, or is it an intention?* — and answers
it from observation rather than from the document restating itself.

## Checks observed

`python scripts/verify.py` from a clean root, on `feat/federation-harness-and-hardening`:

```text
repository hygiene              PASS  172 text files, 23 Python modules, 1 named debt   0.144s
bootstrap and locked evidence   PASS  128 checks                                        0.043s
conformance oracle controls     PASS  cases=20 coverage_gaps=0                          0.042s
conformance oracle tests        OK    17 tests                                          0.108s
Sov context profile             OK     5 tests                                          0.162s
Asset Service reference tests   OK     5 tests                                          0.437s
repository tooling tests        OK    28 tests                                          0.249s

TOTAL                           PASS  55 tests in 1.185s against a 3.000s budget
```

The oracle's ten `-DEF` lines report `FAIL`, which is the expected verdict. `conformance/run.py`
compares each case against its declared `expected_oracle`; a defeating fixture the oracle
failed to defeat would raise `oracle_mismatch` and fail the suite. It did not.

## Row-by-row

| Stack row | Verdict | Evidence |
| --- | --- | --- |
| Language: Python 3.11+ | **certified** | `requires-python = ">=3.11"`; CI matrix runs 3.11 and 3.12; observed 3.12.10 |
| Runtime dependencies: stdlib first | **certified** | 26 distinct module-level imports across 23 modules; zero third-party |
| Machine contracts: JSON Schema 2020-12 | **certified** | every schema document declares `draft/2020-12`; `service.json` files are instances governed by `contracts/service-manifest.schema.json` |
| Human control files: Markdown, small YAML | **certified** | 172 text files pass hygiene; no parallel semantic contract in YAML |
| Tests and lint: `unittest`, dependency-free, under three seconds | **certified** | 55 tests, seven checks, 1.185s — 61% of budget unused |
| Immutable payload custody: filesystem CAS, SHA-256 | certified, one participant | `blobs/sha256/`; digest re-verified on read at `core.py:259` |
| Search and graph: rebuildable projections | certified, one participant | `search_projection`, `graph_projection`, rebuilt by `rebuild_projections` |
| Local surface: Python API and CLI | **partial** | one binding exists; `PRD.md` two-binding proof needs a human surface and two model surfaces |
| Operational record: append-preserving events and receipts in transactional SQLite | **not certified** | `sqlite3` appears in exactly one module. Twelve tables serve the Asset Service lifecycle; no kernel-level append-preserving Event Envelope journal exists. Declared: `KNOWN-GAPS.md` "Operational journal" |
| Model execution: Model Binding plus Model Adapter | **not certified** | `bindings/` and `adapters/` hold README files and a profile skeleton. No adapter executes. `invoke_model` has no implementation. Declared: `KNOWN-GAPS.md` "Model portability" |

Five rows certify cleanly, two certify against a single participant, one is partial, and two
are intentions. Both non-certified rows are the ones `PRD.md` PROD-I-8 and PROD-I-9 depend on.

## Defeating evidence

Two findings that no document currently carries.

**The module budget does not reach the oracle.** `conformance/run.py` is 332 lines against
the 300-line production limit, and passes. `scripts/lint.py:86` sets `is_production` from
whether the path is under `/src/` or begins with `scripts/`, and the oracle is under neither.
It is exempt by path shape, not by the declared reason `ENGINEERING.md` requires. `core.py` at
341 lines is caught and named as debt; the oracle at 332 is not caught at all. The most
semantically load-bearing module in the repository is the one the budget cannot see.

**Four of six diagrams are stale and nothing reports it.** `diagrams/README.md` specifies a
`source_digest` per view so "a stale diagram is detectable rather than merely suspected", and
defers the check to `scripts/lint.py` "once these views are generated rather than authored".
Run by hand against current bytes:

```text
authority-typing.md         STALE  STATUS.yaml
event-outcomes.md           STALE  CLASSIFICATION.md
requirement-lifecycle.md    STALE  STATUS.yaml
service-map.md              STALE  CLASSIFICATION.md, STATUS.yaml
source-reader-recording.md  ok
standing-transition.md      STALE  CLASSIFICATION.md
```

The mechanism works — `CONTRACT.md`, `SPEC.md`, and `PRD.md` digests all still match their
recorded values, so this is real drift and not a broken check. `service-map.md` additionally
renders Console as `chartered, not built — O14`, and the merge renumbered Console to O18.

## Residuals

- The oracle has never validated the reference participant. Binding them yields 20 `INVALID`
  and 9 coverage gaps: the oracle indexes by `CONF-I*-POS`/`-DEF`, the Asset Service emits
  `RUN-I*`. `STATUS.yaml` carries this honestly as
  `conformance_status: EXECUTABLE_ORACLE_CONTROLS_PARTICIPANT_BINDING_OPEN`. Until it closes,
  every certified row above is certified against hand-authored controls only.
- Coverage is per requirement, not per predicate. Ten positive/defeating pairs cover nine
  requirements; `SPEC.md` declares 25 predicates across 14 transitions and its Conformance
  boundary asks for a pair per predicate. `ROADMAP.md` F2 exit is not met.
- The root workspace is unpackaged, so the 3.11 floor is enforced by the Asset Service
  `pyproject.toml` and the CI matrix, not by anything at the root.

## Judgement queue for Bdo (nothing decided)

1. **O2 stands, better evidenced.** Two of ten rows are unexercised, and both are load-bearing
   for PROD-I-8 and PROD-I-9. Ratifying the baseline now ratifies two intentions along with
   eight observations. Deferring O2 until an adapter executes is also a position. This report
   takes neither.
2. **Does the module budget apply to `conformance/`?** Either the lint production rule widens
   to reach it, or the oracle earns a named exemption with a reason. Silence is the current
   answer, and it is the one option `ENGINEERING.md` does not offer.
3. **Should diagram staleness gate?** `diagrams/README.md` anticipates the check but defers it
   to generation. Four views are stale today and the gate is green.

## Next bounded operation per domain

- **conformance** — close the participant binding: align observation `case_id` values with the
  oracle's, or give the oracle a declared participant-case mapping. This unblocks every
  certification claim above.
- **verification** — decide finding 2, then either widen the production rule in
  `scripts/lint.py` or record the oracle exemption.
- **diagrams** — refresh the four stale `source_digest` values and the `O14` reference in
  `service-map.md`.
