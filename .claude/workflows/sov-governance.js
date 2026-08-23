export const meta = {
  name: 'sov-governance',
  description: 'Advance Soveraeign design System of Record governance one bounded, witnessed operation: document-set coherence, decision drafting, STATUS.yaml standing fields, and the open-decision judgement queue',
  whenToUse: 'When the governing document set, decisions/ records, STATUS.yaml standing, or the O1-O12 judgement queue needs bounded, witnessed governance work',
  phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }],
}

// Leaf domain workflow: it never nests child workflows; only the federation root may nest.

const ROOT = '.'
const GOVERNING_SET = 'AGENTS.md, STATUS.yaml, SYSTEM.md, CONTRACT.md, CLASSIFICATION.md, PRD.md, SPEC.md, OPEN-SEAMS.md, NAMING.md, PUBLICATION.md, ROADMAP.md, and every record in decisions/'

const PLAN_SCHEMA = { type: 'object', required: ['blocked', 'operations', 'judgement_queue'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] } } } }, judgement_queue: { type: 'array', items: { type: 'string' } } } }

const BUILD_SCHEMA = { type: 'object', required: ['operation_id', 'files_changed', 'summary'], properties: { operation_id: { type: 'string' }, files_changed: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' }, verify_exit_code: { type: 'integer' }, judgement_items: { type: 'array', items: { type: 'string' } } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string' } } }

const objective = (args && args.objective) ? args.objective : 'advance design System of Record governance one bounded operation'

phase('Scope')
log('Scope: planning bounded governance work for: ' + objective)

const plan = await agent(
  'You are the sov-governance planner for Soveraeign at ' + ROOT + '. Read ' + GOVERNING_SET + '. ' +
  'Produce a bounded operation plan for: ' + objective + '. ' +
  'Honor the blockers in STATUS.yaml: O1 blocks public_release, O9 blocks terminology_freeze, O10 blocks f1_closure; every ratification is Bdo-only and must appear in judgement_queue as a question, never be decided. ' +
  'Plan only RECORD_LOCAL or RESOURCE_CONSUMPTION operations; Phase I forbids EXTERNAL_WORLD effects. ' +
  'Do not plan work a blocker gates. If nothing legitimate remains, set blocked true with blocked_reason. ' +
  'Each operation is smallest-change, names exact repo-relative files, and never touches lineage/evidence/.',
  { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' }
)

if (!plan || plan.blocked || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning judgement queue without forcing work')
  return {
    domain: 'governance',
    objective: objective,
    blocked: true,
    planned: plan ? plan.operations : [],
    built: [],
    witness: null,
    residuals: plan && plan.blocked_reason ? [plan.blocked_reason] : [],
    judgement_queue: plan ? plan.judgement_queue : ['scope agent failed to return a plan'],
    standing_proposal: null,
  }
}

phase('Build')
log('Build: executing ' + plan.operations.length + ' planned operation(s)')

function overlaps(a, b) {
  for (let i = 0; i < a.files.length; i++) {
    if (b.files.indexOf(a.files[i]) !== -1) { return true }
  }
  return false
}

function independent(ops) {
  for (let i = 0; i < ops.length; i++) {
    for (let j = i + 1; j < ops.length; j++) {
      if (overlaps(ops[i], ops[j])) { return false }
    }
  }
  return true
}

function buildPrompt(op) {
  return 'You are the sov-governance builder for Soveraeign at ' + ROOT + '. Read AGENTS.md and STATUS.yaml before changing anything. ' +
    'Execute exactly one bounded operation: ' + op.id + ' - ' + op.description + '. Touch only these files: ' + op.files.join(', ') + '. ' +
    'Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class (' + op.effect_class + '), and rollback or refusal boundary. ' +
    'Hard rules: never run git commit or git push; never ratify or witness your own work; queue judgement-typed questions for Bdo in judgement_items instead of deciding them; do not duplicate a rule owned by another document - link to it; lineage/evidence/ is immutable; vocabulary must match CLASSIFICATION.md and SPEC.md. ' +
    'Make the smallest change, then run python scripts/verify.py from the repository root and report its exit code.'
}

let built = []
if (independent(plan.operations)) {
  const results = await parallel(plan.operations.map(function (op) {
    return function () {
      return agent(buildPrompt(op), { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 'build-' + op.id })
    }
  }))
  built = results.filter(function (r) { return r !== null && r !== undefined })
} else {
  for (const op of plan.operations) {
    const r = await agent(buildPrompt(op), { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 'build-' + op.id })
    if (r) { built.push(r) }
  }
}

phase('Witness')
log('Witness: independently inspecting ' + built.length + ' claimed operation(s)')

const claims = built.map(function (r) {
  return { operation_id: r.operation_id, files_changed: r.files_changed }
})

const witness = await agent(
  'You are an independent Soveraeign witness at ' + ROOT + '. You receive only claimed operation ids and changed files - never builder reasoning - because a build report cannot witness itself. ' +
  'Claims: ' + JSON.stringify(claims) + '. ' +
  'Independently inspect the diffs of the changed files (git status and git diff), compare them against AGENTS.md, CONTRACT.md, CLASSIFICATION.md, and SPEC.md, and run python scripts/verify.py from the repository root, recording the exit code. ' +
  'Never treat a green build or an executor report as authority. Return one verdict per operation_id: reproduced, dissented, or unattestable. ' +
  'standing_supported must be exactly "OPEN -> BUILT", "BUILT -> WITNESSED", or "none"; never RATIFIED - only Bdo ratifies.',
  { agentType: 'sov-witness', schema: WITNESS_SCHEMA, phase: 'Witness', label: 'witness' }
)
if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }

let standingProposal = null
if (witness && (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED')) {
  standingProposal = witness.standing_supported
}

const judgementQueue = plan.judgement_queue.slice()
built.forEach(function (r) {
  if (Array.isArray(r.judgement_items)) {
    r.judgement_items.forEach(function (q) { judgementQueue.push(q) })
  }
})

const residuals = witness && Array.isArray(witness.residuals) ? witness.residuals : ['witness returned no residual list']

log('Done: ' + built.length + ' built, ' + (witness && witness.verdicts ? witness.verdicts.length : 0) + ' verdict(s), standing proposal: ' + (standingProposal || 'none') + ', ' + judgementQueue.length + ' judgement item(s) for Bdo')

return {
  domain: 'governance',
  objective: objective,
  blocked: false,
  planned: plan.operations,
  built: built,
  witness: witness || null,
  residuals: residuals,
  judgement_queue: judgementQueue,
  standing_proposal: standingProposal,
}
