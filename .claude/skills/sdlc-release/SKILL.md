---
name: sdlc-release
description: Release domain competence for the SDLC loop - draft release notes, documentation, and marketing artifacts locally, and visibly refuse every external publication step the publication boundary reserves to the owner. Use when a concern's operation prepares released or published material.
---

# Release Domain Skill

Standing: the loop is accepted as the operating shape (`decisions/0024-open-decision-drain.md`,
O13) and read through `decisions/0023-acceptance-not-approval.md`: `RIGHT` is owner
acceptance over an evidenced result, not permission to begin. The implementation is a
skeleton.

This skill is mostly a refusal boundary. `PUBLICATION.md` is an active safety
boundary naming what stays unpublished until Bdo approves its disclosure.
`STATUS.yaml` `owner_holds` carries the live hold: `O1`, reason `PUBLICATION`,
blocking `repository.publish_public`. That hold blocks public release only -
every engineering and strategy task proceeds under the working name.
`AGENTS.md` restricts what publication may ever include.

## Duties

1. Draft release notes, documentation, and marketing material as
   `RECORD_LOCAL` artifacts inside the repository, at proposal standing.
2. Verify the release gate before describing anything as releasable: the
   concern's standing must have passed `BUILT` through a settled Red
   engagement receipt per `SDLC.md`.
3. Keep `lineage/`, ancestor registries, raw evidence, and source-lock
   inventories out of any publication draft; their publication needs a
   separate explicit owner instruction.
4. Refuse, visibly and with a receipt, every `EXTERNAL_WORLD` step:
   publishing, initializing remotes, enabling integrations, announcements.
   Name the blocking carrier in the refusal: `owner_holds` `O1` in
   `STATUS.yaml`, `PUBLICATION.md`, or the applicable `hold_reasons` entry in
   `contracts/acceptance-policy.json`.

## Refusals

Refuse external publication, silent staging of external effects, and any
release claim for work that has not cleared the release gate.
