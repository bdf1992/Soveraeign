# 0067 · The authoritative half of a ticket becomes writable

Status: `OWNER-DIRECTED · RULED AT CONTROL RESOLUTION`

## Decision

Add `set_body` to the `coordination.issue_metadata` scope in
`contracts/external-effect-authorization.json`, under two declared
preconditions: the body being written must validate against
`contracts/issue-metadata.schema.json`, and the body as it stood before the
write must be recorded in the receipt.

Basis: Bdo, 2026-08-26 interactive session, directing a refinement pass over
every issue that updates metadata, comments, and bodies. That is the same form
as the 2026-08-23 "unblock it all" direction already recorded in the contract's
`authorized_by.basis`.

## What was actually wrong

`CONTRIBUTING.md` states that the YAML block at the top of an issue is the
authoritative contract and that display labels are projections of it, never a
second authority. `contracts/external-effect-authorization.json` then
authorized `set_label`, `remove_label`, `set_project_field`, `set_state`, and
`comment`, and no verb at all for the body.

So the projection was writable and the source was not. An agent finding a
ticket whose labels disagreed with its metadata block had exactly one
authorized repair available: change the labels to match the block, including
when the block was the half that was wrong. The declared scope pushed toward
making the coordination surface agree with a stale record rather than
correcting the record.

Nothing exploited this, because nothing could: `adapters/github/apply.py`
admits `LABEL_ADD`, `LABEL_REMOVE`, `LABEL_CREATE`, and `BRANCH_DELETE` and
falls through to no generic call. The gap showed up as work that could not be
done rather than as a write that should not have happened.

## The preconditions, and why they are not decoration

A body write is the one coordination verb that can manufacture a defective
ticket. Every other verb in the scope moves a value between declared states; a
body write authors the record the whole projection derives from. Requiring the
written block to validate makes this verb unable to produce a ticket the
schema refuses, which keeps `sov_epic.py validate` and `sov_ticket.py` reading
a surface no authorized write could have broken.

Recording the prior body is what makes the write reversible in the sense
`reversible_by` claims. A label is restored from the catalogue; a body can only
be restored from a copy of itself. Without the snapshot the scope would be
claiming a reversibility it does not have, which is the defect
`compensation_model` exists to prevent.

## What this does not admit

`merge_pull_request`, `force_push`, `change_branch_protection`,
`change_repository_visibility`, `write_secret`, `change_repository_settings`,
`delete_repository`, `act_outside_this_repository`, and `spend_money` remain
refused by name. Nothing here touches a pull request body, another repository,
or a ticket's standing: writing `standing: WITNESSED` into a block is a claim
about evidence, and the evidence rules in `AGENTS.md` govern whether it is true
regardless of who may type it.

## Change protocol record

1. **Requested outcome and current state.** Before: five verbs, none of them
   able to correct the authoritative record. After: six verbs, the new one
   guarded by two preconditions and a new refusal code.
2. **Affected.** `contracts/external-effect-authorization.json` (`verbs`,
   `preconditions`, `reversible_by`, `note`, `governed_by`,
   `authorized_by.basis`, `refusal_codes.EXTERNAL_EFFECT_PRECONDITION_UNMET`).
3. **Preconditions and expected result.** `verify.py` green; the scope reads
   as one an agent can act inside without inventing an authority.
4. **Effect class.** The contract edit is `RECORD_LOCAL`. What it authorizes is
   `EXTERNAL_WORLD`, receipted like every other crossing.
5. **Rollback.** Remove the verb and its preconditions. Bodies already written
   are restored from the recorded prior bodies under `.local/registrar/
   bodies-before/`.

## Residual

`adapters/github/README.md` describes a write half that renders the containment
edge and an issue body's delimited relations block, with a
`.local/registrar/bodies-before/` snapshot behind it. `apply.py` implements
none of that: it admits four action kinds, none of which touches a body. The
README documents a crossing that does not exist, which is a divergence in the
direction that matters least — the code is narrower than its description — but
it is still a governed document describing a capability the repository does not
have. Repairing it is a separate concern against the registrar, not against
this scope.

## What would defeat this

A body write that lands a block the schema refuses, which would mean the
precondition is declared and not enforced. Or a restore from
`.local/registrar/bodies-before/` that does not reproduce the prior body,
which would mean `reversible_by` is claiming more than the snapshot supports.

## What still waits on Bdo

- Whether a body write should also be admitted on a pull request body. This scope
  names issues and pull requests as its target and the verb is used only on issues
  today; a pull request body carries no ticket block, so the validating precondition
  has nothing to check against it.
- Whether the containment edge, which `plan.py` derives and nothing executes, should
  get an action kind of its own or stay a manual link on the coordination surface.
