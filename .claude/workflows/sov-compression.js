export const meta = {
  name: 'sov-compression',
  description: 'Run the daily gap-compression ritual or weekly super-compression without opening a phase or creating a second truth ledger',
  whenToUse: 'Use daily while the Phase-I-to-successor gap is still operationally visible, and weekly before a new work cycle to compress repeated defects, duplicated truth, stale projections, unjustified gates, lesson debt, and owner-decision noise.',
  phases: [
    { title: 'Orient', detail: 'pin phase state, revision, and bounded lookback' },
    { title: 'Scan', detail: 'independently inspect feedback, governance, and verification pressure' },
    { title: 'Fresh Reader', detail: 'test whether a participant can orient without oral history' },
    { title: 'Compress', detail: 'correlate repeated evidence and rank the smallest removals, derivations, and settlements' },
  ],
}

// args: { cadence?: 'daily'|'weekly', baseline_ref?: string, focus?: string }
// Observe-only harness plumbing. It edits nothing, opens nothing, and cannot
// change contracts/phases.json or STATUS.yaml. Returned readings are reports,
// not authority. The same workflow owns both cadences so the ritual itself does
// not fork into two truth-producing implementations.

const cadence = args && args.cadence === 'weekly' ? 'weekly' : 'daily'
const lookback = cadence === 'weekly' ? '7 days' : '1 day'
const baselineRef = args && args.baseline_ref ? args.baseline_ref : ''
const focus = args && args.focus ? args.focus : 'make the successor-preparation gap operationally invisible'

const ORIENT = {
  type: 'object',
  required: ['phase_i', 'current_phase', 'next_gate', 'head_revision', 'lookback_basis', 'visible_gap'],
  properties: {
    phase_i: { type: 'string' },
    current_phase: { type: 'string' },
    next_gate: { type: 'string' },
    head_revision: { type: 'string' },
    baseline_revision: { type: 'string' },
    lookback_basis: { type: 'string' },
    visible_gap: { type: 'array', items: { type: 'string' } },
    unattestable: { type: 'array', items: { type: 'string' } },
  },
}

const SCAN = {
  type: 'object',
  required: ['lens', 'new_findings', 'repeated_findings', 'compressions', 'cautions'],
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
  required: ['verdict', 'entry_path', 'participant_path', 'oral_history_needed', 'friction'],
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
  required: ['cadence', 'head_revision', 'gap_reading', 'compress_now', 'lesson_movement', 'material_owner_blockers', 'next_operation', 'do_not_open'],
  properties: {
    cadence: { type: 'string', enum: ['daily', 'weekly'] },
    head_revision: { type: 'string' },
    baseline_revision: { type: 'string' },
    gap_reading: { type: 'string', enum: ['GAP_VISIBLE', 'GAP_OPERATIONALLY_INVISIBLE', 'UNATTESTABLE'] },
    new_findings: { type: 'array', items: { type: 'string' } },
    repeated_findings: { type: 'array', items: { type: 'string' } },
    useful_corroboration: { type: 'array', items: { type: 'string' } },
    redundant_recomputation: { type: 'array', items: { type: 'string' } },
    compress_now: { type: 'array', items: { type: 'string' } },
    lesson_movement: { type: 'array', items: { type: 'string' } },
    material_owner_blockers: { type: 'array', items: { type: 'string' } },
    later_owner_items: { type: 'array', items: { type: 'string' } },
    skill_candidates: { type: 'array', items: { type: 'string' } },
    metrics: { type: 'object' },
    next_operation: { type: 'string' },
    do_not_open: { type: 'boolean' },
    terminal_basis: { type: 'array', items: { type: 'string' } },
  },
}

phase('Orient')
const orient = await agent(
  'You are the read-only orienter for the Soveraeign compression ritual. Read .claude/skills/sov-compression/SKILL.md, contracts/phases.json, STATUS.yaml, AGENTS.md, README.md, SOV.md, LESSONS.md, OPEN-SEAMS.md, and git history for the last ' + lookback + '. ' +
  (baselineRef ? 'Resolve baseline ref ' + baselineRef + ' if possible and report if it is not resolvable. ' : '') +
  'Pin the exact HEAD revision. Phase I must be reported from contracts/phases.json, not inferred from old prose. Do not edit, write a report, open an issue, switch branches, or infer a successor opening. Return current phase state, next gate, lookback basis, and only the gap seams still visible from current artifacts.',
  { agentType: 'sov-orchestrator', schema: ORIENT, phase: 'Orient', label: 'compression-orient' }
)

