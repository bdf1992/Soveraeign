# 0024 · Unblock request as a ticket kind

Status: `OWNER-DIRECTED · WORDING PROPOSED`

## Decision

Add `unblock` to the ticket kind enum in `contracts/issue-metadata.schema.json`.
Blocked stops being a status anywhere in the system. A ticket that cannot
advance files an unblock request: a linked ticket that names the held ticket,
the exact unavailable transition, the missing precondition, the governing
rule, the provision that would satisfy it, the tier that asked, the tier
asked, the condition a receipt will settle, and the claim
`reachable_alternative: NONE`. The held ticket lists the request in its
`requires`, so it reads as held-by, like any other dependency edge.

The request is then worked like any other ticket, by the tier it names: a
worker serves a fixture or contract, an orchestrator or controller serves a
grant or observation, the owner serves a judgement. A blocked orchestrator is
assisted by a controller; a blocked controller by the owner; a blocked owner
may be served by a worker. `contracts/ticket-queue-policy.json` declares which
tiers may serve which provision, and the queue sorts the request up by what
it holds. `provision:` and `serve:` labels make the queue typed and coloured
on the coordination surface itself.

## What the schema refuses

- `reachable_alternative` other than `NONE`: if an admissible path exists,
  the held ticket is gated, not blocked, and no request is admitted
  (`AGENTS.md`, Blocked edge is not blocked frontier).
- `requires` on the request: if some ticket will already produce the
  provision, the held ticket requires that ticket directly and is
  dependency-mapped, not blocked. A request exists only when no ticket will
  produce the provision.
- a `judgement` provision addressed to any tier but `owner`: judgement is
  owner-held, and a request for it routed elsewhere is a widened grant.
- `stub_id`, `bit_id`, `engagement_id`, `story_id`: a request asks for a
  provision; it is not itself the surface that closes it.

Positive and defeating cases: `conformance/fixtures/tickets/metadata-cases.json`
MC-021 through MC-028.

## Why a kind and not a flag

Bdo's 2026-08-23 direction: blocked should become a ticket exactly the way a
defect does, worked by provisioned agents, so that a typed and coloured queue
of unblock requests becomes the flywheel rather than a list of stalls.

A `blocked` flag is an executor self-report with no work attached: no surface
a model can act on, no source for the claim, no way to counter it. Against
`AI-NATIVE.md` that fails reachability, provenance, and retraction. A ticket
passes all three. It also makes the `BLOCKED` proof in `AGENTS.md`
mandatory rather than available, because the proof fields are the required
fields of the kind. And it separates two things the old flag collapsed:
dependency-mapped work, which is held by an edge and shows its whole chain,
and genuinely blocked work, which has no edge to anything until a provision
is asked for.

## Change protocol record

1. **Requested outcome and current state.** Before: `blocked` was a boolean
   on the queue projection, a flag in every workflow plan schema, and a word
   in `AGENTS.md` with a proof shape no record enforced. After: a kind with
   eight required fields, six refusals, a routing table, and labels.
2. **Affected.** `contracts/issue-metadata.schema.json` (kind, ten
   properties, two conditional rules), `conformance/fixtures/tickets/
   metadata-cases.json` (eight cases), `contracts/ticket-queue-policy.json`
   (`kind_rank`, `provision_routes`), `contracts/ticket-label-projection.json`
   (`provision_to_label`, `serve_to_label`, two prefixes), `.github/labels.yml`
   (eleven labels), `scripts/sovticket/labels.py` (projects the two new
   axes), `scripts/sovepic/walk.py` and `survey.py` (the kind is workable),
   `scripts/tests/test_sov_ticket.py`, `CONTRIBUTING.md`, `AGENTS.md` (one
   sentence linking doctrine to mechanism), `OPEN-SEAMS.md` S15.
3. **Preconditions and expected result.** Before: 20 metadata cases pass.
   After: 28 pass; `sov_ticket.py selfcheck` green; `verify.py` green; the
   walker accepts an unblock ticket as workable and labels it.
4. **Effect class.** `RECORD_LOCAL`. Label synchronization to GitHub remains
   behind O16 (`coordination.activate_external_effects`).
5. **Rollback.** Revert the files above; no standing, grant, or protected
   boundary changed.

## Defaults taken

- Kind name `unblock` (the request, not the state). Alternatives
  considered: `provision-request`, `blocker`.
- Provision vocabulary: `grant`, `judgement`, `contract`, `fixture`,
  `capability`, `observation`. Tier vocabulary: `worker`, `orchestrator`,
  `controller`, `owner`, matching `SDLC.md` tiers plus the owner.
- `provision_routes` as declared data in the queue policy; serving a grant
  or judgement still needs the live grant the kernel checks.
- `kind_rank` puts `unblock` first; the practical ordering comes from
  `unblocks_count_desc`, which an unblock request always carries.
- Label prefixes `provision:` and `serve:`; colours reuse the purple and
  green families already in the catalogue.
- No open decision minted. The only genuine seam is the overlap with the
  Console Service's judgement request, recorded as S15 for the Console
  charter to resolve by projection, not by a second queue.
- The workflow plan schemas keep their `blocked` boolean for now; under
  decision 0023 a scope agent sets it only when no admissible operation
  exists, and the next bounded operation is to have that path emit an
  unblock ticket draft instead of a bare flag.

These defaults remain proposals. Work continues unless a governing constraint
is violated; Bdo may counter any of them in review.
