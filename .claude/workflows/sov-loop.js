export const meta = {
  name: 'sov-loop',
  description: 'One concern through control, orchestration, work, independent witness, and the landing gate',
  whenToUse: 'The ordinary way to move one bounded concern from selected to landed. Every other workflow in this repository stops at an uncommitted tree and a queue pointed at Bdo; this one ends at the landing gate, which either commits and merges under contracts/standing-grants.json or refuses with the reason. Use sov-federation for multi-domain sweeps and sov-qa to observe without building.',
  phases: [
    { title: 'Select', detail: 'controller names the one concern and its scope' },
    { title: 'Plan', detail: 'orchestrator turns it into one bounded operation' },
    { title: 'Build', detail: 'worker executes it and reports the paths it changed' },
    { title: 'Orchestrator Review', detail: 'evidence mode forms a frozen participant-in-work Finding' },
    { title: 'Witness Review', detail: 'independent evidence mode forms a frozen WORK Finding' },
    { title: 'Compare', detail: 'controller compares frozen cited Findings without ratifying them' },
    { title: 'Land', detail: 'the landing gate grades the request against the standing grant' },
  ],
}

// args: { objective: string, concern?: string, domain?: string, source_session?: string, queue_refs?: string[], source_refs?: string[], target?: string, plan_only?: boolean, evidence_mode?: boolean }
//
// The gate, not this script, is what decides whether anything lands. A workflow
// cannot grant itself authority, so every phase here is evidence-gathering and
// the last step hands that evidence to scripts/sov_land.py to be refused or not.


const objective = args && args.objective ? args.objective : null
if (!objective) {
  return { error: 'sov-loop needs an objective; it selects nothing on its own' }
}
const domain = args && args.domain ? args.domain : null
const concernHint = args && args.concern ? args.concern : null
const sourceSessionHint = args && args.source_session ? args.source_session : null
const queueRefsHint = args && Array.isArray(args.queue_refs) ? args.queue_refs : []
const sourceRefsHint = args && Array.isArray(args.source_refs) ? args.source_refs : []
const target = args && args.target ? args.target : 'main'
const planOnly = !!(args && args.plan_only)
const evidenceMode = !!(args && args.evidence_mode)

const CONCERN = {
  type: 'object',
  required: ['concern', 'concern_id', 'domain', 'source_session', 'queue_refs', 'source_refs', 'rationale', 'in_grant_scope', 'expected_paths'],
  properties: {
    concern: { type: 'string' },
    concern_id: { type: 'string' },
    domain: { type: 'string' },
    source_session: { type: 'string' },
    queue_refs: { type: 'array', items: { type: 'string' } },
    source_refs: { type: 'array', items: { type: 'string' } },
    rationale: { type: 'string' },
    in_grant_scope: { type: 'boolean' },
    out_of_scope_paths: { type: 'array', items: { type: 'string' } },
    expected_paths: { type: 'array', items: { type: 'string' } },
  },
}

const PLAN = {
  type: 'object',
  required: ['concern_id', 'operation', 'files', 'effect_class', 'checks', 'defeating_case'],
  properties: {
    concern_id: { type: 'string' },
    operation: { type: 'string' },
    files: { type: 'array', items: { type: 'string' } },
    effect_class: { type: 'string' },
    checks: { type: 'array', items: { type: 'string' } },
    defeating_case: { type: 'string' },
    blockers: { type: 'array', items: { type: 'string' } },
  },
}

const BUILD = {
  type: 'object',
  required: ['concern_id', 'changed_paths', 'summary', 'checks_run', 'residuals', 'cross_concern_routes'],
  properties: {
    concern_id: { type: 'string' },
    changed_paths: { type: 'array', items: { type: 'string' } },
    cross_concern_routes: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    checks_run: { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } },
    residuals: { type: 'array', items: { type: 'string' } },
  },
}

const WITNESS = {
  type: 'object',
  required: ['concern_id', 'verdict', 'observations', 'residuals', 'observation_file'],
  properties: {
    concern_id: { type: 'string' },
    verdict: { type: 'string' },
    observations: { type: 'array', items: { type: 'string' } },
    residuals: { type: 'array', items: { type: 'string' } },
    observation_file: { type: 'string' },
    judgement_items: { type: 'array', items: { type: 'string' } },
  },
}

