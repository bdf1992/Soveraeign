# Gateway Service Reference Gaps

Observed differences between the chartered boundary and the participant that now exists on this
branch. The service manifest remains at its declared `PROPOSED` standing. Implementation and
participant tests are evidence only; they do not silently advance standing.

Standing is governed under `decisions/0040-the-declared-service-surface.md`, Ruling 5. Research
behind several rows is in `reports/2026-08-23-gateway-research-and-controller-plan.md`.

| Gap | Observed behavior now | Required / remaining behavior | Contract |
| --- | --- | --- | --- |
| Route coverage | One reusable `RECORD_LOCAL + IN_PROCESS` vertical is implemented for `sov://asset/ingest-asset` through an Asset-owned route | Add same-class service-owned routes mechanically; do not add service-specific logic to Gateway | `CHARTER.md`; `contracts/service.json`; PR #87 |
| Request contract | Envelope shape and attribution rules are executable in `core.py` and tests, but there is no standalone `gateway-request.schema.json` | Decide whether the executable envelope needs a canonical schema and positive/defeating fixtures | controller plan G1 |
| Receipt contract | Gateway records crossing evidence and returns the owning service's terminal receipt unchanged; it does not emit a second success receipt | Settle whether `gateway-receipt` is a distinct owned record, a kernel receipt form, or unnecessary beyond crossing evidence | `contracts/service.json`; `contracts/receipt.schema.json` |
| Conflicting grants | Exact covering grants are checked and absence defaults to refusal; the current grant model does not provide a tested positive-vs-negative conflict case | If explicit negative grants are introduced, define deterministic conflict/attenuation semantics before accepting them | `check-authority`; PROD-I-5 |
| Authority failure classification | Typed authority denials become `AUTHORITY_REFUSED`; unexpected reader errors become durable `FAILED / AUTHORITY_CHECK_FAILED` | Preserve typed distinction as authority readers evolve | `CHARTER.md`; PR #87 |
| Capability projection integrity | Gateway checks the input-state digest and rederives the selected row from authored manifest/office inputs before routing | Keep global projection conformance independent; first real federated lookup must revisit strict local freshness semantics | `resolve-capability`; `list-endpoints` |
| Service route convention | `AssetRoutes` supplies the first service-owned operation adapter and keeps checked actor attribution outside domain arguments | Prove the convention on a second operation and then a second service family before considering it generic substrate | PR #87 replication rule |
| The MCP binding | `bindings/mcp/gateway.py` remains an older ingress path with its own resolution/authority/journal behavior | Make MCP call this service path before MCP is treated as an activated Gateway transport | `AGENTS.md` Directory boundaries; controller plan G4 |
| Two things named gateway | The MCP binding and the service still share the word | One name per semantic layer, or an explicit statement that binding vs service is the intended distinction | `OPEN-SEAMS.md` S18; `NAMING.md` |
| Capability negotiation | Local `list-endpoints` semantics can answer what this node declares; there is no two-sided negotiation | Define negotiation only when a real crossing has two independently sovereign sides | deferred; federation boundary |
| Authority source | The reference Gateway checks Console-owned grant records | Settle long-term authority ownership if Authority Service supersedes Console's current grant surface; Gateway must remain a reader either way | `services/console/`; authority issues |
| Independent observation | Participant tests and CI observe behavior, but the Gateway cannot witness itself and there is no fresh independent Gateway witness receipt | Add an independent observer/witness path | C7; `AI-NATIVE.md` check 3 |
| Two-binding proof | Human/model parity is exercised at the envelope semantics level, but two distinct bindings do not yet drive this same Gateway participant | A human binding and a model binding must call the same door and reconcile receipts | PROD-I-3; `AI-NATIVE.md` check 7 |
| External transport | HTTP remains inactive/refused for service capabilities; `node_runtime.py` health/listener existence does not activate application transport | Keep refused until an accepted operation actually requires second-process transport | `contracts/capability-offices.json`; infrastructure topology |
| Node composition | Gateway accepts an injected route map, but there is no canonical Node composition root that assembles identity, Registry, Record, authority, and service routes | Build composition outside the Gateway service; do not turn Gateway into the Node | `CLASSIFICATION.md`; `services/README.md` |

## Where this sits against the AI-native bar

The prior AI-native assessment predates the built slice and is therefore stale as an observation.
Reachability, commitment evidence, provenance, refusal durability, and human/model parity now have
participant evidence that the older score did not include. That evidence still does not witness
itself and does not earn standing automatically. Refresh the assessment only from the accepted
assessment contract rather than editing a score to match confidence.

Two observations worth keeping:

- Gateway is still the most natural place to reach full machine reachability because serving the
  declared machine-usable path is its bounded job rather than a projection over another service.
- A two-binding proof remains cheap once bindings call this exact participant: human and model
  surfaces should drive one door rather than carrying separate authorization/routing semantics.

## Replication test before abstraction

Do not introduce a generic route framework yet. The current claim should survive two increasingly
strong repetitions first:

1. route another same-service operation such as `sov://asset/read-asset` without changing Gateway
   semantics;
2. route an operation from a different service family, preferably `sov://registry/resolve`, through
   the same Gateway and evidence path.

If those repetitions require Gateway domain knowledge, the current decomposition is wrong. If they
only require service-owned route bindings, the vertical has become a usable horizontal substrate.
