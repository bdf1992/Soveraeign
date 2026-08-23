# Adapters

Adapters translate between a Soveraeign service contract and a named external
system. They do not acquire authority from the external system and cannot make
an external graph, model response, repository, or media tool authoritative.

Initial declared adapter boundaries:

| Adapter | Input standing | Allowed output |
| --- | --- | --- |
| Model provider | addressed source or declared projection within its data boundary | proposal, recording, usage/cost receipt, refusal |
| GitHub | repository, commit, and path address | captured source with exact revision provenance |
| Graph | canonical relationship records | rebuildable projection and traversal results |
| Media tool | exact asset version + declared operation | derivative recording and worker report |

Loss or absence of an adapter must produce a visible refusal or
`UNATTESTABLE` result without removing local custody or authority.

Claude, a local Ollama-compatible runtime, or another owner-selected provider is
an implementation of the same Model Adapter role. Provider-specific features
may be declared capabilities; they cannot create a second authority path.

`adapters/ollama/` is the first implementation of the Model provider row: two
declared bindings over locally hosted models, positive and defeating fixtures,
and a check suite in `scripts/verify.py`. It checks declarations and records
against a captured runtime inventory; it does not execute `invoke_model`, which
remains absent (PROD-I-9) and gated by O12. Standing: `BUILT`, self-tested, not
witnessed with dissent: an independent observer found the custody refusal defeasible
(`reports/2026-08-23-local-model-adapter-witness.md`). Standing of the pattern:
`decisions/0027-local-model-adapter.md` (proposed).
