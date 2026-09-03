# 0103 · Carry two bdos cores into the harness

Status: `OWNER-DIRECTED · PROPOSED`

Bdo named `github.com/bdf1992/bdos` in session when asked which skills this repository
should use. This carries two of its sixteen cores into `.claude/skills/` and states why
those two and not the rest.

## Decision

`.claude/skills/can-it-run-doom/SKILL.md` and `.claude/skills/draw-the-owl/SKILL.md` are
byte copies of the same files at `bdf1992/bdos@e715cb11`, `cores/<name>/SKILL.md`. MIT,
Copyright 2026 Bdo. Digests at carry:

| Skill | sha256 |
| --- | --- |
| `can-it-run-doom` | `3336bb53892b1bac4fdb72b6531654acd38cab03116c2c2b463425e2387a495d` |
| `draw-the-owl` | `4796bd13a76da28b7b0392df104ef276360788b867262195ec7fbf528907b7b7` |

## Why these two and not the other fourteen

`AGENTS.md`, Repository protections: an ancestor is carried forward through an invariant,
decision, fixture, schema, or reviewed implementation, never imported wholesale. Sixteen
cores copied because they exist is the wholesale import that rule refuses.

Both of these were used in this repository before being carried, and each produced a
result the record holds:

- `can-it-run-doom` was applied to the Observation Service thin slice and returned a
  missing primitive: a declared relation selector that would make four of the five direct
  edges rows of one composition, with the charter's own "lease, fence, or session" edge
  expressible as a fifth row rather than a sixth function. That finding is the next
  bounded operation in `reports/2026-09-03-phase-1-5-commissioning-pass.md`.
- `draw-the-owl` describes the shape the same session's three witness passes actually
  took: a complete inspectable attempt first, then redraws of the same target from marks,
  with what was adopted left alone.

The other fourteen are unexercised here. They can be carried the same way, one at a time,
when a concern uses one and the use produces something.

## Constraints

- These are host plumbing under `.claude/`. `AGENTS.md` already fixes that the harness
  holds no standing or authority; a skill changes how a participant works and settles
  nothing.
- Neither core reaches the network, writes a repository record, or claims an effect. Both
  are `RECORD_LOCAL` reading instructions.
- The upstream is the source of truth for their wording. A copy here drifts the moment
  bdos edits them, which is what the digest table is for: a later reader can tell whether
  the copy still matches, and `bdos` ships its own installer for anyone who wants the
  whole set under `~/.claude/skills`.

## Defaults taken

- **Byte copies rather than a submodule or a build step.** The repository has no
  submodules and adds a runtime dependency only against a named boundary and an observed
  need. Two files are cheaper than either.
- **The bdos `metadata:` block is kept verbatim**, including fields this host does not
  read. Editing an upstream file to fit local taste is how a copy stops being a copy.

## What would defeat this ruling

- Either file drifting from the upstream digest above without a decision saying so.
- A carried core turning out to reach the network, write a record, or claim authority.
- The fourteen arriving later without each one naming the use that earned it.

## Judgement queue for Bdo

Whether the other fourteen should be carried on the same terms, or whether the repository
should depend on `bdos`'s own installer and carry none.
