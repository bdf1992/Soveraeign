# Gateway Service Charter

Standing: `PROPOSED`. Chartered and contracted; nothing here is implemented.

## Role in Soveraeign

The Gateway Service is the node's door. It is the one place a request from outside a service
turns into a call on that service, and the one place a refusal to let it through is recorded.

Today a caller reaches a service by importing its Python package, or by running the two asset
CLI commands. There is no single place that answers "what can be asked of this node, by whom,
over what". `contracts/fixtures/capability-map.reference.json` already computes that answer as
a projection; the Gateway is the participant that would serve it and act on it.

It exists so that adding a transport later — an operator-facing tool surface, or HTTP once the
phase permits it — is one service learning a new way to be spoken to, not every service growing
its own front door and its own idea of what a grant means.

## What a logical endpoint is

Every declared operation in every service manifest carries an address of the form
`sov://<service>/<operation>`. That address is transport-neutral: it names what is being asked
for, never how the bytes arrive. `contracts/capability-offices.json` binds transports to it —
in-process, CLI, a local tool surface, HTTP — and records which of those are open, declared but
not activated, or refused in this phase.

The Gateway resolves an address to the owning service and nothing else. It cannot invent an
address, and it cannot reach a service except through one.

## The route

A request crosses the door in a fixed order, and each step can refuse:

1. `accept-request` — the envelope is well formed, the transport is activated, the actor and the
   logical endpoint are declared. Otherwise `MALFORMED_REQUEST` or `TRANSPORT_NOT_ACTIVATED`.
2. `resolve-capability` — the address names a declared operation and the capability map is not
   stale. Otherwise `ENDPOINT_UNKNOWN`.
3. `check-authority` — the actor holds a live grant covering the authority the operation
   requires. Otherwise `AUTHORITY_REFUSED` or `GRANT_NOT_COVERED`.
4. `route-request` — the owning service is reachable and the effect class is admissible in this
   phase. Otherwise `SERVICE_UNREACHABLE` or `EFFECT_CLASS_REFUSED`.
5. `return-receipt` — the owning service's terminal receipt is returned unchanged. A route with
   no receipt behind it is `RECEIPT_MISSING`, not a success.

A refusal at any step is itself recorded through `refuse-request`. A request that was turned
away leaves a record; it does not vanish.

## Authoritative versus derived

The Gateway holds no service state. Its own records — the request, the resolution, the authority
check, the routing record, the receipt it returned — are the authoritative account of what
crossed the door. Everything it says about a service's records is derived from that service.

It reads the capability map, which is a projection and rebuildable. It never writes it.

## What it does not do

- It does not settle. The owning service decides whether its operation committed; the Gateway
  carries that receipt back without editing it.
- It does not witness. A request it routed cannot be observed by the thing that routed it.
- It does not issue authority. It checks a grant the Console Service issued; it cannot widen one,
  and it cannot grant on an actor's behalf.
- It does not fall back. If a transport is not activated, the request is refused by name. There
  is no quieter path that still works.
- It does not open an external transport in Phase I. HTTP is refused for every capability while
  the phase stands, and the refusal is recorded rather than assumed.

## Proving operation

The first slice worth building is the refusal, not the success: drive a request at
`sov://asset/ingest-asset` from an actor holding no grant, and prove the door returns
`AUTHORITY_REFUSED` with a recorded gateway receipt, while the Asset Service never sees the
call. Then the same request with a live grant, proving the asset receipt comes back unaltered
and the routing record names both.

That pair is the whole service in miniature: a door that refuses is worth more than a door that
opens, because only the first one proves the door is there.

## Open before this can be built

- Whether the Console Service or a separate permits surface owns `authority-grant`. The Console
  manifest claims it today because `grant`, `revoke`, and `list-grants` are built there; the
  Gateway depends on that and does not resolve the question
  (`services/console/KNOWN-GAPS.md`).
- The in-process calling convention each service exposes. There is no declared adapter shape yet,
  so `route-request` names a precondition it cannot currently check.
- Whether a gateway receipt is a kernel receipt or a distinct record. The manifest treats it as
  its own owned record; `contracts/receipt.schema.json` may absorb it instead.
