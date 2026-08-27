export const meta = {
  name: 'sov-coldstart',
  description: 'Run the cold-start awareness benchmark with fresh agents: fetch the answer-stripped paper, answer it cold per section, grade it, and record both readings',
  whenToUse: 'Daily, or after the orientation layer changes (CLAUDE.md, AGENTS.md, STATUS.yaml, the session hooks). Measures two different things and never averages them: whether the corpus still describes the world (INTEGRITY), and what a fresh agent actually knew on arrival (COMPETENCE). Writes run records under reports/coldstart/ so today can be compared with yesterday. Builds nothing and settles nothing.',
  phases: [
    { title: 'Paper', detail: 'fetch the questions with every answer stripped' },
    { title: 'Integrity', detail: 'grade the corpus against the world' },
    { title: 'Answer', detail: 'one fresh agent per section, answering cold' },
    { title: 'Grade', detail: 'score the answers against the probes and record the run' },
  ],
}

// args: { sections?: string[], participant?: string, fast?: boolean, at?: string }

const PAPER_SCHEMA = {
  type: 'object',
  required: ['questions', 'paper', 'run_instant'],
  properties: {
    corpus_digest: { type: 'string' },
    questions: { type: 'integer' },
    run_instant: { type: 'string' },
    paper: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'section', 'tier', 'q'],
        properties: { id: { type: 'string' }, section: { type: 'string' }, tier: { type: 'integer' }, q: { type: 'string' }, answer_shape: { type: 'string' } },
      },
    },
  },
}

const ANSWER_SCHEMA = {
  type: 'object',
  required: ['answers', 'read_any_file'],
  properties: {
    answers: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'value', 'conf'],
        properties: { id: { type: 'string' }, value: { type: 'string' }, conf: { enum: ['high', 'medium', 'low'] } },
      },
    },
    read_any_file: { type: 'boolean' },
  },
}

const CONFIRM_SCHEMA = {
  type: 'object',
  required: ['found', 'verdict', 'standing', 'defect_codes'],
  properties: {
    found: { type: 'boolean' },
    verdict: { type: 'string', minLength: 1 },
    standing: { type: 'string', minLength: 1 },
    mode: { type: 'string', minLength: 1 },
    corpus_digest: { type: 'string' },
    tier_zero: { type: 'string' },
    defect_codes: { type: 'array', items: { type: 'string' } },
  },
}

const CARD_SCHEMA = {
  type: 'object',
  required: ['exit_code', 'verdict', 'record_path'],
  properties: {
    exit_code: { type: 'integer' },
    verdict: { type: 'string' },
    record_path: { type: 'string' },
    tier_zero: { type: 'string' },
    wrong_ids: { type: 'array', items: { type: 'string' } },
    notes: { type: 'array', items: { type: 'string' } },
  },
}

const DRIFT_SCHEMA = {
  type: 'object',
  required: ['exit_code', 'verdict', 'record_path', 'drift'],
  properties: {
    exit_code: { type: 'integer' },
    verdict: { type: 'string' },
    record_path: { type: 'string' },
    drift: { type: 'array', items: { type: 'string' } },
    errors: { type: 'array', items: { type: 'string' } },
  },
}

const participant = (args && args.participant) || 'unattributed-agent'
// Every run must be stamped with a real instant. It used to fall back to the literal string
// `today`, so the answers file had the same name every day, day two overwrote day one, and
// day one's record - which digests the file it graded - was permanently invalidated. The
// daily cadence is the only reason records exist.
//
// A workflow script cannot read a clock: Date.now() throws here, deliberately, so a resumed
// run replays identically. The schedule runner substitutes nothing into args either. So the
// paper agent reads the clock and returns it, and args.at overrides that when a caller wants
// to replay a specific instant.
const fastFlag = args && args.fast ? ' --fast --offline' : ''
const requested = args && Array.isArray(args.sections) && args.sections.length > 0 ? args.sections : null
// The grade has to be told which sections were asked, or the record claims full coverage
// for a partial run and `records.comparable` cannot refuse the diff it exists to refuse.
const sectionFlags = requested ? requested.map(function (s) { return ' --section ' + s }).join('') : ''
phase('Paper')

