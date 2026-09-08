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

## Amendment, 2026-09-08 · the digest table is now enforced

Added by Bdo's instruction after `scripts/sov_vendor.py` landed. Nothing above this
line is changed: the ruling, the digest table, the constraints, and the status are
as they were written. This section records a consequence of that ruling, not a
revision of it.

The Constraints above say the digest table exists so "a later reader can tell
whether the copy still matches". Until this amendment nothing performed that
comparison, and a table only a reader consults goes stale between readers.
`python scripts/verify.py` now performs it, through `scripts/sov_vendor.py`
registered as two checks. Two consequences a reader of this decision should not
have to discover from the build:

- **Editing a row in the table above is a build-affecting act.** A digest that no
  longer matches its file fails `verify`, which is this decision's own stated
  defeating condition made operative rather than merely written.
- **Adding a skill that declares bdos provenance without a row here fails too.**
  The check reads both directions.

What the check does not reach, stated so its silence is not read as coverage:

- It grades internal consistency between this file and the tree, not provenance.
  Both can move in one commit, so a row rewritten to match a rewritten copy
  passes. What holds that outside the check is `AGENTS.md`: `decisions/` is
  excluded from `grant:standing-landing-loop`, so a table edit cannot land under
  the standing grant.
- The second direction selects on the `bdos: true` marker in a skill's own
  frontmatter. A copy carried in without that marker is invisible to it.
- Whether the upstream has since edited a core cannot be answered from this
  repository. `python scripts/sov_vendor.py sync <bdos working tree>` answers it
  when someone has both trees, compares bytes rather than markers, reports rather
  than refuses, and says plainly when a reading could not be taken. It is not run
  in CI, which has no upstream tree.

It does not reimplement the `artifact_digest` each carried file already carries in
its own frontmatter. That value is bdos's, computed under bdos's rule with the
core's currency block elided so a re-stamp does not invalidate it; the digests in
the table above are plain digests of the bytes, under this repository's rule and
answering this repository's question. The two differ on both carried files. A
reader who notices two digests per file is looking at two rules, not a
disagreement.

Recording the enforcement does not ratify this decision. Its status is unchanged
and the judgement queue below is unanswered, so a build-failing gate now derives
from a table in a `PROPOSED` record. Whether that is acceptable is the second item
in that queue.

## Judgement queue for Bdo

Whether the other fourteen should be carried on the same terms, or whether the repository
should depend on `bdos`'s own installer and carry none.
