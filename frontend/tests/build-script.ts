// A build's events for page tests, shaped as backend/seedfoundry/engine/script.py emits them
// (build-simulation.md sections 2 and 3): the catalogue's 11 phases, sub-step ids and tests,
// iteration 2's feedback sub-steps, sim_t spread over each phase's share of 75 s, and a result
// per phase that a test can choose. By default it is the sample's build from M9 (D-63, D-66):
// iteration 1's Stress & Probe and Harvest Validation complete with findings (L-1; N-1 to N-5 and
// V-1 to V-8, each raised before the result of the test that found it), iteration 2 passes, and
// Compile report emits report.ready.

import type { LabEvent, Level } from '../src/events'
import type { Build, PhasePlan } from '../src/stores/lab'
import type { PhaseResult } from '../src/stepper'

type Row = [id: string, name: string, weight: number, steps: [string, string, number?][], tests: [string, string][]]

const CATALOGUE: Row[] = [
  ['assay', 'Assay', 6, [
    ['feedback-route', 'Route feedback to Ensemble files', 2],
    ['feedback-person', 'Update person.md', 2],
    ['feedback-instrument', 'Update instrument-awareness.md', 2],
    ['feedback-environment', 'Update environment.md', 2],
    ['feedback-music', 'Update music.md', 2],
    ['inventory', 'Inventory files'],
    ['coverage', 'Measure Ensemble coverage per file'],
    ['boundary', 'Ensemble boundary check'],
    ['fingerprint', 'Fingerprint intake'],
  ], [['T-01', 'Core files present'], ['T-02', 'Ensemble coverage'], ['T-03', 'Ensemble boundary check']]],
  ['distill', 'Distillation', 12, [
    ['profile', 'Load model profile from Instrument Awareness'],
    ['budget', 'Plan context budget'],
    ['music', 'Distil Music'],
    ['person', 'Distil Person'],
    ['environment', 'Distil Environment layers'],
    ['context', 'Merge Misc Context'],
    ['feedback', 'Ingest observer feedback and prior findings', 2],
  ], [['T-04', 'All Music sections extracted']]],
  ['synth', 'Synthesis', 10, [['core', 'Draft core.md'], ['adaptation', 'Draft adaptation.md'], ['protection', 'Draft protection.md'], ['manifest', 'Assemble Seed manifest']], [['T-05', 'Manifest schema valid']]],
  ['xexam', 'Cross-Examination', 8, [['core', 'Reviewer pass on core'], ['layers', 'Reviewer pass on adaptation and protection'], ['resolve', 'Resolve contradictions'], ['signoff', 'Sign off drafts']], [['T-06', 'No contradictions between files']]],
  ['germ', 'Germination Trial', 8, [['dry-run', 'Dry run on micro dataset'], ['data-swap', 'Data-swap test on alternate dataset'], ['shape', 'Output shape check']], [['T-07', 'Dry run completes'], ['T-08', 'Data-swap logic unchanged']]],
  ['contain', 'Containment', 7, [['handshake', 'Seed API handshake'], ['sandbox', 'Provision isolated sandbox'], ['upload', 'Upload seed files'], ['checksums', 'Verify upload checksums']], [['T-09', 'Upload checksums match']]],
  ['plant', 'Planting', 8, [['layers', 'Plant the three layers'], ['headings', 'Heading summary per layer'], ['stack', 'List the declared stack']], [['T-10', 'Seed reports ready']]],
  ['seeding', 'Seeding & Life', 16, [['discovery', 'Discovery'], ['assessment', 'Assessment'], ['implementation', 'Implementation'], ['cleanup', 'Cleanup'], ['life', 'Life']], [['T-11', 'All gates resolved'], ['T-12', 'Outputs produced']]],
  ['probe', 'Stress & Probe', 9, [['protection', 'Protection rule probes'], ['malformed', 'Malformed input probes'], ['latency', 'Panel latency measurement']], [['T-13', 'Protection probes'], ['T-14', 'Malformed input rejected'], ['T-15', 'Latency within budget']]],
  ['harvest', 'Harvest Validation', 10, [['collect', 'Collect dashboard payload'], ['numeric', 'Numeric reconciliation'], ['chart', 'Chart and data consistency'], ['visual', 'Visual QA'], ['contrast', 'Contrast check']], [['T-16', 'Numeric reconciliation'], ['T-17', 'Chart fitness'], ['T-18', 'Format and label consistency'], ['T-19', 'Palette and layout'], ['T-20', 'Contrast']]],
  ['report', 'Teardown & Report', 6, [['teardown', 'Tear down sandbox'], ['compile', 'Compile report'], ['package', 'Package seed files']], [['T-21', 'Sandbox torn down cleanly']]],
]

