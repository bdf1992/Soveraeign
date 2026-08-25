# 0038 · The capability map: front office, back office, and which doors are open

Status: `PROPOSED · OWNER ACCEPTANCE OVER EVIDENCE`

Drafted under the acceptance policy of `decisions/0023-acceptance-not-approval.md`
and the lowest-tier rule of `decisions/0033-close-the-founding-docket.md`, Ruling 1.

## Decision

Project every declared service operation into one addressable row: the office and
counter an actor meets it at, the grant it costs, the effect class it may produce,
the actor kinds that may ask, and the activation state of every transport that could
carry it. The projection is `contracts/fixtures/capability-map.reference.json`,
built by `scripts/sovkernel/capability_map.py` from two inputs and nothing else:

- the five service manifests under `services/*/contracts/service.json`;
- `contracts/capability-offices.json`, which owns office assignment, required
  authority, effect class, actor kinds, transport policy, and the CLI commands that
  actually exist.

`contracts/capability-map.schema.json` owns the record shape. The office and counter
names are the ones `.claude/epic/offices.json` already uses; this decision introduces
no vocabulary of its own.

A Gateway is two separable things, and this decision settles only the first:

1. **the map** — which doors exist, who may use them, and what each costs. Effect
   class `RECORD_LOCAL`, buildable today, and the precondition for everything else;
2. **the transport** — actually serving those doors to a caller. Issue `#16`,
   horizon `NEXT`, and deliberately locked while `no_external_effects_in_phase_i`
   stands.

## Why the map is a projection and not a registry

A registry would be a second place where a capability is true. The map is rebuilt
from the manifests and the table alone, carries the digest of both in
`input_state_digest`, and reports `STALE` rather than answering from a stale build.
Two builds over unchanged inputs are byte-identical; `scripts/tests/test_capability_map.py`
proves it. Nothing in the map grants anything: a row names the grant an operation
requires, never one an actor holds.

The endpoint object admits no authority field at all. A transport therefore cannot
become a second authority path by construction rather than by rule, which is the
constraint `adapters/github/README.md` already states for the MCP seam.

Standing vocabulary stays with `contracts/service-manifest.schema.json`. The map
copies whatever standing a manifest declares so that a drifted manifest stays visible
rather than unrepresentable, and a standing the derivation does not recognise as
built simply never opens a door.

## What the map refuses

Six defects, each with a defeating fixture in
`contracts/fixtures/capability-map.fixtures.json`:

| Code | What it catches |
| --- | --- |
| `UNDECLARED_OPERATION` | a row for an operation no manifest declares |
| `UNMAPPED_OPERATION` | a declared operation the map omits, so the map must be total |
| `STANDING_DRIFT` | a row disagreeing with its manifest about standing |
| `COUNTER_UNKNOWN` | an office or counter the table does not declare |
| `AUTHORITY_DRIFT` | the map asking a cheaper grant than the table states |
| `SERVED_BEFORE_BUILT` | a live endpoint on an operation that does not exist |
| `EXTERNAL_TRANSPORT_ACTIVATED` | an external transport not refused in a phase that refuses it |
| `BACK_OFFICE_EXPOSED` | back-office machinery served straight to an operator |

Four further cases fail structurally at the schema: an active endpoint with no
address, a refusal with no code, an endpoint declaring its own authority, and an
effect class outside the `AGENTS.md` vocabulary.

## Observed state at drafting

57 capabilities across five services. 35 front office, 22 back office. Fourteen are
served today, all on `IN_PROCESS` or `CLI`, all belonging to `asset` and `record`.
No capability is served on `MCP`. Every `HTTP` endpoint is `REFUSED_UNCONFIGURED`
with a receipt code. Every operation requiring `ratify:judgement` is restricted to
`actor_kinds: ["HUMAN"]`, which is `AGENTS.md`'s rule that only Bdo ratifies
judgement, made checkable.

## Constraints

- No external-world effect. `HTTP` is refused in this phase by the table, and a test
  reads that refusal off the built map rather than off the policy.
- The map serves nothing. It is a read model; activating any transport is a separate
  governed operation under issue `#16`.
- `MCP` is declared operator-facing and admissible in principle, and activated
  nowhere. Standing up a local stdio MCP surface over the built `asset` and `record`
  operations is the obvious next slice and is not admitted by this decision.
- A capability with no assignment lands at `BACK/unassigned` and is reported, so an
  ungoverned door is visible rather than absent.

## Consequences

- `#14` (Registry Service) gains its executable core: the map is the versioned view
  of participants and operations that `#25`, `#19`, `#29`, and `#40` are held on.
- `#16` (Gateway Service) gains a charter input it did not have; `.claude/epic/offices.json`
  records The Door as `chartered_in: null`.
