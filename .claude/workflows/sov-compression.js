export const meta = {
  name: 'sov-compression',
  description: 'Observe-only daily/weekly compression ritual: deterministic repository reading, independent lenses, fresh-reader test, and bounded synthesis; creates no policy, standing, phase, or ledger',
  whenToUse: 'Daily while the pre-opening gap is operationally visible and weekly before a new work cycle; continue afterward as regression/system compression without manufacturing gap work.',
  phases: [
    { title: 'Measure', detail: 'run the deterministic compression reader at the exact current revision' },
    { title: 'Scan', detail: 'inspect verification, governance, and feedback pressure without editing' },
    { title: 'Fresh Reader', detail: 'independently test whether current entry documents work without oral history' },
    { title: 'Compress', detail: 'correlate evidence, route findings, and judge gap visibility without opening a phase' },
  ],
}

// args: { mode?: 'daily' | 'weekly', cadence?: 'daily' | 'weekly', focus?: string }
// One workflow owns both cadences so the ritual itself does not fork into two
// truth-producing implementations.

const requestedMode = args && (args.mode === 'weekly' || args.cadence === 'weekly') ? 'weekly' : 'daily'
const mode = requestedMode
const focus = args && args.focus ? args.focus : 'make the historical-to-current gap operationally invisible without opening a successor phase'

const MEASURE = {
  type: 'object',
  required: ['command', 'exit_code', 'reading', 'observations', 'residuals'],
  properties: {
    command: { type: 'string' },
    exit_code: { type: 'integer' },
    reading: { type: 'object' },
    observations: { type: 'array', items: { type: 'string' } },
    residuals: { type: 'array', items: { type: 'string' } },
  },
}

const SCAN = {
  type: 'object',
  required: ['lens', 'new_findings', 'repeated_findings', 'useful_corroboration', 'redundant_recomputation', 'compressions', 'cautions'],
  properties: {
    lens: { type: 'string' },
    new_findings: { type: 'array', items: { type: 'string' } },
    repeated_findings: { type: 'array', items: { type: 'string' } },
    useful_corroboration: { type: 'array', items: { type: 'string' } },
    redundant_recomputation: { type: 'array', items: { type: 'string' } },
    compressions: { type: 'array', items: { type: 'string' } },
    cautions: { type: 'array', items: { type: 'string' } },
  },
}

const FRESH = {
  type: 'object',
  required: ['verdict', 'entry_path', 'participant_path', 'oral_history_needed', 'friction', 'evidence'],
  properties: {
    verdict: { type: 'string', enum: ['CLEAR', 'FRICTION', 'BLOCKED', 'UNATTESTABLE'] },
    entry_path: { type: 'array', items: { type: 'string' } },
    participant_path: { type: 'array', items: { type: 'string' } },
    oral_history_needed: { type: 'boolean' },
    friction: { type: 'array', items: { type: 'string' } },
    evidence: { type: 'array', items: { type: 'string' } },
  },
}

const RESULT = {
  type: 'object',
  required: [
    'mode', 'head_revision', 'gap_reading', 'new_defects', 'corroboration',
    'redundant_observations', 'representation_pressure', 'lesson_routing',
    'decision_candidates', 'concern_candidates', 'skill_candidates',
    'subtraction_candidates', 'material_owner_blockers', 'later_owner_items',
    'next_smallest_action', 'do_not_open', 'terminal_basis',
  ],
  properties: {
    mode: { type: 'string', enum: ['daily', 'weekly'] },
    head_revision: { type: 'string' },
    gap_reading: { type: 'string', enum: ['GAP_VISIBLE', 'GAP_OPERATIONALLY_INVISIBLE', 'UNATTESTABLE'] },
    fresh_reader: { type: 'object' },
    new_defects: { type: 'array', items: { type: 'string' } },
    corroboration: { type: 'array', items: { type: 'string' } },
    redundant_observations: { type: 'array', items: { type: 'string' } },
    representation_pressure: { type: 'array', items: { type: 'string' } },
    lesson_routing: { type: 'array', items: { type: 'string' } },
    decision_candidates: { type: 'array', items: { type: 'string' } },
    concern_candidates: { type: 'array', items: { type: 'string' } },
    skill_candidates: { type: 'array', items: { type: 'string' } },
    subtraction_candidates: { type: 'array', items: { type: 'string' } },
    material_owner_blockers: { type: 'array', items: { type: 'string' } },
    later_owner_items: { type: 'array', items: { type: 'string' } },
    metrics: { type: 'object' },
    next_smallest_action: { type: 'string' },
    do_not_open: { type: 'boolean' },
    terminal_basis: { type: 'array', items: { type: 'string' } },
  },
}

phase('Measure')
log('compression: ' + mode + ' reading, observe-only')

const measured = await agent(
  'You are an independent read-only measurer for the Soveraeign compression ritual. '
    + 'Read AGENTS.md and .claude/skills/sov-compression/SKILL.md first. Focus: ' + focus + '. '
    + 'Run exactly `python scripts/sov_compression.py ' + mode + ' --json` from the repository root. '
    + 'Record the real exit code and parse the emitted JSON into `reading`. Inspect only enough repository context to explain anomalies. '
    + 'Do not edit, fix, commit, push, open a phase, change standing, create a report/lesson/decision/concern, or convert churn into a defect by itself.',
  { agentType: 'sov-witness', schema: MEASURE, phase: 'Measure', label: 'compression-measure-' + mode }
)

