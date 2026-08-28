# QA witness sweep over `710f552..c296c25`, 2026-08-23

Status: `OBSERVED INDEPENDENTLY · NOT WITNESSED · NOTHING RATIFIED`

Six `sov-witness` agents observed the nine commits `3341df8..c296c25` on
`feat/federation-harness-and-hardening` under Workflow `sov-qa`, run
`wf_aa118e39-0ea`, across the contracts, console, asset, byom, verification,
and governance domains. 920k subagent tokens, 524 tool uses, 23 minutes. None
of them built, edited, or fixed anything.

The object is the commit range, not a working tree. Nine commits, 91 files,
+20478/-406. Seven builds are in it: the asset module split, seat message
etiquette, node identity, the federation crossing and public projection, the
Console Service continuity path, the declared service surface and gateway
charter, the capability map, and the MCP gateway binding. Before this sweep
only two of them had ever been looked at from outside
(`reports/2026-08-23-console-and-seats-independent-observation.md`).

A report under `reports/` is evidence, not policy. This one proposes at most
`BUILT -> WITNESSED` for four surfaces and settles nothing. Only Bdo ratifies.

## 1 · The correction this record exists to carry

**Six witnesses reported the required gate as failing. It is not.** They
measured `python scripts/verify.py` at 3.17-3.78s against the 3.000s budget
`AGENTS.md` declares, in some cases 8 of 12 runs red, and several concluded
that no artifact in the range could move past `BUILT` because the gate was not
green. One wrote that "the required repository gate is not reliably green,
which means a genuine regression and a slow machine are indistinguishable."

That measurement is an artifact of how the observation was executed. Six
agents were running the 21-way subprocess fan-out concurrently on one machine.
Measured afterwards against a clean detached worktree at `c296c25` with nothing
else running, three consecutive runs gave **2.666s, 2.588s, 2.564s, all 21
checks green**. The landing controller session measured 2.68s in the same
setup. A seventh witness had already reported the honest split - 3.454s and
3.327s under load, 2.577-2.632s warm - without drawing the conclusion the
others drew from it.

The real finding is margin, not failure: roughly 0.35s of headroom on a 3.000s
budget, which any concurrent load erases. That is worth fixing. It is a
different claim from "the gate is red", and the difference is the whole point
of witnessing.

This belongs at the top of the record because it is the failure mode the
exercise exists to catch: **a witness reporting a property of its own execution
as a property of the thing observed.** Fan-out is not free, and an observation
taken under contention is measuring the observer.

## 2 · Four false claims in commit messages, all mine

These cannot be fixed. The commits are pushed and the branch is frozen; a
pushed message is only correctable by a record that cites it. That is what this
section is.

**`d850c6d`** says "A Model Context Protocol server over stdio that reaches the
Asset, Record, and Console services." It does not reach the console.
`git show HEAD:bindings/mcp/gateway.py | grep -ic console` returns 0. The six
endpoints are four `asset`, one `record`, one `repository`. Confirmed
independently by three witnesses and by the landing controller session.

**`0d07767`** says "the checked-in map can go stale between runs without the
gate noticing." False, and it understates the coverage that exists.
`scripts/tests/test_capability_map.py` rebuilds the map from the live manifests
and asserts equality including `input_state_digest`, and `scripts/tests` is
wired into `verify.py` as the "repository tooling tests" check. Two witnesses
disproved it by mutation; a third watched it fire for real when a concurrent
session added `services/registry/`. The same false note sits at
`decisions/0038` line 101. The true, narrower statement is that there is no
dedicated `Check` entry the way `sov_service.py check` has one.

**`c296c25`** says "OPEN-SEAMS gains two." It gained three. S19 (who publishes:
an operator or a seat) is in the file at that commit and is arguably the most
consequential of the three.

**`c296c25`** says "STATUS.yaml carries the new standing." It records five of
seven builds. There is no key for the capability map, none for `bindings/mcp/`,
and none for the seat etiquette contract.

A fifth is a labelling defect rather than a false sentence. `3341df8` is typed
`refactor(asset)` and says "no caller moves." It also landed operator sessions,
grant expiry, issuer attenuation, a first-writer-wins root-issuer rule, three
new public methods, and a grants-table migration under which every grant in a
pre-existing store reads as expired. `SPEC.md` line 326 gives the behaviour
prior contract cover, so it is not ungoverned - but `AGENTS.md` asks for one
coherent behaviour change per commit and for a persistence change to be
recorded, and the message discloses neither.

