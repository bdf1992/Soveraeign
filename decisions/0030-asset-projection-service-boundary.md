# 0030 · Asset Projection Service boundary and parity target

Status: `RULED AT CONTROL RESOLUTION · OWNER ACCEPTANCE OVER EVIDENCE`

Ruled by `decisions/0033-close-the-founding-docket.md` under the acceptance
policy of `decisions/0023-acceptance-not-approval.md`.

## Decision

Define the Asset Projection Service as a fourth sibling service inside a local
Soveraeign Node, owning the retrieval surface over asset records: projection
collections, text, graph, and vector configurations, index declarations,
builds, retrieval receipts, context packages, and fidelity observations. Its
capability target is feature parity with Polygres, reached through
Soveraeign's own rules: every hit resolves to a source address and digest,
every result declares omissions, staleness is declared on the receipt,
embeddings carry binding provenance, exact and approximate are never confused,
and a projection edit returns as a Proposal.

The service reads the Asset Service through a declared read-only crossing and
never writes asset state. Everything it holds is a rebuildable projection under
the `SPEC.md` Projection rule. External indexes, an HTTP binding, Postgres- or
Polygres-backed targets, and cross-node retrieval are declared ports that
refuse `UNCONFIGURED` in Phase I.

## Evidence

- `CONTRACT.md` C1, C2, C7, C8, C9, C15
- `PRD.md` PROD-I-2, I-3, I-4, I-9; two-binding proof; non-goal "optimizing
  performance before semantic conformance"
- `SPEC.md` Projection rule; `ModelBinding` (`input_projection_id`,
  `data_boundary`); `invoke_model` refusals; Local operation
- `ENGINEERING.md` lines 45-48 (vector store and graph database "not yet
  selected"), line 185 (growth trigger), lines 171-173 (`core.py` split
  before new behaviour)
- `CLASSIFICATION.md` naming rules: `<Domain> Service`,
  `<Purpose> Projection`, `<Purpose> Port`
- `services/asset/CHARTER.md` line 74 ("SQLite FTS projection") against
  `core.py` lines 293-332 (`LIKE` scan, one-hop neighbours): the gap this
  boundary absorbs
- `reports/2026-08-23-polygres-parity-pressure-map.md`
- `services/projection/CHARTER.md` and `services/projection/PARITY.md`
- Bdo's 2026-08-23 direction: the Asset Service needs an asset projection
  service, with feature parity to what Polygres offers

## Constraints

- No runtime code before executable positive and defeating fixtures
  (`STATUS.yaml` protected boundary) and before the Asset Service `core.py`
  split, so the stream this service reads has a stable owner.
- The dense and sparse lanes wait on O12; the service never generates
  embeddings itself.
- No new runtime dependency without an observed need and a decision record:
  text and graph lanes use stdlib `sqlite3` FTS5 and recursive CTEs; any
  approximate index is a port.
- A projected value, score, or package never changes an authority check.
- No external-world effect in Phase I: external index, HTTP, and federation
  ports refuse visibly with receipts.

## Consequences

- The Asset Service's own `search_projection` and `graph_projection` become a
  compatibility path until this service exists; the Asset Service keeps
  `rebuild-projection` for them and the `graph-projection` port moves to this
  boundary on ratification. The overlap is recorded as `OPEN-SEAMS.md` S14.
- `services/asset/KNOWN-GAPS.md` gains the FTS row so charter and build agree.
- A `sov-projection` skill and workflow are needed in the harness before the
  first worker is dispatched; they are not created by this decision.

## Defaults taken

- Chose `Asset Projection` as the working name (alternatives considered:
  `Retrieval`, `Context`); renaming on ruling is a find-and-replace.
- Treated Polygres parity (`services/projection/PARITY.md`) as the current
  build target, on Bdo's 2026-08-23 direction.
- Kept the dense and sparse lanes in scope, behind the existing model-binding
  constraint (O12) rather than behind a new decision.
- Build proceeds behind the declared fixtures and the `core.py` split; the
  boundary's ratification (O21, gate `projection.ratify_boundary`) changes the
  standing word, not what may be built.

These defaults remain proposals. Work continues unless a governing constraint
is violated; Bdo may counter any of them in review.