if (!measured || measured.exit_code !== 0) {
  return {
    mode: mode,
    gap_reading: 'UNATTESTABLE',
    error: 'deterministic compression reader did not produce a clean observation',
    measurement: measured || null,
    do_not_open: true,
  }
}

phase('Scan')
const scanPrompts = [
  'Verification lens. Read .claude/skills/sov-verification/SKILL.md and current verification/CI surfaces plus relevant recent history. Correlate repeated red observations before calling them separate defects. Distinguish useful independent corroboration from redundant recomputation. Flag blocking gates whose risk, scope, pass criterion, evidence class, expected cost, or owner is unclear. Prefer exact subject revision and failing predicate evidence; invent no thresholds or metrics.',
  'Governance lens. Read .claude/skills/sov-governance/SKILL.md, contracts/phases.json, STATUS.yaml, current root entry readers, OPEN-SEAMS.md, and only owner queues/holds relevant to the current proving/opening path. Find duplicate authoritative producers, stale live guidance, historical Phase-I material acting as current authority, premature terminal claims, and owner items that actually change a gated transition. Preserve unrelated owner backlog as non-blocking.',
  'Feedback/lifecycle lens. Read .claude/skills/sdlc-feedback/SKILL.md, LESSONS.md, contracts/lessons-loop.json, and current work/custody records directly relevant to the measured delta. Find lessons whose standing outruns their executable carrier, repeated lessons that should be routed once instead of copied, and work that looks merged/green but not settled. Do not create a concern; report only the smallest route if one is needed.',
]

const scans = await parallel(scanPrompts.map(function (prompt, index) {
  return function () {
    return agent(
      prompt + ' Mode: ' + mode + '. Focus: ' + focus + '. HEAD: ' + measured.reading.subject_revision
        + '. Deterministic reading: ' + JSON.stringify(measured.reading)
        + '. Read only; do not fix anything.',
      { agentType: 'sov-witness', schema: SCAN, phase: 'Scan', label: 'compression-scan-' + index })
  }
}))

phase('Fresh Reader')
const fresh = await agent(
  'Act as a genuinely fresh Soveraeign participant. Do not read the scan outputs and do not rely on conversational history. '
    + 'Start from current repository entry documents and determine: (1) historical Phase-I standing, (2) whether any phase is active now, (3) the current next gate, '
    + '(4) how a participant reaches the progressive principal/session -> grant -> operation -> record/projection path, and (5) how ordinary work reaches concern -> custody -> lease -> closure -> landing -> settlement where applicable. '
    + 'Record the exact entry path you followed. Check whether current EFFECTIVE lesson claims are discoverably backed by executable carriers and whether owner decisions appear only at the transitions they actually gate. '
    + 'If oral history, stale historical prose, contradictory current readers, or unexplained reconciliation debris is required, say so. Read only.',
  { agentType: 'sov-witness', schema: FRESH, phase: 'Fresh Reader', label: 'compression-fresh-reader' }
)

phase('Compress')
const synthesis = await agent(
  'You are the compression synthesizer, not a governor. Read .claude/skills/sov-compression/SKILL.md. '
    + 'Mode: ' + mode + '. HEAD: ' + measured.reading.subject_revision + '. Focus: ' + focus + '. '
    + 'Measurement: ' + JSON.stringify(measured) + '. Scans: ' + JSON.stringify(scans) + '. Fresh-reader result: ' + JSON.stringify(fresh) + '. '
    + 'Correlate repeated observations around one underlying subject. Preserve useful independent corroboration. Route findings only as report, lesson, decision, concern, drop, or none; create none of them. '
    + 'Separate owner items that materially block the exact opening/proving transition from later non-blocking owner work. Rank subtraction_candidates by deletion, derivation, correlation, settlement, or narrowing before new surface. '
    + 'For weekly mode, treat seven days as one system and include skill candidates only when a bounded procedure repeated with stable inputs, outputs, refusal boundary, and owners. '
    + 'Metrics must be exact or omitted/UNMEASURED; do not invent a denominator. '
    + 'Report GAP_OPERATIONALLY_INVISIBLE only if the independent fresh reader is CLEAR without oral history, Phase I cannot be mistaken for current authority, no successor phase is active, EFFECTIVE lessons have real carriers, material owner decisions are attached only to exact gated transitions, and surviving work is ordinary readiness rather than archaeology/reconciliation. '
    + 'That reading is readiness only and never opens a phase, so do_not_open must be true. If any required basis is unavailable, use UNATTESTABLE instead of guessing.',
  { agentType: 'sov-controller', schema: RESULT, phase: 'Compress', label: 'compression-synthesis-' + mode }
)

const result = synthesis || {
  mode: mode,
  head_revision: measured.reading.subject_revision,
  gap_reading: 'UNATTESTABLE',
  fresh_reader: fresh || null,
  new_defects: [],
  corroboration: [],
  redundant_observations: [],
  representation_pressure: [],
  lesson_routing: [],
  decision_candidates: [],
  concern_candidates: [],
  skill_candidates: [],
  subtraction_candidates: [],
  material_owner_blockers: [],
  later_owner_items: [],
  next_smallest_action: 'rerun compression when an independent synthesis is available',
  do_not_open: true,
  terminal_basis: [],
}

log('compression complete: ' + result.gap_reading + '; '
  + result.new_defects.length + ' new defect(s), '
  + result.redundant_observations.length + ' redundant observation(s), '
  + result.subtraction_candidates.length + ' subtraction candidate(s), '
  + result.material_owner_blockers.length + ' material owner blocker(s)')

return result
