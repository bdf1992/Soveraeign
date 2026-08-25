# O18 ratification packet · Console Service first slice

Status: `PROPOSED · OWNER RATIFICATION PENDING`

This packet puts open decision O18 in front of Bdo as three yes-or-no questions, shows where the
evidence sits in the working tree, and says plainly what a yes or a no does. It is a Worker
proposal, not Bdo's judgement, and it witnesses nothing it cites (`AGENTS.md`, Authority).

How to read it: each question is one sentence. Answer yes or no. Nothing else is asked of you.

## Owned scope

Owned: the O18 text as written, its split into parts, the name question from `decisions/0014`,
the evidence paths, the consequences each answer directly entails, and three further questions
the workers hit while drafting. Not owned: any answer; any edit to `STATUS.yaml`, `decisions/`,
`services/console/`, or `bindings/`; any runtime code; any claim of `WITNESSED` or `RATIFIED`
standing for itself or for anything it cites.

## The question as written

`STATUS.yaml`, `open_decisions`, id O18, verbatim:

> Is Console Service the accepted third service boundary under that name, and does Bdo authorize a provisional Human Binding target for it ahead of O10?

It is cited here and throughout by its id, O18; what it blocks is `STATUS.yaml`'s field to
name. The service's current state is `console_service_status: CHARTERED_NOT_IMPLEMENTED`
(`STATUS.yaml`, `console_service_status`).

That sentence is two questions joined by "and". `decisions/0014` adds a third, the name. Below
they are split so each can be answered on its own.

## Question 1 · the boundary

**Q1. Is the Console Service accepted as the third service boundary of a Node?**

What this means. A "service boundary" is one fenced-off part of the system that owns its own
records and nobody else's. Two exist already: the Asset Service and the Proofing Service. This
asks whether the operator-facing session (sessions, threads, posts, notifications, judgement
requests, settings, dashboards) gets its own fence as the third.

Where to look: `services/console/CHARTER.md` (Role; Owned domain records);
`services/console/contracts/service.json` (`owns`, `operations`, `ports`, `forbids`);
`decisions/0014-console-service-boundary.md` (Decision; Constraints; Open authority).

## Question 2 · the provisional binding

**Q2. May a local CLI for the owner's judgement surface be built now, before SPEC.md is
ratified?**

What this means. A "Human Binding" is the surface a person uses to drive the system. "Provisional"
means Bdo lets one be built against the current `SPEC.md` transition table even though that
table is still waiting on O10 (`STATUS.yaml`, O10). The rule today is: no binding
implementation until the transition contract is frozen or Bdo explicitly authorizes a provisional
target (`bindings/README.md`, first section). This asks for that explicit authorization, for one
small target only.