## 3 · What was reproduced

The oracles are real, not decorative. One witness mutation-tested six of them -
the `node_identity` peer-root rule, the `manifests` endpoint check, the
`federation` settlement check, `publication.projection_defects`, a console
record field name, and the capability office table - and every one failed as it
should. A seventh mutation, moving one office assignment, turned the full gate
red.

Every new contract in the range carries both polarities: node-identity 8
fixtures (2 positive / 6 defeating), federation-crossing 9 (3/6),
public-projection 9 (3/6), seat-message 19 (5/14), capability-map 10 (1/9),
service-manifest 22 (1/21). No contract in the range is unwitnessable for want
of a defeating case, with the one exception recorded at 4.7 below.

On that basis this report supports `BUILT -> WITNESSED` for four surfaces
only, each reproduced through a path independent of the code that built it:
the capability map derivation, node identity and its registry grading, the
Console Service continuity path, and the seat etiquette checker. The remaining
surfaces are attested as genuinely `BUILT` and genuinely self-tested, which is
not the same claim.

## 4 · Defects

Ordered by what they would cost to find later. The bracketed count is how many
of the six witnesses reached the finding independently.

### 4.1 · An authority grant defaults to the owner's name [1, confirmed by hand]

`services/console/src/soveraeign_console_service/cli.py` lines 97 and 101
default `--granted-by` and `--revoked-by` to the literal string `"Bdo"`,
mirrored at `core.py` lines 82 and 89. A caller with no session, no prior
authority and no flags runs `console grant`, exits 0, and writes an
authority-grant into the operational journal reading `"granted_by": "Bdo"` - a
grant attributed to the one person who holds ratification authority, created by
a caller who holds none. `services/console/KNOWN-GAPS.md` line 18 records the
weaker general form, that anyone may record a grant naming any granter, and not
that the default value is the owner's name.

### 4.2 · The MCP binding exposes an authority bootstrap [3]

Against a fresh state root a witness called `authority_open_session` as
`"attacker"`, then `authority_grant` with `issuer=actor="attacker"` for
`operate:ingest`, then `asset_ingest`. All three succeeded. The gateway's
`GRANT_NOT_HELD` gate is bypassable because `authority_grant` is declared
`service-enforced`, so `_precheck` returns early, and `Authority.grant` makes
whoever issues the first grant against an empty store the root issuer.

`services/asset/src/soveraeign_asset_service/authority.py` lines 14-16 record
that rule as a Default taken, reasoned as a mechanism for making the first
issuer visible. That reasoning is defensible for a library. It does not cover a
stdio transport with `grant` as a served endpoint, and no decision record rules
on the difference.

Related, from the same witnesses: over the binding, the grant `issuer` and the
ingest `actor` are caller-supplied tool arguments never reconciled with the
calling actor, and the Asset Service receipt and the gateway journal recorded
two different actors for one ingest.

### 4.3 · `bindings/mcp/` has no decision record [6, unanimous]

820 lines of executable binding that opens sessions, issues grants, appends to
the operational System of Record, and is a required `verify.py` check.
`decisions/0016`, `0038` and `0040` mention MCP only in passing; `0040`
mentions `bindings/mcp/gateway.py` solely as the S18 naming collision.

Sharper: `decisions/0038` states as a Constraint that no capability is served
on MCP, and that standing up a local stdio MCP surface "is not admitted by this
decision." Commit `d850c6d`, the very next commit, did exactly that. The
decision was not amended and the capability map was not updated.

### 4.4 · The console's public projection does not satisfy the contract it cites [2]

`continuity.py:114` documents `published_threads()` as the read
`contracts/public-projection.schema.json` is built over. A witness drove a live
`ConsoleService` - open channel, open thread, publish thread - and validated
the actual return against that schema: **12 defects, 10 of 13 required
properties absent**. The function returns `published` where the schema requires
`entries`, and `rebuilt_from` where it requires `rebuild_operation_id`.

No test links the two. `scripts/tests/test_public_projection.py` grades only
hand-authored fixtures; `services/console/tests/test_contract_shapes.py` grades
only the console-owned schemas under `services/console/contracts/`. The
kernel-level contract `decisions/0039` landed is unconnected to the
implementation claiming to realize it.