const paper = await agent(
  'Run exactly this from the repository root and return what it printed, parsed: '
  + 'python scripts/sov_coldstart.py paper' + "

"
  + 'That command emits the benchmark questions with every answer, probe and rationale stripped out. '
  + 'Do not open scripts/sovcoldstart/corpus.json, and do not answer any of the questions - you are fetching the paper, not sitting it. '
  + 'Then run: python -c "import datetime; print(datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat())" '
  + 'and return that as run_instant. This workflow cannot read a clock itself and every run has to be stamped, or each day overwrites the previous day\'s answers file. '
  + 'Return corpus_digest, questions (the count), paper (the array, verbatim and complete), and run_instant.',
  { agentType: 'general-purpose', schema: PAPER_SCHEMA, phase: 'Paper', label: 'fetch:paper' }
)

if (!paper || !paper.paper || paper.paper.length === 0) {
  return { error: 'the paper could not be fetched; nothing was measured' }
}

const stamp = (args && args.at) || paper.run_instant
if (!stamp || !/^\d{4}-\d{2}-\d{2}T/.test(stamp)) {
  return { error: 'no run instant: pass args.at as an ISO instant (2026-08-27T06:30:00Z). Without one every run writes the same answers file and invalidates the previous day\'s record.' }
}
const atFlag = ' --at ' + stamp
const answersPath = 'reports/coldstart/answers/' + stamp.slice(0, 10) + '-' + participant.replace(/[^a-zA-Z0-9-]/g, '-') + '.json'

const bySection = {}
paper.paper.forEach(function (q) {
  if (requested && requested.indexOf(q.section) === -1) return
  if (!bySection[q.section]) bySection[q.section] = []
  bySection[q.section].push(q)
})
const sections = Object.keys(bySection).sort()

log('paper: ' + paper.questions + ' question(s), answering ' + sections.length + ' section(s) cold')

phase('Integrity')

// Runs alongside the answering agents. It reads the repository on purpose: this is the
// reading that asks whether the corpus still describes the world.
const integrityRun = agent(
  'Run exactly this from the repository root: '
  + 'python scripts/sov_coldstart.py' + fastFlag + sectionFlags + ' --record' + atFlag + ' run' + "

"
  + 'Report the real exit code, the VERDICT line, the path the run recorded (the line beginning "recorded "), '
  + 'every DRIFT line as "<id>: expected <x> / probe <y>", and every ERROR line. '
  + 'Do not repair anything, do not rebase any expectation, and do not edit the corpus. '
  + 'DRIFT means the corpus and the world disagree and someone has to decide which is wrong; that decision is not yours.',
  { agentType: 'general-purpose', schema: DRIFT_SCHEMA, phase: 'Integrity', label: 'integrity' }
)

phase('Answer')

function sitPrompt(section, questions) {
  return 'You are sitting a cold-start awareness benchmark for the Soveraeign repository. This measures what you know on arrival.\n\n'
    + 'RULES. Answer only from what you already know from the orientation you were given when this session started - CLAUDE.md, AGENTS.md, and any session briefing. '
    + 'Do NOT read, open, grep, search, list or run anything against the repository. Do not open scripts/sovcoldstart/corpus.json under any circumstances; it contains the answers, and reading it makes the measurement worthless. '
    + 'Answer UNKNOWN whenever you do not know. UNKNOWN scores as ABSTAIN, which is explicitly not the same as WRONG - a confident wrong answer is the exact failure this benchmark exists to catch, and abstaining costs you far less than guessing.\n\n'
    + 'Set conf to high, medium or low honestly. Set read_any_file to true if you opened any repository file at all; answering that honestly matters more than the score.\n\n'
    + 'Section: ' + section + '. Answer every question. Return one entry per id.\n\n'
    + JSON.stringify(questions, null, 1)
}

