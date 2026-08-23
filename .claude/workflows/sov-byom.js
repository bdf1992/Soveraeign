export const meta = { name: 'sov-byom', description: 'Advance the Soveraeign byom domain (model bindings, adapters, PROD-I-9 portability) one bounded, witnessed, proposal-marked operation', whenToUse: 'When BYOM.md, bindings/, adapters/, contracts/model-binding.schema.json, or the PROD-I-9 fixtures need bounded work', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

const ROOT = '.'

const PLAN_SCHEMA = {
  type: 'object',
  required: ['blocked', 'operations', 'judgement_queue'],
  properties: {
    blocked: { type: 'boolean' },
    blocked_reason: { type: 'string' },
    operations: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'description', 'files', 'effect_class'],
        properties: {
          id: { type: 'string' },
          description: { type: 'string' },
          files: { type: 'array', items: { type: 'string' } },
          effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] },
        },
      },
    },
    judgement_queue: { type: 'array', items: { type: 'string' } },
  },
}

const BUILD_SCHEMA = {
  type: 'object',
  required: ['operation_id', 'files_changed', 'checks_observed', 'summary'],
  properties: {
    operation_id: { type: 'string' },
    files_changed: { type: 'array', items: { type: 'string' } },
    checks_observed: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    judgement_items: { type: 'array', items: { type: 'string' } },
  },
}

const WITNESS_SCHEMA = {
  type: 'object',
  required: ['verdicts', 'residuals', 'standing_supported'],
  properties: {
    verdicts: {
      type: 'array',
      items: {
        type: 'object',
        required: ['operation_id', 'verdict'],
        properties: {
          operation_id: { type: 'string' },
          verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] },
        },
      },
    },
    residuals: { type: 'array', items: { type: 'string' } },
    standing_supported: { type: 'string' },
  },
}

const objective = (args && args.objective) ? args.objective : 'advance the byom domain one bounded operation that produces inspectable evidence'

phase('Scope')
log('Scope: planning bounded byom work for objective: ' + objective)

const scopePrompt = 'You are scoping the Soveraeign byom domain (bring-your-own-model bindings and adapters). ' +
  'Read ' + ROOT + '/AGENTS.md, ' + ROOT + '/STATUS.yaml, ' + ROOT + '/BYOM.md, ' + ROOT + '/bindings/README.md, ' + ROOT + '/adapters/README.md, ' + ROOT + '/contracts/model-binding.schema.json, ' + ROOT + '/decisions/0011-local-personal-byom.md, and the PROD-I-9 section of ' + ROOT + '/PRD.md. ' +
  'The founding docket is closed: open_decisions is empty and the O<n> identifiers are retired (decisions/0033-close-the-founding-docket.md). Settle a decision at the lowest tier that can produce evidence defeating the alternatives, and record what would defeat the ruling. Only PUBLIC-CLEARANCE and owner-held product intent, public naming, external commitment, irreversible external effect, secrets, and destructive repository administration reach Bdo, and his gate is acceptance over an evidenced result, never permission to begin. The exact binding fields, the three data-boundary modes, and the two-model shape are accepted (decisions/0024-open-decision-drain.md, O12); what a binding still owes is independent observation, which its builder cannot supply. ' +
  'Produce a bounded plan of mutually independent operations for this objective: ' + objective + '. ' +
  'Allowed effect classes: RECORD_LOCAL and RESOURCE_CONSUMPTION only. No runtime code before logical spec and defeating fixtures. No provider SDK types in kernel or service contracts. No silent provider fallback. Model selection never changes authority. ' +
  'Do not decide judgement-typed questions; put each in judgement_queue. Blocked edge is not blocked frontier (AGENTS.md, Self-direction is not delegation): an unresolved owner decision gates only the transition that needs it. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. Each judgement_queue entry is an owner-held boundary only, and names why no evidence at this tier could settle it.'

