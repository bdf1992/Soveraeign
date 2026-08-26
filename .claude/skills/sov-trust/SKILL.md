---
name: sov-trust
description: Working knowledge for the Soveraeign trust domain — the two boundaries of the trust-and-control village whose components are already built, services/identity/ and services/registry/. Load when a task mentions "sov-trust", "trust domain", "Identity Service", "Registry Service", "challenge", "recovery secret", "verification basis", "name resolution", "registry entry", "drift finding", "owner record", or names the artifacts CHARTER.md, contracts/service.json, soveraeign_identity_service (challenges.py, recovery.py), or soveraeign_registry_service (core.py, index.py, routes.py). Covers issues #11 and #14 of the epic tree. Not for Authority (#12), Gates (#13), or the Capability Broker (#15) — no repository artifact evidences those yet, so they stay unrouted — and not for kernel contracts, the conformance oracle, or governance work.
---

# sov-trust

## Purpose

Advance the two boundaries of the `trust-and-control` village that already exist
on disk: the Identity Service's challenge and recovery components, and the
Registry Service's `resolve` slice. Those components are `BUILT` by their own
tests and neither is independently witnessed. The boundaries above them are not
built: the Identity manifest is `PROPOSED` with its placement provisional, and
every Registry operation except `resolve` is `PROPOSED`. The domain exists
because those artifacts exist; it claims nothing about the parts of the village
that have no artifact.

## Why one domain and not two

`.claude/README.md` owns the domain table, and a domain is added when repository
artifacts evidence the ownership, not per issue. Identity and Registry are one
domain because the evidence is one shape: a charter, a service manifest, an
implementation under `src/`, and tests that `python scripts/verify.py` runs. They
also answer the same question from two sides — who a participant is, and what a
name resolves to — and neither grants anything. Splitting them would double the
harness surface without doubling the evidence.

## Owns / Must not

Owns: `services/identity/` and `services/registry/` — their charters, service
manifests, implementations, and tests, plus `contracts/domain-owners.json` and
`contracts/domain-owners.schema.json`, which the Registry charter names as the
authored owner-record table it reads.

