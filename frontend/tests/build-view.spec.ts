// The Build page (ui-spec.md section 3, FR-B-3 to FR-B-9, FR-RB-8, AC-7, D-54), against
// tests/fake-server.ts and a fake event stream. D-54 (h): this file held the M5 placeholder's
// tests (OQ-18) until M6 replaced the placeholder.

import { mount, type VueWrapper } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, type Router } from 'vue-router'
import App from '../src/App.vue'
import type { LabEvent } from '../src/events'
import { createAppRouter } from '../src/router'
import { derivePhases } from '../src/stepper'
import { useLabStore, type Build } from '../src/stores/lab'
import { buildRecord, expectedLines, script } from './build-script'
import { FakeServer } from './fake-server'

class FakeEventSource {
  static last: FakeEventSource | null = null
  url: string
  listeners = new Map<string, (message: MessageEvent) => void>()
  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
  constructor(url: string) {
    this.url = url
    FakeEventSource.last = this
  }
  addEventListener(type: string, listener: (message: MessageEvent) => void) {
    this.listeners.set(type, listener)
  }
  close() {}
  emit(event: { type: string }) {
    this.listeners.get(event.type)?.({ data: JSON.stringify(event) } as MessageEvent)
  }
}

let server: FakeServer
let wrapper: VueWrapper
let router: Router
/** Requests for a build's events wait here while `holding` is set. */
let holding = false
let held: (() => void)[] = []

async function settle(times = 4): Promise<void> {
  for (let i = 0; i < times; i++) await new Promise((r) => setTimeout(r))
}

beforeEach(() => {
  server = new FakeServer()
  holding = false
  held = []
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    if (holding && String(input).endsWith('/events')) await new Promise<void>((go) => held.push(go))
    return server.fetch(input, init)
  })
  vi.stubGlobal('EventSource', FakeEventSource)
  FakeEventSource.last = null
})

afterEach(() => {
  wrapper?.unmount()
  vi.unstubAllGlobals()
  document.body.innerHTML = ''
})

/** Open a page as main.ts does: mount, then connect to the (fake) server. */
async function open(path: string): Promise<void> {
  const pinia = createPinia()
  setActivePinia(pinia)
  router = createAppRouter(createMemoryHistory())
  await router.push(path)
  await router.isReady()
  wrapper = mount(App, { global: { plugins: [pinia, router] }, attachTo: document.body })
  await useLabStore().connect()
  await settle()
}

/** The server as it stands after these events of one build. */
function serverAt(events: LabEvent[], build: Build, upTo = events.length): void {
  const held = events.slice(0, upTo)
  const last = held[held.length - 1]
  const phase = [...held].reverse().find((e) => e.type === 'phase.started')?.phase ?? null
  const done = held.some((e) => e.type === 'build.completed')
  server.builds = [...server.builds.filter((b) => b.iteration !== build.iteration), { ...build, phase, status: done ? 'completed' : build.status }]
  server.buildEvents.set(build.id, held)
  server.seq = last ? last.seq : server.seq
}

/** Stream events to the page, the server moving on with them. */
async function stream(events: LabEvent[], all: LabEvent[], build: Build): Promise<void> {
  for (const event of events) {
    serverAt(all, build, all.indexOf(event) + 1)
    FakeEventSource.last!.emit(event)
  }
  await settle()
}

const $ = (selector: string) => document.querySelector<HTMLElement>(selector)
const $$ = (selector: string) => Array.from(document.querySelectorAll<HTMLElement>(selector))
/** Visible text, with a space between elements, as a reader would see it. */
function text(selector: string): string {
  const el = $(selector)
  if (!el) return ''
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
  const parts: string[] = []
  for (let node = walker.nextNode(); node; node = walker.nextNode()) parts.push(node.textContent ?? '')
  return parts.join(' ').replace(/\s+/g, ' ').replace(/\s+([?.,:])/g, '$1').trim()
}
const calls = (path: string | RegExp) => server.calls.filter((c) => c.method === 'GET' && (typeof path === 'string' ? c.path === path : path.test(c.path))).length
const shownSeqs = () => $$('[data-test="console-line"]').map((li) => li.textContent ?? '')
const phaseStates = () => $$('[data-test="phase"]').map((li) => li.dataset.state)