### 4.5 · The capability map is wrong about the only live transport [4]

`contracts/fixtures/capability-map.reference.json` records
`DECLARED_NOT_ACTIVATED` on the MCP transport for all 79 capabilities. The MCP
server serves six tools including `asset_ingest` (act tier, writes) and
`authority_grant`. The map's `derived_from` is the six service manifests plus
`contracts/capability-offices.json`; `bindings/` is not an input, so
`input_state_digest` can never move when a binding opens a door, and
`sov_capability.py check` correctly reports "not stale" about a map that
misdescribes the node.

The consequence is worse than the error. `PhaseBoundaries::test_no_back_office_capability_is_served_operator_facing`
asserts that no BACK-office capability is ACTIVE on an operator-facing
transport. `console.grant` is BACK office with `actor_kinds: ["HUMAN"]`; MCP is
`operator_facing: true`; the gateway exposes `authority_grant` to a model
client with no gateway-side capability check. The test passes only because the
map cannot represent MCP as active. **A phase-boundary guarantee is passing
vacuously.**

### 4.6 · One node, two meanings for scope `*` [1]

`soveraeign_console_service/authority.py:70` matches scope by exact string
equality, so a grant scoped `*` admits nothing but an operation scoped `*`.
`soveraeign_asset_service/authority.py` matches with SQL `scope IN (?, '*')`,
treating `*` as a wildcard. A witness hit this directly: a console grant scoped
`*` was refused for a channel in domain `operations`. Nothing reconciles the
two, and the capability map's `required_authority` says nothing about scope
semantics.

### 4.7 · Two graders admit what they were written to refuse [2]

`sovkernel/publication.py` `_omission_defects` compares `len(entries)` to
`len(source_addresses)` rather than checking coverage. A projection with two
entries pointing at one source address and two declared sources - one never
rendered, never declared as an omission - returns zero defects. The module
docstring claims it proves that a filtered rebuild says it filtered; a
duplicate entry defeats that, and `contracts/public-projection.schema.json`
sets no `uniqueItems`. No fixture covers the case, so on that one rule the
contract is currently unwitnessable.

`sovkernel/federation.py` `_admitted_origins` treats admission outcome
`COUNTERED` as admitting the origin node, alongside `COMMITTED`. The crossing
schema defines `COUNTERED` as creating a counter-record against a local record
the offer contradicts - the node contradicted the peer, it did not admit it.
With the only inbound crossing at `COUNTERED`, `projection_defects` returns
`[]` and the peer's thread publishes. At `REFUSED` it correctly reports the
origin as unadmitted. No fixture covers `COUNTERED`, and the module docstring
calls this rule the whole boundary failing at once.

Also in `federation.py`: no `crossing_id` uniqueness and no timestamp ordering.
Two crossings sharing one id with opposite outcomes produce zero defects, as
does an admission dated 2020 against an offer dated 2026.

### 4.8 · The declared surface is checked in one direction only [4]

`sov_service.py check` proves that everything declared is coherent. Nothing
proves that everything implemented is declared. Concretely:

- Deleting `ingest-asset` from the asset manifest passes at exit 0. There is no
  defeating case for an implemented-but-undeclared operation, and the capability
  map inherits the hole.
- `AssetService` exposes at least 17 public methods; the manifest declares 9.
  `search`, `open_session`, `close_session`, `grant`, `revoke`, `claim`,
  `report_derivative`, `observe`, `neighbors`, `receipts` and `federation_cross`
  are undeclared and absent from the map. Two of them are served over MCP now.
- A manifest may declare its own `standing` as `WITNESSED` or `RATIFIED` and the
  checker accepts it. Nothing cross-checks a manifest's standing against
  `STATUS.yaml` or any observation. All six are honest today, so this is a hole
  and not a live misstatement.
- `service_id` is not checked against the directory holding the manifest.
  Renaming the asset manifest's `service_id` to `proofing` and rewriting its
  endpoints to match produced zero defects.
- Declared preconditions are not reconciled against enforcement. The console
  manifest declares `session_live`, `declared_capability`, `declared_scope` and
  `issuer_holds_authority` on `grant`; `ConsoleService.grant` takes no
  `session_id` and performs no session or issuer check.
