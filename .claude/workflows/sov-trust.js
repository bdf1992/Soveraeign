export const meta = { name: 'sov-trust', description: 'Advance the Soveraeign trust domain - the built Identity and Registry boundaries of the trust-and-control village - by bounded charter, contract, fixture, or test operations with independent witnessing', whenToUse: 'When services/identity or services/registry needs charter refinement, contract work, defeating fixtures, test placement, or doc coherence. Both are BUILT by their own tests and neither is independently witnessed.', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

const ROOT = '.'

const PLAN_SCHEMA = { type: 'object', required: ['blocked', 'operations', 'owner_held_items'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] } } } }, owner_held_items: { type: 'array', items: { type: 'string' } } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string', enum: ['OPEN->BUILT', 'BUILT->WITNESSED', 'none'] } } }

const objective = (args && args.objective) ? args.objective : 'advance the trust domain one bounded charter, contract, fixture, or test operation'

function buildPrompt(op) {
  return 'You are the trust domain builder for Soveraeign at ' + ROOT + '. Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml first, then load .claude/skills/sov-trust/SKILL.md. ' +
    'Execute exactly one bounded operation. Operation ' + op.id + ': ' + op.description + '. Files in scope: ' + op.files.join(', ') + '. Effect class: ' + op.effect_class + '. ' +
    'Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class, and rollback or refusal boundary. ' +
    'Work outward from services/identity/CHARTER.md and services/registry/CHARTER.md; never invent Identity or Registry semantics those charters do not already carry. Contract and defeating fixtures come before code; make the smallest change; run python scripts/verify.py from ' + ROOT + ' and record its exit code. ' +
    'Hard limits: never run git commit or git push; never settle where principal identity lives (decisions/0048 judgement 3 is the owner seat\'s); never promote either service past BUILT_SELF_TESTED_NOT_WITNESSED; never witness or ratify your own work; never touch Asset Service state or lineage/evidence/. ' +
    'Report files changed, checks observed with commands and exit codes, standing proposals (at most BUILT), anything genuinely owner-held, and the next bounded operation. If the operation cannot proceed within these limits, return a reasoned refusal instead of forcing work.'
}

function filesOverlap(ops) {
  const seen = {}
  for (const op of ops) {
    for (const f of op.files) {
      if (seen[f]) { return true }
      seen[f] = true
    }
  }
  return false
}

