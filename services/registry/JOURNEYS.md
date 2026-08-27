# Registry Service Journeys

Status: `BUILT · SELF-REPORTED, NOT WITNESSED`

`decisions/0067-service-srd-spec-ground.md` introduces this document with no
root-level analog: the abstract journeys a caller takes through this service,
each marked whether it completes or dead-ends, citing the charter or
`contracts/service.json` standing that makes it so, plus a named section for
open custody or ownership questions the journeys expose. Naming a question
here does not assign it, resolve it, or make it the Registry's to decide —
see `decisions/0067`, What this is not.

## Journey 1 — Resolve a name · `COMPLETES`

The one journey the Registry currently completes end to end.

1. **Discover.** The caller already holds a name to resolve — a logical
   endpoint (`sov://asset/ingest-asset`) or a capability id
   (`asset.ingest-asset`). The Registry does not itself expose a separate
   discovery operation; `console.discover-operations` is the artifact
   `GROUND-006` names for that, a different service.
2. **Authority-check.** In the one wired composition
   (`scripts/sovnode/composition.py`), the Gateway checks `read:registry`
   against a live grant through Console's authority path
   (`console_authority.check`) before dispatching to
   `registry:in-process`. `contracts/capability-offices.json` admits both
   `HUMAN` and `MODEL` actor kinds for `resolve`.
3. **Invoke.** `RegistryRoutes.call("resolve", {"name": ...}, actor)`
   validates the argument contract (exactly one non-empty string, `name`) and
   calls `RegistryService.resolve` (`src/soveraeign_registry_service/routes.py`,
   `core.py`).
4. **Freshness check.** `resolve` re-digests every declared source through
   `_source_drift` before answering anything — a stale source refuses the
   whole lookup, not only the entry it touched.
5. **Receipt.** A terminal receipt returns: `COMMITTED` with the resolution
   (entry, owning manifest address and digest, policy source address and
   digest, office, required authority, Kernel binding, `standing_effect:
   NONE`), or `REFUSED` with `NAME_UNKNOWN` (no such name) or `INDEX_STALE`
   (a source moved). The receipt is appended to the Record Service journal.
6. **Provenance.** The resolution names, rather than restates, the document
   that owns the answer — its address and digest, not a copy of its content.

Cites `CHARTER.md`, Built resolve slice and Proving narrative;
`contracts/service.json`, `resolve` standing `BUILT`;
`scripts/tests/test_registry_horizontal.py`, which exercises every step
above including the two refusal branches.

## Journey 2 — Register a new named thing · `DEAD-ENDS`

1. **Discover.** `contracts/service.json` declares `register-entry`: name,
   kind, owning document address and digest, actor.
2. **Authority-check.** `contracts/capability-offices.json` names the
   required authority (`register:entry`) and admits both actor kinds.
3. **Invoke.** Dead-ends here. `RegistryRoutes.OPERATIONS = ("resolve",)` is
   the complete route census; calling `register-entry` raises `KeyError`
   ("registry route 'register-entry' is not bound"),
   `src/soveraeign_registry_service/routes.py`.

Cites `CHARTER.md`, standing line: "Standing: `BUILT` participant with one
bounded `resolve` operation. The rest of the chartered operation set remains
`PROPOSED`; this evidence grants no standing to any resolved entry."
`contracts/service.json` marks `register-entry` `PROPOSED`.

## Journey 3 — Declare who is accountable for a domain · `DEAD-ENDS`

1. **Discover.** `contracts/service.json` declares `declare-owner`: domain,
   owner, mandate, budget, deadline, witness — the fields
   `contracts/domain-owners.json` already carries by hand for `registry`,
   `record`, and `gateway`.
2. **Authority-check.** `contracts/capability-offices.json` requires
   `declare:owner` and restricts `actor_kinds` to `HUMAN` alone —
   `declare-owner` does not admit a model caller even once built.
3. **Invoke.** Dead-ends here, the same way as Journey 2:
   `declare-owner` is absent from `RegistryRoutes.OPERATIONS`.

What actually happens today instead: `contracts/domain-owners.json` is
authored by hand and checked by `python scripts/sov_owners.py check`, a
standalone script that reads the table directly and never calls the
Registry. The mandate is real and the table is policy input the Registry
would read (`CHARTER.md`, Owner records), but the operation that would let a
caller declare, supersede, or retire that mandate *through* the Registry does
not exist. Cites `contracts/service.json`, `declare-owner` standing
`PROPOSED`; `CHARTER.md`, Owner records, "The `declare-owner` operation is
the built path that would later replace hand-authoring; until then the table
is policy input and the Registry reads it."