- Declared refusal codes are not reconciled against emission. The console
  manifest declares `SESSION_NOT_LIVE`, which appears zero times in
  `services/console/src/`; `refusals.py` emits `SESSION_CLOSED`,
  `CLAIM_WITHOUT_PROPOSAL`, `PIN_INCOMPLETE`, `STANDING_NOT_OWNED` and
  `THREAD_ARCHIVED`. The console manifest also declares `INCOMPLETE_PROPOSAL`,
  the exact phantom code OPEN-SEAMS S17 records as unemittable.

### 4.9 · Smaller, confirmed

- **The MCP refusal trace is thinner than three places claim.** A precondition
  refusal writes a `RECEIPT` with no `EVENT` and no `entry_id`; an
  `UNKNOWN_OPERATION` refusal writes nothing. `_precheck` raises from inside
  `_refuse` before `record.append("EVENT", ...)` is reached (`gateway.py`
  129-133). The commit message, `gateway.py` line 120, and the docstring of
  `test_a_refusal_is_journalled_too` all say otherwise; that test's assertion is
  weaker than its name.
- **`observe_verify` is declared `RECORD_LOCAL`.** Its handler spawns
  `scripts/verify.py` - 21 subprocesses, roughly 11s of CPU work - on request
  from an MCP client. Under the declared vocabulary that is
  `RESOURCE_CONSUMPTION`.
- **`scripts/sov_node.py` line 109 is dead code.** `return 0 if not args.strict
  or not defects else 1` is unreachable in its interesting branch because line
  107 already returned. The advertised `--strict` flag does nothing.
- **The node registry document envelope has no schema.** `registry_schema`,
  `status`, `self_node` and `nodes` are hand-checked by `holder_defects`; only
  the records inside are validated.
- **`manifests.prd_requirements()` uses `re.findall(r"PROD-I-[1-9]")`** with no
  boundary, while the schema admits `^PROD-[IVX]+-[1-9][0-9]*$`. `PROD-I-10`
  would read as `PROD-I-1`. Latent - PRD.md carries 1 through 9 today, and it
  fails safe.
- **Console node scoping binds the CLI, not the service.**
  `ConsoleService.__init__` validates `node_id` against the pattern and nothing
  else, so any caller may construct a console writing records for any
  well-formed node id, including a peer's. `test_sov_node.py` checks only
  `cli.DEFAULT_NODE`. Decision 0039's rule that a console writing for an unknown
  node fails the build holds for the CLI only.
- **MCP receipt operation names resolve to nothing declared.** `manifest.json`
  uses `open_session`, `grant`, `ingest`, `search`, `entries`, `verify`;
  manifest operation ids are kebab-case and logical endpoints are
  `sov://asset/ingest-asset`. A reader of a receipt cannot resolve the operation
  to a declared endpoint.
- **Two services own grants and sessions.**
  `services/console/contracts/service.json` declares `authority-grant` and
  `operator-session` among the records the Console Service owns; `gateway.py`
  routes `authority_open_session` and `authority_grant` to the Asset Service's
  authority layer - a different store, a different implementation.
- **`services/gateway/KNOWN-GAPS.md` and `ai-native-gateway-service.yaml`** exist
  on disk, are not gitignored, and are untracked, while every other service's
  equivalents are tracked.

## 5 · Vocabulary and record drift

`AGENTS.md` gives `CLASSIFICATION.md` and `SPEC.md` ownership of vocabulary and
forbids synonyms for existing standing, event, effect, or role terms.

- **`effect_class: "NONE"`** in `bindings/mcp/manifest.json` on `asset_search`
  and `record_entries`. The vocabulary is closed at three values and
  `contracts/capability-map.schema.json` enforces exactly that enum. The
  capability map has a defeating fixture refusing precisely this
  (`CAPMAP-NEG-UNKNOWN-EFFECT-CLASS`), and the MCP manifest shipped one two
  commits later, ungraded because the MCP manifest is not an input to that
  schema.
- **`DERIVED` and `REBUILT`** in the service-manifest `commit` enum, and
  **`SUPERSEDE` and `REBUILD`** in its `crud` enum: zero occurrences in
  `CLASSIFICATION.md`, `SPEC.md`, `CONTRACT.md` or `PRD.md`. The same enum mixes
  event outcomes (`COMMITTED`, `COUNTERED`) with record standing values
  (`RECORDED`, `EFFECTIVE`), scales `CLASSIFICATION.md` keeps distinct.
  `decisions/0040` does not gloss any of them as a declared extension.
