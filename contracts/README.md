# Shared Contracts

Status: `PROPOSED · STACK-NEUTRAL`

These schemas compile the logical fields in `SPEC.md` into portable validation
surfaces. They constrain records crossing service and participant boundaries;
they do not prescribe storage tables, programming-language classes, transport,
or deployment topology.

| Contract | Purpose |
| --- | --- |
| `service-manifest.schema.json` | declares a service boundary, ownership, dependencies, operations, Kernel contracts used, and forbidden shortcuts; decisions/0052 proposes reading each manifest as that service's authored Kernel Binding |
| `operation-plan.schema.json` | declares consequential work before execution |
| `receipt.schema.json` | records the terminal outcome of a crossing or transition |
| `participant-observation.schema.json` | carries implementation observations into the conformance oracle |
| `observation.schema.json` | records independent evidence of what occurred: what an observer looked at, how it avoided relying solely on the executor's report, and which predicates held (`SPEC.md` `Observation`) |
| `model-binding.schema.json` | declares an owner-selected local or remote model without granting provider authority |
| `event-envelope.schema.json` | records who decided or acted, why, exact inputs and outputs, authority, effects, and outcome |
| `source.schema.json` | identifies captured bytes by address, digest, and size so a reading can verify its input before it begins (`SPEC.md` `Source`) |
| `recording.schema.json` | records a reading of a source: exact source digest, reader version and configuration, fidelity, and recoverable omissions; it never replaces or mutates its source (`SPEC.md` `Recording`) |
| `seat-registry.schema.json` | PROPOSED (decisions/0020): the ownership topology as a rebuildable projection — seats, owner edges, what each settles, attributable occupancy claims |
| `seat-message.schema.json` | PROPOSED (decisions/0035): the envelope one seat speaks to another in — who speaks, from which seat, to which seat, what kind of statement, the highest standing it proposes, and what it carries onward; the body is deliberately unconstrained |
| `seat-etiquette.json` | the relationship table `seat-message.schema.json` is graded against: which acts each seat type may speak, in which direction, and how far each may propose standing |
| `work-lease.schema.json` | PROPOSED (decisions/0056): one concern actively possessed by one attributable machine principal, under a grant, inside a multidimensional budget, against a stated closure condition; it is the difference between a ticket that has an assignee and work somebody is holding right now, and it grants nothing |
| `node-identity.schema.json` | PROPOSED (decisions/0039): who a node is and which seat settles for it, for itself and every peer a local seat has admitted; it cannot express a grant, so a peer's self-description can never arrive as permission |
| `federation-crossing.schema.json` | PROPOSED (decisions/0039, clarified by 0051): one record offered across the surfaces of two nodes and what the receiving node did about it; it carries attribution and evidence, never sender authority or standing — an admitted record enters the receiving node at `RECORDED` |
| `public-projection.schema.json` | PROPOSED (decisions/0039): the outward read model of a node, derived from threads an operator marked public; inbound is an addressed input that queues, never a record the surface admits by itself |
| `kernel-paradigms.schema.json` | PROPOSED (decisions/0052): shape of the registry that resolves stable service-manifest Kernel contract ids to the governing sources defining each paradigm |
| `kernel-paradigms.json` | PROPOSED (decisions/0052): addressable index of the current standing, typed-authority, operation, observation, receipt, retraction, and attestation Kernel paradigms; the indexed sources remain authoritative |
| `kernel-closure.schema.json` | PROPOSED (decisions/0052): shape of the rebuildable Node-wide projection showing service bindings, paradigm participation, type ownership, transition usage, and explicitly unmapped operations |
| `kernel-transitions.json` | the authored executable traversal projection compiled from the `SPEC.md` transition contract, with preconditions and refusals; drift checks keep it aligned with the specification |
| `transition.schema.json` | a request to perform one declared transition, with the pre-state, lease, observation, and authority it is checked against |
| `kernel-parity.json` | executable/declarative correspondence evidence between participant refusal behavior and the Kernel transition rule it realizes; parity is distinct from manifest binding |

## Kernel definitions, bindings, and projections

`SPEC.md` remains the principal stack-neutral logical source for the Shared Kernel.
`CLASSIFICATION.md` supplies the proposed canonical vocabulary used to read it. A
Kernel paradigm is an indexed coherent slice of that grammar; a service manifest
binds a service to the paradigms and types it participates in; and the Kernel Closure
is a derived view across all those manifests.

The direction of authority is intentionally one-way:

`governing sources -> paradigm index -> service manifest bindings -> derived closure`

The arrow never reverses. Editing or passing the closure cannot change a service
manifest, grant authority, promote standing, or alter a governing Kernel source.
`python scripts/sov_kernel.py binding-check` checks the authored service bindings
against one another, and `python scripts/sov_kernel.py closure` emits the derived
closure as JSON for humans and agents.

## Named gap and reuse

`Reader` has no schema of its own: its fields (`reader_id`, `reader_version`,
`configuration_digest`, `fidelity`, `omissions`) are carried by `Recording`,
which is the record that crosses a boundary. `participant-observation` and
`receipt` do not carry reader, fidelity, or omissions, so neither can stand in
for a reading; that gap is why a `Recording` schema (the brief's plain word:
recording manifest) exists rather than a widened existing contract. `Source` is
compiled so that `lineage/SOURCES.lock` entries have a declared shape. `SPEC.md`
is accepted as the Phase-I logical specification (`decisions/0024-open-decision-drain.md`,
O10), so these three compile an accepted object rather than anticipate one; each
still needs its own defeating fixture before it carries evidence.

The coordination files in this directory (`ticket-transition.schema.json`,
`ticket-transitions.json`, `ticket-queue-policy.json`,
`ticket-label-projection.json`, `issue-metadata.schema.json`) are owned by
`decisions/0016-github-coordination-registrar.md` as extended by decisions
0018, 0022, and 0032. They are coordination contracts, not Kernel definitions.
The Kernel transition table is different: it is an authored executable projection of
the accepted `SPEC.md` transition contract (`decisions/0019`, `0024`) and is checked
for drift rather than treated as the whole Kernel.

A schema-valid record can still be semantically unfit. Binding checks, conformance
fixtures, executable parity, and independent observation remain distinct evidence.
