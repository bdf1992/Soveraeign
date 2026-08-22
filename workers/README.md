# Workers

A worker is a scoped executor, not an authority or observer by default.

Every worker operation requires:

- an `OperationPlan` with exact input state;
- a scoped capability grant;
- resource limits and effect class;
- a lease with an increasing fence;
- a report that cannot settle its own claim;
- an independent observation path;
- and a terminal receipt for commit, failure, refusal, or unresolved state.

A stale lease may leave an attributable refused report, but it cannot publish a
new effective result. Worker identity, model identity, adapter identity, and
observer identity remain separate even when one process hosts several roles.