const sat = await parallel(sections.map(function (section) {
  return function () {
    return agent(sitPrompt(section, bySection[section]), {
      agentType: 'general-purpose', schema: ANSWER_SCHEMA, phase: 'Answer', label: 'sit:' + section,
    })
  }
}))

const answers = []
const contaminated = []
sections.forEach(function (section, i) {
  const result = sat[i]
  if (!result) return
  if (result.read_any_file) contaminated.push(section)
  result.answers.forEach(function (a) { answers.push(a) })
})

log('answered ' + answers.length + ' of ' + paper.questions + ' question(s)'
  + (contaminated.length ? '; ' + contaminated.length + ' section(s) self-reported reading a file' : ''))

phase('Grade')

const submission = {
  baseline_id: 'coldstart-' + stamp.slice(0, 10) + '-' + participant,
  participant: participant,
  binding: 'claude-code',
  captured_at: stamp,
  method: 'Answered by fresh agents launched from the sov-coldstart workflow, one per section, '
    + 'each handed the answer-stripped paper in its prompt and instructed not to read any repository file. '
    + 'Compliance is self-reported in read_any_file and is not enforced.',
  // Carried into the submission, not just into this run's return value: the submission is
  // the file the record digests, so this is the only place a later reader can find out
  // whether a section admitted reading the tree or how sure it was.
  self_reported_contamination: contaminated,
  confidence: answers.reduce(function (acc, a) { acc[a.conf] = (acc[a.conf] || 0) + 1; return acc }, {}),
  answers: answers,
}

const graded = answers.length === 0 ? null : await agent(
  'Write this JSON verbatim to ' + answersPath + ' (create the directory if needed), then run exactly:\n'
  + 'python scripts/sov_coldstart.py' + fastFlag + sectionFlags + ' --record' + atFlag + ' grade ' + answersPath + '\n\n'
  + 'Report the real exit code, the VERDICT line, the recorded record path, the TIER 0 line verbatim, and the ids marked WRONG. '
  + 'Do not pass --owner-verdicts and do not write a verdict file: the hand-graded questions are meant to read UNGRADED until an owner grades them, and manufacturing that file would be the participant settling its own output. '
  + 'Do not edit the corpus, do not rebase anything, and do not change any answer.\n\n'
  + JSON.stringify(submission, null, 1),
  { agentType: 'general-purpose', schema: CARD_SCHEMA, phase: 'Grade', label: 'grade:' + participant }
)

const integrity = await integrityRun

// D9: the grading agent reported its own result and the record it wrote went unread. A
// separate reader opens the contract-graded file, so what this workflow returns comes from
// the artifact rather than from the participant that made it.
// The path comes from the agent being checked, so it is constrained before it is used: a
// run record lives under reports/coldstart/ and nowhere else.
const recordPath = graded && typeof graded.record_path === 'string'
  && graded.record_path.indexOf('reports/coldstart/') === 0
  && graded.record_path.indexOf('..') === -1 ? graded.record_path : null

const confirmed = recordPath ? await agent(
  'Read the JSON file at ' + recordPath + ' and return exactly what it contains: '
  + 'verdict, standing, mode, the corpus digest, and the tier 0 row as hit/scored. '
  + "

Then run: python scripts/sov_coldstart.py history

"
  + 'You did not produce this record and you must not edit it, re-run the benchmark, or '
  + 'repair anything. If the file is not there, say so; if history flags it with a defect '
  + 'code, report the code. Do not report what you expected to find.',
  { agentType: 'sov-witness', schema: CONFIRM_SCHEMA, phase: 'Grade', label: 'read-back' }
) : null