// Harness shape of contracts/finding.schema.json. A review result is an
// envelope around a real Finding, not a weakened Finding used to represent a
// missing projection. UNATTESTABLE therefore has no `finding` member.
const FINDING = {
  type: 'object',
  required: ['finding_schema', 'finding_id', 'subject', 'evaluator', 'scope',
             'record_projection_id', 'claims', 'evidence_addresses',
             'counterevidence_addresses', 'input_finding_ids', 'created_at',
             'frozen_at', 'authority_effect', 'settlement_effect', 'supersedes'],
  properties: {
    finding_schema: { type: 'string' },
    finding_id: { type: 'string' },
    subject: { type: 'object', required: ['kind', 'address'], properties: {
      kind: { type: 'string' }, address: { type: 'string' },
    } },
    evaluator: { type: 'object', required: ['principal_id', 'relation'], properties: {
      principal_id: { type: 'string' }, relation: { type: 'string' },
    } },
    scope: { type: 'object' },
    record_projection_id: { type: 'string' },
    claims: { type: 'array', items: { type: 'object', required: ['claim_id', 'verdict', 'detail'], properties: {
      claim_id: { type: 'string' }, verdict: { type: 'string' }, detail: { type: 'string' },
    } } },
    evidence_addresses: { type: 'array', items: { type: 'string' } },
    counterevidence_addresses: { type: 'array', items: { type: 'string' } },
    input_finding_ids: { type: 'array', items: { type: 'string' } },
    created_at: { type: 'string' },
    frozen_at: { type: 'string' },
    authority_effect: { type: 'string' },
    settlement_effect: { type: 'string' },
    supersedes: { type: 'array', items: { type: 'string' } },
  },
}

const REVIEW_RESULT = {
  type: 'object',
  required: ['concern_id', 'status'],
  properties: {
    concern_id: { type: 'string' },
    status: { type: 'string' },
    projection_as_of: { type: 'string' },
    finding: FINDING,
    defect: { type: 'string' },
    observation_file: { type: 'string' },
  },
}

// This is deliberately a comparison envelope, not a Finding. A valid
// FINDING_SET Finding needs its own real RecordProjection over durably recorded
// input Findings; pre-opening rehearsal must not invent that projection.
const COMPARISON = {
  type: 'object',
  required: ['status', 'classifications', 'input_finding_ids', 'authority_effect',
             'settlement_effect', 'detail'],
  properties: {
    status: { type: 'string' },
    classifications: { type: 'array', items: { type: 'string' } },
    input_finding_ids: { type: 'array', items: { type: 'string' } },
    authority_effect: { type: 'string' },
    settlement_effect: { type: 'string' },
    detail: { type: 'string' },
  },
}

const BAD_PROJECTION_IDS = ['NONE', 'UNAVAILABLE', 'MISSING']
function frozenFinding(result, subjectKind) {
  const finding = result && result.status === 'FINDING' ? result.finding : null
  return !!(finding && finding.finding_schema === 'soveraeign-finding/v1'
    && finding.subject && finding.subject.kind === subjectKind
    && finding.record_projection_id
    && BAD_PROJECTION_IDS.indexOf(finding.record_projection_id) === -1
    && finding.frozen_at && finding.authority_effect === 'NONE'
    && finding.settlement_effect === 'NONE')
}
function claimsConfirmed(result) {
  const claims = result && result.finding && Array.isArray(result.finding.claims)
    ? result.finding.claims : []
  return claims.length > 0 && claims.every(function (claim) { return claim.verdict === 'CONFIRMED' })
}

const LAND = {
  type: 'object',
  required: ['exit_code', 'verdict', 'detail', 'command'],
  properties: {
    exit_code: { type: 'integer' },
    verdict: { type: 'string' },
    detail: { type: 'string' },
    command: { type: 'string' },
    commit: { type: 'string' },
  },
}

