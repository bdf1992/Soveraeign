// Validate policies.cedar against schema.cedarschema.json, then authorize every
// CEDAR and SCOPE case in requests.json through @cedar-policy/cedar-wasm.
// An OUTSIDE case is never sent - those refusal codes are not an authority
// decision Cedar's schema even declares a shape for.
//
// A case with more than one requested path (D-007) makes one isAuthorized call
// per path and ANDs the decisions: sovkernel.authority.evaluate() grades a
// request's whole path list against one grant in a single call, so reproducing
// that with Cedar's one-resource-per-call model needs a small loop this schema
// carries no equivalent for.

import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import * as cedar from "@cedar-policy/cedar-wasm";

const HERE = path.dirname(fileURLToPath(import.meta.url));

const schema = JSON.parse(readFileSync(path.join(HERE, "schema.cedarschema.json"), "utf8"));
const policyText = readFileSync(path.join(HERE, "policies.cedar"), "utf8");
const entities = JSON.parse(readFileSync(path.join(HERE, "entities.json"), "utf8"));
const requests = JSON.parse(readFileSync(path.join(HERE, "requests.json"), "utf8"));
const materialised = JSON.parse(readFileSync(path.join(HERE, "cases.materialised.json"), "utf8"));
const byId = new Map(materialised.cases.map((c) => [c.case_id, c]));

const policies = { staticPolicies: policyText };

const validation = cedar.validate({ schema, policies, validationSettings: { mode: "strict" } });
if (validation.type !== "success") {
  console.error("policy set failed schema validation:", JSON.stringify(validation, null, 2));
  process.exit(1);
}
if (validation.validationErrors.length > 0) {
  console.error("validation errors:", JSON.stringify(validation.validationErrors, null, 2));
  process.exit(1);
}
console.log(
  `validation: ${validation.validationErrors.length} error(s), ${validation.validationWarnings.length} warning(s)`
);

const results = [];

for (const req of requests) {
  const kernelCase = byId.get(req.case_id);
  if (req.tier === "OUTSIDE") {
    results.push({
      case_id: req.case_id,
      tier: req.tier,
      precomputed: req.precomputed,
      sent_to_cedar: false,
      kernel_verdict: kernelCase.kernel_verdict,
      cedar_decision: null,
      calls: [],
    });
    continue;
  }

  const callResults = req.calls.map((call) => {
    const answer = cedar.isAuthorized({
      principal: call.principal,
      action: call.action,
      resource: call.resource,
      context: call.context,
      schema,
      validateRequest: true,
      policies,
      entities,
    });
    if (answer.type !== "success") {
      return { raw_path: call.raw_path, error: answer.errors };
    }
    return {
      raw_path: call.raw_path,
      decision: answer.response.decision,
      determining_policies: answer.response.diagnostics.reason,
      errors: answer.response.diagnostics.errors,
    };
  });

  const failed = callResults.find((r) => r.error);
  const decision = failed
    ? "error"
    : callResults.every((r) => r.decision === "allow")
      ? "allow"
      : "deny";
  const cedarVerdict = decision === "allow" ? "PERMITTED" : "AUTHORITY_REFUSED";

  results.push({
    case_id: req.case_id,
    tier: req.tier,
    precomputed: req.precomputed,
    sent_to_cedar: true,
    kernel_verdict: kernelCase.kernel_verdict,
    cedar_decision: decision,
    cedar_verdict: cedarVerdict,
    match: cedarVerdict === kernelCase.expected,
    kernel_detail: kernelCase.kernel_detail,
    kernel_considered: kernelCase.kernel_considered,
    calls: callResults,
  });
}

writeFileSync(path.join(HERE, "results.json"), JSON.stringify({ validation, results }, null, 2) + "\n");

const sent = results.filter((r) => r.sent_to_cedar);
const mismatches = sent.filter((r) => !r.match);
console.log(`authorized ${sent.length} case(s), ${results.length - sent.length} OUTSIDE case(s) not sent`);
console.log(`mismatches: ${mismatches.length}`);
for (const m of mismatches) {
  console.log(`  ${m.case_id}: expected ${byId.get(m.case_id).expected}, cedar said ${m.cedar_verdict}`);
}
