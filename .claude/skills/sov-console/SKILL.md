---
name: sov-console
description: Domain know-how for the Soveraeign console domain - the services/console chartered boundary (Console Service). Load when a task mentions "sov-console", "console domain", "Console Service", "operator session", "thread", "post", "notification", "judgement request", "operator setting", "dashboard projection", "activity view", "human in the loop", "human on the loop", or names the artifacts CHARTER.md, README.md, contracts/service.json, or conformance/ seed fixtures under services/console. Covers charter gap closure, schema refinement, seed-fixture authoring, doc coherence, sibling read-path precondition mapping, and Human Binding interface declaration while O18 keeps implementation queued. Not for the Asset Service, Proofing Service, kernel contracts, conformance oracle, byom, or governance work - those have sibling sov-* skills.
---

# sov-console

## Purpose

Advance the Console Service boundary of the Soveraeign repository - charter,
record contracts, seed fixtures, and a declared (not implemented) Human Binding
interface - without crossing the protected boundary that forbids runtime code
before a ratified logical spec and executable defeating fixtures. The domain
governs the operator-facing session inside a local Node: what needs an
operator's attention, what an operator prefers, what is waiting on a human
right, and what has happened across the node's services. It surfaces pending
rights and spent judgement; it never holds, infers, or delegates a right, and
its dashboards and activity views are rebuildable projections whose every
value resolves to an authoritative record.

## Owns / Must not

Owns: `services/console/` - one bounded lifecycle, its contract drafts, and
seed fixtures. Owned domain records (per CHARTER.md and contracts/service.json):
operator-session, channel, thread, post, notification, judgement-request,
operator-setting, projection-view, console-receipt. Declared operations:
open-session, close-session, open-channel, open-thread, post, notify,
acknowledge-notification, request-judgement, resolve-judgement, set-setting,
rebuild-projection. Declared ports: human-binding, model-binding,
service-activity, delivery, federation.

Must not: implement runtime code before O18 ratification plus logical spec and
defeating fixtures (`no_runtime_code_before_logical_spec_and_defeating_fixtures`);
implement a binding before the shared transition contract is frozen or Bdo
authorizes a provisional target (`bindings/README.md`); write Asset Service or
Proofing Service state (the crossing is read-only); let a setting, session,
dashboard role, or thread state widen an authority check; let a model resolve
a judgement request; block the node on a judgement request or hide a pending
right; treat a projection or a notification as the record it points to; write
service state from a dashboard edit; report external delivery or cross-node
activity as anything but `UNCONFIGURED`; rewrite or erase a post,
notification, or request instead of countering it; let an executor's or
renderer's report count as observation; modify `lineage/evidence/`; create
`EXTERNAL_WORLD` effects; run `git commit` or `git push`.

## Key files

- `services/console/CHARTER.md` - role, Phase-I requirement mapping, owned
  records, proposed lifecycles and loop modes, sibling and kernel integration,
  human and model participation, proving narrative, defeating cases, deferred
  scope.
- `services/console/README.md` - four implementation gates; no placeholder
  code.
- `services/console/contracts/service.json` - owns/references/operations/
  uses_kernel_contracts/ports/forbids declaration, standing `PROPOSED`.
- `services/console/conformance/` - declarative seed fixtures CONS-001..007
  (`001-judgement-request-never-blocks.yaml` through
  `007-activity-view-declares-omissions.yaml`) in the PROOF-001 shape that a
  future participant must satisfy; no runtime code.
- `services/console/contracts/*.schema.json` - eight proposed record schemas:
  operator-session, channel, thread, post, notification, judgement-request,
  operator-setting, projection-view.
- `decisions/0014-console-service-boundary.md` - boundary decision, PROPOSED.
- `bindings/README.md` - binding parity requirements and the admission rule
  for any binding implementation.
- Governing set: `AGENTS.md`, `STATUS.yaml`, `CLASSIFICATION.md`, `SPEC.md`,
  `PRD.md`, `CONTRACT.md`.

## Standing and blockers

- `console_service_status: CHARTERED_NOT_IMPLEMENTED` (STATUS.yaml).
- O18 - "Is Console Service the accepted third service boundary under that
  name, and does Bdo authorize a provisional Human Binding target for it ahead
  of O10?" - blocks `console_implementation`. Per decision 0014 it bundles: whether
  the console is the accepted third boundary; whether `Console` is the
  accepted name (alternatives `Session`, `Operator`); and whether Bdo
  authorizes a provisional binding target ahead of O10. All implementation
  requests are refused and queued as judgement items for Bdo.
- O2 - engineering baseline ratification - blocks `production_implementation`.
- O10 - SPEC.md ratification - blocks `f1_closure`.
- Protected boundary `no_runtime_code_before_logical_spec_and_defeating_fixtures`
  applies to the service and to its bindings alike.
