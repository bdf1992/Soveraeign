export const meta = {
  name: 'sov-review',
  description: 'Review a change set across code and governance dimensions, adversarially verify every finding, and report - never edits, never posts',
  whenToUse: 'Scheduled or ad hoc review of a branch, pull request, or working tree. Reads the diff from local git and runs entirely offline: it never reaches GitHub, never edits the tree, and never posts a comment. Findings are PROPOSED until independently reproduced.',
  phases: [
    { title: 'Review', detail: 'one reviewer per dimension over the diff' },
    { title: 'Verify', detail: 'adversarial reproduction of each finding' },
    { title: 'Aggregate', detail: 'rank confirmed findings and queue judgement items' },
  ],
}

// args: { base?: string, head?: string, dimensions?: string[], focus?: string }

const DIMENSIONS = {
  correctness: 'Defects in the changed code: wrong logic, unhandled cases, broken invariants, defeating inputs the change does not survive. Read the changed files whole, not just the hunks.',
  contracts: 'Conformance to the owning contract. Does each change match its schema in contracts/, its service CHARTER.md, and the SPEC.md transition it claims? Does new behavior carry the positive AND defeating conformance case AGENTS.md requires?',
  standing: 'Honesty of claims. Does any document, commit message, report, or STATUS.yaml field assert standing the evidence does not support? A passing self-test is BUILT only. A builder self-report is never a witness. Flag every claim that outruns its evidence.',
  boundaries: 'Protected boundaries and effect classes. Does the change introduce an EXTERNAL_WORLD effect, import a whole repository, add runtime code with no prior logical spec or defeating fixture, or mutate immutable lineage evidence?',
  reuse: 'Duplication and simplification. Does the change reimplement something the repository already owns, or add structure that a smaller change would have achieved?',
}

const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['dimension', 'findings'],
  properties: {
    dimension: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['file', 'summary', 'failure_scenario', 'severity'],
        properties: {
          file: { type: 'string' },
          line: { type: 'integer' },
          summary: { type: 'string' },
          failure_scenario: { type: 'string' },
          severity: { type: 'string', enum: ['blocking', 'residual', 'judgement'] },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['reproduced', 'reasoning'],
  properties: {
    reproduced: { type: 'boolean' },
    reasoning: { type: 'string' },
  },
}

const requested = args && Array.isArray(args.dimensions) && args.dimensions.length > 0
  ? args.dimensions
  : Object.keys(DIMENSIONS)
const selected = requested.filter(function (d) { return Object.prototype.hasOwnProperty.call(DIMENSIONS, d) })

if (selected.length === 0) {
  return { error: 'no known dimensions selected', known: Object.keys(DIMENSIONS) }
}

const base = args && args.base ? args.base : 'origin/main'
const head = args && args.head ? args.head : 'HEAD'
const focus = args && args.focus ? args.focus : ''

phase('Review')
log('Review: ' + selected.length + ' dimension(s) over ' + base + '...' + head + ' - offline, read-only')

function reviewPrompt(d) {
  return 'You are reviewing a Soveraeign change set on the ' + d + ' dimension.\n\n'
    + 'DIMENSION: ' + DIMENSIONS[d] + '\n\n'
    + (focus ? 'FOCUS: ' + focus + '\n\n' : '')
    + 'Read the change with: git diff ' + base + '...' + head + ' --stat, then git diff ' + base + '...' + head + ' for the files that matter, '
    + 'then read those files whole. Read AGENTS.md first for the operating contract, and the owning contract or skill for anything you are unsure about.\n\n'
    + 'You are OFFLINE and READ-ONLY. Do not run gh. Do not edit, fix, stage, commit, or push anything. Do not post a comment anywhere. '
    + 'You may run python scripts/verify.py and read anything in the repository.\n\n'
    + 'Report only defects you can point at in a specific file. For each: the file, the line if you have one, a one-sentence summary, '
    + 'a concrete failure scenario (inputs or state, then the wrong outcome), and a severity - "blocking" if it must not merge, '
    + '"residual" if it should be recorded and fixed later, "judgement" if only Bdo can decide it. '
    + 'Report nothing you are not prepared to have independently reproduced. An empty findings array is a valid and useful result.'
}

const reviewed = await pipeline(
  selected,
  function (d) {
    return agent(reviewPrompt(d), { agentType: 'sov-witness', schema: FINDINGS_SCHEMA, phase: 'Review', label: 'review:' + d })
  },
  function (result, dimension) {
    if (!result || !result.findings || result.findings.length === 0) {
      return { dimension: dimension, confirmed: [], refuted: [], missing: !result }
    }
    return parallel(result.findings.map(function (f) {
      return function () {
        const prompt = 'Independently reproduce or refute this review finding against the Soveraeign repository.\n\n'
          + 'CLAIM: ' + f.summary + '\n'
          + 'FILE: ' + f.file + (f.line ? ':' + f.line : '') + '\n'
          + 'CLAIMED FAILURE: ' + f.failure_scenario + '\n\n'
          + 'Read the file yourself and trace the scenario. Default to reproduced=false if you cannot demonstrate the failure concretely. '
          + 'A finding that only sounds plausible is refuted. Do not edit anything.'
        return agent(prompt, { agentType: 'sov-witness', schema: VERDICT_SCHEMA, phase: 'Verify', label: 'verify:' + f.file })
          .then(function (v) { return { finding: f, verdict: v } })
      }
    })).then(function (votes) {
      const kept = []
      const dropped = []
      votes.filter(Boolean).forEach(function (v) {
        if (v.verdict && v.verdict.reproduced) { kept.push(v.finding) } else { dropped.push(v.finding) }
      })
      return { dimension: dimension, confirmed: kept, refuted: dropped, missing: false }
    })
  }
)

phase('Aggregate')

const RANK = { blocking: 0, residual: 1, judgement: 2 }
const confirmed = []
const judgementQueue = []
const unreviewed = []
let refutedCount = 0

reviewed.filter(Boolean).forEach(function (r) {
  if (r.missing) { unreviewed.push(r.dimension); return }
  refutedCount += r.refuted.length
  r.confirmed.forEach(function (f) {
    if (f.severity === 'judgement') { judgementQueue.push(r.dimension + ': ' + f.summary + ' (' + f.file + ')') }
    confirmed.push({ dimension: r.dimension, file: f.file, line: f.line, summary: f.summary, failure_scenario: f.failure_scenario, severity: f.severity })
  })
})

confirmed.sort(function (a, b) { return (RANK[a.severity] || 9) - (RANK[b.severity] || 9) })

const blocking = confirmed.filter(function (f) { return f.severity === 'blocking' })

log('Review complete: ' + confirmed.length + ' confirmed (' + blocking.length + ' blocking), '
  + refutedCount + ' refuted, ' + judgementQueue.length + ' judgement item(s)')

return {
  base: base,
  head: head,
  dimensions: selected,
  unreviewed: unreviewed,
  confirmed: confirmed,
  blocking_count: blocking.length,
  refuted_count: refutedCount,
  judgement_queue: judgementQueue,
  standing_note: 'Findings are PROPOSED. Each survived one independent reproduction attempt; that is not owner ratification, and this workflow posted nothing.',
}