Must not: invent Identity or Registry semantics that the charters do not already
carry; settle where principal identity lives (`decisions/0048` judgement 3 is
open and is the owner's); promote either service past
`BUILT_SELF_TESTED_NOT_WITNESSED`; witness its own build; write another service's
directory or the Asset Service's state; modify `lineage/evidence/`; create an
`EXTERNAL_WORLD` effect; run `git commit` or `git push`.

## Key files

- `services/identity/CHARTER.md` — the challenge as a lease, the two structural
  properties (no token in any record; the window closes when it says it does),
  sealed recovery, and the full refusal table.
- `services/identity/contracts/service.json` — seven declared operations, all
  `PROPOSED`, and the local-to-kernel refusal mapping.
- `services/identity/src/soveraeign_identity_service/challenges.py`,
  `recovery.py` — the built components. Storage-free: clock, token source, and
  identifier source are injected.
- `services/identity/tests/` — 32 positive and defeating cases, run by
  `scripts/verify.py` as the check named `Identity component tests`.
- `services/registry/CHARTER.md` — the `resolve` slice, owned domain records,
  owner records, the proving narrative, and the defeating cases.
- `services/registry/contracts/service.json` — `standing: BUILT`, with only
  `resolve` built and the rest of the operation set `PROPOSED`.
- `services/registry/src/soveraeign_registry_service/core.py`, `index.py`,
  `routes.py` — the built resolve path; the index is rebuildable and persisted
  nowhere.
- `contracts/domain-owners.json` + `.schema.json`, checked by
  `python scripts/sov_owners.py check`.
- `decisions/0048-principal-identity.md` — the identity decision record.
- Governing set: `AGENTS.md`, `STATUS.yaml`, `CLASSIFICATION.md`, `SPEC.md`,
  `PRD.md`, `CONTRACT.md`.

## Standing and constraints

- Identity: `PROPOSED · PLACEMENT PROVISIONAL · CHALLENGE AND RECOVERY BUILT`
  (`services/identity/CHARTER.md`). Whether identity is a service boundary at all
  is `decisions/0048` judgement 3, open and owner-held. The charter makes the
  assumption cheap on purpose: a ruling of "kernel registry" moves one file and
  changes no semantics.
- Registry: `BUILT` participant with one bounded `resolve` operation; every other
  chartered operation is `PROPOSED`. The charter states plainly that the parity
  evidence is `BUILT`, not an independent observation.
- Epic tree: issue #11 (Identity Service) and #14 (Registry Service) route here
  on that evidence (`.claude/epic/villages.json`). Both are currently `HELD` by
  an unsatisfied `requires` edge on #8, which is a dependency state and not a
  question for anyone.
- A verified identity claim is identity, never authority. Every consequential
  transition still checks a live typed grant.
- A registry entry is a referent, never standing, authority, or permission.

## Named operations (available now)

1. Independent witness: have a participant that did not build either component
   observe the identity tests and the registry resolve path, so the `BUILT`
   claims can be proposed for `WITNESSED`.
2. Registry test placement: `scripts/tests/test_registry_horizontal.py` exercises
   `soveraeign_registry_service` from the repository tooling suite while the
   Identity component has its own `services/identity/tests/`. Reconcile the two
   placements against `AGENTS.md`, Testing and verification.
3. Defeating-fixture authoring for the Registry defeating cases the charter
   lists but no test yet drives — above all the stale-index case and the
   same-name collision.
4. Doc coherence: align `services/README.md`, both `CHARTER.md` files, and both
   `service.json` manifests with `CLASSIFICATION.md` vocabulary.
5. Owner-record work: extend or repair `contracts/domain-owners.json` under its
   schema, keeping the two load-bearing constraints (an owner is never its own
   witness; budget and deadline are required).
6. Acceptance packet: over a slice that is built and independently observed,
   assemble the six-part packet of `decisions/0023-acceptance-not-approval.md`.

## Verification

- `python scripts/verify.py` — required, from the repository root, graded budget
  (PLATINUM 3 s, GOLD 6 s, SILVER 15 s).
- `python scripts/lint.py` — hygiene, module size, secret shapes.
- `python -m unittest discover -s tests` from `services/identity/` — the 32
  component cases.
- `python scripts/sov_owners.py check` — the owner-record table.
- `python -m json.tool services/identity/contracts/service.json` and the same for
  `services/registry/contracts/service.json`.

## Vocabulary (exact; no synonyms)

- Repository artifact standing: `OPEN -> BUILT -> WITNESSED -> RATIFIED`.
- Epic-tree state: `READY`, `HELD` (an unsatisfied `requires` edge), `UNROUTED`
  (no repository artifact evidences a domain owner), `OWNER_HELD` (a judgement
  asked of the owner). Only the last waits on Bdo.
- Identity claim: `UNVERIFIED -> VERIFIED`, upgraded by presenting a live token
  inside its window; that presentation is the claim's `verification_basis`.
- Identity refusals: `CHANNEL_UNDECLARED`, `CHANNEL_REFUSED`,
  `PRINCIPAL_REVOKED`, `TOKEN_UNKNOWN`, `CHALLENGE_SPENT`, `CHALLENGE_EXPIRED`,
  `PRINCIPAL_MISMATCH`; recovery adds `NOT_ENROLLED`, `SECRET_UNKNOWN`,
  `SECRET_SPENT`, `SET_REVOKED`, `ALREADY_ENROLLED`.
- Registry refusals: `NAME_UNKNOWN`, `INDEX_STALE`.
- Effect class: `RECORD_LOCAL`, `RESOURCE_CONSUMPTION`, `EXTERNAL_WORLD`.
- Attestation outcome: `REPRODUCED | DISSENTED | UNATTESTABLE`.

## Report format

Report: files changed (repository-relative paths); checks observed (exact
commands with exit codes); standing proposals (own work supports at most `BUILT`;
a build report cannot witness itself); anything genuinely owner-held, named as
such and distinguished from held and unrouted work; next bounded operation.
