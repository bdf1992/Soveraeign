# Shared Contracts

Status: `PROPOSED · STACK-NEUTRAL`

These schemas compile the logical fields in `SPEC.md` into portable validation
surfaces. They constrain records crossing service and participant boundaries;
they do not prescribe storage tables, programming-language classes, transport,
or deployment topology.

| Contract | Purpose |
| --- | --- |
| `service-manifest.schema.json` | declares a service boundary, ownership, dependencies, operations, and forbidden shortcuts |
| `operation-plan.schema.json` | declares consequential work before execution |
| `receipt.schema.json` | records the terminal outcome of a crossing or transition |
| `participant-observation.schema.json` | carries implementation observations into the conformance oracle |
| `observation.schema.json` | records independent evidence of what occurred: what an observer looked at, how it avoided relying solely on the executor's report, and which predicates held (`SPEC.md` `Observation`) |
| `model-binding.schema.json` | declares an owner-selected local or remote model without granting provider authority |
| `event-envelope.schema.json` | records who decided or acted, why, exact inputs and outputs, authority, effects, and outcome |
| `source.schema.json` | identifies captured bytes by address, digest, and size so a reading can verify its input before it begins (`SPEC.md` `Source`) |
| `recording.schema.json` | records a reading of a source: exact source digest, reader version and configuration, fidelity, and recoverable omissions; it never replaces or mutates its source (`SPEC.md` `Recording`) |
| `seat-registry.schema.json` | PROPOSED (decisions/0020): the ownership topology as a rebuildable projection — seats, owner edges, what each settles, attributable occupancy claims |
| `kernel-transitions.json` | the transitions compiled from the SPEC.md transition contract, with their preconditions and refusals |
| `transition.schema.json` | a request to perform one declared transition, with the pre-state, lease, observation, and authority it is checked against |
| `kernel-parity.json` | the declared correspondence between each participant's own refusal vocabulary and the kernel refusal it realizes |

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
0018, 0022, and 0032, and `kernel-transitions.json` is a rebuildable projection
of the `SPEC.md` transition table accepted by
`decisions/0024-open-decision-drain.md` (O20); none of them is a kernel or
crossing contract.

A schema-valid record can still be semantically unfit. Conformance fixtures and
independent observation remain necessary.
