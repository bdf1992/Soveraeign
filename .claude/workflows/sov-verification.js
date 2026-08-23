export const meta = { name: 'sov-verification', description: 'Advance the Soveraeign verification harness and engineering baseline one bounded operation with independent witnessing', whenToUse: 'When scripts/verify.py, scripts/lint.py, scripts/verify_bootstrap.py, the CI gate .github/workflows/verify.yml, or ENGINEERING.md baseline stewardship needs bounded, witnessed work', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

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

const objective = (args && args.objective) ? args.objective : 'advance the verification harness and engineering baseline one bounded operation'

phase('Scope')
log('Scope: planning verification-domain work for: ' + objective)
const plan = await agent(
  'You are scoping work for the Soveraeign verification domain. Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml fully, then ' + ROOT + '/ENGINEERING.md, ' + ROOT + '/scripts/verify.py, ' + ROOT + '/scripts/lint.py, ' + ROOT + '/scripts/verify_bootstrap.py, and ' + ROOT + '/.github/workflows/verify.yml. ' +
  'Produce a bounded operation plan for: ' + objective + '. ' +
  'The founding docket is closed: open_decisions is empty and the O<n> identifiers are retired (decisions/0033-close-the-founding-docket.md). Settle a decision at the lowest tier that can produce evidence defeating the alternatives, and record what would defeat the ruling. Only PUBLIC-CLEARANCE and owner-held product intent, public naming, external commitment, irreversible external effect, secrets, and destructive repository administration reach Bdo, and his gate is acceptance over an evidenced result, never permission to begin. The ENGINEERING.md baseline is accepted (decisions/0024-open-decision-drain.md, O2): Python 3.11+, SQLite, filesystem content-addressed custody, JSON Schema Draft 2020-12, dependency-light unittest, local-process and CLI first. They are mechanisms, not semantic authority. Every check must declare how it avoids relying on the thing it checks; if that relation string is false the check is worse than absent. ' +
  'Every operation must declare effect class RECORD_LOCAL or RESOURCE_CONSUMPTION (EXTERNAL_WORLD is refused in Phase I), keep scripts/ dependency-free, never weaken a gate or marker, and respect the three-second budget of python scripts/verify.py. ' +
  'Settle what evidence can settle at this tier and put only an owner-held boundary in judgement_queue. An owner-held boundary is public naming, external commitment, irreversible external-world effect, secrets, or destructive repository administration. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. Each judgement_queue entry is an owner-held boundary only, and names why no evidence at this tier could settle it. ' +
  'Return {blocked, blocked_reason, operations: [{id, description, files, effect_class}], judgement_queue}.',
  { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' }
)
if (!plan || plan.blocked || plan.operations.length === 0) {
  log('Scope: blocked or empty plan - returning judgement queue without forcing work')
  return {
    domain: 'verification',
    objective: objective,
    blocked: true,
    planned: plan ? plan.operations : [],
    built: [],
    witness: null,
    residuals: [],
    judgement_queue: plan ? plan.judgement_queue : ['scope agent failed to return a plan'],
    standing_proposal: null
  }
}

phase('Build')
log('Build: executing ' + plan.operations.length + ' planned operation(s)')
const buildThunks = plan.operations.map(function (op) {
  return function () {
    return agent(
      'Execute exactly one bounded operation in the Soveraeign verification domain. ' +
      'Operation ' + op.id + ': ' + op.description + '. Files in scope: ' + op.files.join(', ') + '. Effect class: ' + op.effect_class + '. ' +
      'First read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml. Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class, and rollback or refusal boundary. ' +
      'Contract and defeating fixture before code; make the smallest change; then run python scripts/verify.py from ' + ROOT + ' and record the exact exit code and timing against the three-second budget. ' +
      'Never weaken a gate to pass, never add runtime dependencies, never put product business logic in scripts/. ' +
      'You must NOT run git commit or git push; leave changes in the working tree. You emit a build report only - you cannot witness or ratify your own work. Settle what evidence can settle at your tier and name what would defeat each ruling; put only an owner-held boundary in the queue. ' +
      'Return {operation_id, files_changed, checks_observed, judgement_items}.',
      { agentType: 'sov-worker', phase: 'Build', label: 'build-' + op.id }
    )
  }
})
const buildResults = await parallel(buildThunks)
const built = buildResults.filter(function (result) { return result !== null && result !== undefined })

phase('Witness')
log('Witness: independently verifying ' + built.length + ' build claim(s)')
const claims = plan.operations.map(function (op) {
  return { operation_id: op.id, description: op.description, files: op.files }
})
const witness = await agent(
  'You are the independent witness for Soveraeign verification-domain work. You receive ONLY the claimed operations and changed files below; no builder reasoning is provided, because a build report cannot witness itself. ' +
  'Claims: ' + JSON.stringify(claims) + '. ' +
  'Independently inspect the working-tree diffs of those files at ' + ROOT + ' (git diff plus direct reads), compare against AGENTS.md, ENGINEERING.md, and CLASSIFICATION.md/SPEC.md vocabulary, then run python scripts/verify.py from ' + ROOT + ' and record the exact command, exit code, and timing against the three-second budget. ' +
  'Never treat a green build, confidence, or any report as authority; re-derive every claim from the artifact and the record. Dissent is a valid outcome. ' +
  'Return {verdicts: [{operation_id, verdict}], residuals, standing_supported} where verdict is reproduced, dissented, or unattestable, and standing_supported is none, OPEN->BUILT, or BUILT->WITNESSED. You can never support RATIFIED - only Bdo ratifies.',
  { agentType: 'sov-witness', phase: 'Witness', schema: WITNESS_SCHEMA, label: 'witness' }
)
if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }

let standingProposal = null
if (witness && (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED')) {
  standingProposal = witness.standing_supported
}
log('Witness: complete - standing proposal: ' + (standingProposal ? standingProposal : 'none'))

return {
  domain: 'verification',
  objective: objective,
  blocked: false,
  planned: plan.operations,
  built: built,
  witness: witness,
  residuals: (witness && witness.residuals) ? witness.residuals : ['witness agent returned no observation'],
  judgement_queue: plan.judgement_queue,
  standing_proposal: standingProposal
}
