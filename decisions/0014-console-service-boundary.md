# 0014 · Console Service boundary

Status: `RULED AT CONTROL RESOLUTION · OWNER ACCEPTANCE OVER EVIDENCE`

Ruled by `decisions/0033-close-the-founding-docket.md`.

## Decision

Define the Console Service as a third sibling service inside a local
Soveraeign Node, owning the operator-facing session: operator sessions,
channels, threads, posts, notifications, judgement requests, operator settings,
and declared dashboard and activity projections. The threaded, domain-driven
operator interface is a Human Binding over this service; a Model Binding reads
the same records as typed structure.

The Console Service surfaces pending rights and spent judgement; it never
holds, infers, or delegates a right. Its dashboards and activity views are
rebuildable projections. External delivery and cross-node activity are declared
ports that refuse `UNCONFIGURED` in Phase I.

## Evidence

- `CONTRACT.md` C1, C3, C4, C6-C9
- `PRD.md` PROD-I-3, I-4, I-5, I-6; two-binding proof; non-goal "graphical
  production interface"
- `SPEC.md` Interface parity and Projection rule; `EventEnvelope`, `Receipt`,
  `AuthorityGrant`
- `SYSTEM.md` Initial subsystems: Atlas, Observation, Interfaces
- `bindings/README.md` human-facing binding requirements
- `CLASSIFICATION.md` Participation and boundary roles; naming rules
- `services/console/CHARTER.md`
- Bdo's 2026-08-22 direction to build a session-based interface surfacing
  notifications, settings, admin dashboards, human-in-and-on-the-loop
  workflows, and distributed activity reporting, threaded and domain-driven

## Constraints

- No runtime code before the logical specification and executable defeating
  fixtures (`STATUS.yaml` protected boundary); no binding implementation before
  the transition contract is frozen or a provisional target is authorized.
- A setting, session, dashboard role, or thread state never changes an
  authority check.
- A judgement request queues without blocking and is never hidden.
- Every projected value resolves to a source address and digest and declares
  omissions.
- No external-world effect in Phase I: delivery and federation ports refuse
  visibly with receipts.

## Open authority

The source corpus establishes same-world parity, non-blocking judgement
accounting, and the projection rule, but does not name a console as a service
boundary. Whether it is the accepted third boundary, whether `Console` is the
accepted name (alternatives: `Session`, `Operator`), and whether Bdo authorizes
a provisional binding target ahead of O10 remain Bdo's judgement (O18).
