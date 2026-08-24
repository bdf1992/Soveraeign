export const meta = {
  name: 'sov-witness',
  description: 'Run an adversarial witness pass over a named subject and return a witness record for witness/ - never edits, never ratifies',
  whenToUse: 'Before asking Bdo to advance any standing. AGENTS.md fixes OPEN -> BUILT -> WITNESSED -> RATIFIED and a build report cannot witness itself, so nothing may be put to the owner until something that did not build it has tried to defeat it. Produces the record scripts/sov_standing.py requires.',
  phases: [
    { title: 'Attack', detail: 'independent witnesses, each told to defeat the artifact' },
    { title: 'Reconcile', detail: 'merge findings, keep every dissent' },
  ],
}

// args: { subject: string, artifacts?: string[], commit?: string, lenses?: string[] }

const LENSES = {
  coherence: 'Does it contradict itself, or the documents beside it? Read the artifact whole, then read every governed document it cites or that cites it. Hunt for a term defined one way here and used another way elsewhere, two names for one thing, one name for two things, and any claim the neighbouring document denies.',
  grounding: 'Is every claim backed by something a stranger could check? Follow each citation to its target and confirm the target exists and says what is claimed. A citation to a file that is absent from the checkout is a blocking finding, not a minor one. Run the commands the artifact claims pass, and report their real exit codes.',
  coverage: 'Does it cover what it says it covers? Count. How many things does it declare, how many carry a positive case, how many carry a defeating case, how many carry neither? Report the numbers you counted, never an estimate, and say what you counted them from.',
  enforcement: 'Is each stated rule actually enforced, or only stated? For every rule the artifact asserts, find the code that would refuse a violation. Feed that code a violating input and report whether it refuses. A rule with no enforcement is a claim, not a rule, and the gap between the two is the highest-value finding available here.',
  consequence: 'What breaks if this is ratified as written? Trace concretely. Does saying yes to this silently settle a question held separately open? Does switching it on deadlock any legitimate path? Would a reader be misled by a green result that means less than it appears to?',
}

const FINDING_SCHEMA = {
  type: 'object',
  required: ['lens', 'verdict', 'scores', 'findings', 'verified', 'uncovered'],
  properties: {
    lens: { type: 'string' },
    verdict: { type: 'string', enum: ['RATIFIABLE', 'RATIFIABLE-WITH-CONDITIONS', 'NOT-YET'] },
    scores: {
      type: 'object',
      required: ['coherence', 'grounding', 'coverage', 'defeat_resistance'],
      properties: {
        coherence: { type: 'integer' }, grounding: { type: 'integer' },
        coverage: { type: 'integer' }, defeat_resistance: { type: 'integer' },
      },
    },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'where', 'what', 'consequence'],
        properties: {
          severity: { type: 'string', enum: ['blocking', 'material', 'minor'] },
          where: { type: 'string' }, what: { type: 'string' }, consequence: { type: 'string' },
        },
      },
    },
    verified: { type: 'array', items: { type: 'string' } },
    conditions: { type: 'array', items: { type: 'string' } },
    uncovered: { type: 'array', items: { type: 'string' } },
    judgement_items: { type: 'array', items: { type: 'string' } },
  },
}

const subject = args && args.subject
if (!subject) {
  return { error: 'sov-witness needs a subject: the thing being witnessed, named as its status field or document' }
}

const requested = args && Array.isArray(args.lenses) && args.lenses.length > 0 ? args.lenses : Object.keys(LENSES)
const selected = requested.filter(function (l) { return Object.prototype.hasOwnProperty.call(LENSES, l) })
if (selected.length === 0) {
  return { error: 'no known lenses selected', known: Object.keys(LENSES) }
}

const artifacts = args && Array.isArray(args.artifacts) ? args.artifacts : []
const commit = args && args.commit ? args.commit : null

phase('Attack')
log('Witnessing "' + subject + '" through ' + selected.length + ' lens(es) - adversarial, read-only')

