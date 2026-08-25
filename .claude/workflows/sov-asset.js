export const meta = { name: 'sov-asset', description: 'Advance the Soveraeign Asset Service (services/asset) one bounded operation - gap closure, fixtures, module splits, or doc coherence - with independent witnessing', whenToUse: 'When the asset domain needs bounded, witnessed work against its frozen contracts: closing a KNOWN-GAPS.md row, authoring defeating fixtures, splitting core.py, or refreshing the conformance baseline', phases: [{ title: 'Scope' }, { title: 'Build' }, { title: 'Witness' }] }

const ROOT = '.'

const PLAN_SCHEMA = { type: 'object', required: ['blocked', 'operations', 'judgement_queue'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'files', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, files: { type: 'array', items: { type: 'string' } }, effect_class: { type: 'string', enum: ['RECORD_LOCAL', 'RESOURCE_CONSUMPTION'] } } } }, judgement_queue: { type: 'array', items: { type: 'string' } } } }

const BUILD_SCHEMA = { type: 'object', required: ['operation_id', 'files_changed', 'checks'], properties: { operation_id: { type: 'string' }, files_changed: { type: 'array', items: { type: 'string' } }, checks: { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } }, residuals: { type: 'array', items: { type: 'string' } } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string', enum: ['none', 'OPEN->BUILT', 'BUILT->WITNESSED'] } } }

const objective = (args && args.objective) ? args.objective : 'close one observed KNOWN-GAPS.md gap in the Asset Service reference participant, fixtures first, against the frozen conformance oracle'

phase('Scope')
log('Scope: planning bounded asset-domain work for: ' + objective)

const scopePrompt = 'You are the sov-asset scope planner for Soveraeign at ' + ROOT + '. '
  + 'Read ' + ROOT + '/AGENTS.md, ' + ROOT + '/STATUS.yaml, ' + ROOT + '/services/asset/CHARTER.md, '
  + ROOT + '/services/asset/KNOWN-GAPS.md, ' + ROOT + '/services/asset/contracts/service.json, and '
  + ROOT + '/services/asset/conformance/BASELINE.md. Produce a bounded operation plan for: ' + objective + '. '
  + 'The founding docket is closed: open_decisions is empty and the O<n> identifiers are retired (decisions/0033-close-the-founding-docket.md). Settle a decision at the lowest tier that can produce evidence defeating the alternatives, and record what would defeat the ruling. Only PUBLIC-CLEARANCE and owner-held product intent, public naming, external commitment, irreversible external effect, secrets, and destructive repository administration reach Bdo, and his gate is acceptance over an evidenced result, never permission to begin. The engineering baseline, SPEC.md, CLASSIFICATION.md and the BYOM contract are all accepted, so gap closure within existing contracts, '
  + 'positive/defeating fixture authoring, splitting core.py by owned responsibility, conformance observation '
  + 'refresh, and doc coherence all build on accepted ground; a gap fix is never Phase-I qualification, which needs any '
  + 'Phase-I closure claim. Anything gated queues as a judgement item for Bdo - never decide or block on it. '
  + 'Never plan changes to conformance/ scenarios or the oracle, another service, or lineage/evidence/. '
  + 'Effect classes are RECORD_LOCAL or RESOURCE_CONSUMPTION only; EXTERNAL_WORLD is forbidden in Phase I. '
  + 'Each operation names its repo-relative files. '
  + 'Blocked edge is not blocked frontier (AGENTS.md, Self-direction is not delegation): an unresolved owner decision gates only the transition that needs it. Plan the reachable precursors, take reversible defaults for every other choice and name them in the operation descriptions, and set blocked true only when no admissible operation exists for this objective. Each judgement_queue entry is an owner-held boundary only, and names why no evidence at this tier could settle it.'

const plan = await agent(scopePrompt, { agentType: 'sov-orchestrator', schema: PLAN_SCHEMA, phase: 'Scope', label: 'scope' })

if (!plan || plan.blocked || !plan.operations || plan.operations.length === 0) {
  log('Scope: blocked or empty plan; returning judgement queue without forcing work')
  const wasBlocked = !plan || plan.blocked === true
  const scopeResiduals = plan && plan.blocked_reason ? [plan.blocked_reason] : (plan && !plan.blocked ? ['scope returned an empty plan; nothing was attempted'] : [])
  return { domain: 'asset', objective: objective, blocked: wasBlocked, planned: plan && plan.operations ? plan.operations : [], built: [], witness: null, residuals: scopeResiduals, judgement_queue: plan ? plan.judgement_queue : ['scope agent returned no plan; asset scoping itself needs review'], standing_proposal: null }
}

phase('Build')
log('Build: executing ' + plan.operations.length + ' planned operation(s)')

function buildPrompt(op) {
  return 'You are the sov-asset builder for Soveraeign at ' + ROOT + '. Read ' + ROOT + '/AGENTS.md and '
    + ROOT + '/STATUS.yaml first. Execute exactly this one bounded operation and nothing else: [' + op.id + '] '
    + op.description + '. Expected files: ' + op.files.join(', ') + '. Follow the AGENTS.md change protocol: '
    + 'record requested outcome and current authoritative state, affected contracts and fixtures, preconditions '
    + 'and expected observable result, effect class (' + op.effect_class + '), and the rollback or refusal '
    + 'boundary. Contract and defeating fixtures come before implementation code; make the smallest change; '
    + 'keep modules under 300 lines; stay inside services/asset. Never edit conformance/ scenarios or the '
    + 'oracle, never touch another service state, and never run git commit or git push. Run python '
    + 'scripts/verify.py from ' + ROOT + ' and record the exact command and exit code in checks. Your output '
    + 'is a builder self-report: BUILT evidence only - it cannot witness or ratify itself.'
}

function filesAreDisjoint(ops) {
  const seen = {}
  for (let i = 0; i < ops.length; i++) {
    const files = ops[i].files || []
    for (let j = 0; j < files.length; j++) {
      if (seen[files[j]]) { return false }
      seen[files[j]] = true
    }
  }
  return true
}

let built = []
if (plan.operations.length > 1 && filesAreDisjoint(plan.operations)) {
  const thunks = plan.operations.map(function (op) {
    return function () { return agent(buildPrompt(op), { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 'build-' + op.id }) }
  })
  const results = await parallel(thunks)
  built = results.filter(function (r) { return r !== null && r !== undefined })
} else {
  for (let i = 0; i < plan.operations.length; i++) {
    const result = await agent(buildPrompt(plan.operations[i]), { agentType: 'sov-worker', schema: BUILD_SCHEMA, phase: 'Build', label: 'build-' + plan.operations[i].id })
    if (result) { built.push(result) }
  }
}

if (built.length === 0) {
  log('Build: no builder returned a report; nothing to witness')
  return { domain: 'asset', objective: objective, blocked: false, planned: plan.operations, built: [], witness: null, residuals: ['no build report was produced; run is unattestable'], judgement_queue: plan.judgement_queue, standing_proposal: null }
}

phase('Witness')
log('Witness: independent inspection of ' + built.length + ' claimed operation(s)')

const claims = built.map(function (b) { return { operation_id: b.operation_id, files_changed: b.files_changed } })

const witnessPrompt = 'You are an independent witness for the Soveraeign asset domain at ' + ROOT + '. You were '
  + 'not the builder; a build report cannot witness itself, so do not consult builder reasoning - only the '
  + 'repository itself. Claimed operations and changed files: ' + JSON.stringify(claims) + '. Independently '
  + 'inspect the actual diffs and current content of those files (git diff, git status, direct reads), check '
  + 'them against services/asset contracts, KNOWN-GAPS.md, and AGENTS.md boundaries, and run python '
  + 'scripts/verify.py from ' + ROOT + ', observing the real exit code yourself. Never treat a green build or '
  + 'the claim list as authority. For each operation_id return a verdict: reproduced (independently confirmed '
  + 'in the repository), dissented (evidence contradicts the claim), or unattestable (cannot be independently '
  + 'confirmed). List residual defects. Set standing_supported to BUILT->WITNESSED only when every verdict is '
  + 'reproduced and verification passed; otherwise none. Never RATIFIED - ratification is Bdo-only.'

const witness = await agent(witnessPrompt, { agentType: 'sov-witness', schema: WITNESS_SCHEMA, phase: 'Witness', label: 'witness' })
if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }

let standingProposal = null
if (witness && (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED')) {
  standingProposal = witness.standing_supported
}
const residuals = witness && witness.residuals ? witness.residuals : ['witness agent returned no result; run is unattestable']

const report = { domain: 'asset', objective: objective, blocked: false, planned: plan.operations, built: built, witness: witness || null, residuals: residuals, judgement_queue: plan.judgement_queue, standing_proposal: standingProposal }

log('Report: standing proposal ' + report.standing_proposal + '; residuals: ' + residuals.length + '; judgement items: ' + report.judgement_queue.length)

return report