- `.claude/epic/offices.json` groups issues by office; this map groups operations by
  office. They must not disagree, and nothing yet checks that they do not.
- Two service manifests do not satisfy `contracts/service-manifest.schema.json`, and
  no check in `scripts/verify.py` currently validates them against it. Recorded as a
  residual below rather than fixed here.

## Defaults taken

- Assigned all 57 operations to an office in one pass rather than leaving any
  `unassigned`. Office placement is a judgement about where an actor meets the
  system; every assignment is reversible by editing one table entry.
- Chose `verb:noun` for `required_authority`, matching the strings the Asset Service
  already uses (`ratify:judgement`, `retract:record`).
- Restricted every `ratify:judgement` capability to `HUMAN` on `AGENTS.md`'s rule.
- Placed `console.grant`, `console.revoke`, and `console.list-grants` at
  `BACK/permits-office`, since they are authority machinery rather than operator work.
- Kept the reference map under `contracts/fixtures/` beside the other reference
  projections rather than minting a new directory.

These defaults are proposals. Work continues unless a governing constraint is
violated; Bdo may counter any of them in review.

## What would defeat this ruling

- A capability that cannot be expressed as one operation at one counter.
- An office assignment that changes what an operation is allowed to do, which would
  make the map authoritative rather than descriptive.
- A transport that must carry its own authority to be useful, which would defeat the
  no-authority-on-endpoints construction.
- Evidence that the map and `.claude/epic/offices.json` cannot be kept in agreement.

## Residuals

- `services/console/contracts/service.json` and `services/record/contracts/service.json`
  do not validate against `contracts/service-manifest.schema.json`; nothing in
  `scripts/verify.py` checks them.
- Nothing reconciles this map's office assignments against `.claude/epic/offices.json`.
- `The Door` and `drafting-window` hold zero capabilities; `permits-office` holds
  three, all from Console. That is the shape of what is not built yet.

## Movement 2026-08-24

Observed while reconciling receipt event names to capability identifiers
(`reports/2026-08-24-product-canon-attribution-discovery.md`). The ruling stands; these
lines record what moved under it, and none of them reopens it.

**Residual 1 is closed.** `scripts/verify.py` now runs `scripts/sov_service.py check`,
and it reports 8 manifests and 102 declared operations with no defect. Both manifests
named above validate. The check the residual said was absent exists and passes.

**Residual 2 stands.** Nothing reconciles this map's office assignments against
`.claude/epic/offices.json`. That gap is now the exact edge a work item would need to
name the operation it serves, and it is unchanged.

**Residual 3 has moved.** The map covers 102 capabilities across eight services rather
than 57 across five. `The Door` holds 7 and `permits-office` 17. `drafting-window` still
holds zero, which remains the accurate reading: the counter where a governed artifact is
composed before it is proposed has no operation behind it.

**The map gained a model-facing transport.** `contracts/capability-offices.json` now
carries `mcp_tools` beside `cli_commands`, so a capability served by
`bindings/mcp/manifest.json` reads `ACTIVE` on `MCP` rather than
`DECLARED_NOT_ACTIVATED`. Before this, six MCP tools were live and no input to the
derivation could carry them, so the projection that exists to say what is reachable
could not see the one reachable model surface in the node. The table and the binding are
held together by check rather than by coincidence in
`scripts/tests/test_capability_map.py`, the shape `decisions/0037` settled for the two
ticket readers.

**One capability was withheld rather than served, and the choice is Bdo's to counter.**
`bindings/mcp/manifest.json` served `record_entries`, realizing `record.read-entry`.
Activating it fires this decision's own `BACK_OFFICE_EXPOSED` defect: the table places
`record.read-entry` at `BACK/record` with `actor_kinds: ["SYSTEM"]`, and `MCP` is
declared operator-facing, so the tool handed a model operator the whole journal under no
grant. The rule was written for exactly this case and nothing could trigger it until
`MCP` became representable.

Default taken (`AGENTS.md`, Self-direction is not delegation): the endpoint is withheld
in the binding, with its reason recorded in `withheld_endpoints`, and the implementation
stays in `gateway.py`. Policy is older and accepted; the binding is `PROPOSED` plumbing,
and withholding is reversible in one entry while re-officing a capability is not.

The recorded view of the participant that took it: **the table is more likely the wrong
side than the binding.** Reading operational history is how an operator inspects why
something happened, `actor_kinds: ["SYSTEM"]` was applied to all eight `record.*` rows in
the one-pass assignment this decision records under Defaults taken, and a node whose
model operators cannot read history is less AI-native, not more. That is a view, not a
ruling. Bdo settles whether reading the journal is an operator act or back-office
machinery; either answer is one line.
