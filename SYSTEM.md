# System

Status: `PROVISIONAL SYNTHESIS`

## Scope

Soveraeign is a locally owned operating environment where people and models work on the
same governed state.

People may use screens. Models may use structured bindings. Both resolve to the same
operations, authority checks, records, evidence, and history.

The node keeps custody of its authoritative record, authority, operation, and continuity.
It may borrow remote compute, including remote models, without making the provider the
owner of those functions.

"Algorithmic" means consequential work is represented in inspectable state with declared
inputs, explicit authority, executable transitions, observable results, and receipts. It
does not mean replacing human judgement with automation.

"AI-native" means model participation is part of the operating model itself. A model does
not work through a privileged side channel or a human-only imitation of the system.

## Nodes, owners, and models

Personal, team, and enterprise deployments use the same node contract. A one-person node
is a complete Soveraeign Node. Adding participants or federating later must not require
moving its authority or record into a provider-owned system.

Bring Your Own Model is the intended model practice. The owner selects a compatible local
or remote model through a declared Model Binding and Model Adapter. Each invocation
records the model, version, runtime, host, capabilities, data boundary, usage, and cost.

Changing models may change quality, latency, cost, context limits, and available
capabilities. It must not change authoritative state, standing, grants, receipts, or
service contracts. An unavailable model refuses visibly rather than silently switching to
another model.

**Sov** is the portable operating profile a compatible model can load. Sov helps the model
choose attention, context, legal operations, refusal, and handoff. Loading the profile
grants no authority and creates no authoritative state.

## How state changes

The logical flow is:

1. Capture a payload as an addressed source.
2. A declared reader interprets the source without changing it.
3. A derivation may produce a recording with provenance.
4. A recording or proposal begins as recorded, not authoritative.
5. Admission marks that the proposal passed the admission gate. It does not make the
   proposal true.
6. A holder of the required typed authority may ratify the claim.
7. Runtime attestation checks whether the ratified claim currently reproduces.
8. Effective state may condition later operations.
9. Operations leave receipts and can be checked through an independent observation path.
10. Correction or retraction changes what applies now without erasing what happened.

## Distinctions the system must preserve

| Dimension | Distinctions |
| --- | --- |
| Standing | recorded · admitted · ratified · effective |
| Data | payload · source · reading · view · recording · proposal · receipt · witness |
| Identity | identity · address · digest · label · route · handle |
| Event | attempted · committed · failed · refused · countered · unresolved |
| Effect | record-local · resource consumption · external-world mutation |
| Authority signal | proposal authority · ratification authority · runtime attestation |

Two fields may contain the same value without becoming the same kind of thing. A digest is
not an identity. A report is not an observation. A recorded proposal is not effective
state.

## Main parts

The logical system needs these responsibilities. They do not all need to be separate
services.

- **Record:** keeps immutable payloads, revisioned records, provenance, and enough history
  to reconstruct what happened.
- **Runtime kernel:** applies admission, transition, observation, settlement, receipt, and
  retraction rules.
- **Authority:** represents typed, scoped, revocable grants and the rules for ratification.
- **Attestation:** records reproduction, dissent, and outcomes that cannot be attested
  without turning runtime success into authority.
- **Discovery and projections:** expose addressable views, routes, available operations,
  and rebuildable read models.
- **Observation:** checks world state and operation results through a path the executor did
  not control.
- **AI-native evaluation:** grades named operations for reachability and the stronger
  Soveraeign qualification in `AI-NATIVE.md`.
- **Definitions and learning:** keep concepts revisioned and make a fresh participant able
  to understand the node from its artifacts.
- **Bindings:** present the same declared operations to people and models.
- **Adapters:** translate between Soveraeign and named external systems without moving
  authority into the adapter.
- **Federation:** later allows governed exchange between complete nodes without either node
  absorbing the other.

The older names `Atlas` and `Gauge` may appear in historical or classification material.
Here the responsibility is named directly unless that shorter label preserves a required
machine distinction.

## Phase-I boundary

Phase I is closed and recorded as `CLOSED_INCOMPLETE`. Its historical target was a local
system that refused uncontained external effects and proved:

- metered proposals;
- immutable, reconstructable memory;
- provenance across human/model use;
- gated admission and record retraction;
- typed authority;
- owner judgement that does not stop unrelated work;
- reconstruction by a fresh witness;
- runtime attestation after ratification;
- human/model use of the same governed state; and
- portability across two materially different model bindings, including one supplied by
  the owner.

Phase I did not prove distributed consensus, rollback of external-world effects,
autonomous external action, enterprise-wide integration, or federation. Its terminal
status records that the full qualification exit was not earned.