/** D-71: iteration 2's Apply observer feedback summaries, as the real routing of the demo's feedback writes them (D-68). */
const FEEDBACK_SUMMARIES: Record<string, string> = {
  'assay.feedback-route': '9 of 10 segments to 4 files',
  'assay.feedback-person': '+4 lines in Reasoning methods',
  'assay.feedback-instrument': '+4 lines in Model Behaviour',
  'assay.feedback-environment': '+10 lines in Styling; +4 lines in User Experience; +4 lines in Data Layer',
  'assay.feedback-music': '+4 lines in Value Logic',
}

export function plan(iteration = 1): PhasePlan[] {
  return CATALOGUE.map(([id, name, weight, steps, tests]) => ({
    id,
    name,
    weight,
    // A step marked 2 runs in every iteration from 2 on (D-81).
    steps: steps.filter(([, , from]) => from === undefined || iteration >= from).map(([step, stepName]) => ({ id: `${id}.${step}`, name: stepName })),
    tests: tests.map(([test, testName]) => ({ id: test, name: testName })),
  }))
}

export function buildRecord(overrides: Partial<Build> = {}): Build {
  const iteration = overrides.iteration ?? 1
  return {
    id: 'b-1',
    iteration,
    status: 'running',
    seed_name: 'License Optimization',
    fingerprint: 'a127ba',
    phase: null,
    plan: plan(iteration),
    sim_seconds: 75,
    ...overrides,
  }
}

const LEVEL: Record<PhaseResult, Level> = { passed: 'PASS', findings: 'WARN', incomplete: 'TEST', failed: 'FAIL' }

export interface ScriptOptions {
  build?: Build
  /** Seq of build.started. */
  first?: number
  /** Results other than passed, by phase id, over the sample's (iteration 1: probe and harvest findings). */
  results?: Partial<Record<string, PhaseResult>>
  /** A phase to raise one boundary advisory in, which never counts as a finding (D-12). */
  advisoryIn?: string
  /** Iteration 2 on: the feedback sub-steps log what the real routing of the demo's feedback logs (D-83). */
  routing?: boolean
}

type Data = Record<string, unknown>
const placed = (segment: number, file: string, category: string, section: string, matched: string[]): Data => ({ segment, file, category, section, matched })
const updated = (file: string, section: string, segments: number[], lines_added: number): Data => ({ file, section, segments, lines_added, created: false })

/**
 * The routing log lines of the demo's feedback, by sub-step, with the data the backend gives them
 * (engine/script.py feedback_route and feedback_update, D-36, D-83).
 */
export const DEMO_ROUTING: Record<string, [message: string, data: Data][]> = {
  'assay.feedback-route': [
    ['Read observer-feedback-iteration-1.md: 10 segments, 1,812 bytes', { segments: 10, bytes: 1812 }],
    ['Segment 1 to environment.md, Data Layer: totals', placed(1, 'environment.md', 'environment', 'Data Layer', ['totals'])],
    ['Segment 2 to environment.md, Styling: pie, slices', placed(2, 'environment.md', 'environment', 'Styling', ['pie', 'slices'])],
    ['Segment 3 to environment.md, Styling: red', placed(3, 'environment.md', 'environment', 'Styling', ['red'])],
    ['Segment 4 to environment.md, Styling: number formats', placed(4, 'environment.md', 'environment', 'Styling', ['number formats'])],
    ['Segment 5 to environment.md, Styling: misaligned', placed(5, 'environment.md', 'environment', 'Styling', ['misaligned'])],
    ['Segment 6 to environment.md, User Experience: spinner', placed(6, 'environment.md', 'environment', 'User Experience', ['spinner'])],
    ['Segment 7 to instrument-awareness.md, Model Behaviour: language model', placed(7, 'instrument-awareness.md', 'instrument_awareness', 'Model Behaviour', ['language model'])],
    ['Segment 8 to person.md, Reasoning methods: reasoning', placed(8, 'person.md', 'person', 'Reasoning methods', ['reasoning'])],
    ['Segment 9 to music.md, Value Logic: value', placed(9, 'music.md', 'music', 'Value Logic', ['value'])],
    ['Segment 10 kept in observer-feedback-iteration-1.md only: it fits no Ensemble file', { segment: 10, kept: true }],
    ['Routed 9 of 10 segments to 4 files; 1 kept in observer-feedback-iteration-1.md only', { routed: 9, kept: [10], files: 4 }],
  ],
  'assay.feedback-person': [['person.md: +4 lines in Reasoning methods (segment 8)', updated('person.md', 'Reasoning methods', [8], 4)]],
  'assay.feedback-instrument': [['instrument-awareness.md: +4 lines in Model Behaviour (segment 7)', updated('instrument-awareness.md', 'Model Behaviour', [7], 4)]],
  'assay.feedback-environment': [
    ['environment.md: +10 lines in Styling (segments 2, 3, 4, 5)', updated('environment.md', 'Styling', [2, 3, 4, 5], 10)],
    ['environment.md: +4 lines in User Experience (segment 6)', updated('environment.md', 'User Experience', [6], 4)],
    ['environment.md: +4 lines in Data Layer (segment 1)', updated('environment.md', 'Data Layer', [1], 4)],
  ],
  'assay.feedback-music': [['music.md: +4 lines in Value Logic (segment 9)', updated('music.md', 'Value Logic', [9], 4)]],
}

