---
name: sov-byom
description: Domain know-how for the Soveraeign byom domain - Bring Your Own Model bindings and adapters. Load when work touches BYOM.md, bindings/README.md, adapters/README.md, contracts/model-binding.schema.json, decisions/0011-local-personal-byom.md, PRD requirement PROD-I-9, or conformance scenarios 006-two-binding-parity and 008-model-portability. Trigger words: "sov-byom", "byom domain", "model binding", "model adapter", "data boundary", "model portability", "two-model fixture", "invoke_model". Not for asset, proofing, contracts-kernel, conformance-oracle, governance, or verification domain work - those have sibling sov-* skills.
---

## Purpose

Advance Soveraeign's Bring Your Own Model practice: one governed Model Binding
contract that admits materially different local or remote models without moving
authority, provenance, receipts, or custody. The binding contract is accepted
(`decisions/0024-open-decision-drain.md`, O12); an implementation still owes
independent observation before it is witnessed.

## Owns / Must not

Owns: `BYOM.md` practice; `bindings/` (operator realizations of declared
interfaces) and `adapters/` (translation to named external systems) boundary
documents; `contracts/model-binding.schema.json` alignment with the SPEC.md
`ModelBinding` object; PROD-I-9 model portability. Every invocation records
binding, adapter, provider, model, version, runtime, host, input projection,
data boundary, usage, and cost.

Must not: admit provider SDK types into kernel or service contracts; permit
silent provider fallback; let bindings or adapters make authoritative writes or
semantic forks (AGENTS.md directory boundaries: `/bindings` must not own
authoritative writes or semantic forks; `/adapters` must not own standing,
ratification, settlement, or hidden fallback); let model selection change
authority.

## Key files

- `BYOM.md` - the practice: personal-local pattern, binding/adapter boundary, data-boundary modes, portability test.
- `bindings/README.md` - operator bindings and the two-model parity requirement.
- `adapters/README.md` - declared adapter boundaries; Model provider row.
- `adapters/ollama/` - the first Model Adapter implementation: `capture.py` (attended runtime read), `inventory.json` (rebuildable projection), `adapter.py` and `validate.py` (binding, invocation, and parity checks), two declared bindings, sixteen fixtures, and `tests/`. Standing `BUILT`, self-tested, not witnessed; `decisions/0027-local-model-adapter.md`.
- `contracts/model-binding.schema.json` - proposed Model Binding schema (Draft 2020-12).
- `decisions/0011-local-personal-byom.md` - owner-directed decision and sources.
- `PRD.md` - PROD-I-9 "Bring your own model" and the "Two-binding proof" section.
- `SPEC.md` - `ModelBinding` object and the `invoke_model` transition with its refusal codes.
- `CLASSIFICATION.md` - Binding, Adapter, Operator, and naming rules.
- `STATUS.yaml` - `byom_status` and `local_model_adapter_status`.
- `conformance/founding-scenarios/006-two-binding-parity.yaml` and `008-model-portability.yaml`.
- `conformance/oracle-controls.json`, `conformance/scenarios.json`, `conformance/run.py`.

## Standing and constraints

- `byom_status: RULED_CONTRACT_STANDS_O12` (STATUS.yaml). The exact binding
  fields, the three data-boundary modes, and the two-model shape stand as a
  reversible default, not as owner acceptance: no packet exists for them and
  `decisions/0046-decision-queue-drain.md` says so outright. The counter that
  overturns O12 is a second adapter the declared fields cannot describe.
- `local_model_adapter_status: BUILT_SELF_TESTED_NOT_WITNESSED`. Accepting the
  adapter boundary (`decisions/0033-close-the-founding-docket.md`) did not witness
  the implementation; that needs an agent other than its builder.
- `no_runtime_code_before_logical_spec_and_defeating_fixtures` still binds: the
  defeating fixture comes before the code, every time.
  `no_external_effects_in_phase_i` always applies, and a remote crossing needs a
  declared adapter, data-boundary mode, input projection, authority, and receipt.
- Nothing here waits on Bdo. Settle what evidence can settle and record what would
  defeat it (`decisions/0033-close-the-founding-docket.md`, Ruling 1).

## Named operations (available now)

1. Gap closure: reconcile `contracts/model-binding.schema.json` field-by-field with the SPEC.md `ModelBinding` object and BYOM.md prose; record divergences as proposals.
2. Fixture authoring: draft positive and defeating binding instances against the schema (e.g., a silent-fallback or missing-provenance binding that must fail validation).
3. Portability fixture refinement: tighten FOUND-008 wording so each PROD-I-9 defeating case is individually testable on its own.
4. Defeating-case audit: check every PROD-I-9 defeating case has a matching control in `conformance/oracle-controls.json`; record gaps without weakening the oracle.
5. Acceptance packet: over a binding that is built and independently observed, assemble the six-part packet of `decisions/0023-acceptance-not-approval.md` - claim, visible result, evidence, why it matters, what could defeat it, owner action.
6. Doc coherence pass: align BYOM.md, bindings/README.md, adapters/README.md, and decisions/0011 with CLASSIFICATION.md vocabulary and cross-references.
7. Adapter witness: have a different agent verify `adapters/ollama/` through an independent path, above all whether the recorded inventory can be trusted as the custody authority.
8. Vocabulary drift scan: grep byom-owned files for synonyms of standing, event, effect, or role terms and propose exact-term corrections.

## Verification

- `python scripts/verify.py` (from repo root; required gate, graded budget (PLATINUM 3 s, GOLD 6 s, SILVER 15 s)).
- `python scripts/lint.py` (text, syntax, module size, secret shapes).
- `python conformance/run.py` (oracle self-controls; proves the oracle distinguishes positive and defeating narratives, does not witness a participant).
- `python conformance/run.py --cases conformance/scenarios.json --observations <path>` (participant binding form; derives defects from observation records, never trusts pass/fail claims).

## Vocabulary (exact terms)

- **Model Binding** - realizes the operator interface for a configured model; **Model Adapter** - translates that binding to a named runtime or provider; neither gains authority by operating.
- **Operator** / **Actor** / **Worker** / **Witness** per CLASSIFICATION.md; the model is the operator for an attributed run, the adapter is not.
- `data_boundary`: `LOCAL_ONLY | REDACTED_REMOTE | REMOTE_ALLOWED` (a maximum allowance, not permission by itself).
- `provider_kind`: `LOCAL | REMOTE`; `fallback_policy`: `NONE | EXPLICIT`.
- `invoke_model` refusals: `MODEL_UNAVAILABLE`, `MODEL_INCOMPATIBLE`, `DATA_BOUNDARY_REFUSED`.
- Information roles: **Proposal**, **Recording**, **Receipt**, **Projection**; model output enters as proposal or recording, never as authoritative state.
- Effect classes: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD` (refused in Phase I).
- Repository standing lifecycle: `OPEN -> BUILT -> WITNESSED -> RATIFIED`; record standing: `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`; attestation outcomes: `REPRODUCED | DISSENTED | UNATTESTABLE`.

## Report format

- files_changed: exact repo-relative paths.
- checks_observed: commands run with exit codes and bounded output excerpts.
- standing_proposals: at most `OPEN -> BUILT` from a builder; `BUILT -> WITNESSED` requires an independent witness; only Bdo ratifies.
- judgement_items: questions queued for Bdo, stated as questions.
- next_bounded_operation: the single next operation, or none.
