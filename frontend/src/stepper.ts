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

// Feedback routing (FR-RB-8, D-83)

/** The Ensemble files, by their Update sub-step, in plan order, with their screen category. */
const FEEDBACK_FILES = [
  { step: 'assay.feedback-person', id: 'person', category: 'Person' },
  { step: 'assay.feedback-instrument', id: 'instrument_awareness', category: 'Instrument Awareness' },
  { step: 'assay.feedback-environment', id: 'environment', category: 'Environment' },
  { step: 'assay.feedback-music', id: 'music', category: 'Music' },
] as const

export interface RoutedSection {
  section: string
  segments: number[]
  lines: number
  created: boolean
}

export interface RoutedFile {
  step: string
  /** The intake category id (`person`, `instrument_awareness`, ...). */
  id: string
  /** The file's name as the build logged it, else from its sub-step ("Update person.md"). */
  name: string
  category: string
  /** pending until the routing names a segment for it; then its Update sub-step's state. */
  state: StepState
  /** Segments the routing sent here, in order, as soon as the routing decides. */
  segments: number[]
  /** What the Update sub-step added, section by section, as it plays. */
  sections: RoutedSection[]
}

export interface FeedbackRouting {
  /** The feedback file this build routes: observer-feedback-iteration-<n - 1>.md. */
  feedback: string
  /** The routing sub-step's state. */
  state: StepState
  /** Segments in the feedback, once read. */
  total: number | null
  /** Every placement so far, in segment order: a file and section, or kept in the feedback file. */
  placements: { segment: number; file: string | null; section: string | null; matched: string[] }[]
  files: RoutedFile[]
  /** Segments that fit no Ensemble file and stay in the feedback file only. */
  kept: number[]
}

/**
 * Where the observer feedback goes, for the Build page's panel (D-83): the routing's decisions and
 * each core file's update, from the build's events alone, so it fills in as the sub-steps play and
 * reads the same after a refresh. Null for a build with no feedback sub-steps (iteration 1).
 */
export function feedbackRouting(build: Build, events: readonly LabEvent[]): FeedbackRouting | null {
  const steps = (build.plan ?? []).flatMap((phase) => phase.steps)
  if (!steps.some((step) => step.id.startsWith(FEEDBACK_PREFIX))) return null
  const routeStep = `${FEEDBACK_PREFIX}route`
  const view: FeedbackRouting = {
    feedback: `observer-feedback-iteration-${Math.max(1, build.iteration - 1)}.md`,
    state: 'pending',
    total: null,
    placements: [],
    files: FEEDBACK_FILES.map(({ step, id, category }) => ({
      step,
      id,
      name: steps.find((s) => s.id === step)?.name.replace(/^Update /, '') ?? category,
      category,
      state: 'pending' as StepState,
      segments: [],
      sections: [],
    })),
    kept: [],
  }
  const byStep = new Map(view.files.map((file) => [file.step, file]))
  const states = new Map<string, StepState>()
  const numbers = (value: unknown) => (Array.isArray(value) ? value.filter((n): n is number => typeof n === 'number') : [])

  for (const event of events) {
    const step = event.step ?? ''
    if (!step.startsWith(FEEDBACK_PREFIX)) continue
    if (event.type === 'step.started') states.set(step, 'active')
    else if (event.type === 'step.completed') states.set(step, 'done')
    else if (event.type !== 'log') continue
    const data = event.data ?? {}
    if (step === routeStep) {
      if (typeof data.segments === 'number' && typeof data.bytes === 'number') view.total = data.segments
      if (typeof data.segment === 'number') {
        if (data.kept) {
          view.kept.push(data.segment)
          view.placements.push({ segment: data.segment, file: null, section: null, matched: [] })
        } else if (typeof data.file === 'string') {
          const section = typeof data.section === 'string' ? data.section : null
          const matched = Array.isArray(data.matched) ? data.matched.filter((m): m is string => typeof m === 'string') : []
          view.placements.push({ segment: data.segment, file: data.file, section, matched })
          const target = view.files.find((f) => f.id === data.category) ?? view.files.find((f) => f.name === data.file)
          if (target) {
            target.name = data.file
            if (!target.segments.includes(data.segment)) target.segments.push(data.segment)
          }
        }
      }
      continue
    }
    const file = byStep.get(step)
    if (!file) continue
    if (typeof data.file === 'string') file.name = data.file
    const added = numbers(data.segments)
    if (typeof data.section === 'string' && added.length && typeof data.lines_added === 'number' && data.lines_added > 0) {
      file.sections.push({ section: data.section, segments: added, lines: data.lines_added, created: Boolean(data.created) })
    }
  }
  view.state = states.get(routeStep) ?? 'pending'
  for (const file of view.files) file.state = states.get(file.step) ?? 'pending'
  if (build.status === 'interrupted') {
    if (view.state === 'active') view.state = 'stopped'
    for (const file of view.files) if (file.state === 'active') file.state = 'stopped'
  }
  return view
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
