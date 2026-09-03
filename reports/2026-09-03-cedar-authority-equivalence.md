# Cedar grades the grant corpus

This is a report, not a decision (`AGENTS.md`: a file under `reports/` records
observation, not standing). It settles nothing, recommends nothing, and carries
none of `ADOPT`, `PROFILE`, `DEFER`, `DEVIATE`, or `MONITOR`. Everything below is
a fact produced by running code, cited at its address, from the experiment under
`experiments/cedar-authority/`.

Sources: `scripts/sovkernel/authority.py`, `scripts/sovkernel/scope.py`,
`scripts/sov_grant.py`, `conformance/fixtures/authority/grant-cases.json` (37
cases, `soveraeign-authority-grant-cases/v1`), `contracts/authority-grant.schema.json`,
`ENGINEERING.md` lines 46-101 (stdlib-first; a dependency crosses a named port),
`reports/2026-08-23-gateway-research-and-controller-plan.md` finding 2 and its
residual at line 128 (the conflicting-grant rule is not in any contract).

## What was run

`experiments/cedar-authority/materialise.py` applies every case's `grant_patch`
and `request_patch` over the corpus's `base_grant`/`base_request` (the same
`_merge` function `scripts/sov_grant.py` uses for its own `selfcheck`), calls
`sovkernel.authority.evaluate`, and records the kernel's actual verdict beside
the case's declared expectation, tiered as `CEDAR`, `SCOPE`, or `OUTSIDE` from
the expected refusal code and the patched fields alone (`materialise.py`,
`tier()`). `project.mjs` turns the materialised cases into a Cedar schema,
policy set, per-case entities, and per-case requests. `run.mjs` validates the
policy set against the schema in strict mode and authorizes every `CEDAR` and
`SCOPE` case through `@cedar-policy/cedar-wasm` 4.12.0; `OUTSIDE` cases are
never sent. `check.mjs` is the gate: it fails on any mismatch, on any `OUTSIDE`
case reaching Cedar, on a tier count that doesn't sum to 37, or on a working-tree
change under `scripts/`, `contracts/`, or `conformance/` against `dev`.

Result: `node experiments/cedar-authority/check.mjs` passes. 37 of 37 cases are
accounted for; the 32 sent to Cedar (14 `CEDAR`, 18 `SCOPE`) match the kernel's
verdict; the 5 `OUTSIDE` cases were never sent.

## Tiers

| Tier | Count | What it turns on |
| --- | --- | --- |
| `CEDAR` | 14 | status, actor, capability, JUDGEMENT issuer, revocation, `valid_from`/`valid_until`, effect ceiling, branch, budget |
| `SCOPE` | 18 (13 precomputed, 5 native) | the case turns on path scope |
| `OUTSIDE` | 5 | `OBSERVATION_MISSING`, `OBSERVER_NOT_INDEPENDENT`, `MISSING_PRECONDITION` - not an authority decision |

`SCOPE` cases split further by whether the requested path survives
`sovkernel.scope._ungradeable` unchanged:

| Path | `_ungradeable` fires | Cedar representation |
| --- | --- | --- |
| `services/asset/src/core.py`, `decisions/0061-x.md` (D-007, two-path case) | no | real Path entities in the fixed hierarchy |
| `contracts/standing-grants.json` (D-008a) | no | real Path entity, literal excluded entry |
| `README.md` (D-008) | no | real Path entity, no admitted ancestor |
| `contracts` (D-008m) | no | real Path entity; excluded via the reverse-direction literal clause below |
| `contracts/sub` (P-003) | no | real Path entity, admitted, nothing excluded beneath it |
| `scripts/../STATUS.yaml`, `scripts/../contracts/standing-grants.json`, `scripts/../../etc/passwd`, `contracts/./standing-grants.json`, `contracts//standing-grants.json`, `scripts/sov_land.py/`, `contracts/*`, `contracts/standing-grants.jso?`, `contracts/[s]tanding-grants.json`, `:!contracts/standing-grants.json`, `C:/checkouts/Soveraeign/scripts/sov_land.py`, `scripts\tests\x.py`, `scripts/tests\x.py` (13 cases) | yes | orphan Path entity keyed to the case id, no parents |