- `bindings/README.md`: no binding implementation is admitted until the shared
  transition contract is frozen or explicitly authorized as a provisional
  target. Interface declaration is allowed; realization is not.
- Judgement-typed questions queue for Bdo; they never block bounded doc,
  contract, or fixture work and are never silently decided by an agent.

## Named operations (available now)

1. Charter gap closure: reconcile `CHARTER.md` with the `CLASSIFICATION.md`
   service map, the SPEC.md Projection rule and Interface parity, and
   decision 0014, preserving the proving narrative and defeating cases.
2. Schema refinement against SPEC.md: draft or align record schemas under
   `services/console/contracts/` for the owned records (JSON Schema Draft
   2020-12) with SPEC.md object shapes - `EventEnvelope`, `Receipt`,
   `AuthorityGrant`, standing, actor attribution - as proposals.
3. Seed-fixture authoring and tightening: turn CHARTER.md proving-narrative
   steps and defeating cases into declarative positive and defeating seed
   fixtures under `services/console/conformance/` (payloads a future
   participant must satisfy or refuse), without runtime code.
4. Doc coherence: align `README.md`, `contracts/service.json`, and
   `CHARTER.md` vocabulary, owned records, operations, ports, forbids, and
   cross-references with `CLASSIFICATION.md` and decision 0014.
5. Sibling read-path precondition mapping: record exactly what the Asset
   Service and Proofing Service event and receipt streams must stabilize
   before the console can project them without direct database access
   (README gate 3), as a proposal.
6. Human Binding interface declaration: declare under `bindings/` the
   interface the console Human Binding realizes - the operations it invokes
   and the state, choices, authority, provenance, and receipts it must expose
   - with the Model Binding reading the same records as typed structure. A
   declared interface only; no implementation.
7. O18 judgement-queue drafting: write the precise O18 ratification question
   set for Bdo (boundary, name, provisional binding target) with the evidence
   paths a decision needs.

## Verification

- `python scripts/verify.py` - required, from repo root, three-second budget.
- `python scripts/lint.py` - hygiene, module size, secret shapes.
- `python -m json.tool services/console/contracts/service.json` (and any
  `.schema.json` or fixture `.json` file added) - JSON syntax check per file.
- No `services/console/tests/` exists yet by design; do not create test
  scaffolding that implies implementation before O18.

## Vocabulary (exact; no synonyms)

- Repository artifact standing: `OPEN -> BUILT -> WITNESSED -> RATIFIED`.
- Record standing: `RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`.
- Event outcome: `ATTEMPTED | COMMITTED | FAILED | REFUSED | COUNTERED |
  UNRESOLVED`.
- Attestation outcome: `REPRODUCED | DISSENTED | UNATTESTABLE`.
- Effect class: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD`.
- Service manifest standing: `PROPOSED`.
- Proposed lifecycles (CHARTER.md; service policy awaiting owner
  ratification; they do not replace the shared record standings):
  operator session `OPEN -> CLOSED`; thread `OPEN -> ARCHIVED`;
  judgement request `QUEUED -> RESOLVED | WITHDRAWN | EXPIRED`;
  notification `ISSUED -> ACKNOWLEDGED`.
- Proposed loop modes for a judgement request (CHARTER.md): `IN_LOOP` - the
  conditioned operation stays `UNRESOLVED` until a human right resolves it;
  `ON_LOOP` - the operation proceeds; the human watches and may counter
  through retraction.
- Notification kinds (proposed, `notification.schema.json`): `MENTION`,
  `ASSIGNMENT`, `JUDGEMENT_REQUESTED`, `JUDGEMENT_RESOLVED`,
  `RECEIPT_OUTCOME`, `COUNTERED`. Delivery: `LOCAL` only in Phase I.
- Projection view kinds (proposed, `projection-view.schema.json`):
  `DASHBOARD` (administrative, scoped-grant read) and `ACTIVITY`; every view
  carries `authoritative: false`.
- Charter outcome and actor terms: `UNRESOLVED` receipt for a
  judgement-conditioned operation; `REFUSED` for a model resolution attempt;
  `UNCONFIGURED` for the delivery and federation ports; `SYSTEM` actor for
  notification emission; `JUDGEMENT` authority type.
- Roles: Operator, Actor, Worker (report is not observation), Witness,
  Binding, Adapter, Projection (never authoritative by convenience).
- Information roles: Proposal, Recording, Receipt, Observation, Retraction.

## Report format

Report: files changed (repo-relative paths); checks observed (exact commands
with exit codes); standing proposals (own work supports at most `BUILT`; a
build report cannot witness itself); judgement items queued for Bdo; next
bounded operation.
