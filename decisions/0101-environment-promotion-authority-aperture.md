# 0101 · Environment promotion uses exact scoped authority

Status: `OWNER-DIRECTED · ACCEPTED POLICY`

Accepted by Bdo (`seat:root`) on 2026-08-30 while reviewing the first local
Environment / Trunk / Deployment proving vertical (#189 / #190 / #191). The
building session recorded the decision as scribe; the judgement is the owner's.

## Decision

Admit one narrow authority aperture for the proving vertical without opening the
broader Authority Service (#12):

- the capability is `environment.promote`;
- it reuses the existing authority classes `VERIFICATION` and `JUDGEMENT`;
- a grant covers an Environment promotion only when its scope identifies the exact
  pattern digest, trunk instance, source instance, target instance, candidate
  revision, and artifact digest;
- those fields are equality-scoped. An environment name, branch name, prefix,
  successful test, lease, witness role, or caller-supplied authority label cannot
  widen them;
- `repository.land` remains a separate capability. Permission to move an exact
  Environment candidate and permission to land repository bytes are different
  crossings and neither implies the other.

The aperture is represented as an optional exact `scope.environment` resource in
`contracts/authority-grant.schema.json` and enforced by the existing
`sovkernel.authority` evaluator. Existing repository path-scoped grants keep their
existing semantics.

## What this decision does not grant

This decision admits the **rule**, not a blanket authorization. It does not create
or ratify a standing `environment.promote` grant for the builder, witness, CI, or
any other participant. A concrete crossing still requires a separately supplied,
valid, unrevoked, unexpired grant whose actor, capability, authority class, effect
ceiling, evidence preconditions, and exact Environment resource cover the request.

`JUDGEMENT` remains owner-issued. Production-style crossings that additionally
require explicit acceptance cannot infer it from CI green or from a VERIFICATION
grant.

## Phase boundary

The same root ruling explicitly **does not open Phase 2 or any successor phase**.
`STATUS.yaml` remains `phase: NONE_ACTIVE` and historical `phase:i` remains
`CLOSED_INCOMPLETE` with no successor inferred by this work.

The owner wants Phase 2 to be a specific discussion whose readiness is earned by
working evidence rather than created by this vertical's existence. Environment
work may therefore continue only within the already-declared reversible proving
boundary; it cannot use this decision as phase authority.

## Witness reading

The owner is a legitimate human/root witness of the judgement recorded here and
of product-intent or acceptance decisions they directly make or observe. That is
not the same claim as independent technical reconstruction of code produced by the
building session. #191 still needs an independent participant that did not build
or read the implementation to reconstruct the exact candidate before any witness
standing is claimed.

## Defeating cases

This decision is defeated if any of the following becomes possible:

- `--authority VERIFICATION` or another caller label admits a crossing without a
  covering AuthorityGrant;
- a grant for one target, trunk, revision, or artifact authorizes another;
- an Environment name confers authority;
- a lease, CI result, or observation silently becomes a grant;
- `repository.land` is treated as `environment.promote` or vice versa;
- accepting this authority rule is interpreted as opening Phase 2;
- the builder's own tests or account are recorded as the independent technical
  witness of the candidate.

## Evidence / relationships

- #12 — broader Authority Service; this decision consumes only its minimal aperture.
- #173 — permits a narrow `VERIFICATION` / `JUDGEMENT` authority aperture for one
  proving vertical when explicitly ruled by root.
- #189 — generalized Environment and Delivery obligation.
- #190 — local SDLC implementation stub.
- #191 / draft PR #192 — first proving implementation of this rule.

This decision changes authority policy only at the exact Environment crossing
boundary above. It neither completes #12 nor ratifies #173, #189, #190, or #191.
