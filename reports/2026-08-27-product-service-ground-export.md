# Product and service ground: an export, and the collapse-to-7 check

An export of `GROUND.md` plus the seven `SERVICE-GROUND.md` files
`decisions/0067` produced, plus the check its own scope note deferred: is
seven the right number, or an artifact of which names got listed? Short
answer: **the collapse is real but it isn't to seven — it's to ten, and seven
was which names got recalled, not a principled boundary.** Full accounting
below.

## Part 1 — Product Ground, `GROUND.md`'s sixteen claims

| ID | Claim |
| --- | --- |
| `GROUND-001` | custody stays with the enterprise |
| `GROUND-002` | one governed world |
| `GROUND-003` | authority is granted, never acquired |
| `GROUND-004` | you act by crossing a declared operation |
| `GROUND-005` | a consequential act binds to exact state |
| `GROUND-006` | the node is discoverable from the artifact alone |
| `GROUND-007` | every crossing leaves a record |
| `GROUND-008` | refusal is an outcome |
| `GROUND-009` | correction never erases occurrence |
| `GROUND-010` | a report is not an observation |
| `GROUND-011` | standing does not collapse |
| `GROUND-012` | human judgement is reserved and scarce |
| `GROUND-013` | the model is substitutable |
| `GROUND-014` | effort resolves to intention |
| `GROUND-015` | work survives the loss of context |
| `GROUND-016` | a node is whole at any size |

## Part 2 — the service map as it actually stands: ten, not seven

`services/` holds ten directories with a real `CHARTER.md`. `decisions/0067`
was applied to seven of them — the seven names that came up when this
conversation was recalling them from memory. Three chartered services were
never in scope, not because of any ontological test, just because nobody
named them:

| Service | Charter standing | Got SRD/Spec/Ground/Journeys? |
| --- | --- | --- |
| Identity | `PROPOSED · PLACEMENT PROVISIONAL` | yes |
| Console | `PROPOSED SERVICE BOUNDARY` | yes |
| Registry | `BUILT` (one operation) | yes |
| Host | `BUILT` (one operation) | yes |
| Asset | `PROPOSED VERTICAL-SLICE BOUNDARY` | yes |
| Gateway | `PROPOSED SERVICE BOUNDARY` | yes |
| Record | `BUILT_SELF_TESTED_NOT_WITNESSED` | yes |
| **Proofing** | `PROPOSED SERVICE BOUNDARY · NOT IMPLEMENTED` | **no** |
| **Projection** | `PROPOSED SERVICE BOUNDARY · NOT IMPLEMENTED` | **no** |
| **Observation** | `PROPOSED` chartered, nothing implemented | **no** |

This is the first concrete finding: the "collapse to 7" worry is justified,
but the actual gap it should point at is that **Proofing, Projection, and
Observation have exactly as much claim to a `SERVICE-GROUND.md` as the seven
that got one, and don't have one.** Nothing about them makes them less real —
Proofing and Projection are both named in `CLASSIFICATION.md`'s own "Initial
service map" section (see Part 4) alongside Asset and Console, two of the
seven that did get the treatment.

## Part 3 — the seven service grounds, compressed

