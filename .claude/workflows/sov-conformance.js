export const meta = { name: 'sov-conformance', description: 'Advance the Soveraeign conformance domain (oracle, controls, scenarios, fresh-witness qualification) one bounded operation with independent witnessing', whenToUse: 'When conformance/ needs bounded, witnessed work: fixture gap closure, control pair authoring, oracle self-test hardening, scenario coherence, or participant-binding interface sharpening under the open F2 blockers', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

// Leaf domain workflow: never calls another workflow. args: { objective?: string }

const ROOT = '.'

const PLAN_SCHEMA = { type: 'object', required: ['blocked', 'operations', 'judgement_queue'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] } } } }, judgement_queue: { type: 'array', items: { type: 'string' } } } }

const BUILD_SCHEMA = { type: 'object', required: ['operation_id', 'status', 'files_changed'], properties: { operation_id: { type: 'string' }, status: { type: 'string', enum: ['done', 'partial', 'refused'] }, files_changed: { type: 'array', items: { type: 'string' } }, refusal_reason: { type: 'string' } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string' } } }

const objective = (args && args.objective) ? args.objective : 'close one positive-or-defeating fixture gap or harden one oracle self-test in conformance/ without weakening any check'

phase('Scope')
log('Scope: planning bounded conformance work for: ' + objective)

const plan = await agent(
  'You are the conformance domain planner for Soveraeign. Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml fully, then ' + ROOT + '/conformance/README.md, ' + ROOT + '/conformance/run.py, ' + ROOT + '/conformance/oracle-controls.json, ' + ROOT + '/conformance/scenarios.json, the SPEC.md sections Requirement predicates and Conformance boundary, PRD.md PROD-I-7 and Two-binding proof, and ROADMAP.md F2. ' +
  'Produce a bounded operation plan for: ' + objective + '. ' +
  'The founding docket is closed: open_decisions is empty and the O<n> identifiers are retired (decisions/0033-close-the-founding-docket.md). Settle a decision at the lowest tier that can produce evidence defeating the alternatives, and record what would defeat the ruling. Only PUBLIC-CLEARANCE and owner-held product intent, public naming, external commitment, irreversible external effect, secrets, and destructive repository administration reach Bdo, and his gate is acceptance over an evidenced result, never permission to begin. conformance_status is EXECUTABLE_ORACLE_CONTROLS_PARTICIPANT_BINDING_OPEN: no participant has bound. SPEC.md, the semantic cold-start observation shape, and the BYOM binding fields are all accepted, so a fixture that contradicts one is a defect in the fixture. F2 exit needs one positive and one defeating fixture per normative predicate, bindable to more than one implementation. ' +
  'Every operation must stay inside conformance/, never import participant implementation code, never weaken an oracle check, and use effect class RECORD_LOCAL or RESOURCE_CONSUMPTION only (no EXTERNAL_WORLD in Phase I). ' +
  'Settle what evidence can settle at this tier and put only an owner-held boundary in judgement_queue. An owner-held boundary is public naming, external commitment, irreversible external-world effect, secrets, or destructive repository administration. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. Each judgement_queue entry is an owner-held boundary only, and names why no evidence at this tier could settle it.',
  { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' }
)

if (!plan || plan.blocked || !plan.operations || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning judgement queue without forcing work')
  return { domain: 'conformance', objective: objective, blocked: true, planned: (plan && plan.operations) ? plan.operations : [], built: [], witness: null, residuals: [], judgement_queue: plan ? plan.judgement_queue : ['scope agent returned no plan for: ' + objective], standing_proposal: null }
}

phase('Build')
log('Build: executing ' + plan.operations.length + ' planned operation(s)')

function buildPrompt(op) {
  return 'You are a Soveraeign conformance domain builder. Read ' + ROOT + '/AGENTS.md and ' + ROOT + '/STATUS.yaml before editing anything. ' +
    'Execute exactly this one bounded operation and nothing else. Operation id: ' + op.id + '. Description: ' + op.description + '. Files in scope: ' + op.files.join(', ') + '. Effect class: ' + op.effect_class + '. ' +
    'Follow the AGENTS.md change protocol: record requested outcome and current authoritative state, affected contracts and fixtures, preconditions and expected observable result, effect class, and rollback or refusal boundary. ' +
    'Contract and fixtures before code; smallest change that satisfies the visible case. Never import participant implementation code into the oracle, never weaken an oracle check to make a participant pass, never trust a participant self-report. ' +
    'Run python scripts/verify.py from ' + ROOT + ' and record the exit code. You must NOT run git commit or git push; leave changes in the working tree. ' +
    'Refuse with status refused and refusal_reason only when the operation would cross an owner-held boundary; settle anything evidence can settle. Return operation_id, status, and files_changed.'
}

const opsById = {}
const fileSeen = {}
let overlap = false
for (let i = 0; i < plan.operations.length; i++) {
  const op = plan.operations[i]
  opsById[op.id] = op
  for (let j = 0; j < op.files.length; j++) {
    if (fileSeen[op.files[j]]) { overlap = true }
    fileSeen[op.files[j]] = true
  }
}

let buildResults = []
if (plan.operations.length > 1 && !overlap) {
  const settled = await parallel(plan.operations.map(function (op) {
    return function () {
      return agent(buildPrompt(op), { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 'build-' + op.id })
    }
  }))
  buildResults = settled.filter(function (r) { return r !== null && r !== undefined })
} else {
  for (let i = 0; i < plan.operations.length; i++) {
    const result = await agent(buildPrompt(plan.operations[i]), { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 'build-' + plan.operations[i].id })
    if (result) { buildResults.push(result) }
  }
}

log('Build: ' + buildResults.length + ' of ' + plan.operations.length + ' operation(s) returned a report')

phase('Witness')

const claims = buildResults.map(function (r) {
  const op = opsById[r.operation_id]
  return { operation_id: r.operation_id, description: op ? op.description : '', status: r.status, files_changed: r.files_changed }
})

log('Witness: independent verification of ' + claims.length + ' claim(s)')

const witness = await agent(
  'You are the independent Soveraeign witness. A build report cannot witness itself; you receive only the claimed operations and changed files, never the builder reasoning, and you must re-derive every claim from the artifact and the record. ' +
  'Claims: ' + JSON.stringify(claims) + '. ' +
  'In ' + ROOT + ': inspect the actual diffs of the changed files (git status and git diff, read-only), compare them against SPEC.md Requirement predicates, CLASSIFICATION.md vocabulary, and the conformance boundary that the oracle must not import participant implementation code and no check may be weakened. ' +
  'Run python scripts/verify.py from the repository root and python conformance/run.py; record exact commands and exit codes. Never treat a green build or the builder report as authority. ' +
  'Return verdicts (one of reproduced, dissented, unattestable per operation_id), residuals, and standing_supported as one of: OPEN->BUILT, BUILT->WITNESSED, or none. You may never support RATIFIED.',
  { agentType: 'sov-witness', schema: WITNESS_SCHEMA, phase: 'Witness', label: 'witness' }
)
if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }

let standingProposal = null
if (witness && (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED')) {
  standingProposal = witness.standing_supported
}

const residuals = witness && Array.isArray(witness.residuals) ? witness.residuals.slice() : []
if (!witness) { residuals.push('witness agent returned no observation; all build claims remain unwitnessed') }
if (buildResults.length < plan.operations.length) { residuals.push('one or more planned operations returned no build report') }

log('Witness: complete; standing proposal: ' + (standingProposal ? standingProposal : 'none') + '; ' + plan.judgement_queue.length + ' judgement item(s) queued for Bdo')

return { domain: 'conformance', objective: objective, blocked: false, planned: plan.operations, built: buildResults, witness: witness, residuals: residuals, judgement_queue: plan.judgement_queue, standing_proposal: standingProposal }