// Every agent this workflow spawns counts against the grant's budget, so the
// count is carried to the gate rather than estimated there.
let invocations = 0

phase('Select')
invocations += 1
const selected = await agent(
  'You hold the Control tier for one concern in Soveraeign. Objective: ' + objective + '. '
  + (domain ? 'Owning domain hint: ' + domain + '. ' : 'Resolve the owning domain from repository contracts and discoverable skills; no closed domain vocabulary exists here. ')
  + 'Read AGENTS.md and contracts/standing-grants.json. Read `python scripts/sov_session.py console --json` when available. Name exactly one bounded concern that serves the objective. ' + (concernHint ? 'The source session supplied concern ' + concernHint + '; preserve it. ' : '') + (sourceSessionHint ? 'Source session: ' + sourceSessionHint + '. ' : '') + (queueRefsHint.length ? 'Available queue refs: ' + queueRefsHint.join(', ') + '. ' : '') + (sourceRefsHint.length ? 'Source refs: ' + sourceRefsHint.join(', ') + '. ' : '') + 'Concern labels route and attribute work; they grant no authority. '
  + 'Then decide whether the whole concern falls inside the standing grant scope: the grant admits services/, contracts/, conformance/, scripts/, .claude/, adapters/, bindings/, workers/, and diagrams/, and excludes decisions/, lineage/, STATUS.yaml, and every root governing document. '
  + 'Set in_grant_scope false and list out_of_scope_paths if the concern would have to touch anything excluded - that concern is still worth doing, it just ends at an acceptance packet for Bdo instead of at a merge. '
  + 'Do not build anything. Return concern, concern_id, domain, source_session, queue_refs, source_refs, rationale, in_grant_scope, out_of_scope_paths, and expected paths.',
  { agentType: 'sov-controller', schema: CONCERN, phase: 'Select', label: 'select' })

if (!selected) {
  return { error: 'controller returned no concern', objective: objective }
}
log('Concern: ' + selected.concern + ' (' + selected.domain + ')')
if (!selected.in_grant_scope) {
  log('Outside the standing grant: this concern ends at an acceptance packet, not a merge')
}

phase('Plan')
invocations += 1
const plan = await agent(
  'You hold the Orchestration tier. Concern id: ' + selected.concern_id + '. Turn this concern into exactly one bounded operation: ' + selected.concern + '. Preserve the same concern id; do not silently switch concerns. '
  + 'Enumerate .claude/skills/ and load the relevant skill if one exists, then read AGENTS.md and the owning contract/fixture. A missing skill name is not a refusal. '
  + 'Follow the implementation order in AGENTS.md: name the operation and owned lifecycle, then the contract and its positive and defeating case, then the smallest change. '
  + 'You plan only; you do not build, witness, or dispatch. Return unchanged concern_id, operation, exact files, effect class, checks, defeating case, and blockers.',
  { agentType: 'sov-orchestrator', schema: PLAN, phase: 'Plan', label: 'plan:' + selected.domain })

if (!plan) {
  return { error: 'orchestrator returned no plan', concern: selected }
}
if (plan.concern_id !== selected.concern_id) {
  return { error: 'orchestrator changed the session concern instead of routing it', expected: selected.concern_id, observed: plan.concern_id }
}
if (plan.blockers && plan.blockers.length > 0) {
  log('Planned with ' + plan.blockers.length + ' blocker(s) named')
}

phase('Build')
invocations += 1
const built = await agent(
  'You hold the Work tier for exactly one operation under concern ' + selected.concern_id + ': ' + plan.operation + '. Preserve that concern for this session. '
  + 'Files: ' + (plan.files || []).join(', ') + '. Effect class: ' + plan.effect_class + '. '
  + 'Enumerate .claude/skills/ and load the relevant skill if one exists, then read AGENTS.md. Write the defeating case (' + plan.defeating_case + ') and prove it fails as declared before you call the work done. If you discover another concern, record a route with sov_session.py route; do not retarget this session. '
  + 'Run python scripts/lint.py and python scripts/verify.py from the repository root and report their real exit codes; do not report a check you did not run. '
  + 'Do not commit, merge, push, or edit decisions/ or STATUS.yaml. Do not witness your own work. '
  + 'Return unchanged concern_id, every path changed, summary, checks with exit codes, residuals, and route ids for cross-concern work you sourced.',
  { agentType: 'sov-worker', schema: BUILD, phase: 'Build', label: 'build:' + selected.domain })

