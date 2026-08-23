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
| `model-binding.schema.json` | declares an owner-selected local or remote model without granting provider authority |
| `event-envelope.schema.json` | records who decided or acted, why, exact inputs and outputs, authority, effects, and outcome |
| `kernel-transitions.json` | the transitions compiled from the SPEC.md transition contract, with their preconditions and refusals |
| `transition.schema.json` | a request to perform one declared transition, with the pre-state, lease, observation, and authority it is checked against |
| `kernel-parity.json` | the declared correspondence between each participant's own refusal vocabulary and the kernel refusal it realizes |

A schema-valid record can still be semantically unfit. Conformance fixtures and
independent observation remain necessary.