async function click(el: Element | null): Promise<void> {
  if (!el) throw new Error('nothing to click')
  ;(el as HTMLElement).click()
  await settle()
}

/** The console text the page should show for these events. */
function linesFor(events: LabEvent[]): string[] {
  const keep = new Set(expectedLines(events))
  return events.filter((e) => keep.has(e.seq)).map((e) => e.message)
}

const messages = () => $$('[data-test="console-line"] .line__message').map((el) => el.textContent ?? '')

describe('route (D-54 (g), closes OQ-18)', () => {
  it('renders the Build page inside the shell', async () => {
    await open('/build/1')
    expect(router.currentRoute.value.name).toBe('build')
    expect($('header [data-test="wordmark"]')).not.toBeNull()
    expect($('main [data-test="build"]')).not.toBeNull()
  })

  it('says when iteration 1 has no build, and points to Knowledge', async () => {
    await open('/build/1')
    expect(text('[data-test="no-build"]')).toBe(
      'Build, iteration 1 No build for iteration 1 yet. Start Build is on the Knowledge page once the four core files are in. Go to Knowledge',
    )
    expect($('[data-test="no-build"] a')?.getAttribute('href')).toBe('/knowledge')
  })

  it('says when iteration 2 has no build, and points to iteration 1 once it exists', async () => {
    await open('/build/2')
    expect(text('[data-test="no-build"] p')).toBe("No build for iteration 2 yet. Iteration 2 starts when you rebuild from iteration 1's report.")
    expect($('[data-test="no-build"] a')?.getAttribute('href')).toBe('/knowledge')
    wrapper.unmount()
    serverAt(script(), buildRecord({ status: 'completed' }))
    await open('/build/2')
    expect($('[data-test="no-build"] a')?.getAttribute('href')).toBe('/build/1')
  })

  it("shows the iteration's own build", async () => {
    const one = buildRecord({ status: 'completed' })
    const two = buildRecord({ id: 'b-2', iteration: 2 })
    serverAt(script({ build: one }), one)
    const second = script({ build: two, first: 300 })
    serverAt(second, two, 10)
    await open('/build/2')
    expect(text('[data-test="build-iteration"]')).toBe('Iteration 2 of 2')
    expect(server.calls.some((c) => c.path === '/api/builds/b-2/events')).toBe(true)
    expect(server.calls.some((c) => c.path === '/api/builds/b-1/events')).toBe(false)
  })
})