An orphan entity is never `in` any included prefix, so Cedar refuses it through
the same general "resource must be in `includedPaths`" rule every other
out-of-scope path fails - no separate boolean policy exists for these 13 cases.
What was precomputed outside Cedar is which raw strings could be given a real
tree position at all, not the verdict; every one of these 13 cases still expects
(and gets) `AUTHORITY_REFUSED` for the same reason a `README.md`-shaped miss
would, by construction of the orphan rather than by a per-case rule.

## 1. Per-capability leverage

| Our module or function | Upstream primitive that did its job here | Or: none |
| --- | --- | --- |
| `authority._grant_unavailable` (status, actor, capability, effect ceiling checks) | `permit(...) when { ... }` conditions over `Grant` entity attributes | - |
| `authority._branch_refused` | `context.branch in context.grant.branches` (`Branch` entity-set membership) | - |
| `authority._budget_exceeded` (amount vs. ceiling, same unit) | `if-then-else` guarded comparison over `Long` attributes | - |
| `authority._budget_exceeded` (unit mismatch refuses) | not modeled - no case in the corpus exercises it (see Residuals) | none exercised |
| JUDGEMENT-issuer check (`_grant_unavailable`, `JUDGEMENT_ISSUER`) | one `forbid` policy over `authorityType`/`issuerId` string attributes | - |
| revocation (`_grant_unavailable`, `revoked_at`) | `forbid(...) when { context.grant has revokedAt }` | - |
| `valid_from`/`valid_until` window | `context.now >= context.grant.validFrom && context.now < context.grant.validUntil`, Cedar's `datetime` extension | - |
| effect ceiling ordering (`EFFECT_ORDER.index`) | `Long` ordinal attribute compared with `<=` | - |
| `scope._covers` (included-prefix membership) | `resource in context.grant.includedPaths`, Path entity hierarchy | - |
| `scope._selects_excluded`, "is inside" direction | `resource in context.grant.excludedPaths` | - |
| `scope._selects_excluded`, "is a directory containing" direction | partial - see Residuals; Cedar's `in` has no descendant query | partial |
| `scope._ungradeable` (wildcards, pathspec magic, backslash, non-naming segments, absolute paths) | none - see Residuals | none |
| `authority._observation_verdict`, `_precondition_unmet`, `_preconditions` | none - `OUTSIDE` tier is never sent to Cedar by contract | none |
| `authority._instant` (ISO-8601 parsing) | Cedar's `datetime` extension parsed the same strings unchanged | - (no conversion needed, but the kernel still parses its own reads independently) |

## 2. Adapter size

| Measure | Value |
| --- | --- |
| Lines we wrote (`materialise.py`, `project.mjs`, `run.mjs`, `check.mjs`, `next-load.mjs`, `schema.cedarschema.json`, `policies.cedar`) | 738 (`wc -l`: 116 + 172 + 111 + 55 + 140 + 78 + 66) |
| Upstream concepts the adapter had to learn | 9: (1) `EntityJson` shape (`uid`/`attrs`/`parents`); (2) namespaced `SchemaJson` (`entityTypes`, `actions`, `commonTypes`); (3) action `appliesTo` (`principalTypes`/`resourceTypes`/`context`); (4) the `PolicySet` wrapper object (`{staticPolicies}`, not a bare string); (5) policy syntax (`permit`/`forbid`/`when`, `has`, `in`, `.contains()`, `if`-`then`-`else`); (6) strict-mode optional-attribute narrowing, which only `if`-`then`-`else` reliably satisfies, not `!has \|\| ...`; (7) the `datetime`/`decimal` extension-value encoding (`{"__extn":{"fn":"datetime","arg":...}}`); (8) the discriminated-union `Answer` shapes (`type: "success" \| "failure"`) every call returns; (9) `in`'s ancestor-only semantics - no descendant query exists |
| Upstream packages installed | 1 (`@cedar-policy/cedar-wasm`), 0 transitive dependencies (`npm ls --all`) |
| `node_modules` size | 13M |
| Build/install wall time | 17s (`npm install`, cold) |
| Node/tool version required | Node v24.11.1, npm 11.6.2 - first attempt, no version pin needed beyond what was already on this host |
| Native modules compiled | 0 - the package ships prebuilt `cedar_wasm_bg.wasm` for `esm`/`nodejs`/`web`; no `.node` file exists anywhere under `node_modules/` |