// The five verdicts a run record may carry. An agent reports prose, so its report is
// reduced to one of these before comparison, and anything else compares as itself.
const VERDICTS = ['NOT_ADMISSIBLE', 'ADMISSIBLE', 'DEGRADED', 'UNPROVEN', 'PARTIAL']
// Whole tokens. The first version scanned for substrings in a lucky order, so prose naming
// two verdicts resolved to whichever came first in the array rather than to what it meant,
// and "ok" agreed with "ok" although neither is a verdict. An agent reports prose, so the
// prose is split into words and the words are looked up.
function verdictToken(text) {
  const words = String(text).toUpperCase().split(/[^A-Z_]+/).filter(function (w) { return w })
  const found = words.filter(function (w) { return VERDICTS.indexOf(w) !== -1 })
  if (found.length === 1) { return found[0] }
  if (found.length > 1) { return 'AMBIGUOUS:' + found.join('+') }
  return 'NOT_A_VERDICT:' + String(text).trim().slice(0, 40)
}

// Gathering an independent reading and not comparing it to the report it checks is the same
// as not taking one. This is the comparison.
const disagreements = []
if (graded && !recordPath) {
  disagreements.push('the grading agent named a record path outside reports/coldstart/: ' + (graded.record_path || 'none'))
}
if (graded && confirmed) {
  if (!confirmed.found) { disagreements.push('the record the grading agent named is not on disk') }
  // Whole tokens, never a substring: "NOT_ADMISSIBLE".indexOf("ADMISSIBLE") is 4, so the
  // first version of this check could not tell the two apart. CLAUDE.md records that shape
  // as trap T3, and it landed here in the one check whose purpose is independence.
  // Each of these used to be guarded by the field being non-empty, so an empty string from
  // the party being checked switched the check off.
  const onDisk = verdictToken(confirmed.verdict)
  const reported = verdictToken(graded.verdict)
  if (VERDICTS.indexOf(onDisk) === -1) {
    disagreements.push('the record does not state one of the five verdicts: ' + onDisk)
  }
  if (onDisk !== reported) {
    disagreements.push('verdict: the record says ' + confirmed.verdict + ', the grading agent reported ' + graded.verdict)
  }
  if (confirmed.standing !== 'BUILT') {
    disagreements.push('the record states standing ' + (confirmed.standing || '(none)') + ', which a benchmark run may never do')
  }
  if (!Array.isArray(confirmed.defect_codes)) {
    disagreements.push('the read-back reported no defect_codes array, so nothing says whether the record grades clean')
  }
  if (confirmed.corpus_digest && paper.corpus_digest && confirmed.corpus_digest !== paper.corpus_digest) {
    disagreements.push('corpus digest: the record was graded against ' + confirmed.corpus_digest + ', the paper came from ' + paper.corpus_digest)
  }
  if (Array.isArray(confirmed.defect_codes) && confirmed.defect_codes.length > 0) {
    disagreements.push('the recorded run carries defect code(s): ' + confirmed.defect_codes.join(', '))
  }
}
if (disagreements.length) {
  log('read-back disagrees with the grading agent on ' + disagreements.length + ' point(s)')
}

return {
  participant: participant,
  corpus_digest: paper.corpus_digest,
  sections: sections,
  integrity: integrity || { error: 'the integrity run returned nothing' },
  competence: graded || { error: 'no answers were produced; nothing was graded' },
  competence_record_read_back: confirmed || { error: 'no record was read back' },
  read_back_disagreements: disagreements,
  answers_written_to: answers.length ? answersPath : null,
  self_reported_contamination: contaminated,
  standing: 'BUILT',
  caveats: [
    'A benchmark cannot witness the participant that ran it. Both readings establish BUILT and settle nothing.',
    'competence_record_read_back is a separate reader opening the file on disk. Everything under competence is the grading agent describing its own run. The two are compared: read_back_disagreements is empty only when the record on disk says what the grading agent said it said.',
    'The corpus ships its expected answers inside the repository under test. The paper strips them from the prompt; it cannot stop an agent opening the file.',
    'Hand-graded questions read UNGRADED without a separate owner verdict file, so a COMPETENCE verdict of UNPROVEN is the normal unattended result, not a fault.',
  ],
}
