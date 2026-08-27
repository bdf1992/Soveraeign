# Adding a binding or an adapter

Three bindings and three adapters exist. This says how to add the next one, from
what those six actually do rather than from what the boundary documents hoped
they would.

Nothing here grants authority. Following it produces a `BUILT` artifact that
still cannot witness itself (`AGENTS.md`, Evidence and standing).

## Which one are you writing

The two get confused because both sit between this node and something outside
it. The distinction is what they translate:

| | Binding | Adapter |
| --- | --- | --- |
| Translates | one authoritative transition contract, for a kind of **operator** | one service contract, to a named **external system** |
| Examples here | `bindings/mcp/` (model operators over MCP), `bindings/console/` (a human at the judgement surface), `bindings/sov/` (the portable agent profile) | `adapters/ollama/` (a model runtime), `adapters/github/` (a repository host), `adapters/host/` (the process execution environment) |
| Owns | a projection of state, choices, authority, provenance and receipts | a crossing, its data boundary, and its receipt |
| Must never | introduce private standing, authority, transitions, or direct storage writes | acquire authority from the external system, or fall back silently to another provider |

A model provider is an adapter, not a binding. `bindings/mcp/` is a binding
because MCP is how an operator reaches this node; `adapters/ollama/` is an
adapter because Ollama is a system this node reaches out to. Getting this wrong
is the most common way a change lands in the wrong directory.

## The order of work

This is `AGENTS.md`, Implementation order, applied to a crossing. Steps 2 and 3
are the ones people skip, and skipping them is what makes a new adapter
unreviewable.

1. **Name the operation and the service that owns its lifecycle.** An adapter
   without an owning service has nowhere to send a receipt.
2. **Add the contract row.** For an adapter, a row in the table in
   `adapters/README.md` naming input standing and allowed output. For a model
   binding, a document validating against
   `contracts/model-binding.schema.json` — nineteen required fields, listed
   below.
3. **Write the defeating fixture before the implementation.** At minimum one
   case that must be refused, and it must fail before your code exists.
   `adapters/ollama/fixtures/` carries fourteen; the smallest useful set is
   one positive and one defeating.
4. **Write the smallest implementation that satisfies the visible case.**
5. **Add focused unit tests** under `<your directory>/tests/`.
6. **Wire the check into `scripts/verify.py`** by adding a `Check` in
   `scripts/sovverify/checks.py` naming what it reads and what it does not
   prove. An adapter with no check in the gate is not integrated; it is
   present.
7. **Record the standing** in `decisions/` and, if it changes,
   `STATUS.yaml`.

## What a model binding declares

`contracts/model-binding.schema.json` requires all nineteen:

```text
binding_id      adapter_id       provider_id      provider_kind
model_id        model_version    runtime_id       runtime_version
host_id         interface_contract_id             capabilities
data_boundary   input_projection_id               omissions
usage_meter     cost_meter       fallback_policy  authority_source
created_at
```

Two of them carry the rules that matter. `provider_kind` is `LOCAL` or
`REMOTE`. `data_boundary` is `LOCAL_ONLY`, `REDACTED_REMOTE`, or
`REMOTE_ALLOWED`, and it states where the operation's input may go — not where
the model happens to be running.

`adapters/ollama/` exists because those two fields can be declared truthfully
and still be wrong. Its recorded inventory holds `gpt-oss:20b` and
`gpt-oss:20b-cloud` with identical family, parameter size, quantisation,
context length and capabilities; they differ in one field, `remote_host`. Both
answer on the same loopback port. A binding naming the second, declaring
`LOCAL` and `LOCAL_ONLY`, and checked against its tag would pass while sending
input off the machine. Every check there reads the recorded inventory instead.

Copy that pattern: check the crossing against a recorded observation of the
external system, never against what the binding says about itself.

## What will refuse you

These are not style preferences. Each has a defeating fixture somewhere in the
tree.

- **Operating successfully grants nothing.** A model, adapter, credential,
  process or provider receives no authority by working. Every consequential
  transition needs a typed, scoped, live grant at the operation boundary.
- **No provider SDK type may enter a kernel or service contract.** Translate at
  the adapter edge.
- **No silent provider fallback.** Absence of the external system produces a
  visible refusal or an `UNATTESTABLE` result. It never quietly becomes a
  different provider, and it never removes local custody.
- **A refusal leaves the same trace a success does.** `bindings/mcp/gateway.py`
  appends an `EVENT` before executing and a `RECEIPT` carrying `COMMITTED`,
  `REFUSED` or `FAILED` after, on every path.
- **A receipt never claims the world was rolled back.** Retraction adds a
  counter-record. `RESOURCE_CONSUMPTION` and `EXTERNAL_WORLD` effects are not
  undone by it.
- **Your tests establish `BUILT` and nothing more.** They cannot claim
  `WITNESSED` or `RATIFIED`, and the participant that wrote the adapter cannot
  observe it.

## Three worked examples, smallest first

| Read | For |
| --- | --- |
| `adapters/host/` | The minimum shape. One read-only crossing, standard library only, unreadable fields returned as `null` and named in `limitations`. No shell, no elevation, no mutation. |
| `bindings/mcp/` | The dispatch pattern. One path for every operation — resolve the endpoint from `manifest.json` or refuse `UNKNOWN_OPERATION`, check the tier, journal, execute, journal — rather than one wrapper per operation. |
| `adapters/ollama/` | The full treatment: two declared bindings, a captured runtime inventory, fourteen defeating fixtures, thirteen tests, and a check in `verify.py`. Also read `reports/2026-08-23-local-model-adapter-witness.md`, where an independent observer reproduced every claim and still refused the transition. That report is what a witness of your adapter will look like. |

## What is not settled

- The shared transition contract is not frozen. `bindings/README.md` long said
  no binding was admitted until it was, while three bindings shipped; that
  sentence cited O10 and O18, retired in `decisions/0024` and `decisions/0033`.
  Build against the current contracts and record the standing you claim.
- No binding parity proof exists. `bindings/README.md` requires a human binding
  and a model binding performing equivalent operations with reconciled
  receipts, demonstrated across two materially different models. That is
  PROD-I-9 and it is open.
- `invoke_model` is declared in `contracts/kernel-transitions.json` with no
  kernel implementation. `adapters/ollama/invoke.py` executes against the local
  runtime and grades its own output; it settles nothing.
- No external-world effect has ever put bytes in front of a third party in
  Phase I. If your adapter would be the first, that is an owner-held
  transition, not an engineering one (`contracts/acceptance-policy.json`).
