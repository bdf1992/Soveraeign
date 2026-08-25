# 0052 · Owner ruling: the product ground is accepted, and four things move

Status: `OWNER-RULED 2026-08-24 · APPLIED`

Bdo ruled on `reports/2026-08-24-product-ground-acceptance.md`. This records what he
decided and what changed as a result. `decisions/0051` records the correction pass that
produced the artifacts; this records their acceptance and the four rulings that came with
it.

## 1 · `EPOCH-1 / GROUND-1` — `ACCEPT`

The Product Ground is accepted as the stable semantic ground for Soveraeign. Sixteen
claims, admitted by the test that changing one means a materially different product rather
than a different implementation.

Recorded in `STATUS.yaml` as `product_ground_status: OWNER_ACCEPTED_EPOCH_1_GROUND_1`, and
in `contracts/product-ground.json` under `accepted`. The two must agree:
`ground.acceptance_defects()` refuses an artifact that calls itself accepted while the
acceptance record does not name that exact revision, which is `decisions/0037`'s
agreement-by-check applied to acceptance.

The rendering moved `GROUND-1.0` → `GROUND-1.1`. The revision did not: recording acceptance
changed no claim, which is exactly what the rendering level is for.

**Two things the ruling preserved explicitly.**

The four planes stay separate — ground is meaning, declared state is what claims to exist,
evidence is what reality demonstrated, and a fact is a proposition read through ground and
supported by both. Ground is never itself evidence that a state fact is true. `GROUND-010`,
a report is not an observation, is accepted and the node cannot presently keep it, and
saying both at once is what the separation is for.

Accepted ground is not rewritten in place. A change of meaning mints a revision; retiring
or replacing a claim mints an epoch.

## 2 · `CANON-2` — `ACCEPT` with `PROMISE-14` struck

Bdo did not accept "standing up a node" as a durable product promise merely because a node
has to come into existence somehow. `GROUND-016` carries the durable claim — a node is
whole at any size — and installation, establishment, bootstrapping, first run, deployment
and onboarding sit beneath it as product experiences. They may become important journeys
and requirements without becoming permanent canon promises.

`PROMISE-14` is retired in `CANON-3` with no successor. The identifier is not repointed.

`JOURNEY-12` is **kept**: someone still has to go from nothing to a node, `node.establish`
and `node.read-identity` are still `MISSING`, and a journey does not have to be eternal
product identity to be a real gap. It now serves `PROMISE-02`.

One consequence, recorded rather than smoothed over: `GROUND-016` is now carried by
`PROMISE-15` alone, which is `LATER`. The check requires a ground claim to be carried, not
carried in this phase, so this is admissible — and it means the only `PHASE_I` reading of
"a node is whole at any size" today is `JOURNEY-12`'s gap list.

`CANON-3.0` is accepted under `EPOCH-1`. No promise now carries
`OWNER_CONFIRMATION_REQUIRED`; the one that did was struck rather than confirmed.

## 3 · Reading operational history is an operator act

`GROUND-002` says people and models resolve through the same history, so an operator must
be able to inspect the history it is authorized to see. The Record Service still owns the
lifecycle and the authoritative journal; that does not make reading it back-office
machinery.

The split Bdo drew, applied exactly:

| Capability | Office | Why |
| --- | --- | --- |
| `record.read-entry` | **`FRONT/operator-desk`**, `HUMAN` and `MODEL` | Authorized history reading. Subject `journal-entry`, also reads terminal receipts and counter-records |
| `record.reconstruct-journal` | `BACK/record`, `SYSTEM` | Subject `digest-chain`. Chaining is journal machinery |
| `record.read-projection` | `BACK/record`, `SYSTEM` | Internal projection mechanics |
| `record.append-entry`, `record.append-receipt` | `BACK/record`, `SYSTEM` | Storage |
| `record.counter-entry` | `BACK/record`, `SYSTEM` | Not a read. The operator-facing correction is `asset.retract-record`; this is the kernel transition beneath it |
| `record.rebuild-projections`, `record.drop-projections` | `BACK/record`, `SYSTEM` | Maintenance |

