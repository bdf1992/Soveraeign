# Gateway research, AI-native reading, and controller plan

Observed 2026-08-23 on `feat/federation-harness-and-hardening`. A report, not policy
(`AGENTS.md`: a file under `reports/` is not a decision). It informs
`decisions/0040-the-declared-service-surface.md`, Ruling 5, and proposes the operation
sequence a controller would run. Nothing here settles standing.

External sources were read at the addresses cited. They are attributed context, not evidence
under `lineage/SOURCES.lock`, and no claim below rests on their authority alone.

## What the category actually is

"Gateway" names three different products that share a word.

| Shape | Examples | What it does | What it records |
| --- | --- | --- | --- |
| Edge / API gateway | Kong, Apigee, AWS API Gateway | Terminates a protocol, authenticates, rate-limits, routes, aggregates | An access log line |
| Mesh data plane | Envoy under xDS, Istio | The same functions per service, configured by a push from a management server | Statistics, access logs, traces |
| Model-facing tool gateway | MCP servers and hosts | Declares tools to a model, negotiates capabilities, invokes | Whatever the host chooses |

All three answer "may this call proceed, and where does it go". None of them answers "what
durable record exists that it was refused". That gap is where the Soveraeign gateway sits.

## Five findings that bear on our design

**1. Every production gateway is eventually consistent about what exists. Ours refuses
instead.** Envoy's xDS is a server-driven push inside a pull framework, versioned per resource
type, ACKed or NACKed by the client against a nonce that does not survive a stream restart.
The protocol states plainly that traffic may briefly drop during conflicting updates. Our
`resolve-capability` and `list-endpoints` declare `capability_map_fresh` as a hard
precondition and refuse when it does not hold. That is a stronger claim than any distributed
gateway makes, and we can afford it precisely because the map is a checked-in file rebuilt by
`scripts/sov_capability.py build` on one machine, not config racing across a network. If the
node ever federates, this precondition is the first thing that breaks, and the choice between
refusing and going eventually consistent becomes a real decision rather than a free one.

**2. Policy languages decide; they do not record.** Cedar's evaluation is
principal / action / resource / context, implicit deny by default, with an explicit deny always
overriding any permit. That shape is almost exactly our `check-authority`: actor, required
authority, subject, and a live grant. Two things we should take and one we should not. Take:
explicit-deny-wins, because our manifest currently says nothing about what happens when two
grants disagree, and "the widest grant wins" is the wrong default in a system built on
attenuation. Take: implicit deny as the default. Do not take: a decision that leaves no
record. Cedar's documentation describes no decision record at all, and our `refuse-request`
exists because a refusal that leaves nothing behind cannot be read back by the actor it
refused.

**3. Recording the refusal is the actual novelty, and it is the AI-native part.** A commercial
gateway logs a 403. A log line is not an append-preserving record with a digest, an
attributable actor, and a counter-record path. A model that gets refused by our door can read
the receipt as a record and learn why; a model refused by Kong can read an HTTP status. This
is the one place our design is not a poorer version of an existing product.