## 3. Upgrade burden

| `@cedar-policy/cedar-wasm` release | Date | Gap from previous |
| --- | --- | --- |
| 4.11.0 | 2026-05-18 | - |
| 4.11.1 | 2026-06-09 | 22 days |
| 4.11.2 | 2026-06-23 | 14 days |
| 4.12.0 | 2026-07-28 | 35 days |

Every upstream surface this spike touched is a documented, public entry point:
`isAuthorized`, `validate`, `checkParseSchema`, `checkParsePolicySet`, the
`Schema`/`PolicySet`/`EntityJson`/`AuthorizationCall` types, and the Cedar
policy language itself. Nothing under `node_modules/@cedar-policy/cedar-wasm`
was read, patched, or relied upon beyond its published `.d.ts` and README - no
internal module, undocumented field, or private function was touched.

## 4. What we could plausibly stop owning

| Ours (path / function) | Upstream did this job here |
| --- | --- |
| `scripts/sovkernel/authority.py::_grant_unavailable` (status/actor/capability/effect-ceiling clauses, ~18 of its 26 lines) | Cedar's `permit` conditions |
| `scripts/sovkernel/authority.py::_branch_refused` (9 lines) | Cedar `Branch`-set `in` |
| `scripts/sovkernel/authority.py::_budget_exceeded` (the ceiling-comparison branch, ~10 of its 18 lines) | Cedar `if`-`then`-`else` over `Long` attributes |
| `scripts/sovkernel/authority.py` JUDGEMENT-issuer clause (~3 lines inside `_grant_unavailable`) | one `forbid` policy |
| `scripts/sovkernel/scope.py::_covers` (7 lines) and `out_of_scope`'s prefix-admission half | `resource in includedPaths` |
| `scripts/sovkernel/scope.py::_selects_excluded`, "is inside" half (~4 of its 22 lines) | `resource in excludedPaths` |

| Ours that stayed ours | Why |
| --- | --- |
| `scripts/sovkernel/scope.py::_ungradeable` (64 lines) | No Cedar primitive inspects a string for `..`, a doubled separator, a trailing separator, a pattern character, pathspec magic, a backslash, or an absolute-path spelling. Cedar only ever sees the consequence (an orphan entity) after this function has already decided the string is ungradeable. 13 of the corpus's 18 `SCOPE` cases exist only because this function exists. |
| `scripts/sovkernel/scope.py::_selects_excluded`, "is a directory containing" half | Cedar's `in` walks ancestors only; there is no "is an ancestor of something excluded" query over a dynamic set. `policies.cedar`'s forbid clause for this direction names the corpus's five excluded entries as policy literals rather than reading `context.grant.excludedPaths`, because expressing it generically would need one literal disjunct per possible excluded entity regardless of which grant is live - see Residuals. |
| `authority.py::_observation_verdict`, `_precondition_unmet`, `_preconditions` (composing grant-wide and capability-specific checks) | `OUTSIDE`-tier by construction; the contract never sends these to Cedar because they are not an authority decision (`AGENTS.md`, "a build cannot witness itself" is the same fact `OBSERVATION_MISSING`/`OBSERVER_NOT_INDEPENDENT` encode). |
| `authority.py::_instant` | Still needed for the kernel's own reads; Cedar's `datetime` extension parsed the same ISO-8601-with-`Z` strings without a conversion step, but the kernel does not call into Cedar to parse its own inputs. |

