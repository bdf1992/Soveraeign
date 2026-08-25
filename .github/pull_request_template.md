## Summary

<!-- What changed and why. One coherent policy or behaviour change per pull request. -->

## Change protocol

<!-- AGENTS.md, Change protocol. Required for policy, contract, schema, transition,
     authority, persistence, or external-effect changes. -->

- Requested outcome and current authoritative state:
- Affected contracts, fixtures, and sources:
- Preconditions and expected observable result:
- Effect class: `RECORD_LOCAL` | `RESOURCE_CONSUMPTION` | `EXTERNAL_WORLD`
- Rollback, counteraction, or refusal boundary:

## Concern and settlement

<!-- Name the durable concern this execution branch carries. Product meaning stays on
     the concern's canonical source references; do not copy product semantics into the
     branch or PR. See contracts/ticket-settlement.json. -->

- Concern: #
- Relation: `advances` | `satisfies` | `supersedes`
- Remaining unsatisfied state or named successor:

<!-- Use GitHub's `Closes #N` syntax only when Relation is `satisfies`. A PR that merely
     advances a concern must leave it open. A superseded concern must name its successor
     before closure. -->

## Related tickets

<!-- Name implementation stubs or other tickets this change touches without implying
     settlement. Use `Closes #N` only under the satisfies rule above. A branch or pull
     request cannot by itself close a bit, promote a village, satisfy independent witness,
     or ratify the epic. -->

Related #

## Observation

<!-- What you observed through a path independent of the code that performed the
     change, and every residual failure. A passing self-test establishes BUILT only. -->

## Proposed standing change

<!-- OPTIONAL. Include a soveraeign-ticket-transition/v1 request only when this change
     proposes advancing a ticket's standing. The purple gate evaluates it against
     contracts/ticket-transitions.json and refuses what the contract forbids.
     Omit this block entirely for an ordinary change. -->

```json
{
  "request_schema": "soveraeign-ticket-transition/v1",
  "ticket": "#0",
  "from": "CHARTERED_NOT_IMPLEMENTED",
  "to": "BUILT_SELF_TESTED_NOT_WITNESSED",
  "actor_id": "",
  "actor_kind": "MODEL",
  "reason": "",
  "effect_class": "RECORD_LOCAL",
  "evidence": {
    "closure_contract_complete": "",
    "blue_receipt": ""
  }
}
```
