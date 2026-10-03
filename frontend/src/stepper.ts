// The Build page's stepper, header and console, derived from the build record and its events
// alone (FR-B-3, FR-B-4, NFR-1, D-54). Times come from sim_t, never from a clock, so the page
// reads the same at any speed (FR-DC-4).

import type { LabEvent, Level } from './events'
import type { Build, PhasePlan } from './stores/lab'

/** How a phase ended (D-51): `phase.completed` data.result. */
export type PhaseResult = 'passed' | 'findings' | 'incomplete' | 'failed'

/**
 * pending, active, done (with a result), or stopped: the phase that was running when the build
 * was interrupted (D-33). A phase of an interrupted build that ran but whose events were lost
 * in a restart is done with no result.
 */
export type PhaseState = 'pending' | 'active' | 'done' | 'stopped'

export type StepState = 'pending' | 'active' | 'done' | 'stopped'

export interface StepView {
  id: string
  name: string
  state: StepState
  /** The `step.completed` summary. */
  summary: string | null
  /** Iteration 2's "Apply observer feedback" sub-steps (FR-RB-8). */
  feedback: boolean
}

export interface PhaseView {
  id: string
  name: string
  /** 1-based, as the log says "Phase 3 of 11". */
  index: number
  state: PhaseState
  result: PhaseResult | null
  /** Findings raised in the phase, advisories aside (they never change a result, D-12). */
  findings: number
  tests: number
  notRun: number
  failedTests: string[]
  /** Simulated seconds from phase.started to phase.completed. */
  duration: number | null
  steps: StepView[]
}

/** Sub-step ids of iteration 2's "Apply observer feedback" group (build-simulation.md section 9). */
export const FEEDBACK_PREFIX = 'assay.feedback-'

export function derivePhases(build: Build, events: readonly LabEvent[]): PhaseView[] {
  const plan: PhasePlan[] = build.plan ?? []
  const phases = plan.map<PhaseView>((phase, i) => ({
    id: phase.id,
    name: phase.name,
    index: i + 1,
    state: 'pending',
    result: null,
    findings: 0,
    tests: phase.tests.length,
    notRun: 0,
    failedTests: [],
    duration: null,
    steps: phase.steps.map((step) => ({
      id: step.id,
      name: step.name,
      state: 'pending',
      summary: null,
      feedback: step.id.startsWith(FEEDBACK_PREFIX),
    })),
  }))
  const byId = new Map(phases.map((phase) => [phase.id, phase]))
  const started = new Map<string, number>()

  for (const event of events) {
    const phase = event.phase ? byId.get(event.phase) : undefined
    if (!phase) continue
    const step = event.step ? phase.steps.find((s) => s.id === event.step) : undefined
    switch (event.type) {
      case 'phase.started':
        phase.state = 'active'
        started.set(phase.id, event.sim_t ?? 0)
        break
      case 'step.started':
        if (step) step.state = 'active'
        break
      case 'step.completed':
        if (step) {
          step.state = 'done'
          step.summary = typeof event.data.summary === 'string' && event.data.summary ? event.data.summary : null
        }
        break
      case 'finding.raised':
        if (!event.data.advisory) phase.findings++
        break
      case 'phase.completed': {
        phase.state = 'done'
        phase.result = isResult(event.data.result) ? event.data.result : 'passed'
        const tests = event.data.tests && typeof event.data.tests === 'object' ? (event.data.tests as Record<string, string>) : {}
        const statuses = Object.entries(tests)
        if (statuses.length) phase.tests = statuses.length
        phase.notRun = statuses.filter(([, status]) => status === 'not_run').length
        phase.failedTests = statuses.filter(([, status]) => status === 'fail').map(([id]) => id)
        const from = started.get(phase.id)
        if (from !== undefined && event.sim_t !== null) phase.duration = event.sim_t - from
        break
      }
    }
  }

  if (build.status === 'interrupted') {
    // An interrupted build: what was running stopped, and a phase before the one it stopped in
    // ran even when its events did not survive a restart (D-49 keeps no log for it).
    const last = Math.max(
      plan.findIndex((phase) => phase.id === build.phase),
      ...phases.map((phase, i) => (phase.state === 'pending' ? -1 : i)),
    )
    phases.forEach((phase, i) => {
      if (phase.state === 'active' || (phase.state === 'pending' && i === last)) phase.state = 'stopped'
      else if (phase.state === 'pending' && i < last) phase.state = 'done'
      for (const step of phase.steps) if (step.state === 'active') step.state = 'stopped'
    })
  }
  return phases
}

