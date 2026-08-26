export const meta = { name: 'sov-librarian', description: 'Curate the Soveraeign asset library - read library conformance, plan curation against declared collection types, execute it, and witness the result independently', whenToUse: 'When the asset library needs organizing or auditing: declaring a collection type, filing assets into typed collections, closing MISSING_FIELD or UNFILED findings, or producing a conformance report an operator can act on', phases: [{ title: 'Survey' }, { title: 'Curate' }, { title: 'Witness' }] }

const ROOT = '.'
const STATE = ROOT + '/.soveraeign-asset'
const CLI = 'python -m soveraeign_asset_service.cli --root ' + STATE

const SURVEY_SCHEMA = { type: 'object', required: ['blocked', 'library', 'operations', 'judgement_queue'], properties: { blocked: { type: 'boolean' }, blocked_reason: { type: 'string' }, library: { type: 'object', required: ['collections', 'defects', 'unfiled'], properties: { collections: { type: 'integer' }, defects: { type: 'integer' }, unfiled: { type: 'integer' }, counts: { type: 'object' } } }, operations: { type: 'array', items: { type: 'object', required: ['id', 'description', 'verdict_addressed', 'effect_class'], properties: { id: { type: 'string' }, description: { type: 'string' }, verdict_addressed: { type: 'string', enum: ['MISSING_FIELD', 'CLAIMED_UNRATIFIED', 'VOCABULARY_REFUSED', 'MEMBER_KIND_REFUSED', 'EMPTY_COLLECTION', 'UNFILED', 'NONE'] }, effect_class: { type: 'string', enum: ['RECORD_LOCAL'] } } } }, judgement_queue: { type: 'array', items: { type: 'string' } } } }

const CURATE_SCHEMA = { type: 'object', required: ['operation_id', 'acts', 'checks'], properties: { operation_id: { type: 'string' }, acts: { type: 'array', items: { type: 'string' } }, descriptions_recorded: { type: 'integer' }, descriptions_ratified: { type: 'integer' }, checks: { type: 'array', items: { type: 'object', required: ['command', 'exit_code'], properties: { command: { type: 'string' }, exit_code: { type: 'integer' } } } }, residuals: { type: 'array', items: { type: 'string' } } } }

const WITNESS_SCHEMA = { type: 'object', required: ['verdicts', 'residuals', 'standing_supported'], properties: { verdicts: { type: 'array', items: { type: 'object', required: ['operation_id', 'verdict'], properties: { operation_id: { type: 'string' }, verdict: { type: 'string', enum: ['reproduced', 'dissented', 'unattestable'] } } } }, defects_before: { type: 'integer' }, defects_after: { type: 'integer' }, residuals: { type: 'array', items: { type: 'string' } }, standing_supported: { type: 'string', enum: ['none', 'OPEN->BUILT', 'BUILT->WITNESSED'] } } }

const objective = (args && args.objective) ? args.objective : 'reduce the largest defect class in the asset library conformance report without widening any collection type'

const LAW = 'The librarian curates and reports; it settles nothing. Load the sov-librarian skill and follow it. '
  + 'Three verdicts are distinct and must never be collapsed: CONFORMING means a RATIFIED description carries the '
  + 'required field with a permitted value; CLAIMED_UNRATIFIED means somebody recorded it and nobody ratified it, '
  + 'which is a claim and not conformance; MISSING_FIELD means nothing carries it. You may record a description '
  + 'under propose:description. You may never ratify one - ratify:judgement is Bdo\'s alone '
  + '(decisions/0063-asset-collections-and-the-librarian.md, Ruling 3). You may never widen a collection type to '
  + 'make members pass, never invent a value outside a declared vocabulary, and never file an asset into a '
  + 'collection merely to clear an UNFILED finding. Effect class is RECORD_LOCAL only. Never run git commit or '
  + 'git push. Never touch the Asset Projection Service, whose declare-collection builds an index and is a '
  + 'different record (OPEN-SEAMS S22).'

phase('Survey')
log('Survey: reading library conformance before planning anything')

const surveyPrompt = 'You are the sov-librarian surveyor for Soveraeign at ' + ROOT + '. ' + LAW + ' '
  + 'Read ' + ROOT + '/AGENTS.md, ' + ROOT + '/STATUS.yaml, ' + ROOT + '/services/asset/contracts/service.json, '
  + 'and ' + ROOT + '/decisions/0063-asset-collections-and-the-librarian.md. Then run, from '
  + ROOT + '/services/asset/src, `' + CLI + ' conformance` and `' + CLI + ' types`, observing the real exit '
  + 'codes yourself. Report the library figures from that output, never from memory. Produce a bounded curation '
  + 'plan for: ' + objective + '. Each operation names the verdict class it addresses. Take reversible defaults '
  + 'for every ordinary choice and name them in the descriptions; escalating a question this tier could settle '
  + 'with available evidence is a defect (decisions/0033, Ruling 1). Set blocked true only when no admissible '
  + 'curation exists - an empty library with no declared type is not blocked, it is a library that needs a type '
  + 'declared. Each judgement_queue entry names an owner-held boundary only: ratifying descriptions, settling '
  + 'seam S22, or a collection type whose vocabulary cannot express the real state of its members.'