| Service | Claim IDs | Titles |
| --- | --- | --- |
| Identity | `SVC-IDENTITY-GROUND-1..7` | a token/secret exists in exactly one place · verification is never authority · a challenge keeps its declared window · what may be asked is readable from the artifact · every attempt is journalable, none durable here · revocation counters without erasing · a root with no live recovery is reported terminal |
| Console | `SVC-GROUND-1..9` | a judgement request never blocks the node · only a human resolves judgement · a declared authority requirement is checked for the class it names · an operator setting never widens authority · correction is a new record · a projection resolves to the record it names, twice · refusal is legible · a record stays scoped to its node · an observation of this service is not its own report |
| Registry | `SVC-GROUND-REGISTRY-1..6` | a resolution never outruns its sources · the Registry answers where, never what · resolving grants nothing · an owner is never its own witness · retiring an owner counters, never erases · human and model callers see the same answer |
| Host | `SVC-HOST-GROUND-1..7` | an OS credential never becomes SOV authority through Host · the declared boundary is the process execution host, never the physical machine · an unsupported reading is declared missing, never fabricated · every crossing leaves a durable receipt · actor kind alone never substitutes for a live grant · a raw adapter diagnostic never reaches a receipt/log/caller · a mutating host effect never settles on the executor's own report |
| Asset | `AG-1..7` | captured bytes stay exactly what was captured · a recording is never called that unless reconstructible · nothing here is authoritative merely by being claimed · every attempted operation leaves a receipt · retraction never deletes the record it counters · search/graph results are never a second authoritative store · a grant here expires, never a permanent credential |
| Gateway | `G-GW-1..6` | a caller acts by crossing a declared address, not by having access · refusal is legible and distinct from failure · every crossing leaves a record · what comes back is the owning service's receipt, unchanged · neither human nor model gets a private door · a network transport does not open itself |
| Record | *(unlabeled, 6 claims)* | a journal row, once committed, is never mutated or deleted · retraction preserves the countered entry · every entry binds to the exact digest of the entry before it · a projection cannot become the record · this journal is verifiable without trusting this service's own code · every crossing into this journal leaves a durable attributable record |

50 service-level claims total, none claiming `WITNESSED` or `RATIFIED`
standing — all `BUILT` at most, self-reported by the drafting session, per
`decisions/0067`.

## Part 4 — where `CLASSIFICATION.md` itself has already drifted

`CLASSIFICATION.md` — the document that owns the canonical vocabulary,
including the word "Service" — carries its own "Initial service map" section.
It names exactly **four** services: Asset, Proofing, Console, Asset
Projection. That's the map the canonical vocabulary contract still shows.
It does not mention Identity, Registry, Host, Gateway, or Observation at
all — five of the ten real chartered services are invisible in the document
that is supposed to be the source of truth for what a Service is. This is
the same failure mode Registry's own charter names about the eight
hand-maintained tables it exists to reconcile (`services/registry/CHARTER.md`,
"drift silently and a reader has no single place to start") — found here in
the document one level above all of them.

## Part 5 — cross-cutting concern traversal

Two independent cuts exist through the service set, and they don't fully
agree, which is itself informative.

**Cut 1 — `CLASSIFICATION.md`'s own declared cross-cutting foundations**
(things that are not services by definition, used by every service):

| Foundation | What it covers | Named service(s) built against it |
| --- | --- | --- |
| Shared Kernel | typology/topology/traversal/invariant grammar, gates, standing, typed authority, transitions, observation, settlement, receipts, retraction | all ten — `contracts/kernel-transitions.json` |
| Runtime | computation/operator/inputs/configuration/authority/resources/state/time/observation/effects as one attributable event | all ten |
| Record substrate | addressed sources, immutable payloads, revisioned records, provenance, reconstruction authority | overlaps directly with the **Record Service** — CLASSIFICATION.md lists "Record substrate" as a foundation and also charters a Record Service; the document does not say which one is which when they conflict |
| Atlas, Gauge, Definition, Pedagogy, Observation | "capabilities until evidence gives one an independently useful service boundary" | Observation alone crossed that bar (chartered, `services/observation/`); Atlas, Gauge, Definition, Pedagogy have no footprint anywhere else in the repository — not in the epic tree, not in any charter |

**Cut 2 — `decisions/0068`'s empirically-found themes**, from the seven
`JOURNEYS.md` files, mapped against Cut 1:

