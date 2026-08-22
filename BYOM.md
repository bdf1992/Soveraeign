# Local, Personal, and Bring Your Own Model

Status: `OWNER-DIRECTED PATTERN · CONTRACT PROPOSED`

Soveraeign is intended to work first as a **personally owned local node**, then
at team and enterprise scale without changing its constitutional rules.

Personal, team, and enterprise are ownership and operating profiles of the same
`Soveraeign Node`. They are not separate products, editions, or architectural
tiers.

## Personal-local pattern

A personal node:

- is owned and administered by one person;
- keeps its authoritative record, authority, receipts, and continuity under
  that person's custody;
- can operate its non-model functions when every external model provider is
  absent;
- can use local hardware, a remote model, or both without transferring
  sovereignty to either;
- may later admit more people or federate with another node through governed
  crossings rather than through a forced migration to a central service.

`Local` describes custody and operational continuity. It does not require every
computation to run on the same machine. Remote computation is allowed only
through a declared data boundary and cannot become the authoritative record or
authority system.

## BYOM definition

**Bring Your Own Model (BYOM)** means the node owner selects and configures a
compatible local or remote model through a declared `Model Binding`. Model
provider, model identity, model version, runtime, host, capabilities, data
boundary, cost meter, and availability behavior are configuration inputs—not
hidden product assumptions.

Changing the model must not change:

- authoritative enterprise state;
- legal operations or their standing transitions;
- typed authority and refusal rules;
- receipt and provenance requirements;
- service contracts;
- or the ability to inspect and retract prior model-caused record effects.

Changing the model may change quality, latency, cost, context limits, and
supported capabilities. Those differences are declared and observed rather
than normalized away.

## Binding and adapter boundary

- A **Model Binding** exposes Soveraeign's operator contract to a configured
  model.
- A **Model Adapter** translates that binding to a named runtime or provider.
- The model is the operator for an attributed run; the adapter is not the
  operator and receives no authority by transporting the request.
- Every invocation records the binding, adapter, provider, model, version,
  runtime, host, input projection, omissions, data boundary, usage, cost, and
  receipt.
- An unavailable or incompatible model refuses visibly. It does not fall back
  silently to another model or fabricate success.

## Data-boundary modes

Every model binding declares one mode:

- `LOCAL_ONLY` — model execution and supplied context remain inside the local
  node's declared host boundary;
- `REDACTED_REMOTE` — only an addressed, declared projection may cross to a
  remote model, with omissions and redactions recorded;
- `REMOTE_ALLOWED` — declared source material may cross to the configured
  remote provider under an explicit grant and receipt.

The mode is a maximum allowance, not permission by itself. Each invocation
still passes scope, authority, source, and operation gates.

## Portability test

From one unchanged local node and authoritative input state:

1. bind two materially different models, including one owner-supplied model;
2. discover the same named domain operation through both bindings;
3. execute it under the same kernel transition and authority contracts;
4. record exact model/runtime identity, input projection, usage, and cost for
   each run;
5. reconcile both results as proposals or recordings without silently merging
   them;
6. make one configured model unavailable and observe a receipted refusal;
7. continue inspecting, operating, and retracting local record state without
   that provider.

The test fails if either model requires a provider-specific authoritative path,
if a model swap changes authority, if model identity disappears from
provenance, if fallback is silent, or if provider loss removes local custody or
operational continuity.

## Non-goals

BYOM does not promise that every model can perform every operation, that model
outputs are equivalent, that arbitrary model code is safe to execute, or that a
remote provider can be used without a declared data boundary. Portability means
one governed contract can admit different capable models honestly—not that
their capabilities are interchangeable by assertion.