const survey = await agent(surveyPrompt, { agentType: 'sov-orchestrator', schema: SURVEY_SCHEMA, phase: 'Survey', label: 'survey' })

if (!survey || survey.blocked || !survey.operations || survey.operations.length === 0) {
  log('Survey: blocked or empty plan; returning the judgement queue without forcing curation')
  const wasBlocked = !survey || survey.blocked === true
  const reason = survey && survey.blocked_reason ? [survey.blocked_reason] : (survey && !survey.blocked ? ['survey returned an empty plan; nothing was attempted'] : [])
  return { domain: 'librarian', objective: objective, blocked: wasBlocked, library: survey ? survey.library : null, planned: survey && survey.operations ? survey.operations : [], curated: [], witness: null, residuals: reason, judgement_queue: survey ? survey.judgement_queue : ['survey agent returned no plan; librarian scoping itself needs review'], standing_proposal: null }
}

phase('Curate')
log('Curate: executing ' + survey.operations.length + ' curation operation(s), sequentially - one library, one writer')

function curatePrompt(op) {
  return 'You are the sov-librarian curator for Soveraeign at ' + ROOT + '. ' + LAW + ' '
    + 'Execute exactly this one operation and nothing else: [' + op.id + '] ' + op.description + '. '
    + 'It addresses the verdict class ' + op.verdict_addressed + '. Work through '
    + '`' + CLI + ' <command>` from ' + ROOT + '/services/asset/src, or in process through '
    + 'service.organization and service.librarian. A refusal exits 2 and prints its declared code: record the '
    + 'code, do not retry around it, and do not change a contract to make it stop firing. Record each act you '
    + 'performed in acts, count descriptions_recorded, and set descriptions_ratified to 0 - any other value is '
    + 'an authority you do not hold. Run `' + CLI + ' conformance` afterwards and `python scripts/verify.py` '
    + 'from ' + ROOT + ', recording both exact commands and exit codes in checks. Your output is a curator '
    + 'self-report: BUILT evidence only, and it cannot witness itself.'
}

const curated = []
for (let i = 0; i < survey.operations.length; i++) {
  const op = survey.operations[i]
  const result = await agent(curatePrompt(op), { agentType: 'sov-worker', schema: CURATE_SCHEMA, phase: 'Curate', label: 'curate-' + op.id })
  if (result) { curated.push(result) }
}

const ratified = curated.reduce(function (total, r) { return total + (r.descriptions_ratified || 0) }, 0)
if (ratified > 0) { log('Curate: WARNING - a curator reported ' + ratified + ' ratified description(s); the librarian holds no ratify:judgement grant') }

phase('Witness')
log('Witness: independent read of the library, by an agent that curated nothing')

const witnessPrompt = 'You are the independent witness for a sov-librarian run at ' + ROOT + '. You curated '
  + 'nothing and you may change nothing. The curator claims: ' + JSON.stringify(curated) + '. The library before '
  + 'the run: ' + JSON.stringify(survey.library) + '. Verify each claim through a path independent of the report: '
  + 'run `' + CLI + ' conformance` yourself from ' + ROOT + '/services/asset/src, run `python scripts/verify.py` '
  + 'from ' + ROOT + ', and read `git status` and `git diff` to see what actually changed. Never treat a green '
  + 'build or the claim list as authority. Check specifically that no description was ratified by the curator '
  + 'and that no collection type was widened - either is a dissent, not a residual. For each operation_id return '
  + 'reproduced, dissented, or unattestable. Report defects_before and defects_after from the two reports. Set '
  + 'standing_supported to BUILT->WITNESSED only when every verdict is reproduced and verification passed; '
  + 'otherwise none. Never RATIFIED - ratification is Bdo-only.'

const witness = await agent(witnessPrompt, { agentType: 'sov-witness', schema: WITNESS_SCHEMA, phase: 'Witness', label: 'witness' })
if (witness && typeof witness.standing_supported === 'string') { witness.standing_supported = witness.standing_supported.split(' ').join('') }

let standingProposal = null
if (witness && (witness.standing_supported === 'OPEN->BUILT' || witness.standing_supported === 'BUILT->WITNESSED')) {
  standingProposal = witness.standing_supported
}
const residuals = witness && witness.residuals ? witness.residuals : ['witness agent returned no result; run is unattestable']

const report = { domain: 'librarian', objective: objective, blocked: false, library: survey.library, planned: survey.operations, curated: curated, witness: witness || null, residuals: residuals, judgement_queue: survey.judgement_queue, standing_proposal: standingProposal }

log('Report: defects ' + (witness && witness.defects_before !== undefined ? witness.defects_before + ' -> ' + witness.defects_after : 'unread') + '; residuals: ' + residuals.length + '; judgement items: ' + report.judgement_queue.length)

return report