| 0068 theme | Services (n/7) | Maps onto a Cut-1 foundation? |
| --- | --- | --- |
| Secret/credential custody | 6/7 | **No existing category.** Not Shared Kernel, not Runtime, not Record substrate. A genuine ontological gap, not just an implementation gap. |
| Authority-grant issuance/ownership | 3/7 | Shared Kernel (typed authority) — but Shared Kernel enforces grants, it doesn't say who *issues* one; that half is uncovered by any foundation |
| Node composition/assembly root | 3/7 | No foundation names this; `CLASSIFICATION.md`'s "Node" entry implies something must own it but nothing is named |
| Admission of verified state into a registry | 2/7 | Record substrate (partially) — writing IS what Record substrate is for, but nothing routes Identity's output there |
| Asset↔Record journal wiring | 2/7 | Record substrate directly — this is exactly what it's for, and it's still unbuilt between the two services that would use it |

The finding: three of five empirically-discovered cross-cutting concerns
(secret custody, composition root, and half of authority-grant ownership)
have **no home in the existing ontology at all** — not merely unimplemented,
genuinely uncategorized. `CLASSIFICATION.md` would need a new row, not just a
new charter, to make secret custody or "who assembles the node" a
first-class concern the way Shared Kernel or Runtime already are.

## Part 6 — full ontological inventory: the epic tree against the built world

The epic-tree villages (`.claude/epic/tree.json`) are the system's own
enumeration of "everything this might need" at service-or-larger grain.
Cross-referencing all of it against `services/` gives the actual size of the
"possible concern space" versus what's chartered:

| Status | Count | Villages |
| --- | --- | --- |
| **Chartered, real `services/` directory** | 10 | Asset (`#8`/`#27`), Identity (`#11`), Registry (`#14`), Gateway (`#16`), Proofing (`#22`/`#28`), Observation (`#9`, "Observation and Attestation"), Console (drift — not in tree), Host (drift — not in tree), Record (`#7`/`#65`), Projection (drift — not in tree by name) |
| **Named village, no charter, no evidence pressure from 0068** | 8 | Graph Service (`#10`), Security and Gates (`#13`), Relay Service (`#17`), Runtime and Workers (`#18`), Bindings and Adapters as a formal boundary (`#19`), Workflow Service (`#20`), Automation Service (`#21`), Federation Horizon (`#24`) |
| **Named village, no charter, evidence pressure found by 0068** | 2 | Authority Service (`#12`), Capability Broker (`#15`) |
| **Named in `CLASSIFICATION.md` only, zero epic-tree or charter footprint** | 4 | Atlas, Gauge, Definition, Pedagogy |
| **Cross-cutting foundation, not eligible to become a service** | 2 | Shared Kernel (`#6`/`#25`/`#26`), Record substrate (overlaps `#7`/`#65`) |
| **Component, not eligible to become a service** | 1 | Adapters (github/ollama/host translations; epic `#19`/`#29` name the boundary, but `CLASSIFICATION.md` fixes its structural kind) |

Three services (Console, Host, Projection) are built and chartered but
**absent from the epic tree entirely** — the tree undercounts the built world
by three, in the opposite direction from the seven-vs-ten gap in Part 2.
Between the two drifts, no single document in the repository currently lists
all ten real services in one place.

## What this export is not

Not a ruling, not a chartering act, and it resolves none of `decisions/0068`'s
thirty-one open questions or adds new ones. It is a reading of what already
exists across `GROUND.md`, the seven `SERVICE-GROUND.md` files,
`CLASSIFICATION.md`, and the epic tree, side by side, so the shape of the
gap is visible rather than asserted. Two concrete follow-on concerns fall out
of it, each its own bounded piece of work per `AGENTS.md` Closure ownership:

1. Apply `decisions/0067` to Proofing, Projection, and Observation — the
   three chartered services that have exactly as much claim to the pattern
   as the seven that already have it.
2. Refresh `CLASSIFICATION.md`'s "Initial service map" to name all ten real
   services, and open a scoping question on whether secret custody and node
   composition need a new ontological category (not just a new charter) —
   Part 5 found neither has a home in the vocabulary contract as it stands
   today.