function attackPrompt(lens) {
  return 'You are an INDEPENDENT WITNESS over: ' + subject + '.\n\n'
    + (artifacts.length ? 'ARTIFACTS: ' + artifacts.join(', ') + '\n\n' : '')
    + 'LENS - ' + lens + ': ' + LENSES[lens] + '\n\n'
    + 'YOUR STANCE IS ADVERSARIAL. You are not confirming this artifact. You are hunting for why it should NOT '
    + 'advance. A witness that returns "looks correct" without having genuinely attacked it is discarded rather '
    + 'than filed, so an honest empty findings list must be earned by a real attempt.\n\n'
    + (commit
        ? 'WITNESS COMMIT ' + commit + '. Several sessions write this tree at once. Establish the artifact bytes at '
          + 'that commit (git show ' + commit + ':<path>) rather than reading a working tree that may change under you, '
          + 'and say in your report if the working tree differs.\n\n'
        : 'This tree is written by several sessions at once. Record the commit you observed and note any file that '
          + 'changed while you were reading it - an observation of a moving tree is not reproducible.\n\n')
    + 'VERIFY INDEPENDENTLY. Do not take any document\'s word about itself, including its claims about its own '
    + 'coverage or enforcement. Run the commands yourself and report real exit codes and real output. Read AGENTS.md '
    + 'for the operating contract before you start. Note that a passing verification here does not mean conformance - '
    + 'the recorded baseline registers failing requirements as expected - so do not read exit 0 as evidence of correctness.\n\n'
    + 'CONSTRAINTS: You may not edit, fix, stage, commit, or push anything; an observation authored by a hand that '
    + 'touched the artifact is void. You may not ratify - only Bdo ratifies, and your report supports at most '
    + 'BUILT -> WITNESSED. If you cannot verify a claim, say so plainly rather than assuming it.\n\n'
    + 'Return your verdict, four scores out of 100, findings with severity and exact location and concrete '
    + 'consequence, the commands you actually ran, the conditions that would discharge each blocking finding, what '
    + 'you did NOT examine, and any question only Bdo can answer.'
}

const reports = await parallel(selected.map(function (lens) {
  return function () {
    return agent(attackPrompt(lens), { agentType: 'sov-witness', schema: FINDING_SCHEMA, phase: 'Attack', label: 'witness:' + lens })
  }
}))

phase('Reconcile')

const RANK = { blocking: 0, material: 1, minor: 2 }
const WORST = { 'NOT-YET': 0, 'RATIFIABLE-WITH-CONDITIONS': 1, RATIFIABLE: 2 }

const returned = reports.filter(Boolean)
const silent = selected.filter(function (l, i) { return !reports[i] })

const findings = []
const verified = []
const conditions = []
const uncovered = []
const judgement = []
const axes = { coherence: [], grounding: [], coverage: [], defeat_resistance: [] }
let verdict = 'RATIFIABLE'

returned.forEach(function (r) {
  if (WORST[r.verdict] < WORST[verdict]) { verdict = r.verdict }
  r.findings.forEach(function (f) { findings.push({ lens: r.lens, ...f }) })
  ;(r.verified || []).forEach(function (v) { verified.push(r.lens + ': ' + v) })
  ;(r.conditions || []).forEach(function (c) { conditions.push(c) })
  ;(r.uncovered || []).forEach(function (u) { uncovered.push(r.lens + ': ' + u) })
  ;(r.judgement_items || []).forEach(function (q) { judgement.push(q) })
  Object.keys(axes).forEach(function (k) {
    if (typeof r.scores[k] === 'number') { axes[k].push(r.scores[k]) }
  })
})

// The lowest score on an axis is the axis score. An artifact is as defensible as
// its weakest examined face, and averaging would let four mild lenses bury one
// blocking one.
const scores = {}
Object.keys(axes).forEach(function (k) {
  scores[k] = axes[k].length ? Math.min.apply(null, axes[k]) : null
})

findings.sort(function (a, b) { return (RANK[a.severity] || 9) - (RANK[b.severity] || 9) })
const blocking = findings.filter(function (f) { return f.severity === 'blocking' })

// A lens that returned nothing is not a lens that found nothing.
if (silent.length > 0 && verdict === 'RATIFIABLE') { verdict = 'RATIFIABLE-WITH-CONDITIONS' }

log('Witness complete: ' + verdict + ' - ' + blocking.length + ' blocking, ' + findings.length
  + ' finding(s) total, ' + judgement.length + ' for Bdo'
  + (silent.length ? ', ' + silent.length + ' lens(es) returned nothing' : ''))

return {
  subject: subject,
  record_path: 'witness/' + subject.replace(/_status$/, '').replace(/_/g, '-') + '.md',
  commit: commit,
  verdict: verdict,
  scores: scores,
  blocking_count: blocking.length,
  findings: findings,
  verified: verified,
  conditions: conditions,
  uncovered: uncovered,
  lenses_returning_nothing: silent,
  judgement_queue: judgement,
  standing_note: 'This observation supports at most BUILT -> WITNESSED, and only if the invoking session writes it to '
    + 'record_path. It is not a ratification and it is not a settlement. Only Bdo ratifies. A lens that returned '
    + 'nothing is recorded as uncovered, not as clean.',
}
