# Gateway Service Reference Gaps

Observed differences between the chartered boundary and what exists. The service is
`PROPOSED`: a charter, a manifest with nine declared operations, and nothing that runs.
Every row below is therefore a gap by construction, not a regression.

Standing under `decisions/0040-the-declared-service-surface.md`, Ruling 5. Research behind
several rows is in `reports/2026-08-23-gateway-research-and-controller-plan.md`.

| Gap | Observed behavior | Required behavior | Contract |
| --- | --- | --- | --- |
| The whole service | Nine operations declared; none implemented | The route from `accept-request` to a terminal receipt | `CHARTER.md`; `contracts/service.json` |
| Request and receipt contracts | Not written | `gateway-request.schema.json` and `gateway-receipt.schema.json` with positive and defeating fixtures | Controller plan G1 |
| Conflicting grants | Undefined. Nothing says what happens when two grants disagree about one call | Explicit deny wins and the default is deny, or a stated reason it should not | `check-authority` preconditions; PROD-I-5 |
| The MCP binding | `bindings/mcp/gateway.py` resolves endpoints, checks preconditions, and writes the journal itself | A transport that calls this service; a binding may not own authoritative writes | `AGENTS.md` Directory boundaries; controller plan G4 |
| Two things named gateway | The binding and the service share the word; a receipt cannot say which refused | One name per layer, or a stated reason the overlap is accurate | `OPEN-SEAMS.md` S18; `NAMING.md` |
| Capability negotiation | `list-endpoints` answers what exists | Two sides declaring what each will honour, once a crossing has two sides | deferred; no owner |
| Stale-map behavior | `capability_map_fresh` is declared as a hard precondition and refuses | Correct for one local node. The first federated crossing forces a choice between refusing and eventual consistency | `resolve-capability`; `list-endpoints` |
| Receipt ownership | The manifest treats `gateway-receipt` as its own owned record | Either that, or `contracts/receipt.schema.json` absorbs it | `decisions/0040`, Defaults taken |
| Authority source | `check-authority` assumes the Console Service owns grants | A settled owner. The Asset Service also keeps its own `grants` table | `decisions/0040`, Judgement queue 1 |
| Independent observation | No check of any kind exists | An observer whose relation to the builder is independent | C7; `AI-NATIVE.md` check 3 |
| Two-binding proof | No binding drives this service | The CLI and a model surface passing the same fixtures against one door | PROD-I-3; `AI-NATIVE.md` check 7 |
| External transport | HTTP is refused for every capability | Unchanged while the phase stands; the refusal is recorded, not assumed | `contracts/capability-offices.json` |

## Where this sits against the AI-native bar

Scored in `contracts/ai-native-gateway-service.yaml`. Reachability is `PARTIAL` on
declaration alone; commitment, provenance, and retraction are `NONE`; `earn_it` is `OPEN` and
is Bdo's to make once there is something to judge. Derived: `NOT_QUALIFIED`.

Two observations worth keeping:

- This is the surface most likely to reach `FULL` on reachability, because being the declared
  machine-usable path is the whole job rather than a projection over one.
- It is also where `two_binding_proof` gets cheap. A human CLI and a model tool surface would
  drive one door instead of two implementations, which is the check every other service
  currently records as `UNATTESTABLE`.

Neither is a claim about the built service. There is no built service.
