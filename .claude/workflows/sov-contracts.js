export const meta = { name: 'sov-contracts', description: 'Advance the Soveraeign contracts domain (shared kernel and crossing JSON Schema contracts) one bounded operation with independent witnessing', whenToUse: 'When the six kernel schemas in contracts/ need a schema-spec gap audit, conformance fixtures, a vocabulary audit, or README coherence work', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

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
          effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] }
        }
      }
    },
    judgement_queue: { type: 'array', items: { type: 'string' } }
  }
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
          verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] }
        }
      }
    },
    residuals: { type: 'array', items: { type: 'string' } },
    standing_supported: { type: 'string', enum: ['none', 'OPEN->BUILT', 'BUILT->WITNESSED'] }
  }
}

const objective = (args && args.objective) ? args.objective : 'advance the contracts domain one bounded operation: close a schema-spec gap, author conformance fixtures, or restore doc coherence'

phase('Scope')
log('Scope: planning bounded contracts-domain work')
const scopePrompt = 'Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml fully, then ' + ROOT + '/contracts/README.md, the six schema files in ' + ROOT + '/contracts/, the logical object blocks in ' + ROOT + '/SPEC.md, and the vocabulary tables in ' + ROOT + '/CLASSIFICATION.md. Produce a bounded operation plan for: ' + objective + '. The founding docket is closed: open_decisions is empty and the O<n> identifiers are retired (decisions/0033-close-the-founding-docket.md). Settle a decision at the lowest tier that can produce evidence defeating the alternatives, and record what would defeat the ruling. Only PUBLIC-CLEARANCE and owner-held product intent, public naming, external commitment, irreversible external effect, secrets, and destructive repository administration reach Bdo, and his gate is acceptance over an evidenced result, never permission to begin. SPEC.md and CLASSIFICATION.md are accepted, so a schema that disagrees with either is a defect in the schema. Every schema change carries a positive and a defeating conformance case; that is the constraint, not owner permission. Every operation declares effect_class RECORD_LOCAL or RESOURCE_CONSUMPTION; EXTERNAL_WORLD is refused in Phase I. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. Each ruling you take names the observation that would defeat it.'
const plan = await agent(scopePrompt, { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' })

if (!plan || plan.blocked || !plan.operations || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning judgement queue without forcing work')
  return { domain: 'contracts', objective: objective, blocked: true, planned: (plan && plan.operations) ? plan.operations : [], built: [], witness: null, residuals: [], judgement_queue: (plan && plan.judgement_queue) ? plan.judgement_queue : ['scope agent failed to return a plan'], standing_proposal: null }
}

phase('Build')
log('Build: executing ' + plan.operations.length + ' planned operation(s)')
const buildOne = function (op) {
  const prompt = 'Execute exactly this bounded Soveraeign contracts-domain operation and nothing else. id: ' + op.id + '. description: ' + op.description + '. files: ' + op.files.join(', ') + '. effect class: ' + op.effect_class + '. Repository root: ' + ROOT + '. Before editing, record the AGENTS.md change protocol: requested outcome and current authoritative state; affected contracts and fixtures; preconditions and expected observable result; effect class; rollback or refusal boundary. Contract and fixtures come before code; make the smallest change that satisfies the visible case; then run python scripts/verify.py from the repository root and report its exit code. NEVER run git commit or git push. If the operation turns out to require an owner-held boundary (public naming, external commitment, irreversible external effect, secrets, destructive repository administration), stop and return it; settle anything else at this tier and record what would defeat it. Return a short report: files changed, commands run with exit codes, residuals.'
  return agent(prompt, { agentType: 'sov-worker', phase: 'Build', label: 'build-' + op.id })
}
const seen = {}
let overlap = false
for (const op of plan.operations) {
  for (const f of op.files) {
    if (seen[f]) { overlap = true }
    seen[f] = true
  }
}
let buildResults = []
if (overlap || plan.operations.length === 1) {
  for (const op of plan.operations) { buildResults.push(await buildOne(op)) }
} else {
  buildResults = await parallel(plan.operations.map(function (op) { return function () { return buildOne(op) } }))
}
const built = buildResults.filter(function (r) { return r !== null && r !== undefined })

phase('Witness')
log('Witness: independent inspection of claimed operations')
const claims = plan.operations.map(function (op) { return op.id + ': ' + op.description + ' [files: ' + op.files.join(', ') + ']' }).join('\n')
const changed = Object.keys(seen).join(', ')
const witnessPrompt = 'You are an independent witness for the Soveraeign contracts domain. You did not build this work; a build report cannot witness itself, so trust no builder claim without inspection. Repository root: ' + ROOT + '. Claimed operations:\n' + claims + '\nClaimed changed files: ' + changed + '. Independently inspect the working-tree diffs for those files (git status, git diff -- <file>), verify each claim against the actual file contents and against SPEC.md and CLASSIFICATION.md, and run python scripts/verify.py from the repository root, recording its exit code. Never treat a green build alone as authority. For each operation return a verdict: reproduced, dissented, or unattestable. List residuals. standing_supported may be OPEN->BUILT or BUILT->WITNESSED only, never RATIFIED: ratification of judgement-typed claims belongs to Bdo alone. Do not run git commit or git push.'
const witness = await agent(witnessPrompt, { agentType: 'sov-witness', phase: 'Witness', schema: WITNESS_SCHEMA, label: 'witness' })
if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }

let standing = null
if (witness && (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED')) { standing = witness.standing_supported }
const residuals = (witness && witness.residuals) ? witness.residuals : ['witness agent returned no result; work remains unwitnessed']
log('Done: witness standing proposal ' + standing)

return { domain: 'contracts', objective: objective, blocked: false, planned: plan.operations, built: built, witness: witness, residuals: residuals, judgement_queue: plan.judgement_queue, standing_proposal: standing }