describe('refresh and reconnect (FR-B-7, AC-7)', () => {
  it('a refresh mid-build resumes with the same stepper state and the full log, no line missing or doubled', async () => {
    const build = buildRecord()
    const events = script({ build })
    const k = events.findIndex((e) => e.type === 'step.started' && e.step === 'contain.upload') + 1
    serverAt(events, build, k)
    holding = true // the events load is slow: the stream gets ahead of it
    await open('/build/1')
    expect(FakeEventSource.last?.url).toBe(`/api/events?after=${events[k - 1].seq}`)
    await stream(events.slice(k, k + 3), events, build)
    expect(text('main')).toContain('Loading the build log')
    // The load answers as the server stood by then: it overlaps what the stream sent.
    holding = false
    held.splice(0).forEach((go) => go())
    await settle()
    await stream(events.slice(k + 3, k + 5), events, build)
    const seen = events.slice(0, k + 5)
    expect(messages()).toEqual(linesFor(seen))
    expect(new Set(shownSeqs()).size).toBe(shownSeqs().length)
    expect(phaseStates()).toEqual(derivePhases({ ...build, phase: 'contain' }, seen).map((p) => p.state))
    expect(phaseStates()).toEqual([...Array(5).fill('done'), 'active', ...Array(5).fill('pending')])
    expect($$('[data-test="phase"][data-state="active"] [data-test="step"]').map((s) => s.dataset.state)).toEqual(['done', 'done', 'done', 'active'])
  })

  it('a refreshed page shows what a page that watched from the start shows', async () => {
    const build = buildRecord()
    const events = script({ build })
    const k = events.findIndex((e) => e.type === 'phase.started' && e.phase === 'seeding') + 3
    serverAt(events, build, 1)
    await open('/build/1')
    await stream(events.slice(1, k), events, build)
    const watched = { lines: messages(), states: phaseStates(), elapsed: text('[data-test="build-elapsed"]'), progress: $('[data-test="build-progress"]')?.getAttribute('aria-valuenow') }
    wrapper.unmount()
    document.body.innerHTML = ''
    await open('/build/1')
    expect({ lines: messages(), states: phaseStates(), elapsed: text('[data-test="build-elapsed"]'), progress: $('[data-test="build-progress"]')?.getAttribute('aria-valuenow') }).toEqual(watched)
  })

  it('applies a whole build from the stream without fetching the snapshot or the events again', async () => {
    const build = buildRecord()
    const events = script({ build })
    server.seq = 0
    await open('/build/1')
    expect($('[data-test="no-build"]')).not.toBeNull()
    await stream(events, events, build)
    expect(calls('/api/state')).toBe(1)
    expect(calls(/^\/api\/builds\/[^/]+\/events$/)).toBe(1)
    expect(messages()).toEqual(linesFor(events))
    expect(phaseStates()).toEqual(Array(11).fill('done'))
    // D-66: the completion hand-off is the build report from M9 (was M6's summary).
    expect($('[data-test="build-report"]')).not.toBeNull()
  })

  it('a gap in the seqs re-loads the build and fills the missing lines', async () => {
    const build = buildRecord()
    const events = script({ build })
    serverAt(events, build, 20)
    await open('/build/1')
    // Events 21 and 22 never arrive; the server has them, and 23 reveals the gap.
    serverAt(events, build, 22)
    await stream([events[22]], events, build)
    expect(calls('/api/state')).toBe(2)
    expect(calls('/api/builds/b-1/events')).toBe(2)
    expect(messages()).toEqual(linesFor(events.slice(0, 23)))
  })

  it('stream.resync re-loads the build', async () => {
    const build = buildRecord()
    const events = script({ build })
    serverAt(events, build, 30)
    await open('/build/1')
    serverAt(events, build, 60)
    FakeEventSource.last!.emit({ type: 'stream.resync' })
    await settle()
    expect(calls('/api/builds/b-1/events')).toBe(2)
    expect(messages()).toEqual(linesFor(events.slice(0, 60)))
  })

  it('a completed build shows its full kept log after a server restart', async () => {
    const build = buildRecord({ status: 'completed' })
    const events = script({ build })
    serverAt(events, build) // the snapshot and the kept log are all a restarted server has
    await open('/build/1')
    expect(phaseStates()).toEqual(Array(11).fill('done'))
    expect(messages()).toEqual(linesFor(events))
    expect(messages()).toHaveLength(events.length - 88)
    expect(text('[data-test="build-elapsed"]')).toBe('01:15')
    expect($('[data-test="build-progress"]')?.getAttribute('aria-valuenow')).toBe('100')
  })

  it('an interrupted build says so, offers the way back to Knowledge, and shows where it stopped', async () => {
    const build = buildRecord({ status: 'interrupted', phase: 'contain' })
    server.builds = [build]
    server.seq = 140
    const interrupted: LabEvent = {
      ...script({ build })[0],
      seq: 140,
      type: 'build.interrupted',
      level: 'WARN',
      message: 'Build b-1 stopped when the server restarted. Start the build again.',
      data: { build_id: 'b-1' },
      sim_t: null,
    }
    server.buildEvents.set('b-1', [interrupted])
    await open('/build/1')
    expect(text('[data-test="interrupted-banner"]')).toBe(
      'This build stopped before it finished. Build b-1 stopped when the server restarted. Start the build again. Go to Knowledge',
    )
    expect($('[data-test="interrupted-banner"] a')?.getAttribute('href')).toBe('/knowledge')
    expect(phaseStates()).toEqual([...Array(5).fill('done'), 'stopped', ...Array(5).fill('pending')])
    expect(text('[data-test="phase"][data-state="stopped"] [data-test="phase-chip"]')).toBe('Stopped')
    expect(text('[data-test="phase"] [data-test="phase-chip"]')).toBe('Result not kept')
    expect(shownSeqs()).toEqual(['--:--.-  WARN   Build b-1 stopped when the server restarted. Start the build again.'])
  })

  it('a page watching when the server restarts keeps its lines and adds the interruption', async () => {
    const build = buildRecord()
    const events = script({ build })
    serverAt(events, build, 50)
    await open('/build/1')
    // The restarted server lost the build's events and marked it interrupted (D-33, D-49).
    const interrupted: LabEvent = { ...events[0], seq: 51, type: 'build.interrupted', level: 'WARN', message: 'Build b-1 stopped when the server restarted. Start the build again.', data: {}, sim_t: null }
    server.builds = [{ ...build, status: 'interrupted', phase: 'xexam' }]
    server.buildEvents.set('b-1', [interrupted])
    server.seq = 51
    FakeEventSource.last!.emit({ type: 'stream.resync' })
    await settle()
    expect(messages()).toEqual([...linesFor(events.slice(0, 50)), interrupted.message])
    expect($('[data-test="interrupted-banner"]')).not.toBeNull()
  })
})