The target, exactly: a local command-line tool over the Python API. No HTTP. No UI framework. No
graphical interface claim. Every effect is `RECORD_LOCAL`, meaning it writes local records and
touches nothing outside the machine (`services/console/CHARTER.md`, "First slice: the owner's
judgement surface (proposed)"; `bindings/console/interface.json`, `realization_target`).

What the slice does, in three steps: a judgement request reaches the owner's pending list
(`services/console/conformance/008-judgement-request-reaches-owner.yaml`); the owner answers it
through the CLI; the answer lands as a judgement-resolution record that can carry `RATIFIED`
standing (`services/console/conformance/009-owner-resolution-lands-ratified.yaml`).

Where to look: `services/console/CHARTER.md`, subsection "First slice: the owner's judgement
surface (proposed)" and its Defeating cases; `services/console/README.md`, "First slice
(proposed)"; `bindings/console/README.md`; `bindings/console/interface.json`;
`bindings/README.md`, Console section; `services/console/contracts/judgement-request.schema.json`;
`services/console/contracts/judgement-resolution.schema.json`;
`services/console/contracts/fixtures/judgement-request.fixtures.json`;
`services/console/contracts/fixtures/judgement-resolution.fixtures.json`.

## Question 3 · the name

**Q3. Is `Console` the accepted name for this service?**

What this means. `decisions/0014`, Open authority, lists two alternatives: `Session` and
`Operator`. A no here does not undo a yes on Q1; it only means the fence keeps its place and
gets a different label. Naming is Bdo's alone (`STATUS.yaml`, `authority.product_name`).

Where to look: `decisions/0014-console-service-boundary.md`, Open authority.

## Evidence paths

All of these are in the working tree this hour; several are uncommitted sibling work from today.

Console domain:

- `services/console/CHARTER.md`, subsection "First slice: the owner's judgement surface
  (proposed)" and the Defeating cases that follow it
- `services/console/README.md`, "First slice (proposed)" and the four gates
- `services/console/contracts/service.json`
- `services/console/contracts/judgement-request.schema.json`
- `services/console/contracts/judgement-resolution.schema.json`
- `services/console/contracts/fixtures/judgement-request.fixtures.json`
- `services/console/contracts/fixtures/judgement-resolution.fixtures.json`
- `services/console/conformance/008-judgement-request-reaches-owner.yaml` (CONS-008, reach)
- `services/console/conformance/009-owner-resolution-lands-ratified.yaml` (CONS-009, land)
- `bindings/console/README.md`
- `bindings/console/interface.json`
- `bindings/README.md`, Console section and the admission rule in its first section

Governing set:

- `OPEN-SEAMS.md`, S12 · Ratification mechanism (Bdo's 2026-08-23 input: a code-owner review
  click cannot be the owner's ratification surface)
- `PRD.md`, PROD-I-5 · Typed authority; PROD-I-6 · Founder judgement budget; "Two-binding proof"
- `SPEC.md`, Transition contract, row `ratify`: preconditions "proposal admitted; live matching
  authority grant"; commit "preserve history; add `RATIFIED` event"; refusal `AUTHORITY_REFUSED`
  or `STALE_STATE`
- `decisions/0014-console-service-boundary.md`
- `decisions/0016-github-coordination-registrar.md` (the code-owner review mechanism S12 is open
  on)
- `STATUS.yaml`, O18, `console_service_status`, `protected_boundaries`

## What a yes or a no does

### Q1, the boundary

If yes:

- `console_service_status` stays `CHARTERED_NOT_IMPLEMENTED`; ratifying the boundary changes only
  the standing word on the charter and decision, not the status. `decisions/0014`,
  Constraints, keeps runtime code behind the logical specification and executable defeating
  fixtures regardless of the boundary ruling, and `services/console/CHARTER.md`, Status, reads
  `PROPOSED SERVICE BOUNDARY · NOT IMPLEMENTED`: the two words are independent.
- `decisions/0014` and `services/console/contracts/service.json` become due for a Status update,
  recorded per `AGENTS.md` Implementation order step 6; this packet performs none.
- No code is admitted. The protected boundary
  `no_runtime_code_before_logical_spec_and_defeating_fixtures` still stands (`STATUS.yaml`,
  `protected_boundaries`).

If no:

- The charter, the nine record schemas, the nine seed fixtures, and the binding declaration stay
  proposals with no owner.
- S12 loses its chartered home: `OPEN-SEAMS.md` names the console charter as where the owner's
  ratification surface lives. A no means Bdo names a different home or none; this packet proposes
  none.
- Q2 is moot until a boundary exists to bind to.

### Q2, the provisional binding

If yes:

- It admits a local CLI only. No HTTP, no UI framework, no graphical interface, no transport
  (`bindings/console/interface.json`, `realization_target`).
- It unlocks three queued operations, in this order: CON-G1, the Python reference participant
  under `services/console/`; CON-G2, `bindings/console/cli.py`; CON-G3, `services/console/tests/`.
  Contracts and defeating fixtures come first in every one of them (`AGENTS.md`, Implementation
  order). CON-G1 to CON-G3 are the orchestrator's working names; they carry no `STATUS.yaml` id.
- The protected boundary still applies: executable defeating fixtures must exist before runtime
  code (`STATUS.yaml`, `protected_boundaries`; `services/console/README.md` gate 2). A yes opens
  gates 1 and 4 provisionally; it does not skip gate 2.
- Gate 3 of `services/console/README.md`, the Asset Service and Proofing Service event and
  receipt read paths being stable enough to project without direct database access, is not
  touched by a yes. The first slice projects only console receipts (CONS-009's `D-1` resolves
  to `RCPT-R`) and reads no sibling stream; gate 3 stays where it is for any later slice.
- O10 stays open. A provisional target is not a ratified `SPEC.md`; whatever the CLI realizes
  may have to move when O10 rules (`bindings/README.md`, first section).
- Nothing in it reaches `RATIFIED` by being built. The CLI produces records; Bdo's use of it
  under a live `JUDGEMENT` grant is what ratifies (`SPEC.md`, `ratify`).

If no:

- `bindings/console/` stays a declaration that realizes nothing; CON-G1 to CON-G3 stay queued.
- The owner's ratification surface waits for O10. Until then the only mechanism on record is the
  code-owner review click in `decisions/0016`, which Bdo has said cannot be the surface
  (`OPEN-SEAMS.md` S12). S12 stays open on the mechanism.
- Judgement requests can still be written as records by hand; none can be answered through a
  kernel transition with a receipt.

### Q3, the name

If yes: `Console` stands; no file changes. If no: the directory, manifest `service_id`, schema
`$id`s, skill, workflow, and decision title become due for a rename under Bdo's chosen word;
`product_name` and `repository_name` are not touched (`AGENTS.md`, Repository protections).

## Three more questions the workers hit

These came up while drafting the first slice. They have no `STATUS.yaml` id yet; Bdo numbers
them on ruling, or declines to. Each is one sentence.

**Q4. Is Bdo's `JUDGEMENT` grant for resolving judgement requests issued once, by Bdo, at node
founding, with the whole node as its scope?**

What this means. A "grant" is the record that says who may do what, where, and until when
(`SPEC.md`, `AuthorityGrant`: issuer, actor, type, capability, scope, budget, time, revocation).
The `ratify` row needs a live one. Somebody has to write Bdo's first grant; the only candidate
issuer on a one-person node is Bdo. CONS-009 assumes such a grant (`G-1`) exists and does not say
where it came from.

**Q5. Once the judgement-resolution record exists, is it the owner's ratification surface for
`STATUS.yaml` and `decisions/`, replacing the code-owner review click in `decisions/0016`?**

What this means. Today `decisions/0016` says ratification enters through a GitHub review on
`STATUS.yaml` and `decisions/`. S12 records that Bdo will not use GitHub for that. This asks
whether the console record is the replacement, so that a standing change in those files is
ratified when its judgement-resolution record carries `RATIFIED`, and not before. CONS-009's
defeating case `A-GH` (a GitHub approval that names no kernel record) already assumes the answer
is yes; it stays a proposal until Bdo says so.

**Q6. Is `ACCEPTED | STRUCK | DEFERRED` the vocabulary for an answered judgement request?**

What this means. The answer field on a judgement-resolution record has three allowed words
(`services/console/contracts/judgement-resolution.schema.json`, `decision`). `ACCEPTED` means
yes. `STRUCK` means no, and the question is closed. `DEFERRED` means not now, and the request
stays open. `SPEC.md` defines none of these words (`bindings/console/README.md`, Open questions).

## The machine-readable twin

Fixture `CONSOLE-JUDGEMENT-REQUEST-POS` in
`services/console/contracts/fixtures/judgement-request.fixtures.json` is this packet's twin in
record form: the O18 question, its digest, its `decision_ref` `STATUS.yaml#O18`, its evidence
addresses, and `addressed_to` Bdo, in lifecycle `QUEUED` and standing `RECORDED`. It records the
question. It is not a ruling, and its existence advances nothing. When a participant exists, that
fixture is the first request the owner's pending list should show.

## Standing

This packet is a Worker proposal and not Bdo's judgement. It proposes at most `OPEN -> BUILT` for
itself and awaits critique by a different agent. Nothing in it advances the standing of O18, the
Console Service, the binding declaration, or any fixture it cites.

## Source and authority

- `STATUS.yaml`, `AGENTS.md`, `OPEN-SEAMS.md`, `PRD.md`, `SPEC.md`, `bindings/README.md`,
  `decisions/0014-console-service-boundary.md`, `decisions/0016-github-coordination-registrar.md`,
  `services/console/`, `bindings/console/`; `CLASSIFICATION.md` for vocabulary.
- `RECORD_LOCAL`: this draft. `RESOURCE_CONSUMPTION`: one local `scripts/lint.py` run and one
  path-existence check, no network.
