export const meta = { name: 'sov-console', description: 'Advance the Soveraeign Console Service domain by bounded charter, contract, or seed-fixture operations with independent witnessing', whenToUse: 'When services/console needs charter gap closure, schema refinement, seed fixtures, doc coherence, sibling read-path preconditions, or a declared Human Binding interface while the service is accepted but unbuilt', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

const ROOT = '.'

const PLAN_SCHEMA = { type: 'object', required: ['blocked', 'operations', 'judgement_queue'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] } } } }, judgement_queue: { type: 'array', items: { type: 'string' } } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string', enum: ['OPEN->BUILT', 'BUILT->WITNESSED', 'none'] } } }

const objective = (args && args.objective) ? args.objective : 'advance the console domain one bounded charter, contract, or seed-fixture operation'

function buildPrompt(op) {
  return 'You are the console domain builder for Soveraeign at ' + ROOT + '. Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml first. ' +
    'Execute exactly one bounded operation. Operation ' + op.id + ': ' + op.description + '. Files in scope: ' + op.files.join(', ') + '. Effect class: ' + op.effect_class + '. ' +
    'Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class, and rollback or refusal boundary. ' +
    'Contract and defeating fixtures come before code; make the smallest change; run python scripts/verify.py from ' + ROOT + ' and record its exit code. ' +
    'Hard limits: never run git commit or git push; never write console runtime code before its defeating fixtures exist; never witness or ratify your own work; never touch Asset Service or Proofing Service state or lineage/evidence/. ' +
    'Report files changed, checks observed with commands and exit codes, standing proposals (at most BUILT), judgement items, and the next bounded operation. If the operation cannot proceed within these limits, return a reasoned refusal instead of forcing work.'
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
log('Scope: planning bounded console-domain work for objective: ' + objective)
const plan = await agent(
  'You are scoping bounded work in the Soveraeign console domain. Read ' + ROOT + '/AGENTS.md, ' + ROOT + '/STATUS.yaml, ' + ROOT + '/CLASSIFICATION.md, the console-relevant sections of ' + ROOT + '/SPEC.md (Interface parity, Projection rule, EventEnvelope, Receipt, AuthorityGrant), everything under ' + ROOT + '/services/console/, ' + ROOT + '/decisions/0014-console-service-boundary.md, and ' + ROOT + '/bindings/README.md. ' +
  'The founding docket is closed: open_decisions is empty and the O<n> identifiers are retired (decisions/0033-close-the-founding-docket.md). Settle a decision at the lowest tier that can produce evidence defeating the alternatives, and record what would defeat the ruling. Only PUBLIC-CLEARANCE and owner-held product intent, public naming, external commitment, irreversible external effect, secrets, and destructive repository administration reach Bdo, and his gate is acceptance over an evidenced result, never permission to begin. Current standing: console_service_status is OWNER_ACCEPTED_BOUNDARY_NOT_IMPLEMENTED. The boundary, the name Console, and the provisional Human Binding target are accepted (decisions/0033-close-the-founding-docket.md). What is missing is the contract and its defeating fixtures, not permission. The ruling is defeated by a Console record producible only through the human interface, which would prove the interface is authority rather than a binding. ' +
  'Plan only charter gap closure, schema refinement against SPEC.md, seed-fixture authoring under services/console/conformance/, doc coherence, sibling read-path precondition mapping, or a declared (never implemented) Human Binding interface under bindings/. Runtime, participant, or binding implementation is gated by the protected boundary no_runtime_code_before_logical_spec_and_defeating_fixtures and by console.authorize_provisional_human_binding, not by a question for Bdo: leave it out of operations and plan the fixtures and precursors that unlock it. Blocked edge is not blocked frontier (AGENTS.md, Self-direction is not delegation): an unresolved owner decision gates only the transition that needs it. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. Each judgement_queue entry is an owner-held boundary only, and names why no evidence at this tier could settle it. ' +
  'Settle what evidence can settle at this tier and name the observation that would defeat each ruling; escalate only an owner-held boundary. Effect classes are limited to RECORD_LOCAL and RESOURCE_CONSUMPTION; no EXTERNAL_WORLD effects in Phase I. Evidence files under lineage/evidence/ are immutable. ' +
  'Produce a bounded operation plan honoring these blockers for: ' + objective,
  { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' }
)

if (!plan || plan.blocked || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning judgement queue without forcing work')
  return {
    domain: 'console',
    objective: objective,
    blocked: true,
    planned: plan ? plan.operations : [],
    built: [],
    witness: null,
    residuals: (plan && plan.blocked_reason) ? [plan.blocked_reason] : [],
    judgement_queue: plan ? plan.judgement_queue : ['scope agent failed; re-run sov-console Scope'],
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
  'Independently inspect the working-tree diffs for those files (git status, git diff), check them against AGENTS.md, STATUS.yaml, CLASSIFICATION.md, and SPEC.md, and run python scripts/verify.py from ' + ROOT + ', recording its exit code. ' +
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
  domain: 'console',
  objective: objective,
  blocked: false,
  planned: plan.operations,
  built: built,
  witness: witness,
  residuals: witness ? witness.residuals : ['witness agent failed; run is unattestable'],
  judgement_queue: plan.judgement_queue,
  standing_proposal: standingProposal
}
