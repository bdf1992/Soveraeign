# MCP gateway, observed over the wire it serves, 2026-08-23

Status: `OBSERVED INDEPENDENTLY · NOT WITNESSED · NOTHING RATIFIED`

Subject: `bindings/mcp/` at `c296c25`, built in `d850c6d`.

The MCP gateway is the surface that lets an outside model client reach this
node's built services. Until now the only thing that had checked it was
`bindings/mcp/tests/test_gateway.py`, which imports `Gateway` and calls it in
process — the builder's own path, and `AGENTS.md` holds that a build cannot
witness itself. This session wrote none of it and looked from outside.

Seventeen observations. Sixteen held. One did not, and it is the reason this
report exists.

## How this was observed

`scripts/witness_mcp.py` speaks JSON-RPC 2.0 to `bindings/mcp/server.py` over
stdio as a subprocess. It imports nothing from the binding for the main run, and
reads the journal back through the gateway's own `record_entries` tool rather
than by opening the store behind it. That is the path a real MCP client takes and
the only one it can take.

Two checks step outside that and say where they do. The startup validation
constructs `Gateway` directly, because `server.py` exposes no way to point at a
different manifest. The attribution check opens the asset store read-only,
because the divergence it looks for is between two records that no single tool
returns together.

## What held

```text
initialize answers the declared protocol version   2024-11-05
ping answers
an unknown method is a JSON-RPC method-not-found   -32601
the served tool list is exactly the manifest       served-only=[] manifest-only=[]
an unexposed tool is refused, not attempted        UNKNOWN_OPERATION
an act call before any session is refused          SESSION_NOT_LIVE
the refusal is in the journal, not only the answer 1 REFUSED receipt
a read-tier call appends nothing                   1 entry before and after
a session opens
an act call with a session but no grant is refused GRANT_NOT_HELD
a narrowly scoped grant admits no gated call       GRANT_NOT_HELD
a granted act call commits and returns a receipt
a secret-shaped argument is not journalled verbatim
journalled arguments are shapes, not values        <str:14>, <str:31>, <str:57>
a declared endpoint with no implementation refuses the start
a refused start opens no store                     no directory
```

Three of those are load-bearing and were pressed rather than read.

**A refusal leaves the same trace a success does.** The README claims it; calling
`asset_ingest` before any session existed produced `SESSION_NOT_LIVE` at the
client and a `REFUSED` receipt in the journal. A caller that never reports the
refusal cannot hide it.

**The manifest really is the tool list, in both directions.** `tools/list`
matched the manifest exactly. Adding a declared endpoint with nothing behind it
made `Gateway` refuse to construct, and — the part worth checking rather than
trusting — the state directory it would have opened was never created. A refused
start costs no handle and leaves no store.

**Arguments reach the journal as shapes.** A label of `sk-` followed by twenty-eight
characters was ingested; the string does not appear anywhere in 6,141 bytes of
journal, and every journalled string argument came back as `<str:N>`. The
redaction claim in `AGENTS.md` context hygiene holds at this boundary.

## What did not hold

**The `actor` argument diverges from the identity the gate checked.**

`asset_ingest` is gated by the gateway: `_precheck` calls
`self.asset.authority.authorized(actor, "operate:ingest", "*")` using
`self.actor`, the identity the server was started with. But `asset_ingest` also
takes an `actor` argument, and `_ingest` passes it straight to
`AssetService.ingest`, which performs no authority check of its own and writes it
onto the asset store's receipt.

So one call leaves two records naming different actors:

```text
server started --actor Bdo, Bdo holds operate:ingest, mallory holds nothing

tools/call asset_ingest {path, label, actor: "mallory"}  ->  COMMITTED

record journal   EVENT + RECEIPT   actor='Bdo'       (the gated identity)
asset store      receipts          actor='mallory'   (the argument)
```

The gate itself is sound and fails closed. Starting the server as
`--actor mallory` and passing `actor: "Bdo"` is refused with `GRANT_NOT_HELD`,
so no authority is widened: the caller cannot do anything the started identity
could not already do. What breaks is attribution. `AGENTS.md` requires every
consequential decision to emit an attributable event naming its actor, and the
asset store's receipt for this ingest names an actor who held no grant and whose
identity was never checked. The string is chosen by the MCP client — which is to
say, by the model.

Two records of one act disagree about who acted, and the caller picks one of
them. A later reader reconstructing custody from the asset store gets the
model's answer, not the gate's.

The narrow fix is to stop accepting the argument for gateway-gated endpoints and
pass the gated identity instead: drop `actor` from `asset_ingest` in
`manifest.json` and have `_ingest` use `self.actor`. Whether that is the right
fix, or whether the asset service should refuse an unchecked actor at its own
boundary, is a builder's call. A witness does not make it.

## Two smaller things

**Scope is offered and cannot be used.** `authority_grant` accepts a `scope`
argument, and `authority.authorized` admits a grant when its scope equals the
requested one or is `*`. The gateway always requests `"*"`. So a grant issued
with any real scope — `assets/reports`, say — can never admit a gateway-gated
call, which is exactly what the observation above recorded. It fails closed, so
this is not a hole. But the surface advertises a knob that only ever locks the
door, and a caller who scopes a grant carefully will find their calls refused
with `GRANT_NOT_HELD` and nothing to tell them why.

**A session cannot be closed through this surface.** The README says "closing the
session withdraws every grant issued under it," and
`AssetService.close_session` implements exactly that. No endpoint exposes it.
Through MCP a session can be opened and never closed; grants bound to it stand
until the TTL expires. The capability exists, the documentation describes it, and
the binding does not reach it.

## What this does not establish

- Nothing here reaches `WITNESSED`. An observation proposes that standing; Bdo
  settles it.
- Only the six declared endpoints were exercised. `observe_verify` was not run
  under observation, because it spawns `scripts/verify.py` and the point was to
  observe the gateway rather than to re-run the repository gate through it.
- No claim is made about MCP client compatibility beyond the four methods
  exercised: `initialize`, `ping`, `tools/list`, `tools/call`.
- The "no external effect" claim was read, not proven. `server.py` opens no
  socket in the code path exercised here, but this observation ran no network
  isolation and cannot rule out a path it did not take.
- The open seam the README records — whether a transport binding must be
  admitted through the Gateway Service's `bind-transport` before it serves —
  stands untouched. It is Bdo's to rule.

## Reproducing

```
python scripts/witness_mcp.py
```

Run from this worktree, which is pinned at `c296c25`. The observation describes a
fixed object and can be retaken rather than trusted.
