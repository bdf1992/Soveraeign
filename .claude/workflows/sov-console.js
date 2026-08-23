export const meta = { name: 'sov-console', description: 'Advance the Soveraeign Console Service domain by bounded charter, contract, or seed-fixture operations with independent witnessing', whenToUse: 'When services/console needs charter gap closure, schema refinement, seed fixtures, doc coherence, sibling read-path preconditions, or a declared Human Binding interface while O18 keeps implementation queued', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

const ROOT = '.'

const PLAN_SCHEMA = { type: 'object', required: ['blocked', 'operations', 'judgement_queue'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] } } } }, judgement_queue: { type: 'array', items: { type: 'string' } } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string', enum: ['OPEN->BUILT', 'BUILT->WITNESSED', 'none'] } } }

const objective = (args && args.objective) ? args.objective : 'advance the console domain one bounded charter, contract, or seed-fixture operation'

function buildPrompt(op) {
  return 'You are the console domain builder for Soveraeign at ' + ROOT + '. Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml first. ' +
    'Execute exactly one bounded operation. Operation ' + op.id + ': ' + op.description + '. Files in scope: ' + op.files.join(', ') + '. Effect class: ' + op.effect_class + '. ' +
    'Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class, and rollback or refusal boundary. ' +
    'Contract and defeating fixtures come before code; make the smallest change; run python scripts/verify.py from ' + ROOT + ' and record its exit code. ' +
    'Hard limits: never run git commit or git push; never write console runtime code or a binding implementation while O18 and O10 are open; never witness or ratify your own work; queue judgement-typed questions for Bdo instead of deciding them; never touch Asset Service or Proofing Service state or lineage/evidence/. ' +
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
  'Current standing: console_service_status is CHARTERED_NOT_IMPLEMENTED. Blockers: O18 blocks console_implementation, O2 blocks production_implementation, O10 blocks f1_closure. No binding implementation is admitted until the shared transition contract is frozen or Bdo authorizes a provisional target. ' +
  'Plan only charter gap closure, schema refinement against SPEC.md, seed-fixture authoring under services/console/conformance/, doc coherence, sibling read-path precondition mapping, or a declared (never implemented) Human Binding interface under bindings/. Any runtime, participant, or binding implementation work must be refused: leave it out of operations and add it to judgement_queue as a question for Bdo. If the objective itself requires implementation, set blocked true with a blocked_reason. ' +
  'Judgement-typed questions are queued, never decided by an agent. Effect classes are limited to RECORD_LOCAL and RESOURCE_CONSUMPTION; no EXTERNAL_WORLD effects in Phase I. Evidence files under lineage/evidence/ are immutable. ' +
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
