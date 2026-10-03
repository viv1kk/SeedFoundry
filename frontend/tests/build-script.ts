// A build's events for page tests, shaped as backend/seedfoundry/engine/script.py emits them
// (build-simulation.md sections 2 and 3): the catalogue's 11 phases, sub-step ids and tests,
// iteration 2's feedback sub-steps, sim_t spread over each phase's share of 75 s, and a result
// per phase that a test can choose (the sample gives only passed and incomplete until M9).

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

export function plan(iteration = 1): PhasePlan[] {
  return CATALOGUE.map(([id, name, weight, steps, tests]) => ({
    id,
    name,
    weight,
    steps: steps.filter(([, , only]) => only === undefined || only === iteration).map(([step, stepName]) => ({ id: `${id}.${step}`, name: stepName })),
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
  /** Results other than passed, by phase id. */
  results?: Partial<Record<string, PhaseResult>>
}

/** Every event of a build, in order, as the server streams them. */
export function script(options: ScriptOptions = {}): LabEvent[] {
  const build = options.build ?? buildRecord()
  const results = options.results ?? {}
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
      } else if (step.id === 'contain.handshake') {
        emit('api.call', 'POST /v0.1/seeds 201 (simulated)', { ...inStep, level: 'API', sim_t: t(), data: { simulated: true } })
      } else {
        emit('log', `${step.name}: working`, { ...inStep, sim_t: t() })
      }
      beat++
      if (i === phase.steps.length - 1) {
        for (const test of phase.tests) {
          const status = result === 'incomplete' ? 'not_run' : result === 'failed' ? 'fail' : 'pass'
          const level: Level = status === 'pass' ? 'PASS' : status === 'fail' ? 'FAIL' : 'TEST'
          emit('test.result', `${test.id} ${test.name}: ${status === 'not_run' ? 'not run, this validator arrives in M9' : status}`, { ...inStep, level, code: test.id, sim_t: t(), data: { id: test.id, name: test.name, status } })
          beat++
        }
        if (result === 'findings') {
          emit('finding.raised', 'N-1 Entitled seats: KPI shows 12,480, product chart sums to 14,976', { ...inStep, level: 'FAIL', code: 'N-1', sim_t: t(), data: { id: 'N-1' } })
          emit('finding.raised', 'B-UI-1 advisory', { ...inStep, level: 'WARN', code: 'B-UI-1', sim_t: t(), data: { id: 'B-UI-1', advisory: true } })
        }
      }
      const summary = step.id.startsWith('assay.feedback-') && step.id !== 'assay.feedback-route' ? 'no change' : `${step.name.toLowerCase()} done`
      beat++
      emit('step.completed', `${step.name}: ${summary}`, { ...inStep, sim_t: t(), data: { name: step.name, summary } })
    })
    done += phase.weight
    start = (75 * done) / total
    const tests = Object.fromEntries(phase.tests.map((test) => [test.id, result === 'incomplete' ? 'not_run' : result === 'failed' ? 'fail' : 'pass']))
    emit('phase.completed', `${phase.name}: ${result}`, { ...at, level: LEVEL[result], sim_t: Math.round(start * 1000) / 1000, data: { index: index + 1, name: phase.name, result, tests } })
  })
  // D-58: T-08 runs from M7, so a sample build passes 13 tests and leaves 8 not run.
  emit('build.completed', 'Build completed: 13 tests passed, 8 not run; 0 findings, 0 boundary advisories', {
    sim_t: 75,
    data: {
      status: 'completed',
      counts: { pass: 13, warn: 0, fail: 0, not_run: 8 },
      findings: [],
      advisories: [],
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
