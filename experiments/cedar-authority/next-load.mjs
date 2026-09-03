// Executes NL-A from next-load-cases.json for real: two RATIFIED grants, the
// newer one excluding a subtree the older one admits, graded first by the
// kernel's evaluate() and then by Cedar against a small standalone policy set
// (not schema.cedarschema.json / policies.cedar - this scenario needs two
// named grants, which the corpus's one-grant schema does not model).
//
// This is exploration recorded for the report, not part of check.mjs's gate.

import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { execFileSync } from "node:child_process";
import * as cedar from "@cedar-policy/cedar-wasm";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, "..", "..");

// --- evaluate() reading, run for real against the two grants ---
const pyScript = `
import json, sys
sys.path.insert(0, r"${path.join(REPO_ROOT, "scripts")}")
from sovkernel import authority

older = {
    "grant_schema": "soveraeign-authority-grant/v1", "status": "RATIFIED",
    "grant_id": "grant:older-unrestricted", "issuer_id": "bdo", "actor_id": "sov",
    "authority_type": "VERIFICATION", "capabilities": ["repository.land"],
    "scope": {"paths": ["services/"], "excluded_paths": []},
    "budget": {"unit": "none", "ceiling": None}, "effect_ceiling": "RESOURCE_CONSUMPTION",
    "valid_from": "2026-08-01T00:00:00Z", "valid_until": "2027-01-01T00:00:00Z", "revoked_at": None,
}
newer = dict(older)
newer["grant_id"] = "grant:newer-carves-out-legacy"
newer["scope"] = {"paths": ["services/"], "excluded_paths": ["services/legacy/"]}

request = {
    "request_schema": "soveraeign-authority-request/v1", "actor_id": "sov",
    "capability": "repository.land", "effect_class": "RESOURCE_CONSUMPTION",
    "at": "2026-09-01T00:00:00Z", "branch": "main",
    "paths": ["services/legacy/thing.py"], "spend": None,
    "evidence": {"checks": {}, "observation": None},
}
result = authority.evaluate([older, newer], request)
print(json.dumps(result))
`;
const evalOut = execFileSync("python", ["-c", pyScript], { encoding: "utf8" });
const evaluateResult = JSON.parse(evalOut);

// --- Cedar reading: two Grant entities, one forbid clause per grant's excludedPaths ---
const NS = "NextLoad";
const schema = {
  [NS]: {
    entityTypes: {
      Actor: { shape: { type: "Record", attributes: {} } },
      Path: { memberOfTypes: ["Path"], shape: { type: "Record", attributes: {} } },
      Grant: {
        shape: {
          type: "Record",
          attributes: {
            excludedPaths: { type: "Set", element: { type: "Entity", name: "Path" } },
          },
        },
      },
    },
    actions: {
      "repository.land": {
        appliesTo: {
          principalTypes: ["Actor"],
          resourceTypes: ["Path"],
          context: {
            type: "Record",
            attributes: {
              olderGrant: { type: "Entity", name: "Grant" },
              newerGrant: { type: "Entity", name: "Grant" },
            },
          },
        },
      },
    },
  },
};

const policyText = `
permit(principal, action, resource);

forbid(principal, action, resource)
when { resource in context.olderGrant.excludedPaths };

forbid(principal, action, resource)
when { resource in context.newerGrant.excludedPaths };
`;

const euid = (type, id) => ({ type: `${NS}::${type}`, id });
const entities = [
  { uid: euid("Actor", "sov"), attrs: {}, parents: [] },
  { uid: euid("Path", "services"), attrs: {}, parents: [] },
  { uid: euid("Path", "services/legacy"), attrs: {}, parents: [euid("Path", "services")] },
  { uid: euid("Path", "services/legacy/thing.py"), attrs: {}, parents: [euid("Path", "services/legacy")] },
  {
    uid: euid("Grant", "older-unrestricted"),
    attrs: { excludedPaths: [] },
    parents: [],
  },
  {
    uid: euid("Grant", "newer-carves-out-legacy"),
    attrs: { excludedPaths: [{ __entity: euid("Path", "services/legacy") }] },
    parents: [],
  },
];

const policies = { staticPolicies: policyText };
const validation = cedar.validate({ schema, policies, validationSettings: { mode: "strict" } });

const answer = cedar.isAuthorized({
  principal: euid("Actor", "sov"),
  action: euid("Action", "repository.land"),
  resource: euid("Path", "services/legacy/thing.py"),
  context: {
    olderGrant: { __entity: euid("Grant", "older-unrestricted") },
    newerGrant: { __entity: euid("Grant", "newer-carves-out-legacy") },
  },
  schema,
  validateRequest: true,
  policies,
  entities,
});

const cedarDecision = answer.type === "success" ? answer.response.decision : `error: ${JSON.stringify(answer.errors)}`;

const output = {
  scenario: "NL-A-later-grant-excludes-what-earlier-admits",
  evaluate_verdict: evaluateResult.verdict === "PERMITTED" ? "PERMITTED" : evaluateResult.code,
  evaluate_detail: evaluateResult.detail,
  evaluate_grant_id: evaluateResult.grant_id,
  cedar_validation_errors: validation.type === "success" ? validation.validationErrors : validation,
  cedar_decision: cedarDecision,
  diverges: (evaluateResult.verdict === "PERMITTED") !== (cedarDecision === "allow"),
};
writeFileSync(path.join(HERE, "next-load-results.json"), JSON.stringify(output, null, 2) + "\n");
console.log(JSON.stringify(output, null, 2));
