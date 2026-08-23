export const meta = { name: 'sov-projection', description: 'Advance the Soveraeign Asset Projection Service domain by bounded charter, parity, fixture, or lane operations with independent witnessing', whenToUse: 'When services/projection needs fixture executable-ization, parity-ledger upkeep, charter gap closure, read-path precondition mapping, contract drafting, doc coherence, or - once fixtures are executable and the asset core.py split lands - lane implementation', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

const ROOT = '.'

const PLAN_SCHEMA = { type: 'object', required: ['blocked', 'operations', 'judgement_queue'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] } } } }, judgement_queue: { type: 'array', items: { type: 'string' } } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string', enum: ['OPEN->BUILT', 'BUILT->WITNESSED', 'none'] } } }

const objective = (args && args.objective) ? args.objective : 'advance the projection domain one bounded charter, parity, fixture, or lane operation'

function buildPrompt(op) {
  return 'You are the projection domain builder for Soveraeign at ' + ROOT + '. Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml first, then load the sov-projection skill. ' +
    'Execute exactly one bounded operation. Operation ' + op.id + ': ' + op.description + '. Files in scope: ' + op.files.join(', ') + '. Effect class: ' + op.effect_class + '. ' +
    'Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class, and rollback or refusal boundary. ' +
    'Contract and defeating fixtures come before code; make the smallest change; run python scripts/verify.py from ' + ROOT + ' and record its exit code. ' +
    'Hard limits: never run git commit or git push; no lane runtime code before executable positive and defeating fixtures and before the Asset Service core.py split gives the stream a stable owner; never open the Asset Service database directly; never generate embeddings in the service (invoke_model or declared provenance only; O12 gates model_binding.ratify_contract); never serve approximate as exact or skip a staleness omission; no new runtime dependency without an observed need and a decision record; never witness or ratify your own work; queue judgement-typed questions for Bdo naming the transition each gates; never touch lineage/evidence/. ' +
    'Report files changed, checks observed with commands and exit codes, standing proposals (at most BUILT), defaults taken, judgement items, and the next bounded operation. If the operation cannot proceed within these limits, return a reasoned refusal instead of forcing work.'
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
log('Scope: planning bounded projection-domain work for objective: ' + objective)
const plan = await agent(
  'You are scoping bounded work in the Soveraeign projection domain. Read ' + ROOT + '/AGENTS.md, ' + ROOT + '/STATUS.yaml, ' + ROOT + '/CLASSIFICATION.md, the SPEC.md Projection rule and transition contract, everything under ' + ROOT + '/services/projection/ (CHARTER.md, PARITY.md, README.md, contracts/, conformance/), and ' + ROOT + '/decisions/0021-asset-projection-service-boundary.md. ' +
  'Current standing: projection_service_status is CHARTERED_NOT_IMPLEMENTED. Gates: O21 gates projection.ratify_boundary only (the parity target and lane scope are defaults taken in decisions/0021 and gate nothing); O12 gates model_binding.ratify_contract, which the dense and sparse lanes wait on for embeddings; O2 gates engineering.ratify_baseline; O10 gates spec.ratify. Precursors, not owner gates: executable positive and defeating fixtures, and the Asset Service core.py split that gives the read stream a stable owner - if the split is not planned anywhere, that is an unblock request for the asset domain (python scripts/sov_unblock.py draft), not a reason to stall this one. ' +
  'Plan only fixture executable-ization under services/projection/conformance/, parity-ledger upkeep in PARITY.md, charter gap closure, read-path precondition mapping, contract drafting under services/projection/contracts/, doc coherence, or - only when fixtures are executable and the core.py split has landed - lane implementation in PARITY.md order (text, graph, filters, fusion, context packages; stdlib only; per-hit source resolution and declared omissions are non-negotiable). Blocked edge is not blocked frontier (AGENTS.md, Self-direction is not delegation): an unresolved owner decision gates only the transition that needs it. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. Each judgement_queue entry names the transition it gates. ' +
  'Judgement-typed questions are queued, never decided by an agent. Effect classes are limited to RECORD_LOCAL and RESOURCE_CONSUMPTION; no EXTERNAL_WORLD effects in Phase I. Evidence files under lineage/evidence/ are immutable. ' +
  'Produce a bounded operation plan honoring these gates for: ' + objective,
  { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' }
)

if (!plan || plan.blocked || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning judgement queue without forcing work')
  return {
    domain: 'projection',
    objective: objective,
    blocked: true,
    planned: plan ? plan.operations : [],
    built: [],
    witness: null,
    residuals: (plan && plan.blocked_reason) ? [plan.blocked_reason] : [],
    judgement_queue: plan ? plan.judgement_queue : ['scope agent failed; re-run sov-projection Scope'],
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
  'Independently inspect the working-tree diffs for those files (git status, git diff), check them against AGENTS.md, STATUS.yaml, CLASSIFICATION.md, the SPEC.md Projection rule, and services/projection/CHARTER.md and PARITY.md, and run python scripts/verify.py from ' + ROOT + ', recording its exit code. Watch specifically for: a hit or projected value that does not resolve to a source address and digest, an undeclared omission, approximate served as exact, embeddings generated in-service, a direct Asset Service database read, or runtime code ahead of its fixtures. ' +
  'For each claimed operation return a verdict: reproduced, dissented, or unattestable. List residual failures. State the highest standing transition your own observation supports: OPEN->BUILT, BUILT->WITNESSED, or none. Never propose RATIFIED; only Bdo ratifies judgement-typed claims.',
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
  domain: 'projection',
  objective: objective,
  blocked: false,
  planned: plan.operations,
  built: built,
  witness: witness,
  residuals: witness ? witness.residuals : ['witness agent failed; run is unattestable'],
  judgement_queue: plan.judgement_queue,
  standing_proposal: standingProposal
}
