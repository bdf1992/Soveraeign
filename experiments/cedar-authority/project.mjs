// Project cases.materialised.json into Cedar entities and requests.
//
// The corpus's one base_grant never has its scope patched, so every case in
// this corpus shares the same five included prefixes and five excluded entries
// (conformance/fixtures/authority/grant-cases.json base_grant.scope). That lets
// this script build one fixed Path entity hierarchy rather than a general
// per-grant one: services, contracts, conformance, scripts, .claude admitted;
// contracts/standing-grants.json, decisions, STATUS.yaml, SPEC.md, AGENTS.md
// excluded. A concrete requested path is given `parents` directly at the
// nearest ancestor Cedar needs - not a full directory chain - because Cedar's
// `in` walks the transitive closure of `parents` however many hops it takes.
//
// A `SCOPE` case tagged `precomputed` in cases.materialised.json (its raw path
// fails sovkernel.scope._ungradeable) gets an orphan Path entity keyed to its
// own case id, with no parents at all. It is then never `in` any included
// prefix, so Cedar refuses it through the same general rule every other
// out-of-scope path fails, without a bespoke boolean. What was precomputed
// outside Cedar is which strings could be given a real tree position at all -
// not the verdict.

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const NS = "SoveraeignAuthority";

const materialised = JSON.parse(readFileSync(path.join(HERE, "cases.materialised.json"), "utf8"));

const EFFECT_ORDER = ["RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD"];

// The known ancestor for every concrete (non-precomputed) path this corpus's
// cases request. Root-level excluded entries and README.md have no parent.
const KNOWN_PARENT = {
  "services/asset/src/soveraeign_asset_service/core.py": "services",
  "services/asset/src/core.py": "services",
  "contracts/standing-grants.json": "contracts",
  "contracts/sub": "contracts",
  "decisions/0061-x.md": "decisions",
};
const ROOT_PATHS = new Set([
  "services", "contracts", "conformance", "scripts", ".claude",
  "contracts/standing-grants.json", "decisions", "STATUS.yaml", "SPEC.md", "AGENTS.md",
  "README.md", "contracts/sub", "decisions/0061-x.md",
  "services/asset/src/soveraeign_asset_service/core.py", "services/asset/src/core.py",
]);

const INCLUDED_PREFIXES = ["services", "contracts", "conformance", "scripts", ".claude"];
const EXCLUDED_ENTRIES = ["contracts/standing-grants.json", "decisions", "STATUS.yaml", "SPEC.md", "AGENTS.md"];

function euid(type, id) {
  return { type: `${NS}::${type}`, id };
}

function entityJson(type, id, attrs, parents) {
  return { uid: euid(type, id), attrs: attrs || {}, parents: (parents || []).map((p) => euid("Path", p)) };
}

function datetimeAttr(value) {
  return { __extn: { fn: "datetime", arg: value } };
}

function entityAttr(type, id) {
  return { __entity: euid(type, id) };
}

const entitiesById = new Map(); // "Type::id" -> entity json
function putEntity(entity) {
  const key = `${entity.uid.type}::${entity.uid.id}`;
  if (!entitiesById.has(key)) entitiesById.set(key, entity);
  return entity;
}

// Static Path entities: the fixed scope hierarchy, plus every concrete path
// named directly by a case that isn't tagged precomputed.
for (const p of ROOT_PATHS) {
  const parent = KNOWN_PARENT[p];
  putEntity(entityJson("Path", p, {}, parent ? [parent] : []));
}

const includedPathsAttr = INCLUDED_PREFIXES.map((p) => entityAttr("Path", p));
const excludedPathsAttr = EXCLUDED_ENTRIES.map((p) => entityAttr("Path", p));

function pathEntityIdFor(rawPath, precomputed, caseId) {
  if (!precomputed) return rawPath;
  const orphanId = `unresolved/${caseId}`;
  putEntity(entityJson("Path", orphanId, {}, []));
  return orphanId;
}

function actorEntity(id) {
  putEntity(entityJson("Actor", id, {}, []));
  return id;
}

function branchEntity(id) {
  putEntity(entityJson("Branch", id, {}, []));
  return id;
}

function actionEntity(capability) {
  // Actions are declared in the schema; cedar-wasm still wants an entity JSON
  // record for each one referenced from an attribute set (Grant.capabilities).
  putEntity({ uid: euid("Action", capability), attrs: {}, parents: [] });
  return capability;
}

const requests = [];

for (const c of materialised.cases) {
  const grant = c.grant;
  const request = c.request;

  const grantId = `grant/${c.case_id}`;
  const actor = actorEntity(grant.actor_id);
  const requestingActor = actorEntity(request.actor_id);
  const capabilities = grant.capabilities.map((cap) => entityAttr("Action", actionEntity(cap)));
  const requestAction = actionEntity(request.capability);

  const grantAttrs = {
    status: grant.status,
    actor: entityAttr("Actor", actor),
    authorityType: grant.authority_type,
    issuerId: grant.issuer_id,
    capabilities,
    includedPaths: includedPathsAttr,
    excludedPaths: excludedPathsAttr,
    effectCeilingOrdinal: EFFECT_ORDER.indexOf(grant.effect_ceiling),
    validFrom: datetimeAttr(grant.valid_from),
    validUntil: datetimeAttr(grant.valid_until),
  };
  if (grant.scope.branches) {
    grantAttrs.branches = grant.scope.branches.map((b) => entityAttr("Branch", branchEntity(b)));
  }
  if (grant.budget.ceiling !== null && grant.budget.ceiling !== undefined) {
    grantAttrs.budgetUnit = grant.budget.unit;
    grantAttrs.budgetCeiling = grant.budget.ceiling;
  }
  if (grant.revoked_at) {
    grantAttrs.revokedAt = datetimeAttr(grant.revoked_at);
  }
  putEntity({ uid: euid("Grant", grantId), attrs: grantAttrs, parents: [] });

  const context = {
    grant: entityAttr("Grant", grantId),
    now: datetimeAttr(request.at),
    branch: entityAttr("Branch", branchEntity(request.branch)),
    effectClassOrdinal: EFFECT_ORDER.indexOf(request.effect_class),
  };
  if (request.spend) {
    context.spendUnit = request.spend.unit;
    context.spendAmount = request.spend.amount;
  }

  const calls = request.paths.map((rawPath, i) => {
    const resourceId = pathEntityIdFor(rawPath, c.precomputed, `${c.case_id}-${i}`);
    return {
      raw_path: rawPath,
      principal: euid("Actor", requestingActor),
      action: euid("Action", requestAction),
      resource: euid("Path", resourceId),
      context,
    };
  });

  requests.push({ case_id: c.case_id, tier: c.tier, precomputed: c.precomputed, calls });
}

writeFileSync(path.join(HERE, "entities.json"), JSON.stringify(Array.from(entitiesById.values()), null, 2) + "\n");
writeFileSync(path.join(HERE, "requests.json"), JSON.stringify(requests, null, 2) + "\n");

console.log(`projected ${entitiesById.size} entities and ${requests.length} case request sets`);