phase('Scope')
log('Scope: planning bounded trust-domain work for objective: ' + objective)
const plan = await agent(
  'You are scoping bounded work in the Soveraeign trust domain. Read ' + ROOT + '/AGENTS.md, ' + ROOT + '/STATUS.yaml, ' + ROOT + '/CLASSIFICATION.md, .claude/skills/sov-trust/SKILL.md, everything under ' + ROOT + '/services/identity/ and ' + ROOT + '/services/registry/, and ' + ROOT + '/decisions/0048-principal-identity.md. ' +
  'The founding docket is closed: open_decisions is empty and the O<n> identifiers are retired (decisions/0033-close-the-founding-docket.md). Settle a decision at the lowest tier that can produce evidence defeating the alternatives, and record what would defeat the ruling. The owner gate is acceptance over an evidenced result, never permission to begin. ' +
  'Current standing: the Identity challenge and recovery components are BUILT by 32 of their own cases, which scripts/verify.py runs as the check named "Identity component tests"; the Registry has one built resolve slice and a service manifest at standing BUILT. Neither is independently witnessed, and a build report cannot witness itself. Where principal identity ultimately lives is decisions/0048 judgement 3 and belongs to the owner seat; the charter is deliberately built so that ruling moves one file and changes no semantics, so it gates placement and nothing else. ' +
  'Plan only work inside services/identity/, services/registry/, and the owner-record table at contracts/domain-owners.json. Blocked edge is not blocked frontier (AGENTS.md, Self-direction is not delegation): an unresolved owner decision gates only the transition that needs it. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. ' +
  'owner_held_items carries ONLY a genuine owner seam - an external-world effect, an irreversible one, publication, owner identity or naming, a secret, destructive administration, or a resource commitment (contracts/acceptance-policy.json). An unsatisfied dependency is HELD and a missing domain owner is UNROUTED; neither is owner-held and neither belongs in this list. Each entry names why no evidence at this tier could settle it. ' +
  'Effect classes are limited to RECORD_LOCAL and RESOURCE_CONSUMPTION; no EXTERNAL_WORLD effects in Phase I. Evidence files under lineage/evidence/ are immutable. ' +
  'Produce a bounded operation plan honoring these constraints for: ' + objective,
  { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' }
)

if (!plan || plan.blocked || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning without forcing work')
  return {
    domain: 'trust',
    objective: objective,
    blocked: true,
    planned: plan ? plan.operations : [],
    built: [],
    witness: null,
    residuals: (plan && plan.blocked_reason) ? [plan.blocked_reason] : [],
    owner_held_items: plan ? plan.owner_held_items : ['scope agent failed; re-run sov-trust Scope'],
    standing_proposal: null
  }
}

phase('Build')
log('Build: executing ' + plan.operations.length + ' planned operation(s)')
let buildResults = []
if (filesOverlap(plan.operations)) {
  for (const op of plan.operations) {
    buildResults.push(await agent(buildPrompt(op), { agentType: 'sov-worker', phase: 'Build', label: 'build-' + op.id }))
  }
} else {
  buildResults = await parallel(plan.operations.map(function (op) {
    return function () { return agent(buildPrompt(op), { agentType: 'sov-worker', phase: 'Build', label: 'build-' + op.id }) }
  }))
}
const built = buildResults.filter(function (r) { return r !== null && r !== undefined })
log('Build: ' + built.length + ' of ' + plan.operations.length + ' operation(s) returned reports')

phase('Witness')
const claimed = plan.operations.map(function (op) { return { operation_id: op.id, description: op.description, files: op.files } })
const changedFiles = []
for (const op of plan.operations) {
  for (const f of op.files) {
    if (changedFiles.indexOf(f) === -1) { changedFiles.push(f) }
  }
}
log('Witness: independent inspection of ' + changedFiles.length + ' claimed file(s)')
const witness = await agent(
  'You are an independent witness for the Soveraeign repository at ' + ROOT + '. You receive only the claimed operations and changed files, never the builder reasoning; a builder report is not observation. ' +
  'Claimed operations: ' + JSON.stringify(claimed) + '. Changed files: ' + changedFiles.join(', ') + '. ' +
  'Independently inspect the working-tree diffs for those files (git status, git diff), check them against AGENTS.md, STATUS.yaml, CLASSIFICATION.md, services/identity/CHARTER.md, and services/registry/CHARTER.md, and run python scripts/verify.py from ' + ROOT + ', recording its exit code. Run python -m unittest discover -s tests from services/identity yourself rather than trusting the reported count. ' +
  'For each claimed operation return a verdict: reproduced, dissented, or unattestable. List residual failures. State the highest standing transition your own observation supports: OPEN->BUILT, BUILT->WITNESSED, or none. Never propose RATIFIED; only Bdo ratifies.',
  { agentType: 'sov-witness', phase: 'Witness', schema: WITNESS_SCHEMA, label: 'witness' }
)
if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }

let standingProposal = null
if (witness && witness.verdicts && witness.verdicts.length > 0) {
  let dissent = false
  let allReproduced = true
  for (const v of witness.verdicts) {
    if (v.verdict === 'dissented') { dissent = true }
    if (v.verdict !== 'reproduced') { allReproduced = false }
  }
  if (!dissent) {
    if (allReproduced && witness.standing_supported === 'BUILT->WITNESSED') {
      standingProposal = 'BUILT -> WITNESSED'
    } else if (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED') {
      standingProposal = 'OPEN -> BUILT'
    }
  }
}
log('Witness: verdicts recorded; standing proposal: ' + (standingProposal ? standingProposal : 'none'))

return {
  domain: 'trust',
  objective: objective,
  blocked: false,
  planned: plan.operations,
  built: built,
  witness: witness,
  residuals: witness ? witness.residuals : ['witness agent failed; run is unattestable'],
  owner_held_items: plan.owner_held_items,
  standing_proposal: standingProposal
}
