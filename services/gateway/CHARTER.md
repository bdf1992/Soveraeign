# Gateway Service Charter

Standing: `CHARTERED_BOUNDARY_NOT_IMPLEMENTED`.

A historical reference participant under `src/` demonstrated one complete
`IN_PROCESS -> sov://asset/ingest-asset -> Asset Service -> terminal receipt` path.
That slice is retained as implementation evidence only. Current repository standing keeps
the Gateway Service at a chartered boundary with no admitted implementation standing.

## Role in Soveraeign

The Gateway Service is the node's door. It is the one place a request from outside a service
turns into a call on that service, and the one place a refusal to let it through is recorded.

The historical in-process participant demonstrated the route pattern below. A caller presents one transport-neutral
`sov://` operation, Gateway resolves the authored service manifest against the capability
projection, revalidates the selected projection row against its authored inputs, checks exact
actor kind and authority/scope, records the crossing, invokes a service-owned route, and returns
the owning service's terminal receipt unchanged.

That path does not make Gateway the owner of service state or settlement. Direct service Python
APIs and CLIs still exist as participant/testing surfaces; they are not a second Gateway contract.

## What a logical endpoint is

Every declared operation in every service manifest carries an address of the form
`sov://<service>/<operation>`. That address is transport-neutral: it names what is being asked
for, never how the bytes arrive. `contracts/capability-offices.json` binds transports to it —
in-process, CLI, a local tool surface, HTTP — and records which of those are open, declared but
not activated, or refused in this phase.

The Gateway resolves an address to the owning service and declared route. It cannot invent an
address, infer a missing route, or treat a stale/tampered capability projection as authority.

## The route

A request crosses the door in a fixed order, and each step can refuse or fail:

1. **accept request** — record the received envelope, validate shape, transport-independent
   attribution, and reject actor smuggling in domain arguments;
2. **resolve capability** — resolve the exact logical endpoint against both authored service
   manifests and the capability projection, verify the projection's input digest, and rederive
   the selected row from authored inputs before trusting it;
3. **check authority** — require the declared actor kind and an exact live grant covering the
   operation's authority and request scope; typed denials are refusals, while reader corruption
   or infrastructure errors are operational failures rather than counterfeit denials;
4. **route request** — require an activated transport, an admitted effect class, and a
   bound service-owned route;
5. **return receipt** — require a recognizable terminal service receipt attributed to the checked
   actor, record that Gateway carried it, and return that receipt object unchanged.

Governed refusal is distinct from operational failure. A missing grant, inactive transport, or
unreachable declared route is a refusal. A corrupt capability row, authority-reader exception,
service exception, or receipt attribution mismatch is `FAILED` evidence. Gateway does not turn
an infrastructure defect into a claim that the actor lacked authority.

## Authoritative versus derived

The Gateway holds no sibling-service domain state. Its crossing records — received request,
resolution evidence, authority decision, routing evidence, refusal/failure evidence, and the
fact that a service receipt was returned — are the authoritative account of what crossed the
door.

Everything it says about a service's operation, standing, effect class, required authority, and
transport activation is derived from authored service/capability inputs. The capability map is a
rebuildable projection and is checked for staleness and selected-row drift before routing.

The owning service's terminal receipt remains settlement for the service operation. Gateway does
not manufacture a second successful settlement receipt.

## What it does not do

- It does not settle a sibling service's operation.
- It does not witness an operation it routed.
- It does not issue or widen authority.
- It does not own capability definitions or repair the capability projection in place.
- It does not fall back to an undeclared transport or route.
- No external transport is active. HTTP remains refused while unconfigured.
- It does not become the Node. Gateway is one service inside the locally sovereign Node.

## Historical implementation evidence

The first proving pair is implemented in `tests/test_gateway_slice.py`:

- without a covering grant, `sov://asset/ingest-asset` leaves durable Gateway refusal evidence
  and the Asset Service does not execute;
- with a live exact grant, the same logical endpoint reaches the Asset-owned route and the
  Asset Service's terminal receipt comes back unchanged and attributed to the checked actor.

The suite also defeats malformed attribution, stale and tampered capability state, inactive HTTP,
undeclared/unbound operations, disallowed effect classes, authority-reader failure, service
execution failure, missing terminal receipts, receipt-actor mismatch, and attempted client actor
overrides.

This is implementation evidence only. It does not move Gateway out of current `CHARTERED_BOUNDARY_NOT_IMPLEMENTED` standing.

## Relationship to node composition

Gateway is the vertical carrier, not the horizontal composition root.

A local Node contains multiple service-owned verticals that share kernel, Registry, Record,
authority, and routing semantics. Growing horizontally therefore means binding additional
service-owned routes behind the same Gateway rather than adding domain logic to Gateway.
`services/README.md` records the working construction vocabulary:
`Kernel -> Vertical -> Horizontal -> Node surface`.

## Remaining seams

`KNOWN-GAPS.md` records the live differences between this participant and the full charter.
The important remaining seams are:

- the canonical contract form, if any, for a distinct `gateway-receipt` versus the current
  crossing evidence plus owning-service terminal receipt;
- explicit conflict semantics if the authority model later gains positive and negative grants;
- replacing the older MCP binding's private ingress behavior with this service path before MCP
  is treated as an activated Gateway transport;
- a genuine independent observation/witness path;
- a two-binding proof over this same door;
- broader service route coverage and any effect/transport class beyond the current
  `RECORD_LOCAL + IN_PROCESS` slice.

None of those seams is resolved by passing participant tests, and none widens current effects.
