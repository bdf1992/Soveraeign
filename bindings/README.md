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

No binding implementation is admitted until the shared transition contract is
frozen or explicitly authorized as a provisional target.

## Sov

[`SOV.md`](../SOV.md) names the main operating agent. `bindings/sov/` is its
owner-directed provisional context profile: a provider-neutral entry point,
machine-readable profile, bounded session declaration, and positive/defeating
checks. It grants no authority and does not claim that live binding parity or
the operator Gateway exists.
