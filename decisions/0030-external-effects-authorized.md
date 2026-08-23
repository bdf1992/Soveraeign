# 0030 · External effects are scoped, not refused

Status: `OWNER-DIRECTED · ACCEPTED AS acceptance/accepted/A4.json`

## Decision

`SPEC.md` no longer refuses `EXTERNAL_WORLD` by effect class. An external effect
is admitted when it names a scope `contracts/external-effect-authorization.json`
declares, uses a verb that scope carries, and leaves a receipt. Every other
external effect is refused, and every verb the contract refuses by name stays
refused whatever scope is claimed.

Two scopes are declared:

- `coordination.issue_metadata` — labels, project fields, open/closed state, and
  comments on this repository's own issues and pull requests.
- `coordination.branch_write` — pushing a new branch, fast-forwarding one, and
  opening a pull request.

Ten verbs are refused by name: force-push, shared-branch deletion, repository
deletion, branch-protection changes, visibility changes, secret writes,
repository-settings changes, merging a pull request, acting on any other
repository, and spending money.

Compensation is forward only. A counteraction records the original occurrence,
the remedy attempted, and what remains changed. A receipt claiming an external
effect was rolled back is a defect, which `CONF-I5-DEF` already fails.

## Why the class refusal went

It was doing two jobs. One was keeping irreversible acts behind an owner, which
is real. The other was keeping ordinary board work behind one too, which is what
left forty-four issues and seven pull requests unmanaged while every agent was
forbidden to touch them. Separating the jobs keeps the first and drops the
second.

The refusal is narrower now, not weaker. Before, one boundary said "no external
effects" and nothing checked which verb an adapter would actually use. Now the
verb is checked, the scope is checked, the receipt is checked, and each check has
a defeating fixture.

## What moved

- `SPEC.md`, effect classes — the `EXTERNAL_WORLD` clause is rewritten. The
  kernel table recompiles from it and `scripts/sov_kernel.py selfcheck` passes.
- `contracts/external-effect-authorization.json` — new, and the only place a
  scope may be added.
- `contracts/kernel-transitions.json`, `contracts/ticket-transitions.json` —
  `phase_refused_effect_classes` is gone; both refuse with
  `EXTERNAL_EFFECT_UNAUTHORIZED` and both read the same authorization contract,
  so `scripts/sov_kernel.py parity` holds.
- Both transition request schemas carry an `authorization` block, with `receipt`
  explicit and nullable: a request intending to leave no record is legal in shape
  and refused by the guard.
- Fixtures: `K-013`, `K-017`, `K-018`, `TC-015`, `TC-018`, `TC-019`, `TC-020`,
  `TC-021`, `TC-022`.
- `STATUS.yaml` — `no_external_effects_in_phase_i` becomes four narrower
  boundaries: no effect outside a declared scope, none without a receipt, no
  refused verb reachable through any scope, and no claim that an effect was
  rolled back. O7 and O16b move from holds to rulings.

## What this does not do

- It does not build a crossing. No adapter performs an authorized effect yet.
- It does not make the repository public. That is O1, still held, still blocking
  exactly `repository.publish_public` and nothing else.
- It does not admit any other target. Every scope names one repository.
- It does not authorise merging. Merging is settlement and belongs to the owning
  seat, proved by `TC-021`.

## Residuals

Named in `acceptance/accepted/A4.json`: no adapter exercises this, receipt
ordering relative to the attempt is unproven, and nothing checks that a scope's
stated inverse verb is genuinely inverse.

## Source and authority

Bdo, 2026-08-23 interactive session: "unblock it all". Built by the control seat
and accepted by the root seat under `0028`; the record is
`.local/acceptance/ledger.ndjson`.