const plan = await agent(scopePrompt, { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' })

if (!plan || plan.blocked || !plan.operations || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning judgement queue without forcing work')
  return {
    domain: 'byom',
    objective: objective,
    blocked: true,
    planned: plan && plan.operations ? plan.operations : [],
    built: [],
    witness: null,
    residuals: plan && plan.blocked_reason ? [plan.blocked_reason] : [],
    judgement_queue: plan && plan.judgement_queue ? plan.judgement_queue : ['byom scope agent returned no plan'],
    standing_proposal: null,
  }
}

phase('Build')
log('Build: running ' + plan.operations.length + ' bounded byom operation(s)')

const buildOne = function (op) {
  const prompt = 'You are the sov-byom builder executing exactly one bounded operation. ' +
    'Operation ' + op.id + ': ' + op.description + '. Files in scope: ' + op.files.join(', ') + '. Effect class: ' + op.effect_class + '. ' +
    'Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml first. Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class, and rollback or refusal boundary. ' +
    'Contract and fixtures before code; smallest change that satisfies the visible case; a passing self-test establishes BUILT and never WITNESSED. ' +
    'Run python scripts/verify.py from the repository root and record the exact command and exit code. ' +
    'You must NOT run git commit or git push. You must not witness or ratify your own work. Settle what evidence can settle at your tier and name the observation that would defeat each ruling. Put only an owner-held boundary in judgement_items. An owner-held boundary is public naming, external commitment, irreversible external-world effect, secrets, or destructive repository administration.'
  return agent(prompt, { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 'build-' + op.id })
}

const seenFiles = {}
let overlap = false
plan.operations.forEach(function (op) {
  const files = op.files || []
  files.forEach(function (f) {
    if (seenFiles[f]) { overlap = true }
    seenFiles[f] = true
  })
})

let buildResults = []
if (overlap || plan.operations.length === 1) {
  for (const op of plan.operations) { buildResults.push(await buildOne(op)) }
} else {
  buildResults = await parallel(plan.operations.map(function (op) { return function () { return buildOne(op) } }))
}

const built = buildResults.filter(function (r) { return r !== null && r !== undefined })
const residuals = []
plan.operations.forEach(function (op, i) { if (!buildResults[i]) { residuals.push('operation ' + op.id + ': builder returned no report') } })

phase('Witness')
const claimed = built.map(function (r) { return { operation_id: r.operation_id, files_changed: r.files_changed } })
log('Witness: independently inspecting ' + claimed.length + ' claimed operation(s)')

let witness = null
if (claimed.length > 0) {
  const witnessPrompt = 'Independently witness these claimed Soveraeign byom operations. ' +
    'Claims (operation ids and changed files only; builder reasoning is deliberately withheld because a build report cannot witness itself): ' + JSON.stringify(claimed) + '. ' +
    'Inspect the actual diffs of the listed files under ' + ROOT + ' against AGENTS.md, BYOM.md, the SPEC.md ModelBinding object, CLASSIFICATION.md vocabulary, and contracts/model-binding.schema.json. ' +
    'Run python scripts/verify.py from the repository root and record the exact command and exit code. ' +
    'Never treat a green build or a builder self-report as authority. Return one verdict per operation_id: reproduced, dissented, or unattestable. ' +
    'standing_supported may be OPEN->BUILT or BUILT->WITNESSED only, or an empty string; never RATIFIED - only Bdo ratifies.'
  witness = await agent(witnessPrompt, { agentType: 'sov-witness', phase: 'Witness', schema: WITNESS_SCHEMA, label: 'witness' })
  if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }
}

if (claimed.length > 0 && !witness) { residuals.push('witness agent returned no observation; build claims remain unwitnessed') }
if (witness && Array.isArray(witness.residuals)) { witness.residuals.forEach(function (x) { residuals.push(x) }) }

const judgementQueue = []
if (Array.isArray(plan.judgement_queue)) { plan.judgement_queue.forEach(function (q) { judgementQueue.push(q) }) }
built.forEach(function (r) {
  if (Array.isArray(r.judgement_items)) { r.judgement_items.forEach(function (q) { judgementQueue.push(q) }) }
})

let standingProposal = null
if (witness && (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED')) {
  standingProposal = witness.standing_supported
}

log('Done: ' + built.length + ' built, ' + residuals.length + ' residual(s), ' + judgementQueue.length + ' judgement item(s) queued for Bdo')

return {
  domain: 'byom',
  objective: objective,
  blocked: false,
  planned: plan.operations,
  built: built,
  witness: witness,
  residuals: residuals,
  judgement_queue: judgementQueue,
  standing_proposal: standingProposal,
}