Where Cedar's diagnostics and `evaluate()`'s `detail` carry the same reason:
every sent case's `diagnostics.reason` names the determining `policyN`, and the
`policies.cedar` comment for that policy states the same fact `evaluate()`'s
`detail` sentence states (e.g. policy2 = revocation, policy3 = JUDGEMENT
issuer). Where they diverge: Cedar never emits a sentence, only a policy id and
(when relevant) a `DetailedError`; in all 32 sent cases `diagnostics.errors` was
empty, so recovering the human-readable reason behind a `policyN` id always
means opening `policies.cedar` and reading the comment, which `evaluate()`'s
`detail` string never requires a reader to do.

## 5. The adversarial next load

Recorded in `experiments/cedar-authority/next-load-cases.json` and
`next-load-results.json`; never added to `grant-cases.json`.

| Scenario | Composed from existing primitives, or bespoke? | Line count either way |
| --- | --- | --- |
| (a) Two RATIFIED grants, the newer excluding a path the older admits | Bespoke for both sides. `evaluate()` needed zero new lines - its existing first-match-wins loop (`authority.py` lines 187-192) already returns `PERMITTED` under the older grant without consulting the newer one's exclusion. Cedar needed a second, separately-named `Grant` entity and a second `forbid` clause per grant (our `next-load.mjs`, ~30 lines), because Cedar has no notion of grant order to resolve first. Executed for real: `evaluate([older, newer], request)` returns `PERMITTED` (`grant:older-unrestricted`); Cedar, given both grants' exclusions as separate forbid clauses, returns `deny`. The two disagree on this exact request. |
| (b) Delegation chain A grants B grants C, C requests | Composes from existing primitives on the Cedar side; bespoke on the kernel side. `evaluate()` has no delegation concept: `_grant_unavailable` compares `actor_id` by string equality (lines 95-96) and would need a new nested loop walking `issuer_id -> actor_id` links, on the order of 15-20 lines plus a cycle guard. Cedar's entity hierarchy already expresses a chain: giving `Actor::C` the parent `Actor::B` and `Actor::B` the parent `Actor::A`, then changing the one permit policy's `principal == context.grant.actor` to `principal in context.grant.actor`, is a one-operator change plus `parents` edges at entity-build time - not executed, since the point is that no new policy is needed, only a different comparison operator. |
| (c) Excluded subtree three levels below an admitted prefix | Composes from existing primitives on both sides. `scope.py`'s `_selects_excluded` and `out_of_scope` already compare full normalised strings with `startswith`/`in`, so depth costs zero new lines on the kernel side. Cedar's `in` walks the full transitive closure of `parents` regardless of how many entities sit between resource and ancestor, so depth costs zero new policy lines there either - the fixed cost was spelling the escape classes (D-008a through D-008l), not how deep an exclusion sits. Not executed: both readings agree the fact is already covered by what D-007/D-008 already exercise. |

## Residuals

- `authority._budget_exceeded`'s unit-mismatch refusal (spend measured in a
  different unit than the grant's budget) is not modeled in `policies.cedar`
  and no corpus case exercises it; `check.mjs` does not grade it either way.
- The "directory containing an excluded entry" forbid clause names the
  corpus's five excluded entries as literals rather than reading them from
  `context.grant.excludedPaths`, because this corpus's one grant's scope is
  never patched - every `SCOPE` case shares one fixed hierarchy. A grant whose
  scope varied per request would need Cedar to answer "is any element of this
  dynamic set an ancestor of the resource", which its `in` operator does not
  express without enumerating that set's members in policy text.
- `next-load-cases.json` scenarios (b) and (c) are analysis, not execution;
  only scenario (a) was run against real Cedar output.
- `node_modules/` is not committed (`.gitignore`) and is deleted from the
  working tree before every `verify.py`/`lint.py` run: this repository's
  `scripts/lint.py` has no exclusion for a vendored JavaScript dependency tree
  (`SKIP_PARTS` in `scripts/lint.py` lists `.git`, `.venv`, `__pycache__`,
  `lineage`, `.local`, `worktrees` - not `node_modules`), and the contract
  forbids editing `scripts/`. `experiments/cedar-authority/evidence/npm-install.txt`
  records the install; `npm install` in that directory restores the package
  for anyone re-running `project.mjs`/`run.mjs`/`next-load.mjs`.
