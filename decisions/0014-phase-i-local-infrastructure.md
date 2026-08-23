# 0014 · Phase-I local infrastructure as code

Status: `PROPOSED · OWNER-DIRECTED IMPLEMENTATION · O2 REMAINS OPEN`

## Context

Requirement implementation needs a reproducible custody ground before worker
count grows. The Phase-I engineering baseline already proposes Python 3.11+,
SQLite, filesystem content-addressed storage, JSON Schema, and a network-free
verification loop. It deliberately does not select cloud, container,
orchestration, queue, identity-provider, graph-database, or model-provider
infrastructure.

The Day-0 Red finding `RED-32-001` also demonstrated that an infrastructure
gate is meaningful only when it examines what source control can actually
admit, including force-added ignored files.

## Proposed decision

Admit a provisional, provider-free Phase-I local infrastructure envelope:

- a versioned declarative manifest owns the required local custody paths;
- a dependency-free tool validates, plans, applies, and verifies that manifest;
- plan is observation-only and apply is limited to an empty or already-managed
  local root;
- every materialization writes a manifest-digest receipt;
- external effects, required network access, provider dependency, path escape,
  symlink substitution, unsafe permissions, unmanaged-root adoption, and
  manifest drift refuse or fail visibly;
- no destroy operation is supplied.

This is a proposed reference implementation of infrastructure custody, not a
ratification of the O2 technology baseline and not a production deployment.

## Consequences

Requirement workers gain one reproducible local ground without inventing cloud
topology. Later infrastructure is added only when an observed conformance case
earns the smallest replaceable boundary. The manifest grants no authority and
does not become the operational System of Record.

## Defeating cases

- planning mutates the target;
- apply adopts a non-empty unmanaged root;
- any custody path escapes the declared root or resolves through a symlink;
- the node requires network or provider availability to establish custody;
- external effects are admitted in Phase I;
- receipt or manifest drift passes verification;
- a force-added ignored secret can enter the Git population without refusal.