if (!orient) {
  return { workflow: 'sov-compression', cadence: cadence, gap_reading: 'UNATTESTABLE', error: 'orientation returned no reading' }
}

phase('Scan')
const prompts = [
  'Verification lens. Read .claude/skills/sov-verification/SKILL.md and current verification/CI surfaces plus the relevant recent history. Correlate repeated red observations before calling them separate defects. Distinguish useful independent corroboration from redundant recomputation. Flag gates whose risk, scope, pass criterion, evidence class, cost, or owner is unclear. Prefer exact revision/check evidence; do not invent metrics.',
  'Governance lens. Read .claude/skills/sov-governance/SKILL.md, current root readers, STATUS.yaml, contracts/phases.json, OPEN-SEAMS.md, owner queues/holds, and recent history. Find duplicate authoritative producers, stale current projections, historical Phase-I material still acting like live guidance, premature terminal claims, and owner items that actually change the opening/proving path. Preserve unrelated owner backlog as non-blocking.',
  'Feedback/lifecycle lens. Read .claude/skills/sdlc-feedback/SKILL.md, LESSONS.md, recent reports/observations and current work/custody records that are directly relevant. Find lessons whose stated standing outruns their executable carrier, repeated lessons that should be routed once instead of copied, and work that looks merged/green but not settled. Do not create a concern; only report the smallest route if one is needed.',
]

const scans = await parallel(prompts.map(function (prompt, index) {
  return function () {
    return agent(
      prompt + ' Cadence: ' + cadence + '. Lookback: ' + lookback + '. Focus: ' + focus + '. HEAD: ' + orient.head_revision + '. Read only; do not fix anything.',
      { agentType: 'sov-witness', schema: SCAN, phase: 'Scan', label: 'compression-scan-' + index })
  }
}))

phase('Fresh Reader')
const fresh = await agent(
  'Act as a genuinely fresh Soveraeign participant. Do not read the three scan outputs and do not rely on conversational history. Starting from the repository entry documents, determine: (1) historical Phase-I standing, (2) whether any phase is active now, (3) the next gate, and (4) how a participant reaches the current principal/session -> grant -> operation -> record/projection path and the concern -> custody -> lease -> closure -> landing -> settlement lifecycle where each is applicable. Record the exact entry path you followed. If you need oral history, stale historical prose, or contradictory current readers, say so. Read only.',
  { agentType: 'sov-witness', schema: FRESH, phase: 'Fresh Reader', label: 'compression-fresh-reader' }
)

phase('Compress')
const synthesis = await agent(
  'You are the compression synthesizer, not a governor. Read .claude/skills/sov-compression/SKILL.md. Cadence: ' + cadence + '. HEAD: ' + orient.head_revision + '. Orientation: ' + JSON.stringify(orient) + '. Scans: ' + JSON.stringify(scans) + '. Fresh-reader result: ' + JSON.stringify(fresh) + '. ' +
  'Correlate repeated observations around one underlying subject. Preserve useful independent corroboration. Route findings only as report, lesson, decision, concern, drop, or none; do not create any of them. Separate owner items that materially block the exact opening/proving transition from later non-blocking owner work. Rank compress_now by deletion/derivation/correlation/settlement before new surface. For weekly cadence, include skill candidates only when the same bounded procedure has repeated with stable inputs/outputs/refusals; do not mint the skill here. Metrics must be exact or the literal string UNMEASURED. ' +
  'Report GAP_OPERATIONALLY_INVISIBLE only if the fresh reader is CLEAR without oral history, historical Phase I cannot be mistaken for current authority, EFFECTIVE lesson claims have real carriers, material owner decisions are attached only to exact gated transitions, and surviving work is ordinary readiness rather than archaeology/reconciliation. This reading never opens a phase, so do_not_open must be true.',
  { agentType: 'sov-controller', schema: RESULT, phase: 'Compress', label: 'compression-synthesis' }
)

return synthesis || {
  cadence: cadence,
  head_revision: orient.head_revision,
  gap_reading: 'UNATTESTABLE',
  compress_now: [],
  lesson_movement: [],
  material_owner_blockers: [],
  next_operation: 'rerun compression with an available synthesizer',
  do_not_open: true,
}