- **`counter` now means two things.** `CLASSIFICATION.md` line 119 uses it for a
  counter-record; `contracts/capability-offices.json` introduces a top-level
  `counters` key meaning service desks. Both are contract layer, not prose.
- **Absent from both owning documents:** `crud`, `logical_endpoint`, `office`,
  `FRONT`, `BACK`, `DECLARED_NOT_ACTIVATED`, `REFUSED_UNCONFIGURED`, `PEER`,
  `node_id`.
- **Pre-existing, unchanged by this range:** `STANDING_ORDER` in `manifests.py`
  is `("PROPOSED", "BUILT", "WITNESSED", "RATIFIED")` while `AGENTS.md` states
  the lifecycle as `OPEN -> BUILT -> WITNESSED -> RATIFIED`.
  `CLASSIFICATION.md` contains zero occurrences of `RESOURCE_CONSUMPTION`
  despite owning the vocabulary.

Two decision records carry observed-state prose that was already wrong at their
own commits. `decisions/0038` line 73 says 57 capabilities across five services
with fourteen served; the reference map at commit `0d07767` holds 79 across six
services with 32 served. `decisions/0040` says 76 declared operations with
asset 9 and console 23, and console 12 built; at commit `35bc49c` the count was
79 with console at 26 declared and 15 built. `0040` also presents a single
favourable `verify.py` timing as the result.

## 6 · The independence claim is weaker than the commits say

`scripts/witness_console.py` shipped in `955bf55`, the same commit that built
the console. `scripts/witness_seats.py` shipped in `1e758b8`, the same commit
that built the seat checker. Both commit messages call them the independent
look.

Their method is genuinely better than the unit tests - CLI subprocess only,
contract-file projection, journal-scanned receipts, novel mutations - and both
pass when run, 20 of 20 and 16 of 16. But under `AGENTS.md` a build report
cannot witness itself, and a checker shipped in its own build's commit
establishes `BUILT`, not independence. The commit prose overstates them.

Separately, every commit in the range is authored `Bdo` with the same
`Co-Authored-By` trailer, so the earlier report's claim that a session which
built neither surface wrote it is not verifiable from the artifact. That report
names the limit itself at lines 35-39.

## 7 · What waits on Bdo

Deduplicated from 58 judgement items across six witnesses. None of these is a
defect a session may settle.

1. **Is `NONE` an admissible effect class?** Either `CLASSIFICATION.md` gains a
   fourth value or the MCP manifest is wrong. Same question for `DERIVED`,
   `REBUILT`, `SUPERSEDE`, `REBUILD`, and `counters`.
2. **Does `bindings/mcp/` need a decision record before it stays a required
   check?** It executes, opens sessions, issues grants, writes to the
   operational System of Record, and one endpoint spawns the repository gate
   itself. `decisions/0033` admits harness workflows before their fixtures for
   host plumbing; whether a Model Binding of this reach is the same case is
   yours.
3. **Is `decisions/0038` admitted retroactively?** It states MCP is served
   nowhere and that standing up the surface is not admitted by it. The next
   commit did it.
4. **Should `granted_by` default at all** (4.1), and is caller-asserted
   attribution acceptable over a single-operator binding (4.2)?
5. **The 3.000s budget.** With roughly 0.35s of margin: raise the budget, reduce
   the 21-way fan-out, or redefine it as CPU work rather than wall time. Raising
   it is policy you own; reducing fan-out is verification-domain work.
6. **Should the manifest check be bidirectional** - must a service prove that
   everything it implements is declared (4.8)? Buildable now; it changes what a
   manifest is.
7. **Should a manifest carry `standing` at all**, given that a build cannot
   witness itself, or should the field be constrained to `PROPOSED|BUILT`?
8. **Which scope semantics is the node's** (4.6), and does reconciling them
   belong to a shared authority contract under `contracts/`?
9. **Does a `COUNTERED` crossing admit its origin** onto the public surface
   (4.7)? A semantic call about what countering means at a node boundary.
10. **Is `contracts/public-projection.schema.json` the target the console must
    be brought to, or is the console's simpler view the real one** (4.4)?