describe('stepper (FR-B-3)', () => {
  async function openAt(predicate: (e: LabEvent) => boolean, options: Parameters<typeof script>[0] = {}) {
    const build = options.build ?? buildRecord()
    const events = script({ ...options, build })
    serverAt(events, build, events.findIndex(predicate) + 1)
    await open(`/build/${build.iteration}`)
    return events
  }

  it('opens the active phase on its sub-steps; done phases are one line with duration and result', async () => {
    await openAt((e) => e.type === 'step.started' && e.step === 'distill.music')
    const rows = $$('[data-test="phase"]')
    expect(rows.map((r) => r.querySelector('.phase__name')?.textContent)).toHaveLength(11)
    const [assay, distill, synth] = rows
    expect(assay.querySelector('[data-test="step"]')).toBeNull()
    expect(text('[data-test="phase"]:first-child [data-test="phase-duration"]')).toBe('4.5 s')
    expect(text('[data-test="phase"]:first-child [data-test="phase-chip"]')).toBe('Passed')
    expect(distill.dataset.state).toBe('active')
    expect(Array.from(distill.querySelectorAll<HTMLElement>('[data-test="step"]')).map((s) => [s.querySelector('.step__name')?.textContent, s.dataset.state, s.querySelector('[data-test="step-state"]')?.textContent])).toEqual([
      ['Load model profile from Instrument Awareness', 'done', 'load model profile from instrument awareness done'],
      ['Plan context budget', 'done', 'plan context budget done'],
      ['Distil Music', 'active', 'active'],
      ['Distil Person', 'pending', 'pending'],
      ['Distil Environment layers', 'pending', 'pending'],
      ['Merge Misc Context', 'pending', 'pending'],
    ])
    expect(synth.dataset.state).toBe('pending')
    expect(synth.querySelector('[data-test="phase-chip"]')).toBeNull()
  })

  it('a done phase is a button that opens and closes on click or with the keyboard', async () => {
    await openAt((e) => e.type === 'phase.started' && e.phase === 'synth')
    const row = $('[data-test="phase"] [data-test="phase-row"]')!
    expect(row.tagName).toBe('BUTTON') // Enter and Space press a native button
    expect(row.getAttribute('aria-expanded')).toBe('false')
    await click(row)
    expect(row.getAttribute('aria-expanded')).toBe('true')
    expect($$('[data-test="phase"]:first-child [data-test="step"]')).toHaveLength(4)
    await click(row)
    expect(row.getAttribute('aria-expanded')).toBe('false')
    expect($$('[data-test="phase"][data-state="active"] [data-test="phase-row"]')[0].tagName).toBe('DIV')
    expect($$('[data-test="phase"][data-state="pending"] button')).toHaveLength(0)
  })

  it('shows each result as its own chip; incomplete is neutral, neither a pass nor a fault', async () => {
    const build = buildRecord({ status: 'completed' })
    // D-66: the advisory is asked for in Stress & Probe, where it used to be raised by default.
    const events = script({ build, results: { germ: 'incomplete', probe: 'findings', harvest: 'failed' }, advisoryIn: 'probe' })
    serverAt(events, build)
    await open('/build/1')
    const chips = $$('[data-test="phase-chip"]').map((c) => [c.textContent?.trim(), c.className.match(/chip--(\w+)/)?.[1]])
    expect(chips[0]).toEqual(['Passed', 'positive'])
    expect(chips[4]).toEqual(['Incomplete: 2 of 2 not run', 'neutral'])
    expect(chips[8]).toEqual(['Findings: 1', 'warning'])
    expect(chips[9]).toEqual(['Failed: T-16, T-17, T-18, T-19, T-20', 'negative'])
    expect($('[data-test="phase"][data-result="incomplete"]')?.className).toContain('mark--incomplete')
  })

  it('iteration 2 shows the five feedback sub-steps first, under "Apply observer feedback" (FR-RB-8)', async () => {
    const build = buildRecord({ id: 'b-2', iteration: 2 })
    await openAt((e) => e.type === 'step.started' && e.step === 'assay.feedback-music', { build })
    const assay = $('[data-test="phase"]')!
    expect(assay.querySelector('[data-test="step-group"]')?.textContent).toBe('Apply observer feedback')
    const grouped = Array.from(assay.querySelectorAll<HTMLElement>('.steps--grouped [data-test="step"]'))
    expect(grouped.map((s) => [s.querySelector('.step__name')?.textContent, s.querySelector('[data-test="step-state"]')?.textContent])).toEqual([
      // D-71: the real routing's summaries (D-68), where D-52's stub said "no change".
      ['Route feedback to Ensemble files', '9 of 10 segments to 4 files'],
      ['Update person.md', '+4 lines in Reasoning methods'],
      ['Update instrument-awareness.md', '+4 lines in Model Behaviour'],
      ['Update environment.md', '+10 lines in Styling; +4 lines in User Experience; +4 lines in Data Layer'],
      ['Update music.md', 'active'],
    ])
    expect(assay.querySelectorAll('[data-test="step"]')).toHaveLength(9)
  })
})

