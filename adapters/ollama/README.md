# Local Model Adapter (Ollama-compatible runtime)

Standing: `BUILT`, witnessed, **dissented**. An independent observer reproduced every
literal claim below and still refused the transition, because the custody refusal this
adapter exists to make can be defeated three ways — a one-field edit to `inventory.json`
that no check notices, a capture from a non-loopback endpoint that is nonetheless stamped
local, and an invocation record that selects its own data boundary. Read
`reports/2026-08-23-local-model-adapter-witness.md` before relying on anything here. The
defects are open; the text below has not been rewritten around them, so where this README
and that report disagree, the report is what was observed.

Every artifact here is a proposal into open decision O12 (`STATUS.yaml`), which gates
`model_binding.ratify_contract`. Nothing in this directory ratifies a binding, grants
authority, settles a run, or writes authoritative state.

This adapter translates a Soveraeign `Model Binding` to a locally hosted
Ollama-compatible runtime. `adapters/README.md` already named the Model provider row;
this is the first implementation of that row, and it exists because O12 asks Bdo to
ratify "the exact binding fields, data-boundary modes, and two-model Phase-I fixture" —
a question that is easier to answer against two working bindings than against prose.

## What is here

| Artifact | What it is |
| --- | --- |
| `capture.py` | The adapter's one crossing: reads the loopback runtime and projects `inventory.json`. Attended; nothing in `scripts/verify.py` calls it. |
| `inventory.json` | The recorded runtime inventory. Information role `PROJECTION`, rebuildable by re-running `capture.py`. |
| `adapter.py` | The checks: binding against the recorded runtime, invocation record against its binding, and parity across two invocations. |
| `validate.py` | Command line over those checks. Exit 0 accepted, 2 refused with a reason code, 1 unreadable. |
| `bindings/` | Two declared bindings — `qwen3:4b` and `gpt-oss:20b` — both `LOCAL` / `LOCAL_ONLY`. |
| `fixtures/` | Two positive invocations and fourteen defeating cases, each declared in the test table. |
| `tests/` | 13 tests. Establishes `BUILT`; it cannot claim `WITNESSED`. |

## The refusal a tag cannot make

The recorded inventory holds `gpt-oss:20b` and `gpt-oss:20b-cloud`. Their declared
family, parameter size, quantisation, context length, and capabilities are identical.
They differ in one field: `remote_host`, which for the second is `https://ollama.com:443`.
Both answer on the same loopback port and both appear in the same listing.

So a binding that named the second model, declared `provider_kind: LOCAL` and
`data_boundary: LOCAL_ONLY`, and was checked against its tag would pass while sending
the operation's input off the machine. Every check here reads the recorded inventory
instead, and `_check_custody` refuses that binding with `DATA_BOUNDARY_REFUSED`. This is
the `no silent provider fallback` rule in `AGENTS.md` and the "unavailable model silently
falls back" defeating case of `FOUND-008` meeting a concrete runtime.

## Refusal reason codes

Declared by `SPEC.md` for `invoke_model`:

- `MODEL_UNAVAILABLE` — the model, its recorded version, or the runtime version is not
  the one the inventory holds; or the invocation names a binding that is not declared.
- `MODEL_INCOMPATIBLE` — a capability the binding claims that the model does not hold,
  a capability the invocation requests that the binding does not carry, a binding the
  shared schema rejects, or a parity pair that ran one model twice.
- `DATA_BOUNDARY_REFUSED` — a remote-served model under `LOCAL` custody or a
  `LOCAL_ONLY` boundary, or an invocation whose input crossed under `LOCAL_ONLY`.

Proposed here as reasoned refusals, and queued for Bdo (`invoke_model` admits a reasoned
refusal, but this code set is not ratified):

- `SILENT_FALLBACK_REFUSED` — a model other than the bound one ran. An `EXPLICIT`
  fallback policy does not lift this: it permits a new attributed invocation naming the
  replacement binding, not a substitution inside the original invocation.
- `PROVENANCE_INCOMPLETE` — an invocation field, an executed provenance field, or a
  usage or cost meter is absent or empty.
- `PROVENANCE_CONTRADICTED` — the declaration and the record disagree: a foreign adapter,
  a `REMOTE` declaration over a locally recorded model, a runtime or host that is not the
  recorded one, model output entering as anything but `PROPOSAL` or `RECORDING`, or a
  parity pair whose interface contract, required authority, operation, input, or
  requested capability differs.

## The invocation record is adapter-local

`contracts/model-binding.schema.json` is the shared contract and this adapter validates
every binding against it directly. The **invocation record** is different: no kernel
contract for it exists, and minting one under `/contracts` would create a second semantic
authority before Bdo has ruled. So its field set lives in `adapter.py`
(`INVOCATION_FIELDS`) and is offered as proposal input to O12 — the shape `invoke_model`
would need to record if the transition were implemented, not a contract anything else may
rely on.

## Running it

```bash
python adapters/ollama/capture.py                 # attended; rewrites inventory.json
python adapters/ollama/validate.py bindings       # check every declared binding
python adapters/ollama/validate.py binding  adapters/ollama/fixtures/<name>.json
python adapters/ollama/validate.py invocation adapters/ollama/fixtures/<name>.json
python adapters/ollama/validate.py parity \
    adapters/ollama/fixtures/invocation-qwen3-4b.json \
    adapters/ollama/fixtures/invocation-gpt-oss-20b.json
python -m unittest discover -s adapters/ollama/tests -v
```

`python scripts/verify.py` runs the test suite as the `local model adapter` check.

## What this does not do

- It does not execute `invoke_model`. No request is sent to any model; the invocation
  records are declared fixtures, not captured runs. Executing the transition needs the
  kernel path, and the transition is O12-gated.
- It does not prove `FOUND-006` human/model binding parity. There is no human-facing
  binding here; `bindings/console/interface.json` declares one and holds no code.
- It does not cover the `FOUND-008` case "provider loss makes the local record
  inoperable". That is a property of the node, not of this adapter, and no check here
  observes it.
- It grants nothing. An `ACCEPTED` result says a declaration and a recorded runtime do
  not contradict each other. Authority still arrives by grant at the operation boundary.

## Judgement queued for Bdo

1. Are the three proposed reasoned-refusal codes above the right set, and do they belong
   in `contracts/kernel-transitions.json` beside the declared three?
2. Does the invocation record belong under `/contracts` as a kernel contract, or does it
   stay adapter-local until a second adapter needs it?
3. `cost_meter` records `monetary_rate: 0` with `wall_clock_seconds` metered separately.
   Is a locally hosted model's cost zero for budget purposes, or does wall clock spend
   against a run's limits?
4. Is a recorded inventory the right authority for a custody check, or must a binding be
   re-checked against the live runtime at invocation time — and if so, what refuses when
   the runtime is absent?
5. Does `capture.py` reading a loopback port count as `RECORD_LOCAL`, as recorded here,
   or does any socket read need a declared crossing?
