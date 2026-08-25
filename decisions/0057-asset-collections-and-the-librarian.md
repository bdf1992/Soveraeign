# 0057 · Assets are organized in typed collections, and a librarian reports on them

Status: `OWNER-DIRECTED · PROPOSED`

## Decision

A user organizes assets. The Asset Service gains four records and six operations
for it, and a librarian role reports on how well the library holds to its own
declared schema.

- **collection type** — a declared schema: which metadata fields a member must
  carry, which optional ones it may, an optional controlled vocabulary per
  field, and which asset roles the collection admits. `project` is one such
  type, not a special case in the code.
- **asset collection** — a named, typed, curated set of assets.
- **collection membership** — one asset filed into one collection by one actor,
  receipted, and removable only by counter-record.
- **library conformance** — the derived read that judges every member against
  its type, and names every asset filed nowhere.

`services/asset/src/soveraeign_asset_service/organization.py` owns the first
three; `librarian.py` owns the fourth. Both are reached at
`service.organization` and `service.librarian`.

## Ruling 1 — filing is curatorial, and description is judgement

Declaring a type, opening a collection, and filing an asset commit directly
under a live grant. They do not pass through `ratify`.

The alternative — routing every filing through propose/ratify the way an asset
relationship goes — was rejected because it makes an ordinary library
unusable: an operator filing two hundred images would mint two hundred
judgement claims, and `ratify:judgement` would stop meaning what it means
everywhere else. Filing is reversible, record-local, and attributable, which is
what a grant is for.

What a member *claims about itself* keeps the existing rule unchanged. The
conformance read counts only ratified descriptions as conformance, and reports
a recorded-but-unratified field as `CLAIMED_UNRATIFIED` — a third state, never
folded into either pass or fail. That is `AGENTS.md`, Evidence and standing,
applied to metadata rather than restated.

**What would defeat this ruling:** evidence that a filing decision carries
consequence a counter-record cannot undo — an access boundary derived from
membership, or an external effect triggered by it. Either would make membership
a judgement claim and this ruling wrong.

## Ruling 2 — the name is qualified, never bare

`CLASSIFICATION.md` already gives the Asset Projection Service a *projection
collection*: a declared retrieval scope, which is an index. The record this
decision adds is a curated set. They are different things that would otherwise
share one word.

Every machine surface therefore carries the qualified name. The manifest
subject is `asset-collection`; the projection service's stays
`projection-collection`; the required authorities are `declare:asset-collection`
and `declare:collection`, which do not collide. Prose qualifies the bare word.

Renaming either is `NAMING.md`'s screen and Bdo's call, so nothing is renamed
here. The collision is recorded as seam S22.

**What would defeat this ruling:** a reading under which the two are one record
seen from two sides — an index that is also the curated set. If that holds, one
service owns both and the qualifier is hiding a duplicated concept.

## Ruling 3 — the librarian proposes and never ratifies

The librarian is a stance, not a new harness role. `.claude/skills/sov-librarian/`
carries what it knows and it runs on the existing worker and witness agents,
because domain knowledge lives in skills and roles stay stable.

Within it: a librarian may file and unfile assets under `organize:asset`, and
may record a description under `propose:description`. It may not ratify one.
A model that could ratify its own metadata would turn `CLAIMED_UNRATIFIED` into
a formality, which is the exact defect Ruling 1 exists to prevent. It also may
not invent a value outside a declared vocabulary: an unrepresentable value is a
finding against the type, not a reason to widen it.

**What would defeat this ruling:** a declared field whose correct value is
mechanically derivable from the payload — a digest, a MIME type, a pixel
dimension. That is not judgement and holding it to ratification would be
ceremony. Such fields are not in scope here and would need their own ruling.

## Effect class and rollback

`RECORD_LOCAL` throughout. No external effect, no new runtime dependency, no
change to an existing operation's behaviour. Rollback is removing the four
records from `services/asset/contracts/service.json`, the six assignments from
`contracts/capability-offices.json`, the two modules, and rebuilding the
capability map; nothing else reads them.

## Defaults taken

- Membership is stored in its own table rather than reusing `relationships`
  with a `member-of` predicate. A collection has no payload, no digest, and no
  version history, so making it an asset would have required inventing bytes.
- A type may not be redeclared. Editing a live schema under members filed
  against it is a migration question this slice does not answer, so the second
  declaration is refused with `STALE_STATE` rather than silently overwriting.
- `MEMBER_KIND_REFUSED` is checked at filing time and reported again by the
  conformance read, because the two catch different things: the first stops a
  bad filing, the second surfaces members filed under a spec that has since
  been re-read.
- `EMPTY_COLLECTION` is a defect rather than a clean bill. A collection nobody
  filed into reads as passing under every other rule, which is the wrong answer
  for an operator scanning a report.

## Standing

Proposed. The implementation is `BUILT` and self-tested: 40 cases in
`services/asset/tests/test_organization.py` and `test_librarian.py`, every
declared refusal produced by at least one of them. That is `BUILT` evidence
only. Independent witnessing has not run, and only Bdo ratifies.