/** The sample's findings by phase, and the tests that find them (D-63). */
export const SAMPLE_FINDINGS: Record<string, [id: string, test: string][]> = {
  probe: [['L-1', 'T-15']],
  harvest: [
    ['N-1', 'T-16'],
    ['N-2', 'T-16'],
    ['N-3', 'T-16'],
    ['N-4', 'T-16'],
    ['N-5', 'T-16'],
    ['V-1', 'T-17'],
    ['V-4', 'T-18'],
    ['V-5', 'T-18'],
    ['V-2', 'T-19'],
    ['V-3', 'T-19'],
    ['V-6', 'T-19'],
    ['V-7', 'T-19'],
    ['V-8', 'T-20'],
  ],
}

/** A test's status in a phase that completes with findings: fail with a high (numeric) finding, warn with medium ones. */
function findingStatus(findings: [string, string][], test: string): 'pass' | 'warn' | 'fail' {
  const own = findings.filter(([, t]) => t === test)
  if (!own.length) return 'pass'
  return own.some(([id]) => id.startsWith('N-')) ? 'fail' : 'warn'
}

/** Every event of a build, in order, as the server streams them. */
export function script(options: ScriptOptions = {}): LabEvent[] {
  const build = options.build ?? buildRecord()
  const results: Partial<Record<string, PhaseResult>> = { ...(build.iteration === 1 ? { probe: 'findings', harvest: 'findings' } : {}), ...options.results }
  const statuses: Record<string, string> = {}
  const raised: string[] = []
  let seq = (options.first ?? 1) - 1
  const events: LabEvent[] = []
  const emit = (type: LabEvent['type'], message: string, extra: Partial<LabEvent> = {}): LabEvent => {
    const event: LabEvent = {
      seq: ++seq,
      build_id: build.id,
      iteration: build.iteration,
      phase: null,
      step: null,
      type,
      level: 'INFO',
      code: null,
      message,
      data: {},
      sim_t: 0,
      wall_ts: '2026-10-03T12:00:00.000+00:00',
      ...extra,
    }
    events.push(event)
    return event
  }
  emit('build.started', `Build started: iteration ${build.iteration}, seed "${build.seed_name}"`, { data: { build: { ...build }, replaces: [] } })
  const phases = build.plan ?? []
  const total = phases.reduce((sum, p) => sum + p.weight, 0)
  let start = 0
  let done = 0
  phases.forEach((phase, index) => {
    const seconds = (75 * phase.weight) / total
    const result = results[phase.id] ?? 'passed'
    // Beats: each step has three (started, a line, completed), and the tests one each.
    const beats = phase.steps.length * 2 + phase.tests.length
    let beat = 0
    const t = () => Math.round((start + (beat / beats) * seconds) * 1000) / 1000
    const at = { phase: phase.id }
    emit('phase.started', `Phase ${index + 1} of ${phases.length}: ${phase.name}`, { ...at, sim_t: t(), data: { index: index + 1, name: phase.name, weight: phase.weight } })
    phase.steps.forEach((step, i) => {
      const inStep = { ...at, step: step.id }
      emit('step.started', step.name, { ...inStep, sim_t: t(), data: { name: step.name } })
      if (i === 1 && phase.id === 'distill') {
        emit('llm.call', `distil ${step.name}: 910 tokens in, 572 out (simulated)`, { ...inStep, level: 'LLM', sim_t: t(), data: { simulated: true } })
      } else if (options.routing && DEMO_ROUTING[step.id]) {
        for (const [message, data] of DEMO_ROUTING[step.id]) emit('log', message, { ...inStep, sim_t: t(), data })
      } else if (step.id === 'contain.handshake') {
        emit('api.call', 'POST /v0.1/seeds 201 (simulated)', { ...inStep, level: 'API', sim_t: t(), data: { simulated: true } })
      } else {
        emit('log', `${step.name}: working`, { ...inStep, sim_t: t() })
      }
      beat++
      if (step.id === 'report.compile') {
        const count = raised.length
        emit('report.ready', `Report compiled: ${count ? `${count} findings across 3 categories; verdict Completed with findings` : '0 findings; verdict Passed'}`, { ...inStep, sim_t: t() })
      }
      if (i === phase.steps.length - 1) {
        const findings = result === 'findings' ? (SAMPLE_FINDINGS[phase.id] ?? [['N-1', phase.tests[0]?.id ?? '']]) : []
        if (options.advisoryIn === phase.id) {
          emit('finding.raised', 'B-UI-1 music.md line 69: "pie chart" belongs in environment.md, Styling (advisory)', { ...inStep, level: 'WARN', code: 'B-UI-1', sim_t: t(), data: { id: 'B-UI-1', advisory: true } })
        }
        for (const test of phase.tests) {
          for (const [id, by] of findings.filter(([, t]) => t === test.id)) {
            raised.push(id)
            const level: Level = id.startsWith('N-') ? 'FAIL' : 'WARN'
            emit('finding.raised', `${id} finding`, { ...inStep, level, code: id, sim_t: t(), data: { id, test: by, phase: phase.id, advisory: false } })
          }
          const status = result === 'incomplete' ? 'not_run' : result === 'failed' ? 'fail' : findingStatus(findings, test.id)
          statuses[test.id] = status
          const level: Level = status === 'pass' ? 'PASS' : status === 'fail' ? 'FAIL' : status === 'warn' ? 'WARN' : 'TEST'
          emit('test.result', `${test.id} ${test.name}: ${status === 'not_run' ? 'not run' : status}`, { ...inStep, level, code: test.id, sim_t: t(), data: { id: test.id, name: test.name, status } })
          beat++
        }
      }
      const summary = FEEDBACK_SUMMARIES[step.id] ?? `${step.name.toLowerCase()} done`
      beat++
      emit('step.completed', `${step.name}: ${summary}`, { ...inStep, sim_t: t(), data: { name: step.name, summary } })
    })
    done += phase.weight
    start = (75 * done) / total
    const tests = Object.fromEntries(phase.tests.map((test) => [test.id, statuses[test.id]]))
    emit('phase.completed', `${phase.name}: ${result}`, { ...at, level: LEVEL[result], sim_t: Math.round(start * 1000) / 1000, data: { index: index + 1, name: phase.name, result, tests } })
  })
  // D-66: every test runs from M9; the sample's iteration 1 passes 15, warns 5 and fails 1 with its 14 findings.
  const all = Object.values(statuses)
  const counts = { pass: 0, warn: 0, fail: 0, not_run: 0 }
  for (const status of all) counts[status as keyof typeof counts]++
  const parts = [`${counts.pass} tests passed`]
  if (counts.warn) parts.push(`${counts.warn} warned`)
  if (counts.fail) parts.push(`${counts.fail} failed`)
  if (counts.not_run) parts.push(`${counts.not_run} not run`)
  const verdict = raised.length ? 'Completed with findings' : 'Passed'
  emit('build.completed', `Build completed: ${parts.join(', ')}; ${raised.length} findings, 0 boundary advisories; verdict ${verdict}`, {
    sim_t: 75,
    data: {
      status: 'completed',
      verdict: { id: raised.length ? 'findings' : 'passed', label: verdict, tone: raised.length ? 'warning' : 'positive' },
      counts,
      findings: raised,
      advisories: options.advisoryIn ? ['B-UI-1'] : [],
      gates: ['servicenow-incident-api', 'solution-approval', 'close-seeding'],
      sim_seconds: 75,
    },
  })
  return events
}

/** Lines the console should show for these events: every event but step.started and step.completed. */
export function expectedLines(events: readonly LabEvent[]): number[] {
  return events.filter((e) => e.type !== 'step.started' && e.type !== 'step.completed').map((e) => e.seq)
}
