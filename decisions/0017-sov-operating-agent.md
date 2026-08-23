# 0017 · Sov main operating agent

Status: `OWNER-DIRECTED NAME AND PURPOSE · EXACT PROFILE PROPOSED`

Numbering note: concurrent infrastructure and coordination branches already
occupy decisions 0014 through 0016. This decision uses 0017 so those histories
can merge without address collision.

## Decision

Name **Sov** as Soveraeign's main operating agent and establish it first as a
portable, lightweight context profile that a compatible underlying model can
load.

Sov is a stable operator profile rather than a provider, model, runtime, host,
credential, authority slot, durable memory, or kernel. The underlying model may
change without changing Sov's identity. Each invocation still attributes its
exact model binding and host.

Give Sov self-directed agency over its bounded participation: attention,
relevant-context selection, declared omissions, legal-operation selection,
proposal, action within live grants, refusal, escalation, and handoff. Preserve
the opposition that makes this safe: context grants no authority; Sov cannot
widen a grant, ratify judgement, self-witness, self-settle, keep private
standing, bypass a governed transition, or silently change models.

`SOV.md` is the portable entry point. `bindings/sov/profile.json` is the machine
target. Host bindings may point to them but own no semantics.

## Consequences

- The model receives a named place from which to exercise initiative without
  pretending that agency and authority are the same thing.
- Sov is the default candidate for the Control tier, not its automatic holder.
  Occupying any tier still requires the current task, capability, and grant.
- The first pass validates coherent `REQUEST_ONLY` context declarations and
  refuses consequential effects until live authority resolution exists.
- No private concern registry or model memory becomes a third System of Record.
- Dynamic context compilation remains behind #40/#42; explicit source loading
  and declared omissions are the honest present mechanism.
- This built profile does not prove a live controller, Gateway path, binding
  parity, independent witness, or Phase-I qualification.

## Open review

O17 asks Bdo to accept or redraw the exact agency envelope, declaration fields,
and activation gates. The name **Sov** and the intent to give the underlying
model bounded sovereignty over its own participation are owner-directed; the
precise realization remains reviewable.

## Source and authority

- `AGENTS.md` authority, change protocol, context hygiene, and completion report
- `SYSTEM.md` ownership and model portability
- `CONTRACT.md` C1, C3, C6-C8, C11-C12, and C15
- `SPEC.md` ModelBinding, OperationPlan, EventEnvelope, and interface parity
- `SDLC.md` Control tier, concern registry, and Bindings
- `BYOM.md` provider neutrality and explicit fallback
- issues #19, #30, #40, #42, and #45
- Bdo's 2026-08-23 direction naming Sov and defining it as a lightweight,
  mostly contextual agency pattern for the core underlying model