## Journey 4 — Ask who owns domain X · `DEAD-ENDS`

1. **Discover.** `contracts/service.json` declares `read-owner`: given a
   domain, return its owner record.
2. **Authority-check.** `read:registry`, both actor kinds admitted.
3. **Invoke.** Dead-ends here: `read-owner` is absent from
   `RegistryRoutes.OPERATIONS`, the same census `resolve` alone occupies.

This is the journey that matters most for the question the Registry exists
to answer, and it is the one most clearly unreachable today. See Open
custody and ownership questions below.

## Open custody and ownership questions

The Registry's whole purpose is answering "who owns this." These are
questions its own current boundary — built or proposed — does not answer,
named here rather than silently absorbed or silently answered by inventing
an owner, per `decisions/0067`.

**Does the Registry resolve "who owns secret or credential custody" today?
No.** Two separate reasons, not one:

- *The operation isn't there.* Journey 4 dead-ends. `resolve` answers "what
  is this and which document owns it," never an accountability question; even
  `read-owner`, the operation that would answer "who is accountable for
  domain X," is `PROPOSED` and unreachable.
- *Even the authored answer doesn't exist.* None of the eight hand-maintained
  tables `CHARTER.md` names as the Registry's eventual reconciliation targets
  — `services/README.md`, `.claude/README.md`, `.claude/epic/villages.json`,
  `STATUS.yaml`, `CLASSIFICATION.md`,
  `contracts/fixtures/seat-topology.reference.json`,
  `contracts/fixtures/node-registry.reference.json`,
  `contracts/capability-offices.json` — nor `contracts/domain-owners.json`
  itself, assigns a domain owner for "secrets" or "credential custody." A
  direct search for `secret` and `credential` across all nine finds exactly
  two hits, and neither is an ownership record: `STATUS.yaml`'s
  `no_secret_exposure` is a cross-cutting refusal-behavior line, not an
  accountability assignment; `CLASSIFICATION.md` states, of the Model Binding
  and Model Adapter, "Neither owns authoritative state or gains authority
  from provider credentials" — a statement of what does *not* own
  credentials, not of what does. `AGENTS.md`, Secrets and local boundaries, states the rule everyone
  must follow; it does not name who is accountable for the domain. So the
  honest state is: no participant is named as accountable for secret or
  credential custody anywhere the Registry is chartered to read, and nothing
  built or proposed here would currently surface that as a gap rather than
  silently returning `NAME_UNKNOWN` for a domain that was never asked about.

**Who reconciles the seven hand-maintained tables `rebuild-index` doesn't
read?** The one built index derives from the Kernel closure, per-service
`contracts/service.json` manifests, and `contracts/capability-offices.json`
(`src/soveraeign_registry_service/index.py`) — three of the eight sources
`CHARTER.md` lists, the same three the domain-owners mandate for
`owner-registry@1` scopes itself to: "Build the index and its rebuild path so
a name resolves to the document that owns it, and every source it reads is
digest-checked at answer time." The other seven — including `STATUS.yaml` and
`CLASSIFICATION.md`, both load-bearing governing documents — are not sources
the built index reads, and `register-entry`/`relate-entries`/`report-drift`,
the operations that would let those tables' subjects be entered and checked
for drift, are all `PROPOSED`. No owner record names bringing those seven
tables into the index as anyone's mandate. Until `register-entry` exists,
`drift-finding` cannot fire against a disagreement between, say,
`services/README.md`'s registry row and `STATUS.yaml`'s registry standing.

**Is one witness seat's independence checked only per-record, or across its
whole load?** `contracts/domain-owners.json` names `sov-witness@1` as witness
for all three declared owner records (`registry`, `record`, `gateway`)
simultaneously. `WITNESS_NOT_INDEPENDENT` in `contracts/service.json` and
`AGENTS.md`'s "a build report cannot witness itself" both check that one
owner record's owner and witness differ; neither the Registry's declared
refusals nor `CHARTER.md`'s constraints say anything about whether the same
witness holding several simultaneous mandates is itself a custody concern.
Raised here as unresolved, not answered.
