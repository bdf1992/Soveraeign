// Gate: exit 1 unless every CEDAR/SCOPE case matches the kernel, no OUTSIDE
// case was ever sent to Cedar, tier counts sum to 37, and the working tree
// under scripts/, contracts/, conformance/ is untouched relative to `dev`.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { execFileSync } from "node:child_process";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(HERE, "..", "..");

const results = JSON.parse(readFileSync(path.join(HERE, "results.json"), "utf8")).results;

const failures = [];

const mismatches = results.filter((r) => r.sent_to_cedar && !r.match);
for (const m of mismatches) {
  failures.push(`${m.case_id}: kernel said ${m.kernel_verdict}, cedar said ${m.cedar_verdict}`);
}

const outsideSent = results.filter((r) => r.tier === "OUTSIDE" && r.sent_to_cedar);
for (const o of outsideSent) {
  failures.push(`${o.case_id}: an OUTSIDE case was sent to Cedar`);
}

const tierCounts = {};
for (const r of results) tierCounts[r.tier] = (tierCounts[r.tier] || 0) + 1;
const total = Object.values(tierCounts).reduce((a, b) => a + b, 0);
if (total !== 37) {
  failures.push(`tier counts sum to ${total}, not 37: ${JSON.stringify(tierCounts)}`);
}

let diffClean = true;
try {
  const diff = execFileSync(
    "git",
    ["diff", "--quiet", "dev", "--", "scripts", "contracts", "conformance"],
    { cwd: REPO_ROOT }
  );
} catch (err) {
  diffClean = false;
  failures.push(
    `git diff dev -- scripts contracts conformance is not clean: ${err.status === 1 ? "differs" : err.message}`
  );
}

if (failures.length > 0) {
  console.error("CHECK FAILED:");
  for (const f of failures) console.error(`  - ${f}`);
  process.exit(1);
}

console.log(`CHECK PASSED: ${total} cases, tiers ${JSON.stringify(tierCounts)}, 0 mismatches, ` +
  `0 OUTSIDE cases sent, working tree unchanged under scripts/contracts/conformance`);
