# Operator Bindings

Bindings realize one authoritative transition contract for different operator
types. Human and model bindings may present different projections, but neither
may introduce private standing, authority, transitions, or direct storage
writes.

The first parity proof must show equivalent operations through:

- a human-facing binding that exposes state, choices, authority, provenance,
  and receipts intelligibly;
- a model-facing binding that exposes the same material as typed structure;
- reconciled receipts proving both invoked the same kernel behavior.

The model side must be demonstrated with two materially different configured
models. One must be supplied by the node owner through `BYOM.md`; changing the
binding cannot create a provider-specific state or authority path.

The shared transition contract is not frozen. That was once written here as a
bar on implementing any binding at all, gated on O10 and O18; both identifiers
were retired (`decisions/0024-open-decision-drain.md`,
`decisions/0033-close-the-founding-docket.md`) and three bindings shipped past
it. What the unfrozen contract actually costs is narrower: a binding built now
records the standing it claims and carries the risk that the contract moves
under it. It does not wait.

## Adding one

[`INTEGRATING.md`](INTEGRATING.md) is the path: which of the two things you are
writing, the order of work, what a binding must declare, what will refuse you,
and three worked examples. Adapters translate to a named external system rather
than to an operator type and live under [`adapters/`](../adapters/README.md),
which carries their declared boundary table.

## Sov

[`SOV.md`](../SOV.md) names the main operating agent. `bindings/sov/` is its
owner-directed provisional context profile: a provider-neutral entry point,
machine-readable profile, bounded session declaration, and positive/defeating
checks. It grants no authority and does not claim that live binding parity or
the operator Gateway exists.

## Console

[`services/console/CHARTER.md`](../services/console/CHARTER.md) charters the
Console Service. `bindings/console/` declares the Human Binding interface for
its first slice, the owner's judgement surface: `interface.json` names the
operations the binding invokes, maps `resolve-judgement` to the `SPEC.md`
`ratify` transition, and states what the binding must expose under the five
requirements above. It is a declaration only, standing `PROPOSED`: it holds no
code and grants no authority. Implementing it is admissible under the paragraph
above; what it lacks is an implementation, not a permission.
