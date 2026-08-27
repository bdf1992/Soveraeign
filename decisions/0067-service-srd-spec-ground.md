# 0067 · Service SRD, Service Spec, Service Ground, and journey maps

Status: `PROPOSED`

## Decision

The root design System of Record (`PRD.md`, `SPEC.md`, `GROUND.md`) speaks about
one user of the whole Node: Bdo, human operators, and model operators. Nothing
at that fidelity exists for a service's own caller, and a service's own caller
is usually not a human at all — it is Soveraeign itself: the Gateway routing
into it, another service depending on it, an operator binding invoking it
through the Node Interface. Charters state a service's *role*. They do not
state, at requirement/spec/ground fidelity, what that service owes the node
that depends on it, or where its callers' journeys currently stop short.

Add four documents per chartered service under `services/<domain>/`, scoped
copies of the root pattern with the node as the named user rather than a
human, plus one new artifact the root pattern has no analog for:

- **`SRD.md`** — Service Requirements Document. Mirrors `PRD.md`'s shape:
  product outcome (one sentence, scoped to this service), enumerated callers,
  numbered requirements `SVC-<DOMAIN>-<n>` each with a defeating case, each
  citing which `PROD-I-<n>` it serves if any, non-goals. Same
  `OPEN → BUILT → WITNESSED → RATIFIED` lifecycle as `PRD.md` requirements.
- **`SERVICE-SPEC.md`** — mirrors `SPEC.md`'s shape at service scope: owned
  domain records, service-local states, legal transitions (citing
  `contracts/kernel-transitions.json` and `services/<domain>/contracts/service.json`
  rather than re-deriving them), refusal reason codes, persistence and
  authority notes. Named `SERVICE-SPEC.md`, not `SPEC.md` — the root document
  owns that name and a per-service file must not appear to compete with it.
- **`SERVICE-GROUND.md`** — a short list (not forced to sixteen) of claims this
  service commits to always being true for its caller, each with what would
  defeat it, each citing the root `GROUND-<nnn>` claim it specializes where one
  applies. Named to avoid colliding with root `GROUND.md`.
- **`JOURNEYS.md`** — the piece the root pattern has no analog for. Enumerates
  the abstract journeys a caller takes through this service (discover →
  authority-check → invoke → receipt → provenance, or the service's own
  shape), and states plainly, per journey, whether it completes or dead-ends,
  citing the charter/`KNOWN-GAPS.md` standing that makes it so. Carries a
  named section for open custody or ownership questions the journey exposes —
  a question this service's own boundary cannot answer, stated rather than
  silently absorbed or silently answered by inventing an owner.

## What this is not

A new authority slot, a new standing ladder, or a fourth requirement ladder
competing with `PRD.md`. These are a projection at service scope of decisions
already made at root scope, the same discipline `AGENTS.md` Context hygiene
already asks for applied to service documentation, not a new kind of claim.
Nothing here grants a service authority over its own account of itself:
`BUILT` is what self-report produces; `WITNESSED` still requires a party that
did not write the document.

Where a `JOURNEYS.md` names an open custody question, that question is not
thereby assigned, resolved, or made this service's to decide — the whole
point of naming it there is that no existing document currently owns it. It
routes to a decision record the ordinary way, at whichever tier the
resolution rule in `STATUS.yaml` names.

## Precedent disposition

Per `decisions/0066` (Precedent before invention), `ADOPT` this repository's
own root-document shape rather than inventing a new one: same status line
convention, same requirement-lifecycle vocabulary, same defeating-case
discipline. `DEVIATE` only where the caller-is-the-node reframing requires it,
and where a fourth document (`JOURNEYS.md`) has no root-level analog to adopt
from.

## Scope of this decision

This decision authorizes the pattern and its first application to the seven
service directories that hold a real `CHARTER.md` today: `identity`,
`console`, `registry`, `host`, `asset`, `gateway`, `record`. It does not
charter `relay`, `storage`, or `tokens` as services — those remain either
epic-tree intentions (`relay`) or concepts with no service boundary
(`storage`, `tokens`) until a separate decision charters them, per the
existing rule that a service boundary is minted deliberately
(`decisions/0011`, `0040`).

## Rollback

Deleting the four files under a service directory removes the projection and
changes no standing: `CHARTER.md` remains that service's authoritative role
statement, `PRD.md`/`SPEC.md`/`GROUND.md` remain the root System of Record,
and nothing elsewhere reads these four files as a dependency.

## Defaults taken

- File names avoid colliding with reserved root document names
  (`SERVICE-SPEC.md`, `SERVICE-GROUND.md`, not `SPEC.md`/`GROUND.md`).
- Requirement IDs use `SVC-<DOMAIN>-<n>` to stay visibly distinct from
  `PROD-I-<n>`.
- Standing on every instance starts `BUILT` at most (self-report by the
  drafting session); none may claim `WITNESSED` or `RATIFIED` on first
  landing.
