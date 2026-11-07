export const meta = {
  name: 'panel',
  description: 'Run istack workers in Herdr, then verify each report, cross-judge, or synthesize them',
  whenToUse: 'Called by the istack swarm, arena, interrogate, how, why and reflect skills with their framed args',
  phases: [
    { title: 'Fan out', detail: 'one Herdr worker per brief, each retried once without a report' },
    { title: 'Verify', detail: 'rerun every finding a worker reports' },
    { title: 'Judge', detail: 'one judge from a model family other than the parent' },
    { title: 'Synthesize', detail: 'one synthesizer over every report' },
  ],
}

// args: {
//   dir, cwd, roles (output of `istack-worker roles --json`), parentFamily (default 'claude'),
//   workers: [{ name, role, seat?, cwd?, brief? | briefText?, effort?, claude? }],
//   verify?: { instructions },          // per report: rerun its findings, keep the reproduced ones
//   judge?: { role, briefText },        // after all workers: one judge from another family
//   synthesize?: { role, briefText, claude? },  // after all workers: one synthesizer
// }

const OUTCOME = {
  type: 'object',
  properties: {
    name: { type: 'string' }, status: { type: 'string' }, report: { type: 'string' },
    spec: { type: 'string' }, family: { type: 'string' }, tail: { type: 'string' },
  },
  required: ['name', 'status', 'report'],
}
const FINDINGS = {
  type: 'object',
  properties: {
    verified: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, command: { type: 'string' }, output: { type: 'string' },
      expected: { type: 'string' }, breaks: { type: 'string' },
    }, required: ['title', 'command', 'output', 'expected', 'breaks'] } },
    dropped: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, reason: { type: 'string' },
    }, required: ['title', 'reason'] } },
  },
  required: ['verified', 'dropped'],
}
const RETRYABLE = ['no-report', 'exited', 'failed']

const quote = text => `'${String(text).replace(/'/g, `'\\''`)}'`
const reportPath = name => `${args.dir}/${name}.md`

function relayWorker(worker, phaseTitle) {
  const report = worker.report || reportPath(worker.name)
  const flags = [
    `--role ${quote(worker.role)}`, `--seat ${worker.seat || 0}`, `--name ${quote(worker.name)}`,
    `--cwd ${quote(worker.cwd || args.cwd)}`,
    worker.brief ? `--brief ${quote(worker.brief)}` : `--brief-text ${quote(worker.briefText)}`,
    `--report ${quote(report)}`, '--quiet', '--max-seconds 540',
    worker.effort ? `--effort ${worker.effort}` : '', worker.claude ? '--claude' : '',
  ].filter(Boolean).join(' ')
  return agent(`You relay one istack worker. Use only the Bash tool, with timeout 600000 on every call. Run only the commands below and write no files: your returned fields are your whole output.
1. Run exactly: istack-worker run ${flags}
2. It prints one JSON line. While that JSON has "status": "working", run: istack-worker wait --name <the JSON's name> --report ${quote(report)} --max-seconds 540
3. Return the fields of the last JSON line. If a command printed {"error": ...} instead, return name ${quote(worker.name)}, status "failed", report ${quote(report)}, and the error text as tail.`,
    { label: worker.name, phase: phaseTitle, model: 'haiku', effort: 'low', schema: OUTCOME })
}

async function runWorker(worker, phaseTitle) {
  const first = await relayWorker(worker, phaseTitle)
  if (first && !RETRYABLE.includes(first.status)) return first
  log(`${worker.name}: ${first ? first.status : 'no result'}, retrying once`)
  const second = await relayWorker({ ...worker, name: `${worker.name}-r`, report: reportPath(worker.name) }, phaseTitle)
  return second || first || { name: worker.name, status: 'failed', report: reportPath(worker.name) }
}

function listReports(outcomes) {
  const done = outcomes.filter(outcome => outcome.status === 'done')
  const gaps = outcomes.filter(outcome => outcome.status !== 'done')
  return [
    'Reports:', ...done.map(outcome => `- ${outcome.name} (${outcome.spec || 'unknown model'}): ${outcome.report}`),
    gaps.length ? 'Missing reports, name each as a gap:' : '', ...gaps.map(outcome => `- ${outcome.name}: ${outcome.status}`),
  ].filter(Boolean).join('\n')
}

async function runJudgment(step, seatIndex, name, phaseTitle) {
  const seat = args.roles[step.role].seats[seatIndex]
  const briefText = `${step.briefText}\n\n${listReports(outcomes)}`
  if (seat.harness !== 'claude' || step.claude) {
    return runWorker({ name, role: step.role, seat: seatIndex, briefText, claude: step.claude }, phaseTitle)
  }
  const report = reportPath(name)
  const options = { label: name, phase: phaseTitle }
  if (seat.model) options.model = seat.model
  if (seat.effort) options.effort = seat.effort
  await agent(`${briefText}\n\nWrite your complete output to ${report} in one write. Return only that path.`, options)
  return { name, status: 'done', report, spec: seat.spec, family: seat.family }
}

phase('Fan out')
const verifyReport = async (outcome, worker) => {
  if (!args.verify || !outcome || outcome.status !== 'done') return { outcome, findings: null }
  const findings = await agent(`Verify an adversary's findings by running them. Instructions: ${args.verify.instructions}
The adversary's report: ${outcome.report}. Its worktree: ${worker.cwd || args.cwd}.
Rerun each finding's command in that worktree. Keep a finding only when the output you see shows the failure and that failure breaks the stated intent. Put every other finding in dropped with the reason.`,
    { label: `verify ${outcome.name}`, phase: 'Verify', schema: FINDINGS })
  return { outcome, findings }
}
const results = await pipeline(args.workers, worker => runWorker(worker, 'Fan out'), verifyReport)
const outcomes = results.filter(Boolean).map(result => result.outcome).filter(Boolean)
log(`${outcomes.filter(outcome => outcome.status === 'done').length} of ${args.workers.length} workers reported`)

let judge = null
if (args.judge) {
  phase('Judge')
  const parentFamily = args.parentFamily || 'claude'
  const seats = args.roles[args.judge.role].seats
  const seatIndex = seats.findIndex(seat => seat.family !== parentFamily)
  if (seatIndex === -1) log(`judge skipped: every ${args.judge.role} seat is the ${parentFamily} family`)
  else judge = await runJudgment(args.judge, seatIndex, 'judge', 'Judge')
}

let synthesis = null
if (args.synthesize) {
  phase('Synthesize')
  synthesis = await runJudgment(args.synthesize, 0, 'synthesis', 'Synthesize')
}

return {
  workers: outcomes,
  gaps: outcomes.filter(outcome => outcome.status !== 'done').map(outcome => `${outcome.name}: ${outcome.status}`),
  findings: results.filter(result => result && result.findings).map(result => ({ worker: result.outcome.name, ...result.findings })),
  judge,
  synthesis,
}
