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

## Tickets

<!-- Implementation stubs this change closes. A branch or pull request may close a
     stub; it cannot by itself close a bit, promote a village, satisfy independent
     witness, or ratify the epic. -->

Closes #

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