The journal was **not** duplicated into a second history surface. The existing Record
capability is exposed under normal authority: the read still costs the `read:journal`
grant, and moving the counter widens who may ask, never what they hold.

The MCP withholding is reversed. `bindings/mcp/manifest.json` serves `record_entries`
again, `withheld_endpoints` is empty, and `contracts/capability-offices.json` names the
tool so the table and the binding stay held together by a check.

The withholding machinery stays, and stays tested: `bindings/mcp/tests/test_gateway.py`
now exercises it against a manifest the case builds rather than against whatever happens
to be withheld, and adds a positive case recording that nothing is.

`scripts/tests/test_capability_map.py` still drives `BACK_OFFICE_EXPOSED` — through
`record.reconstruct-journal`, which is genuinely back-office. The rule was never weakened;
the example moved because the example stopped being an example.

## 4 · Bare `Requirement` means the product ladder

`PROD-I-*` is older, owner-visible and already load-bearing in the attribution spine, so it
keeps the bare word. The `#41`/`#48` concept is `CompetenceRequirement`.

```text
ProductRequirement     something the product or phase must prove
CompetenceRequirement  something a participant or skill must be competent to satisfy
```

No unqualified `Requirement` edge may ambiguously cross those two ladders. `PROD-I-*` is
not renamed; in a typed graph `ProductRequirement` is the explicit form of the bare word
where disambiguation helps.

`CLASSIFICATION.md` owns the distinction and gained a section for it.
`OPEN-SEAMS.md` S20 records the collision as closed, and notes the difference from S18:
this one was caught before either half landed.

**Residual, and it is an external action.** `#41` and `#48` still carry the unqualified
word in their live bodies. The amendment is one sentence in each:

> `Requirement` here means `CompetenceRequirement` — an obligation a skill or capability
> carries. It is a different ladder from `PRD.md`'s `PROD-I-*` product requirements, which
> keep the bare word (`CLASSIFICATION.md`, `decisions/0052`). No unqualified `Requirement`
> edge may cross the two.

Pushing it is an attended crossing and has not been taken. `adapters/github/` is also held
by another live session.

## 5 · Do not expand `SOV` as an acronym

Accepted from the investigation in `decisions/0051` §8 and the acceptance report I2:

- Product Ground is the stable semantic vocabulary.
- Sov is the operating profile that can read it.
- Perspectival reading is a Sov capability and a projection, not a third meaning of "SOV".

The double backronym would have added ambiguity without adding structure, and reproduced
`OPEN-SEAMS.md` S18 in the one place the repository can least afford it. `SOV.md` is
unchanged.

## 6 · Defaults accepted implicitly

Bdo accepted these and said they do not return to him unless new evidence defeats them:
`GROUND.md` at the repository root; rendering, revision and epoch as distinct concepts;
`source` rather than a third use of `standing` on promises; `evidential_status` rather than
a third standing lifecycle on facts; `IMPLEMENTATION_DERIVED` as a hard defect; retirement
rather than semantic repointing; `JOURNEY-14` as the recorded perspectival-read gap; the
ground size bound as a machine-enforced contract; and distinct-unit accounting rather than
summing semantic views.

## 7 · The acceptance consequence

From here, accepted ground is the stable semantic reference for product attribution. New
work does not have to be product ground to be legitimate, but meaningful product work
should be able to explain its relationship upward without inventing product intent after
implementation.

Infrastructure and harness work may correctly terminate at an engineering or enabling
objective rather than pretending to realize a promise. The harness derives from no ground
claim, and that is the right answer rather than a gap.

## What was not decided

Bdo accepted the semantic ground. He did not assert that the implementation keeps any of
it, and the artifacts say so in their own words.

## Residuals

- `#41` and `#48` bodies still carry the unqualified word. Attended, not taken.
- `GROUND-016` is carried by a `LATER` promise alone.
- The `ground` counter in `contracts/capability-offices.json` means local infrastructure
  and deployment custody, while Product Ground means product meaning. Two things named
  ground, in different cases and different shapes, and neither is an identifier of the
  other's kind. Not a collision today and worth watching, since S18 and S20 are both this
  failure. Naming is Bdo's; nothing was renamed.
- `OPEN-SEAMS.md` S10, the product boundary, is untouched by the acceptance.
