# MCP Gateway

Standing: `BUILT_SELF_TESTED_NOT_WITNESSED`. Declared as `PROPOSED` in
`manifest.json`; nothing here is witnessed or ratified.

A Model Context Protocol server over stdio that exposes this node's built
services to any MCP-capable model client. It is a Model Binding
(`AGENTS.md`, Directory boundaries): it executes within grants and never
ratifies, settles, or witnesses.

## Why a gateway and not a set of wrappers

A tool call already carries what an operation boundary needs — a caller, a named
operation, typed arguments, and a return. So there is one dispatch path in
`gateway.py`, not one wrapper per operation:

1. resolve the endpoint from `manifest.json`, or refuse `UNKNOWN_OPERATION`;
2. check the tier's preconditions;
3. append an `EVENT` to the Record Service journal;
4. execute;
5. append a `RECEIPT` carrying `COMMITTED`, `REFUSED`, or `FAILED`.

A refusal leaves the same trace a success does. The journal is the operational
System of Record, so the gateway writes there rather than inventing storage.

## Tiers

| Tier | Session | Grant | Journal |
| --- | --- | --- | --- |
| `read` | no | no | nothing |
| `observe` | yes | no | `EVENT`, `OBSERVATION`, `RECEIPT` |
| `act` | yes | see below | `EVENT`, `RECEIPT` |

Every `act` endpoint declares which layer holds its gate:

- `gateway` — the gateway requires the caller to hold the declared capability;
- `service-enforced` — the service owns the check, and the gateway adds no
  second rule it has no bootstrap for. `authority_grant` is this: the first
  grant of a store has nothing that could already cover it, which is what the
  Authority layer's root-issuer rule exists to close;
- `bootstrap` — establishes the session the others require, so it cannot itself
  require one. Only `authority_open_session`.

## The manifest is the tool list

`gateway.py` builds its MCP tool descriptors from `manifest.json` and refuses to
start when the two disagree in either direction — a declared endpoint nothing
implements, or an implemented endpoint nothing declares. That check runs before
any store opens, so a refused start costs no file handle and creates no state.

This is why `services/projection` and `services/proofing` are absent. Both
declare operations and both stand `PROPOSED`, so exposing them would turn a
written-but-unbuilt service into a tool that errors at call time. Adding an
endpoint is a manifest entry plus a handler; the startup check makes forgetting
either half loud.

## Running it

```
python bindings/mcp/server.py --state-root .soveraeign --actor Bdo
```

To attach a client, point it at that command over stdio. For Claude Code:

```
claude mcp add soveraeign -- python bindings/mcp/server.py --state-root .soveraeign --actor Bdo
```

The first call is always `authority_open_session`. Every later act-tier call
runs under the returned session, and closing it withdraws every grant issued
under it.

## Boundaries

- Standard library only. MCP on stdio is JSON-RPC 2.0 line by line, so no
  runtime dependency and no provider SDK type reaches a service contract.
- Local pipes only. It opens no socket and reaches no network, so it adds no
  external-world effect (`STATUS.yaml`, `no_external_effects_in_phase_i`).
- Journalled arguments are shapes, not payloads: `<str:6>`, never the value
  (`AGENTS.md`, Context hygiene).

## Open seam

`services/gateway/contracts/service.json` declares a Gateway Service owning
`transport-binding` and a `bind-transport` operation, standing `PROPOSED`. This
binding is a stdio transport that currently enforces its own gates rather than
being admitted through that operation. Whether a transport binding must be
admitted by the Gateway Service before it serves is Bdo's to rule; it blocks
nothing today because both are local and neither is ratified.
