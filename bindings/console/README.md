# Console Human Binding (declared, not implemented)

`interface.json` declares the interface the Console Service Human Binding
realizes: `urn:soveraeign:interface:console-owner-cli-v1`, binding kind
`HUMAN`, standing `PROPOSED`. It is the binding the console seed fixtures
call `HB-CLI` (`services/console/conformance/008-*.yaml`, `009-*.yaml`).

This directory holds a declaration and nothing else. There is no code here,
no Python module, and no realization. Read the admission statement at the end
before reading anything else as a promise.

## What it realizes

The first console slice in `services/console/CHARTER.md` ("First slice: the
owner's judgement surface"): the surface through which the owner receives a
judgement request, answers it, and has the answer land as a record that can
carry `RATIFIED` standing. The binding realizes the console's `human-binding`
port (`services/console/contracts/service.json`) over the shared transition
contract (`SPEC.md`, Transition contract).

Realization target: a local CLI over the Python API, the `Local surface` row
of `ENGINEERING.md` (Python API and CLI; human and model bindings use the
same kernel operations). No HTTP, no UI framework, and no graphical interface
claim. Every effect the binding can cause is `RECORD_LOCAL`.

## Operations

Each binding operation maps to a console manifest operation and, where one
applies, to a `SPEC.md` transition row. Reads are manifest operations and are
receipted like writes.

| Binding operation | Manifest operation | `SPEC.md` transition | Record | Refusals |
| --- | --- | --- | --- | --- |
| `open-session` | `open-session` | none (console proposal) | operator-session `OPEN` | reasoned refusal |
| `list-pending-judgement-requests` | `list-pending-judgement-requests` | none (console proposal) | judgement-request, lifecycle `QUEUED`, addressed to the operator | reasoned refusal |
| `show-judgement-request` | `show-judgement-request` | none (console proposal) | one judgement-request with question, evidence, and `decision_ref` resolved | reasoned refusal |
| `resolve-judgement` | `resolve-judgement` | `ratify` | judgement-resolution; request `QUEUED -> RESOLVED`; successor receipt | `AUTHORITY_REFUSED`, `STALE_STATE`; `REFUSED` for a `MODEL` actor |
| `acknowledge-notification` | `acknowledge-notification` | none (console proposal) | notification `ISSUED -> ACKNOWLEDGED` | reasoned refusal |
| `show-receipt` | `show-receipt` | none (console proposal) | one Receipt in the `SPEC.md` Receipt shape | reasoned refusal |
| `close-session` | `close-session` | none (console proposal) | operator-session `OPEN -> CLOSED` | reasoned refusal |

Notes on the table:

- The pending list is read from judgement-request records on a record read
  path, never from notification records or a projection-view (CONS-008). A
  setting, session state, unread cursor, or dashboard role never changes its
  membership.
- `resolve-judgement` is the `SPEC.md` Transition contract row `ratify`:
  preconditions "proposal admitted; live matching authority grant"; commit
  "preserve history; add `RATIFIED` event"; refusal `AUTHORITY_REFUSED` or
  `STALE_STATE`. `contracts/kernel-transitions.json` carries the same row as
  a rebuildable projection under `transitions.ratify`; `SPEC.md` is the
  authority. The request's question is the Proposal being ratified, and the
  answer lands as a judgement-resolution record with `resolver_kind` `HUMAN`,
  the grant checked, its receipt, and `unresolved_receipt_id` naming the
  conditioned operation's `UNRESOLVED` receipt (CONS-009). A `MODEL` actor's
  attempt is `REFUSED` and records no resolution (CONS-002).

## Obligations

`bindings/README.md` requires a human-facing binding to expose state,
choices, authority, provenance, and receipts intelligibly. For this binding:

| Obligation | The CLI must expose | Resolves to |
| --- | --- | --- |
| State | session lifecycle; each pending request's lifecycle, `loop_mode`, and standing; the conditioned operation's current receipt outcome (`UNRESOLVED` while `QUEUED`); notification lifecycle | operator-session, judgement-request, judgement-resolution, notification, and Receipt records; never a projection-view |
| Choices | the legal operations for the current actor and their required inputs; for `resolve-judgement`, the decision vocabulary `ACCEPTED`, `STRUCK`, `DEFERRED` and the optional rationale | this declaration's `operations`; `service.json` `operations`; `judgement-resolution.decision` |
| Authority | before an attempt, the authority the resolution will check (`required_authority_type` `JUDGEMENT`, `capability` `resolve-judgement`, `scope` the request's `request_id`); after it, the grant named in the receipt's `authority_grant_ids` and the resolution's `resolver_grant_id` | judgement-request fields; `Receipt.authority_grant_ids`; `judgement-resolution.resolver_grant_id`; `SPEC.md` `AuthorityGrant` |
| Provenance | the request's address and digest; `question_address` and `question_digest` with the rendered question checked against them; `evidence_addresses`; `decision_ref`; requester id and kind; a notification's `source_address` and `source_digest`; a resolution's `rationale_address` and digest | judgement-request, notification, and judgement-resolution fields |
| Receipts | every invocation's receipt by id with outcome, `reason_code`, `interface_id` equal to this interface, `authority_grant_ids`, `effect_class`, and `prior_receipt_id`; a refusal as its `REFUSED` receipt, never an error string alone | `SPEC.md` Receipt; `contracts/receipt.schema.json`; `judgement-resolution.receipt_id`; `notification.receipt_id` |

The binding holds, infers, caches, and widens no grant. It introduces no
private standing, authority, or transition, and writes no storage directly.

## Parity with the Model Binding

A Model Binding over the console's `model-binding` port reads the same
records as typed JSON structure: the same judgement-request with the same
address and digest, the same receipts and reason codes. The two pending lists
differ in rendering only and are compared by digest (CONS-008).
`resolve-judgement` is `REFUSED` for a `MODEL` actor; a model may draft a
recommendation into the thread but may not resolve. Parity is proven by
equivalent operations and reconciled receipts (`SPEC.md`, Interface parity),
not by this declaration.

## Admission

This is a declared interface, not an implementation. Per the admission rule in
`bindings/README.md`, no binding implementation is admitted until the shared
transition contract is frozen (`STATUS.yaml` O10) or Bdo explicitly
authorizes a provisional Human Binding target for the Console Service
(`STATUS.yaml` O18). The protected boundary
`no_runtime_code_before_logical_spec_and_defeating_fixtures` applies to this
binding as it applies to the service. Until one of those decisions is ruled,
this directory contains no code and `interface.json` realizes nothing.

## Open questions queued for Bdo

- Whether the refusal `reason_code` for a `MODEL` attempt at
  `resolve-judgement` is `AUTHORITY_REFUSED` or a console-specific name
  (CONS-002).
- The decision vocabulary `ACCEPTED`, `STRUCK`, `DEFERRED` is a console
  proposal not yet defined by `SPEC.md` (`judgement-resolution.schema.json`).
