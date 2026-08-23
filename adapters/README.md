# Adapters

Adapters translate between a Soveraeign service contract and a named external
system. They do not acquire authority from the external system and cannot make
an external graph, model response, repository, or media tool authoritative.

Initial declared adapter boundaries:

| Adapter | Input standing | Allowed output |
| --- | --- | --- |
| Model provider | addressed source or declared projection within its data boundary | proposal, recording, usage/cost receipt, refusal |
| GitHub (read) | repository, commit, and path address; issue, pull request, and branch refs | captured source with exact revision provenance, and a capture receipt |
| GitHub (write) | one owner-approved board action: a label on an issue, or a merged branch ref | an `EXTERNAL_WORLD` receipt per attempt, including refusals and failures |
| Graph | canonical relationship records | rebuildable projection and traversal results |
| Media tool | exact asset version + declared operation | derivative recording and worker report |

Loss or absence of an adapter must produce a visible refusal or
`UNATTESTABLE` result without removing local custody or authority.

Claude, a local Ollama-compatible runtime, or another owner-selected provider is
an implementation of the same Model Adapter role. Provider-specific features
may be declared capabilities; they cannot create a second authority path.