11. **S17**: which of the three readings of `INCOMPLETE_PROPOSAL` holds? It is
    now declared in six manifests and emitted by nothing.
12. **S18**: the gateway naming collision. Nothing is built behind the service
    yet, so renaming now costs almost nothing and renaming later costs a receipt
    vocabulary.
13. **S19**: is outward publication a judgement the root seat settles, or work
    any seat may perform?
14. **Should `STATUS.yaml` gain entries** for the capability map, the MCP
    binding, and the seat etiquette contract - or is there a deliberate line
    about what it tracks? Nothing validates `STATUS.yaml` at all.
15. **Should `decisions/0038` and `0040` be corrected** for the stale numbers in
    section 5?
16. **`.claude/settings.json` is now checked in**, so opening this repository in
    any Claude Code host writes an operator session to the console journal at
    session start. Is that the intended default for anyone who clones it?
17. **Is a self-authored subprocess-only checker acceptable as an independence
    claim in commit prose** (section 6)?
18. **Should witnessing run against a committed ref or a clean worktree by
    rule?** Two consecutive independent reports have now been partly invalidated
    by concurrent edits.

## 8 · What this report cannot claim

- **It is not a witness.** Six agents observed; `AGENTS.md` reserves
  `WITNESSED` for a judgement this file cannot make and `RATIFIED` for Bdo.
- **The tree moved under the observation.** A concurrent session added
  `services/observation/`, `services/registry/`, `contracts/domain-owners.*`,
  `scripts/sov_surface.py`, `docs/`, and `decisions/0041` between 22:45 and
  23:02, and edited `scripts/verify.py`. The commit-range findings hold because
  the range is fixed, but any timing, any `git status` reading, and any live
  drive taken after roughly 22:45 was taken against a moving target. Findings
  above are drawn from the range or were re-confirmed against `c296c25`
  directly.
- **Coverage is uneven.** The byom witness followed the handed claim set rather
  than its own domain scope, so `adapters/ollama/`, the conformance oracle's
  participant binding, `contracts/model-binding.schema.json` against SPEC.md
  `ModelBinding`, and PROD-I-9's two-binding proof were not exercised by anyone.
- **The brief was wrong.** It told the witnesses the working tree was clean. It
  was not, and had not been for some minutes. Two witnesses dissented from the
  brief on exactly that point, correctly.

## 9 · Residuals of this report

- The four false commit claims in section 2 are uncorrected in the commits
  themselves and can only be corrected by this record. `decisions/0038` line
  101 carries the same false staleness claim and is editable.
- No defect in section 4 is fixed here. `fix/console-grant-attribution` was
  opened by another session against 4.1; nothing else has an owner.
- 4.7's duplicate-entry case has no defeating fixture, so `public-projection` is
  reported as unattestable on that one rule. The rest of the contract holds.
- Section 7 is a queue, not a plan. Nothing in it is scheduled.
- **Outside this range, found while writing this report: `origin/main` does not
  pass its own required gate on Windows.** At `e1ea622`, `python
  scripts/verify.py` fails "ticket coordination tests" with 12 errors and 2
  failures in `scripts/tests/test_infrastructure.py`. The errors are all
  `AttributeError: module 'os' has no attribute 'fchmod'` from
  `scripts/infrastructure.py:139`; `os.fchmod` is POSIX-only and absent on
  Windows, which is the host this repository is developed on. The two failures
  are `CUSTODY_PATH_UNSAFE` not raised for escape and absolute paths, and the
  concurrent-apply fence. Reproduced in a clean worktree at `origin/main` with
  no local changes, so it is neither this branch's doing nor a worktree
  artifact. It is recorded here rather than in a separate report only because
  this run found it; it belongs to whoever owns `scripts/infrastructure.py`.
- **Also outside this range: the LF pin has never reached `main`.**
  `.gitattributes` does not exist at `origin/main`, and `core.autocrlf` is
  `true` in this host's system gitconfig, so every text file checked out from
  `main` arrives CRLF - confirmed on `README.md`, `AGENTS.md` and
  `scripts/lint.py` in a fresh worktree. The file that pins LF exists only on
  the frozen branch and lands on `main` when this range does. Until then the
  `AGENTS.md` line-ending rule is unenforced on `main`, which is consistent with
  what `.gitattributes` itself says about why it was written.
