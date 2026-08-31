# Local, personal, and Bring Your Own Model

Status: `OWNER-DIRECTED PATTERN · CONTRACT PROPOSED`

Soveraeign starts with a personally owned local node and keeps the same node contract as
more people or systems join it.

Personal, team, and enterprise deployments are operating profiles of the same
`Soveraeign Node`. They are not separate editions.

## Personal local node

A personal node:

- is owned and administered by one person;
- keeps its authoritative record, authority, receipts, and continuity under that person's
  custody;
- keeps its non-model functions available when external model providers are unavailable;
- may use local hardware, a remote model, or both without transferring authority to the
  compute provider; and
- may later add participants or federate with another node without migrating its record or
  authority into a central service.

`Local` describes custody and continuity, not the physical location of every computation.
Remote compute is allowed through a declared data boundary. It cannot become the
node's authoritative record or authority system.

## Bring Your Own Model

**Bring Your Own Model (BYOM)** means the owner selects a compatible local or remote model
through a declared `Model Binding`.

The binding records provider, model identity, version, runtime, host, capabilities, data
boundary, cost meter, and availability behavior. These are configuration inputs, not
hidden assumptions in the product.

Changing the model must not change:

- authoritative enterprise state;
- legal operations or standing transitions;
- typed authority and refusal rules;
- receipt and provenance requirements;
- service contracts; or
- the ability to inspect and retract earlier model-caused record effects.

Changing the model may change quality, latency, cost, context limits, and supported
capabilities. The node records those differences instead of pretending the models are
interchangeable.

## Binding and adapter boundary

A **Model Binding** presents Soveraeign's operator contract to one configured model.

A **Model Adapter** translates between that binding and a named runtime or provider. The
model is the attributed operator for the run. The adapter transports the request and does
not gain authority from doing so.

Every invocation records its binding, adapter, provider, model, version, runtime, host,
input projection, omissions, data boundary, usage, cost, and receipt.

An unavailable or incompatible model refuses visibly. It does not silently switch to a
different model or fabricate success.

`contracts/model-binding.schema.json` is the proposed machine shape compiled from the
`ModelBinding` object in `SPEC.md`. Model invocation uses the proposed `invoke_model`
transition and its refusal codes. `CLASSIFICATION.md` owns the vocabulary. The pattern is
recorded in `decisions/0011-local-personal-byom.md`.

## Data boundaries

Every model binding declares one maximum data allowance:

- `LOCAL_ONLY`: model execution and supplied context stay inside the declared local host
  boundary.
- `REDACTED_REMOTE`: only an addressed projection may cross to a remote model, with
  omissions and redactions recorded.
- `REMOTE_ALLOWED`: declared source material may cross to the configured remote provider
  under an explicit grant and receipt.

The mode is an upper limit, not permission by itself. Each invocation still passes its
scope, authority, source, and operation checks.

## Portability test

Starting from one unchanged node and authoritative input state:

1. Bind two materially different models, including one supplied by the owner.
2. Discover the same named domain operation through both bindings.
3. Run it through the same kernel transition and authority rules.
4. Record model and runtime identity, input projection, usage, and cost for each run.
5. Keep the results as distinct proposals or recordings unless a governed operation joins
   them.
6. Make one configured model unavailable and observe a receipted refusal.
7. Continue inspecting, operating, and retracting local record state without that
   provider.

The test fails if a model requires its own authoritative path, a model swap changes
authority, model identity disappears from provenance, fallback is silent, or provider
loss removes local custody or operational continuity.

This is the conformance target for `PRD.md` PROD-I-9. The seed scenario is
`conformance/founding-scenarios/008-model-portability.yaml`. Oracle controls
`CONF-I9-POS` and `CONF-I9-DEF` prove only that the oracle can distinguish the positive
and defeating narratives. They do not witness a participant.

## Non-goals

BYOM does not promise that every model can perform every operation, that model outputs are
equivalent, that arbitrary model code is safe to execute, or that a remote provider may
receive data without a declared boundary.

Portability means different capable models can use one governed contract without owning
that contract. It does not mean their capabilities are identical.