function isResult(value: unknown): value is PhaseResult {
  return value === 'passed' || value === 'findings' || value === 'incomplete' || value === 'failed'
}

/** Simulated seconds reached: the latest sim_t held. */
export function elapsed(events: readonly LabEvent[]): number {
  let latest = 0
  for (const event of events) if (event.sim_t !== null && event.sim_t > latest) latest = event.sim_t
  return latest
}

/** 0 to 1: sim_t over the build's simulated length (D-54), or done phases' weight without it. */
export function progress(build: Build, phases: readonly PhaseView[], seconds: number): number {
  if (build.status === 'completed') return 1
  if (build.sim_seconds) return Math.min(1, seconds / build.sim_seconds)
  const plan = build.plan ?? []
  const total = plan.reduce((sum, phase) => sum + phase.weight, 0)
  const done = plan.reduce((sum, phase, i) => sum + (phases[i]?.state === 'done' ? phase.weight : 0), 0)
  return total ? done / total : 0
}

const pad = (value: number) => String(value).padStart(2, '0')

/** mm:ss, for the header. */
export function clock(seconds: number): string {
  const whole = Math.floor(seconds + 1e-6)
  return `${pad(Math.floor(whole / 60))}:${pad(whole % 60)}`
}

/** mm:ss.s, for log lines (build-simulation.md section 4). A tenth is never rounded up. */
export function stamp(seconds: number | null): string {
  if (seconds === null) return '--:--.-'
  const tenths = Math.floor(seconds * 10 + 1e-6)
  return `${clock(Math.floor(tenths / 10))}.${tenths % 10}`
}

/** "4.5 s" */
export function duration(seconds: number): string {
  return `${(Math.round(seconds * 10) / 10).toFixed(1)} s`
}

// Console

/**
 * Event types that are not console lines: the stepper shows a sub-step starting and its
 * summary, so lines for them would repeat it (D-54). Every other build event is one line.
 */
export const NOT_LINES = new Set<string>(['step.started', 'step.completed'])

export interface ConsoleLine {
  seq: number
  time: string
  level: Level
  message: string
}

export function consoleLines(events: readonly LabEvent[]): ConsoleLine[] {
  return events
    .filter((event) => !NOT_LINES.has(event.type))
    .map((event) => ({ seq: event.seq, time: stamp(event.sim_t), level: event.level, message: event.message }))
}

/**
 * The console's level filter (ui-spec.md section 3, D-54). TEST also shows PASS, as a pass is a
 * test's outcome; INFO shows only under All.
 */
export const FILTERS = [
  { id: 'all', label: 'All', levels: null },
  { id: 'LLM', label: 'LLM', levels: ['LLM'] },
  { id: 'API', label: 'API', levels: ['API'] },
  { id: 'TEST', label: 'TEST', levels: ['TEST', 'PASS'] },
  { id: 'WARN', label: 'WARN', levels: ['WARN'] },
  { id: 'FAIL', label: 'FAIL', levels: ['FAIL'] },
] as const satisfies readonly { id: string; label: string; levels: readonly Level[] | null }[]

export type FilterId = (typeof FILTERS)[number]['id']

export function filterLines(lines: readonly ConsoleLine[], filter: FilterId): readonly ConsoleLine[] {
  const levels: readonly Level[] | null = FILTERS.find((f) => f.id === filter)?.levels ?? null
  return levels ? lines.filter((line) => levels.includes(line.level)) : lines
}