if (!built) {
  return { error: 'worker returned no report', concern: selected, plan: plan }
}
if (built.concern_id !== selected.concern_id) {
  return { error: 'worker changed the session concern instead of routing it', expected: selected.concern_id, observed: built.concern_id }
}
log('Built: ' + (built.changed_paths || []).length + ' path(s) changed')

let orchestrationReview = null
if (evidenceMode) {
  phase('Orchestrator Review')
  invocations += 1
  orchestrationReview = await agent(
    'You are in REVIEW mode under concern ' + selected.concern_id + ', not PLAN mode. Judge PARTICIPANT_IN_WORK for the bounded assignment ' + plan.operation + '. Preserve the concern id. ' +
    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Reconstruct a scoped RecordProjection through the Record service for the assignment/participant-in-work subject and your evaluator relation. ' +
    'Judge assignment, authority, scope, repair, disclosure, and terminal fidelity only; do not judge implementation correctness. Do not read or anticipate the Witness conclusion. ' +
    'If a real projection with cited Record addresses exists, return status FINDING plus projection_as_of and a fully contract-compatible frozen Finding: finding_schema soveraeign-finding/v1; subject PARTICIPANT_IN_WORK; real evaluator principal/relation; scope; real record_projection_id; claims; evidence/counterevidence; input_finding_ids; created_at/frozen_at; authority_effect NONE; settlement_effect NONE; supersedes. ' +
    'If the needed Record projection or material evidence cannot be reconstructed, return status UNATTESTABLE and a concrete defect, with NO finding object. Never use NONE, UNAVAILABLE, MISSING, an invented id, worker prose, or memory to satisfy record_projection_id.',
    { agentType: 'sov-orchestrator', schema: REVIEW_RESULT, phase: 'Orchestrator Review', label: 'review:' + selected.domain })
  if (!orchestrationReview || orchestrationReview.concern_id !== selected.concern_id) {
    return { error: 'orchestrator review returned no concern-safe envelope', concern: selected, build: built }
  }
  if (orchestrationReview.status === 'FINDING' && !frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK')) {
    return { error: 'orchestrator labelled a malformed or projectionless value as a Finding', concern: selected }
  }
  if (orchestrationReview.status !== 'FINDING' &&
      (orchestrationReview.status !== 'UNATTESTABLE' || !orchestrationReview.defect)) {
    return { error: 'orchestrator review must be FINDING or explicit UNATTESTABLE', concern: selected }
  }
}

