# Adapters

Adapters translate between a Soveraeign service contract and a named external
system. They do not acquire authority from the external system and cannot make
an external graph, model response, repository, or media tool authoritative.

Initial declared adapter boundaries:

| Adapter | Input standing | Allowed output |
| --- | --- | --- |
| Claude | addressed source or declared projection | proposal, recording, usage/cost receipt, refusal |
| GitHub | repository, commit, and path address | captured source with exact revision provenance |
| Graph | canonical relationship records | rebuildable projection and traversal results |
| Media tool | exact asset version + declared operation | derivative recording and worker report |

Loss or absence of an adapter must produce a visible refusal or
`UNATTESTABLE` result without removing local custody or authority.