describe('header (FR-DC-4: from sim_t)', () => {
  it('shows the iteration, the simulated elapsed time, the progress and the phase', async () => {
    const build = buildRecord()
    const events = script({ build })
    serverAt(events, build, events.findIndex((e) => e.type === 'phase.started' && e.phase === 'seeding') + 1)
    await open('/build/1')
    expect(text('[data-test="build-iteration"]')).toBe('Iteration 1 of 2')
    expect(text('[data-test="build-elapsed"]')).toBe('00:44')
    expect($('[data-test="build-progress"]')?.getAttribute('aria-valuenow')).toBe('59')
    expect(text('[data-test="build-status"]')).toBe('Phase 8 of 11: Seeding & Life')
  })
})

describe('console (FR-B-4, build-simulation.md section 4)', () => {
  async function openRunning(upTo = 60) {
    const build = buildRecord()
    const events = script({ build, results: { germ: 'incomplete' } })
    serverAt(events, build, upTo)
    await open('/build/1')
    return { build, events }
  }

  it('writes each line as mm:ss.s  LEVEL  message', async () => {
    await openRunning()
    expect(shownSeqs().slice(0, 2)).toEqual(['00:00.0  INFO   Build started: iteration 1, seed "License Optimization"', '00:00.0  INFO   Phase 1 of 11: Assay'])
    expect(shownSeqs().find((l) => l.includes('T-01'))).toMatch(/^\d\d:\d\d\.\d {2}PASS {3}T-01 /)
  })

  it('colours each level with its console token, red only for FAIL (D-37)', () => {
    const source = readFileSync(resolve(__dirname, '../src/components/build/BuildConsole.vue'), 'utf8')
    const colours = Object.fromEntries([...source.matchAll(/\.line--(\w+) \{\s*color: var\((--[\w-]+)\);/g)].map((m) => [m[1], m[2]]))
    expect(colours).toEqual({
      INFO: '--console-text-secondary',
      LLM: '--console-llm',
      API: '--console-api',
      TEST: '--console-text',
      PASS: '--console-pass',
      WARN: '--console-warn',
      FAIL: '--console-fail',
    })
    expect(source.match(/--console-fail/g)).toHaveLength(1)
  })

  it('tags each line with its level for its colour', async () => {
    await openRunning()
    const lines = $$('[data-test="console-line"]')
    expect(lines.every((l) => l.classList.contains(`line--${l.dataset.level}`))).toBe(true)
    expect(new Set(lines.map((l) => l.dataset.level))).toEqual(new Set(['INFO', 'LLM', 'PASS']))
  })

  it('filters by level', async () => {
    const { events } = await openRunning(110)
    const filter = (id: string) => $(`[data-test="console-filter"] [data-filter="${id}"]`)
    await click(filter('LLM'))
    expect(filter('LLM')?.getAttribute('aria-pressed')).toBe('true')
    expect(filter('all')?.getAttribute('aria-pressed')).toBe('false')
    expect(new Set($$('[data-test="console-line"]').map((l) => l.dataset.level))).toEqual(new Set(['LLM']))
    await click(filter('TEST'))
    expect(new Set($$('[data-test="console-line"]').map((l) => l.dataset.level))).toEqual(new Set(['TEST', 'PASS']))
    await click(filter('FAIL'))
    expect(text('[data-test="console-body"]')).toBe('No FAIL lines.')
    await click(filter('all'))
    expect(messages()).toEqual(linesFor(events.slice(0, 110)))
  })

  it('follows new lines, and stops while paused or scrolled up', async () => {
    const { build, events } = await openRunning(40)
    const body = $('[data-test="console-body"]')!
    let height = 2000
    Object.defineProperty(body, 'scrollHeight', { get: () => height, configurable: true })
    Object.defineProperty(body, 'clientHeight', { get: () => 300, configurable: true })
    const more = async (from: number, to: number) => {
      height += 100
      await stream(events.slice(from, to), events, build)
    }
    await more(40, 45)
    expect(body.scrollTop).toBe(height)
    // Pause: lines keep coming, the view stays.
    await click($('[data-test="console-pause"]'))
    expect($('[data-test="console-pause"]')?.getAttribute('aria-pressed')).toBe('true')
    const at = body.scrollTop
    await more(45, 52)
    expect(body.scrollTop).toBe(at)
    expect(text('[data-test="console-paused"]')).toMatch(/^Paused: \d+ new lines below$/)
    // Resume jumps to the latest line and follows again.
    await click($('[data-test="console-pause"]'))
    expect(body.scrollTop).toBe(height)
    expect($('[data-test="console-paused"]')).toBeNull()
    // Scrolling up pauses it too.
    body.scrollTop = 100
    body.dispatchEvent(new Event('scroll'))
    await settle()
    expect($('[data-test="console-pause"]')?.textContent?.trim()).toBe('Resume')
    await more(52, 56)
    expect(body.scrollTop).toBe(100)
  })
})

describe('completion hand-off (FR-B-9, D-54 (f), D-65)', () => {
  async function openCompleted(iteration = 1) {
    const build = buildRecord({ id: `b-${iteration}`, iteration, status: 'completed' })
    serverAt(script({ build }), build)
    await open(`/build/${iteration}`)
  }

  // D-66: M6's summary (no verdict, "arrives in M9") is replaced by the build report above the collapsed stepper.
  it('shows the build report, with its verdict, above the collapsed stepper', async () => {
    await openCompleted()
    expect(text('[data-test="report-verdict"]')).toBe('Completed with findings')
    expect($('[data-test="report-verdict"]')?.className).toContain('chip--warning')
    expect($$('[data-test="report-fact"]').map((d) => d.textContent)).toEqual([
      '1 of 2',
      '01:15 simulated',
      '11, 2 with findings',
      '21: 15 passed, 5 warned, 1 failed',
      '14',
      '0',
      '3',
    ])
    expect(text('[data-test="build-report"]')).not.toContain('M9')
    const report = $('[data-test="build-report"]')!
    expect(report.compareDocumentPosition($('[data-test="phase"]')!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect($$('[data-test="phase"] [data-test="step"]')).toHaveLength(0)
    expect(text('[data-test="build-status"]')).toBe('Completed')
  })

  // D-59: View Dashboard opens the dashboard from M7. D-71: Rebuild opens the rebuild modal from M10;
  // Approve still says which milestone brings it.
  it('offers View Dashboard, which opens the dashboard, Rebuild, which opens the rebuild modal, and Approve, which says M11 brings it', async () => {
    await openCompleted()
    const actions = $$('[data-test="report-actions"] button')
    expect(actions.map((b) => [b.textContent?.trim(), b.getAttribute('aria-disabled')])).toEqual([
      ['View Dashboard', null],
      ['Rebuild', null],
      ['Approve', 'true'],
    ])
    expect(actions[2].hasAttribute('disabled')).toBe(false)
    expect(actions[2].getAttribute('aria-describedby')).toBeTruthy()
    await click(actions[1])
    expect(document.querySelector('[role="dialog"][data-modal="rebuild"]')?.textContent).toContain('Rebuild Seed: observer feedback')
    await click(document.querySelector('[data-action="cancel"]'))
    await click($$('[data-test="report-actions"] button')[2])
    expect(text('[data-test="report-status"]')).toBe('Approve arrives with the Seed page in M11.')
  })

  it('has no Rebuild on iteration 2 (D-6)', async () => {
    await openCompleted(2)
    expect($$('[data-test="report-actions"] button').map((b) => b.textContent?.trim())).toEqual(['View Dashboard', 'Approve'])
    expect(text('[data-test="report-verdict"]')).toBe('Passed')
  })

  it('lets the console be hidden and shown again', async () => {
    await openCompleted()
    await click($('[data-test="console-hide"]'))
    expect($('[data-test="console"]')).toBeNull()
    await click($('[data-test="console-show"]'))
    expect($('[data-test="console"]')).not.toBeNull()
  })

  it('has no Hide while the build runs', async () => {
    const build = buildRecord()
    serverAt(script({ build }), build, 30)
    await open('/build/1')
    expect($('[data-test="console-hide"]')).toBeNull()
    expect($('[data-test="build-report"]')).toBeNull() // D-66: was the summary
    expect(calls(/\/report$/)).toBe(0) // no report is asked for before the build completes
  })
})

describe('keyboard (NFR-6)', () => {
  it('every control is a native button or link, and the log can be focused to scroll it', async () => {
    const build = buildRecord({ status: 'completed' })
    serverAt(script({ build }), build)
    await open('/build/1')
    const controls = $$('main button, main a')
    expect(controls.length).toBeGreaterThanOrEqual(11 + 6 + 1 + 1 + 3)
    for (const control of controls) expect(control.getAttribute('tabindex')).not.toBe('-1')
    expect($('[data-test="console-body"]')?.getAttribute('tabindex')).toBe('0')
  })
})