let witnessed = null
if (evidenceMode) {
  phase('Witness Review')
  invocations += 1
  const cutoffInstruction = frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK')
    ? 'Use this exact shared Record cutoff: ' + orchestrationReview.projection_as_of + '. The cutoff is projection metadata, not the Orchestrator conclusion. '
    : 'No common cutoff was supplied. Establish an exact Record cutoff yourself before writing any observation; comparison will remain a Record defect unless both real Findings exist. '
  witnessed = await agent(
    'You are the independent evaluator of WORK under concern ' + selected.concern_id + '. Concern: ' + selected.concern + '. Operation: ' + plan.operation + '. Preserve the concern id; independence comes from evaluator/session relation, not changing the concern. ' +
    'Use contracts/record-projection.schema.json and contracts/finding.schema.json. Inspect the exact repository state and governing contract/fixtures yourself. ' + cutoffInstruction +
    'Do not read the worker conclusion, Orchestrator Finding, or Controller expectation before freezing your own result. Builder paths may locate the work but are not evidence. ' +
    'If a real WORK RecordProjection exists, freeze a fully contract-compatible Finding first, then write your independent observation JSON under reports/observations/; the observation write occurs after the Finding is frozen so it cannot enter its own evidence basis. Return status FINDING, projection_as_of, finding, and observation_file. ' +
    'If the projection/evidence cannot be reconstructed, write an observation that reports the work UNATTESTABLE, then return status UNATTESTABLE, the concrete Record defect, and observation_file with NO finding object. Never invent a projection id or substitute prose for Record evidence.',
    { agentType: 'sov-witness', schema: REVIEW_RESULT, phase: 'Witness Review', label: 'witness-review:' + selected.domain })
} else {
  phase('Witness')
  invocations += 1
  witnessed = await agent(
    'You are the independent observation for work you did not do and must not touch. Concern id: ' + selected.concern_id + '. Concern: ' + selected.concern + '. Preserve the concern id while keeping an independent session/evaluator relation. ' +
    'The builder reports it changed: ' + (built.changed_paths || []).join(', ') + '. Treat that as a claim, not evidence. ' +
    'Read git status and git diff yourself, read the owning contract and the defeating fixture, and run python scripts/verify.py and python scripts/lint.py observing the real exit codes. ' +
    'Confirm the defeating case actually fails as declared; a fixture that passes when it should fail is a DISSENTED verdict, not a residual. ' +
    'Then write your observation to reports/observations/ as JSON with exactly these fields: observer_id (your agent label), contributed_to_build (false - and if that is not true, say so and set verdict DISSENTED), verdict (CONFIRMED or DISSENTED), concern, and checks. ' +
    'You must not edit, fix, build, or commit anything outside that one observation file. ' +
    'Return concern_id, verdict, what you independently confirmed, residuals, the path you wrote the observation to, and any judgement items only Bdo can settle.',
    { agentType: 'sov-witness', schema: WITNESS, phase: 'Witness', label: 'witness:' + selected.domain })
}

if (!witnessed) {
  return { error: 'witness returned no observation; nothing may land unwitnessed', concern: selected, build: built }
}
if (witnessed.concern_id !== selected.concern_id) {
  return { error: 'witness changed the work concern instead of independently evaluating it', expected: selected.concern_id, observed: witnessed.concern_id }
}
if (evidenceMode && witnessed.status === 'FINDING' && !frozenFinding(witnessed, 'WORK')) {
  return { error: 'witness labelled a malformed or projectionless value as a Finding', concern: selected }
}
if (evidenceMode && witnessed.status !== 'FINDING' &&
    (witnessed.status !== 'UNATTESTABLE' || !witnessed.defect)) {
  return { error: 'witness review must be FINDING or explicit UNATTESTABLE', concern: selected }
}
log('Witness: ' + (evidenceMode ? witnessed.status : witnessed.verdict))

let comparison = null
if (evidenceMode) {
  const haveParticipantFinding = frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK')
  const haveWorkFinding = frozenFinding(witnessed, 'WORK')
  if (haveParticipantFinding && haveWorkFinding) {
    phase('Compare')
    invocations += 1
    comparison = await agent(
      'Compare these two already-frozen Findings. You do not witness, ratify, settle, average, or rewrite them. Preserve both subjects, input ids, and citations. ' +
      'Participant-in-work Finding: ' + JSON.stringify(orchestrationReview.finding) + '. WORK Finding: ' + JSON.stringify(witnessed.finding) + '. ' +
      'Use only these classifications: NO_CONFLICT, EVIDENCE_DIFFERENCE, INTERPRETATION_DIFFERENCE, WORK_DEFECT, WORKER_DEFECT, ORCHESTRATION_DEFECT, WITNESS_DEFECT, RECORD_DEFECT, POLICY_SEAM. ' +
      'Return status CLASSIFIED; both finding ids as input_finding_ids; authority_effect NONE; settlement_effect NONE; classifications; and concise evidence-based detail. This comparison envelope is not itself a Finding because this pre-opening workflow has no durable RecordProjection over the Finding set.',
      { agentType: 'sov-controller', schema: COMPARISON, phase: 'Compare', label: 'compare:' + selected.domain })
  } else {
    const ids = []
    if (haveParticipantFinding) ids.push(orchestrationReview.finding.finding_id)
    if (haveWorkFinding) ids.push(witnessed.finding.finding_id)
    comparison = {
      status: 'UNATTESTABLE', classifications: ['RECORD_DEFECT'], input_finding_ids: ids,
      authority_effect: 'NONE', settlement_effect: 'NONE',
      detail: 'Comparison requires two real frozen Findings backed by real Record projections; at least one review is UNATTESTABLE.',
    }
  }
}

