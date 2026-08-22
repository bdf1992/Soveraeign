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

No binding implementation is admitted until the shared transition contract is
frozen or explicitly authorized as a provisional target.