**4. MCP's own architecture argues for the S18 fix.** MCP separates host from server: the host
"enforces security policies and consent requirements" and "handles user authorization
decisions", while servers "expose resources, tools and prompts" and are meant to be
"extremely easy to build" with "focused responsibilities". Our `bindings/mcp/gateway.py` is
doing both — it resolves endpoints, checks preconditions, and writes the journal at
[gateway.py:130-141](../bindings/mcp/gateway.py#L130-L141). That is a server holding the
host's job, and separately it is a binding holding authoritative writes, which the directory
table forbids. The protocol we are binding to draws the same line our contract draws.

**5. We have discovery but not negotiation.** MCP negotiates capabilities at session start:
both sides declare what they support and must respect the declaration for the session. We have
`list-endpoints` and console's `discover-operations`, which answer "what exists" but not "what
will you and I both honour". For one local node with one kernel version this costs nothing.
It becomes real the first time two nodes cross. Named as deferred, not designed.

## Where the surface sits against the AI-native bar

Scored in `services/gateway/contracts/ai-native-gateway-service.yaml`. The short version:
reachability is `PARTIAL` on declaration alone — a model can discover all nine operations, their
subjects, their refusals, and their addresses today through
`python scripts/sov_service.py endpoints --service gateway`, and can invoke none of them.
Commitment, provenance, and retraction are `NONE` because nothing executes. `earn_it` is `OPEN`;
it is Bdo's judgement and has not been made.

Derived: `assessment_state: OPEN`, `minimum_verdict: UNSET`, `qualification: NOT_QUALIFIED`.

That is the accurate reading of a chartered service with no implementation, and it is the same
place the Asset Service assessment sits. Worth stating plainly: the gateway is the surface most
likely to reach `FULL` on reachability, because unlike the other services its entire job is to
be the declared machine-usable path. It is also the surface where `two_binding_proof` becomes
cheap, because the CLI and the MCP tool surface would drive one door instead of two
implementations.

## Controller plan

Six operations. Every one is `RECORD_LOCAL`; none consumes a metered resource or touches the
external world, so the whole sequence is admissible in the current phase without widening any
effect envelope. Blue builds and declares its own defeating cases; Red generates the ones Blue
did not think of; neither hand settles alone. No builder witnesses its own operation.

| # | Operation | Produces | Blue / Red | Depends on |
| --- | --- | --- | --- | --- |
| G1 | `gateway.declare_request_and_receipt_contracts` | `gateway-request.schema.json`, `gateway-receipt.schema.json`, positive and defeating fixtures | Blue | — |
| G2 | `gateway.build_the_refusal_path` | accept → resolve → check-authority refuses → `refuse-request` writes a receipt; the Asset Service is never called | Blue, then Red | G1 |
| G3 | `gateway.build_the_routed_path` | the same request with a live grant; the asset receipt returns unaltered; `read-receipt` reads it back | Blue, then Red | G2 |
| G4 | `gateway.reseat_the_mcp_binding` | `bindings/mcp/gateway.py` stops writing the journal and calls the service; closes the directory-boundary violation | Blue | G3, and Bdo on S18 |
| G5 | `gateway.two_binding_proof` | CLI and MCP drive the same positive and defeating fixtures against one door | Blue | G4 |
| G6 | `gateway.red_engagement` | adversarial witnessing; the receipt that earns `WITNESSED` | Red | G3 minimum |

G2 is the one that matters. The charter says the refusal is the first proving case because a
door that opens proves only that a call went through; a door that refuses, with a receipt,
proves the door is there at all.

Red's named starting angles for G6, none of which Blue should declare in advance: calling a
service directly and bypassing the door entirely; a grant that widens itself through the
authority check; routing against a stale capability map; returning a receipt the owning
service never issued; and the gateway settling an operation it routed.

### What escalates, and what it holds up

- **Does the Console own authority grants, or a permits service?** G2's authority check needs a
  real source. Reversible default in place (Console), so this gates ratification, not the
  build.
- **S18, the two things named gateway.** Gates G4 only. Renaming a binding is reversible; doing
  it after G5 would rewrite tests.
- **`earn_it` for this surface.** Gates the AI-native verdict, nothing else. It cannot be made
  until G3 exists to judge.

Nothing in G1 through G3 waits on Bdo.

## Residuals

- No gateway implementation, tests, or conformance fixtures exist. The charter, the manifest,
  and this plan are the whole of it.
- The conflicting-grant rule from finding 2 is not in any contract. It belongs in the gateway's
  `check-authority` preconditions or in the kernel, and this report does not settle which.
- Capability negotiation (finding 5) is named as deferred with no owner.
- External sources are cited at their addresses and were not captured into `lineage/`.