phase('Land')
const evidenceReviewsConfirmed = !evidenceMode || (
  frozenFinding(orchestrationReview, 'PARTICIPANT_IN_WORK') && claimsConfirmed(orchestrationReview)
  && frozenFinding(witnessed, 'WORK') && claimsConfirmed(witnessed))
const comparisonBlocks = evidenceMode && (!comparison || comparison.status !== 'CLASSIFIED'
  || (comparison.classifications || []).length !== 1
  || comparison.classifications[0] !== 'NO_CONFLICT')
const witnessConfirmed = evidenceMode
  ? (evidenceReviewsConfirmed && !!witnessed.observation_file)
  : witnessed.verdict === 'CONFIRMED'
const mode = planOnly || !selected.in_grant_scope || !witnessConfirmed || comparisonBlocks ? 'plan' : 'land'
if (mode === 'plan') {
  const reason = planOnly ? 'plan_only was set'
    : (!selected.in_grant_scope ? 'concern is outside the grant'
      : (comparisonBlocks ? 'evidence comparison is not a single NO_CONFLICT classification'
        : (!evidenceReviewsConfirmed ? 'one evidence review lacks a confirmed real Finding'
          : 'independent observation is missing or unconfirmed')))
  log('Rehearsing the gate only: ' + reason)
}

const pathArgs = (built.changed_paths || []).map(function (p) { return '--path ' + p }).join(' ')
const observationArg = witnessed.observation_file ? ' --observation ' + witnessed.observation_file : ''
invocations += 1
const landed = await agent(
  'Run the landing gate and report exactly what it said. You did not build this change and you do not decide whether it lands; the gate does. '
  + 'Run this command from the repository root and nothing else that writes:\n\n'
  + '  python scripts/sov_land.py ' + mode + ' ' + pathArgs
  + observationArg
  + ' --target ' + target
  + ' --spend ' + (invocations + 1)
  + ' --message "' + (selected.domain + ': ' + selected.concern).replace(/"/g, "'") + '"\n\n'
  + 'Report its real exit code and its output verbatim in the detail field. Do not retry it with different arguments, do not edit contracts/standing-grants.json, and do not commit or merge by hand if it refuses. A refusal is the correct outcome to report, not a problem to route around.',
  { agentType: 'sov-controller', schema: LAND, phase: 'Land', label: 'land' })

const gate = landed || { exit_code: null, verdict: 'UNKNOWN', detail: 'the gate agent returned nothing', command: 'python scripts/sov_land.py ' + mode }

const residuals = [].concat(built.residuals || [], witnessed.residuals || [])
const judgementQueue = [].concat(witnessed.judgement_items || [])
if (!selected.in_grant_scope) {
  judgementQueue.push('Acceptance: ' + selected.concern + ' touches ' + (selected.out_of_scope_paths || []).join(', ') + ', which the standing grant excludes.')
}
if (gate.exit_code !== 0) {
  judgementQueue.push('The gate refused: ' + gate.detail)
}

return {
  workflow: 'sov-loop',
  objective: objective,
  concern: selected,
  plan: plan,
  build: { summary: built.summary, changed_paths: built.changed_paths, checks_run: built.checks_run },
  witness: evidenceMode ? witnessed : { verdict: witnessed.verdict, observations: witnessed.observations, observation_file: witnessed.observation_file },
  orchestration_review: orchestrationReview,
  orchestration_finding: orchestrationReview && orchestrationReview.finding ? orchestrationReview.finding : null,
  comparison: comparison,
  evidence_mode: evidenceMode,
  gate: gate,
  mode: mode,
  agent_invocations: invocations,
  residuals: residuals,
  judgement_queue: judgementQueue,
  standing: gate.exit_code === 0 ? 'LANDED_BUILT_AND_WITNESSED_NOT_RATIFIED' : 'HELD_AT_THE_GATE',
}
