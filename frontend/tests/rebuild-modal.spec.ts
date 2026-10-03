// The rebuild modal (FR-RB-1 to FR-RB-5, ui-spec.md section 6, D-19, D-47, D-67, D-70), against
// tests/fake-server.ts (which serves the reports and dashboards the backend wrote, and keeps the
// rebuild's rules) and a recorder in place of ECharts. Rebuild on iteration 1's report opens a large
// modal with the Knowledge editor; the view toggle shows the feedback alone or beside iteration 1's
// report or dashboard, whose drill never moves the page URL; Start Rebuild is one request and is
// disabled while the feedback is empty; Cancel and Escape save nothing and lose nothing typed;
// Shift+F prefills only inside the modal; Rebuild is not offered on iteration 2.

import { mount, type VueWrapper } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, type Router } from 'vue-router'
import App from '../src/App.vue'
import { SHORTCUTS } from '../src/demo/shortcuts'
import type { Report } from '../src/report'
import { createAppRouter } from '../src/router'
import { useLabStore, type Build } from '../src/stores/lab'
import { applyTheme } from '../src/theme'
import { buildRecord } from './build-script'
import { chartFor, charts } from './fake-echarts'
import { DEMO_FEEDBACK, dashboardFixture, FakeServer, FEEDBACK_NAME, reportFixture } from './fake-server'

vi.mock('../src/dashboard/echarts', () => import('./fake-echarts'))
const latency = vi.hoisted(() => ({ waits: [] as { ms: number; release: () => void }[] }))
vi.mock('../src/dashboard/latency', () => ({ wait: (ms: number) => new Promise<void>((release) => latency.waits.push({ ms, release })) }))

class FakeEventSource {
  addEventListener() {}
  close() {}
  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
}

const ONE = reportFixture(1) as unknown as Report
const TOKENS_CSS = readFileSync(resolve(__dirname, '../src/styles/tokens.css'), 'utf8')

let server: FakeServer
let wrapper: VueWrapper | null = null
let router: Router

async function settle(times = 6): Promise<void> {
  for (let i = 0; i < times; i++) await new Promise((r) => setTimeout(r))
}

function completed(iteration = 1): Build {
  return buildRecord({ id: `b-${iteration}`, iteration, status: 'completed' })
}

beforeEach(() => {
  server = new FakeServer()
  for (const name of ['person.md', 'instrument-awareness.md', 'environment.md', 'music.md']) {
    server.add(name, name.replace('.md', '').replace('-', '_'), `# ${name}\n\nText.\n`)
  }
  server.builds = [completed(1)]
  charts.length = 0
  latency.waits.length = 0
  vi.stubGlobal('fetch', (input: RequestInfo | URL, init?: RequestInit) => server.fetch(input, init))
  vi.stubGlobal('EventSource', FakeEventSource)
  const style = document.createElement('style')
  style.id = 'tokens'
  style.textContent = TOKENS_CSS
  document.head.append(style)
  applyTheme('light')
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  vi.unstubAllGlobals()
  document.body.innerHTML = ''
  document.getElementById('tokens')?.remove()
})

async function open(path = '/review/1'): Promise<void> {
  const pinia = createPinia()
  setActivePinia(pinia)
  router = createAppRouter(createMemoryHistory())
  await router.push(path)
  await router.isReady()
  wrapper = mount(App, { global: { plugins: [pinia, router] }, attachTo: document.body })
  await useLabStore().connect()
  await settle()
}

const $ = (selector: string, root: ParentNode = document) => root.querySelector<HTMLElement>(selector)
const $$ = (selector: string, root: ParentNode = document) => Array.from(root.querySelectorAll<HTMLElement>(selector))
function text(selector: string | HTMLElement | null): string {
  const el = typeof selector === 'string' ? $(selector) : selector
  return (el?.textContent ?? '').replace(/\s+/g, ' ').trim()
}
async function click(el: Element | null): Promise<void> {
  if (!el) throw new Error('nothing to click')
  ;(el as HTMLElement).click()
  await settle()
}
async function key(target: Element | null, init: KeyboardEventInit): Promise<KeyboardEvent> {
  const event = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, ...init })
  ;(target ?? document.body).dispatchEvent(event)
  await settle()
  return event
}
async function type(value: string): Promise<void> {
  const area = $('[data-modal="rebuild"] [data-test="text"]') as HTMLTextAreaElement
  area.value = value
  area.dispatchEvent(new Event('input'))
  await settle()
}

const dialog = () => $('[role="dialog"][data-modal="rebuild"]')
const rebuildButton = () => $('[data-test="report-actions"] [data-action="rebuild"]')
const startButton = () => $('[data-modal="rebuild"] [data-action="start-rebuild"]')!
const tabs = () => $$('[data-modal="rebuild"] [role="tab"]')
const tab = (view: string) => $(`[data-modal="rebuild"] [role="tab"][data-view="${view}"]`)!
const draft = () => ($('[data-modal="rebuild"] [data-test="text"]') as HTMLTextAreaElement | null)?.value ?? null
const rebuildCalls = () => server.calls.filter((c) => c.method === 'POST' && c.path === '/api/builds')
const highlighted = () => $$('[data-modal="rebuild"] [data-highlight="finding"] > [data-panel]').map((el) => el.dataset.panel)

async function openModal(path = '/review/1'): Promise<void> {
  await open(path)
  await click(rebuildButton())
}

describe('the modal (FR-RB-1, ui-spec.md section 6)', () => {
  it('opens from the iteration 1 report: titled, large, the Knowledge editor pre-titled for the feedback file', async () => {
    await openModal()
    const modal = dialog()!
    expect(modal.getAttribute('aria-modal')).toBe('true')
    expect(text($('h2', modal))).toBe('Rebuild Seed: observer feedback')
    expect(modal.className).toContain('modal--lg')
    expect(text('[data-modal="rebuild"] [data-test="feedback-name"]')).toBe(FEEDBACK_NAME)
    expect(text('[data-modal="rebuild"] .rebuild__category')).toBe('Misc Context')
    // The same editor as Knowledge: Edit / Preview and the mic with its tooltip.
    expect($$('[data-modal="rebuild"] .segmented__option').map((b) => text(b))).toEqual(['Edit', 'Preview'])
    expect($('[data-modal="rebuild"] [data-test="mic"]')?.getAttribute('aria-label')).toBe('Voice input')
    const placeholder = $('[data-modal="rebuild"] [data-test="text"]')!.getAttribute('placeholder')!
    for (const word of ['data', 'correctness', 'style', 'charts', 'latency', 'anything else', 'finding ids']) expect(placeholder).toContain(word)
    // Focus moves into the modal, on the selected view.
    expect(modal.contains(document.activeElement)).toBe(true)
    expect(document.activeElement).toBe(tab('feedback'))
  })

  it('previews the feedback as Knowledge does, sanitised', async () => {
    await openModal()
    await type('**Bold** and <img src=x onerror=alert(1)>')
    await click($('[data-modal="rebuild"] [data-test="mode-preview"]'))
    const preview = $('[data-modal="rebuild"] [data-test="preview"]')!
    expect($('strong', preview)?.textContent).toBe('Bold')
    expect($('img', preview)).toBeNull()
  })

  it('is not offered on iteration 2, nor on iteration 1 once iteration 2 has started (D-6, D-67)', async () => {
    server.builds = [completed(1), completed(2)]
    server.iteration = 2
    await open('/review/2')
    expect($$('[data-test="report-actions"] button').map((b) => text(b))).toEqual(['View Dashboard', 'Approve'])
    // No shortcut reaches the modal: every one pressed on the iteration 2 report opens no dialog.
    for (const shortcut of SHORTCUTS.filter((s) => !['reset', 'clear', 'sample', 'start'].includes(s.action))) {
      await key(document.body, { key: shortcut.key ?? '', code: shortcut.code ?? `Key${(shortcut.key ?? '').toUpperCase()}`, shiftKey: true })
    }
    expect(dialog()).toBeNull()
    await router.push('/review/1')
    await settle()
    expect(rebuildButton()).toBeNull()
    expect(text('[data-test="report-rebuilt"]')).toBe('Iteration 2 was rebuilt from this report. Go to iteration 2')
  })
})

describe('Start Rebuild (FR-RB-3 to FR-RB-5, D-67)', () => {
  it('is disabled, with its reason, while the feedback is empty or only whitespace', async () => {
    await openModal()
    for (const value of ['', '  \n\t ']) {
      await type(value)
      expect(startButton().getAttribute('aria-disabled')).toBe('true')
      const reason = document.getElementById(startButton().getAttribute('aria-describedby')!)
      expect(text(reason)).toBe('Start Rebuild needs observer feedback. Write what iteration 2 should change first.')
      await click(startButton())
    }
    expect(rebuildCalls()).toEqual([])
    expect(dialog()).not.toBeNull()
  })

  it('saves the feedback and starts iteration 2 in one request, then opens /build/2', async () => {
    await openModal()
    await type('The totals do not add up (N-1).')
    expect(startButton().getAttribute('aria-disabled')).toBeNull()
    await click(startButton())
    expect(rebuildCalls().map((c) => c.body)).toEqual([{ iteration: 2, feedback: 'The totals do not add up (N-1).' }])
    expect(server.writes().filter((c) => c.path.startsWith('/api/intake/'))).toEqual([])
    expect(server.files.find((f) => f.name === FEEDBACK_NAME)?.content).toBe('The totals do not add up (N-1).')
    expect(router.currentRoute.value.fullPath).toBe('/build/2')
    expect(dialog()).toBeNull()
  })

  it('keeps the modal and the text open with the server message when the rebuild is refused', async () => {
    await openModal()
    await type('Use bars.')
    server.refuseNext((c) => c.path === '/api/builds', 409, 'build_running', 'A build is running. Wait for it to finish, or use Reset to start.')
    await click(startButton())
    expect(text('[data-modal="rebuild"] [data-test="rebuild-status"]')).toBe('A build is running. Wait for it to finish, or use Reset to start.')
    expect($('[data-modal="rebuild"] [data-test="rebuild-status"]')?.getAttribute('role')).toBe('alert')
    expect(draft()).toBe('Use bars.')
    expect(router.currentRoute.value.fullPath).toBe('/review/1')
  })
})

describe('the views (FR-RB-2, ui-spec.md section 6)', () => {
  it('is a tablist: Feedback, Feedback + Report, Feedback + Dashboard; the arrow keys move between them', async () => {
    await openModal()
    expect(tabs().map((t) => [text(t), t.getAttribute('aria-selected'), t.getAttribute('tabindex')])).toEqual([
      ['Feedback', 'true', '0'],
      ['Feedback + Report', 'false', '-1'],
      ['Feedback + Dashboard', 'false', '-1'],
    ])
    expect($('[data-modal="rebuild"] [role="tabpanel"]')?.getAttribute('aria-labelledby')).toBe(tab('feedback').id)
    expect($('[data-test="rebuild-report"]')).toBeNull()
    expect($('[data-test="rebuild-dashboard"]')).toBeNull()
    await key(tab('feedback'), { key: 'ArrowRight' })
    expect(document.activeElement).toBe(tab('report'))
    expect(tab('report').getAttribute('aria-selected')).toBe('true')
    await key(tab('report'), { key: 'End' })
    expect(document.activeElement).toBe(tab('dashboard'))
    await key(tab('dashboard'), { key: 'ArrowRight' })
    expect(document.activeElement).toBe(tab('feedback'))
  })

  it('Feedback + Report puts the editor left and iteration 1 report right, without its actions', async () => {
    await openModal()
    await type('Kept across views.')
    await click(tab('report'))
    const panel = $('[data-modal="rebuild"] [role="tabpanel"]')!
    expect(panel.className).toContain('rebuild--split')
    expect(Array.from(panel.children).map((el) => (el as HTMLElement).dataset.test)).toEqual(['rebuild-feedback', 'rebuild-report'])
    const report = $('[data-test="rebuild-report"] [data-test="build-report"]')!
    expect(text($('h3', report))).toBe('Build Report')
    expect($('[data-test="report-actions"]', report)).toBeNull()
    expect($$('[data-test="finding"]', report).map((r) => r.dataset.finding)).toEqual(ONE.groups.flatMap((g) => g.findings).map((f) => f.id))
    expect(draft()).toBe('Kept across views.')
  })

  it('Feedback + Dashboard shows iteration 1 dashboard beside the editor; drilling never moves the page URL', async () => {
    await openModal()
    const before = router.currentRoute.value.fullPath
    await click(tab('dashboard'))
    const dashboard = $('[data-test="rebuild-dashboard"] [data-test="dashboard"]')!
    expect(dashboard.dataset.variant).toBe('rough')
    expect(dashboard.className).toContain('defects-overlay')
    const root = dashboardFixture(1, 'root.json') as { payload: { panels: Record<string, { categories?: { id: string; step: unknown }[] }> } }
    const bar = root.payload.panels.entitlement.categories!.find((c) => c.id === 'microsoft-365-e3')!
    chartFor('entitlement').click({ step: bar.step })
    await settle()
    expect(server.calls.filter((c) => c.path === '/api/dashboards/license-optimization').at(-1)!.query).toMatchObject({ iteration: '1', drill: 'microsoft.microsoft-365-e3' })
    expect(text('[data-test="rebuild-dashboard"] [data-test="drill-back"]')).toBeTruthy()
    await click($('[data-test="rebuild-dashboard"] [data-test="drill-back"]'))
    expect(server.calls.filter((c) => c.path === '/api/dashboards/license-optimization').at(-1)!.query.drill ?? '').toBe('')
    expect(router.currentRoute.value.fullPath).toBe(before)
  })

  it('a finding in the embedded report shows that finding on the embedded dashboard, outlined, not a page link', async () => {
    await openModal()
    await click(tab('report'))
    const link = $('[data-test="rebuild-report"] [data-finding="V-3"] [data-test="finding-link"]')!
    expect(link.tagName).toBe('BUTTON')
    await click(link)
    expect(tab('dashboard').getAttribute('aria-selected')).toBe('true')
    expect(highlighted().sort()).toEqual(['entitlement', 'seats-treemap'])
    expect(text('[data-test="rebuild-finding"]')).toContain('Showing V-3 on Seats by vendor and product, Entitled, assigned and active by product.')
    expect(router.currentRoute.value.fullPath).toBe('/review/1')
    await click($('[data-test="rebuild-finding"] button'))
    expect(highlighted()).toEqual([])
  })
})

describe('Cancel, Escape and the keyboard (D-38, D-47, NFR-6)', () => {
  it('Cancel saves nothing and discards nothing already saved; the text typed is still there on reopening', async () => {
    const saved = server.add(FEEDBACK_NAME, 'misc_context', 'Saved on Knowledge.')
    await openModal()
    expect(draft()).toBe('Saved on Knowledge.') // an existing feedback file is where the draft starts
    await type('Saved on Knowledge. And more.')
    await click($('[data-modal="rebuild"] [data-action="cancel"]'))
    expect(dialog()).toBeNull()
    expect(server.writes()).toEqual([])
    expect(server.files.find((f) => f.id === saved.id)?.content).toBe('Saved on Knowledge.')
    await click(rebuildButton())
    expect(draft()).toBe('Saved on Knowledge. And more.')
  })

  it('Escape closes it and puts focus back on Rebuild; a click on the backdrop does not close it', async () => {
    await open()
    rebuildButton()!.focus() // as the keyboard reaches it, then Enter
    await click(rebuildButton())
    expect(dialog()).not.toBeNull()
    $('.backdrop')!.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await settle()
    expect(dialog()).not.toBeNull()
    await key(document.activeElement, { key: 'Escape' })
    expect(dialog()).toBeNull()
    expect(document.activeElement).toBe(rebuildButton())
  })

  it('traps focus: Tab from the last control goes to the first, Shift+Tab from the first to the last', async () => {
    await openModal()
    await type('Something.')
    const start = startButton()
    start.focus()
    await key(start, { key: 'Tab' })
    expect(document.activeElement).toBe(tab('feedback'))
    await key(tab('feedback'), { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(start)
  })

  it('Shift+F prefills the demo feedback inside the modal, and types as text in the editor', async () => {
    await openModal()
    expect(document.activeElement).toBe(tab('feedback'))
    await key(document.activeElement, { key: 'F', code: 'KeyF', shiftKey: true })
    expect(draft()).toBe(DEMO_FEEDBACK)
    expect(startButton().getAttribute('aria-disabled')).toBeNull()
    // In the editor, a capital F is text (D-47): no second fetch.
    const fetches = server.calls.filter((c) => c.path === '/api/demo/feedback').length
    await key($('[data-modal="rebuild"] [data-test="text"]'), { key: 'F', code: 'KeyF', shiftKey: true })
    expect(server.calls.filter((c) => c.path === '/api/demo/feedback')).toHaveLength(fetches)
  })

  it('Shift+F does nothing before the modal exists', async () => {
    await open()
    await key(document.body, { key: 'F', code: 'KeyF', shiftKey: true })
    expect(server.calls.filter((c) => c.path === '/api/demo/feedback')).toEqual([])
    expect(dialog()).toBeNull()
  })
})

describe('Knowledge after a rebuild starts (ui-spec.md section 2, FR-RB-4, FR-RB-7, FR-B-8)', () => {
  it('lists the feedback file in Misc Context, stays read-only, and shows a core file with the section routing added', async () => {
    await openModal()
    await type('Use bars, not a pie.')
    await click(startButton())
    const lab = useLabStore()
    await lab.refresh() // the stream's intake.file_created and build.started, as a snapshot
    const environment = server.files.find((f) => f.name === 'environment.md')!
    await router.push(`/knowledge?file=${environment.id}`)
    await settle()
    expect($$('[data-category="misc_context"] .file__name').map((el) => text(el))).toEqual([FEEDBACK_NAME])
    expect(text('[data-test="read-only-banner"]')).toContain('Knowledge files are read-only until it finishes.')
    // The Update environment.md sub-step plays: the server writes the file and says so (D-68).
    environment.content += '\n## Styling\n\n### Observer feedback (iteration 1)\n\nUse bars, not a pie.\n'
    environment.size = new TextEncoder().encode(environment.content).length
    lab.receive({
      seq: lab.snapshot!.seq + 1,
      build_id: null,
      iteration: 2,
      phase: null,
      step: null,
      type: 'intake.file_updated',
      level: 'INFO',
      code: null,
      message: `environment.md: observer feedback added (${environment.size} bytes)`,
      data: { file: { id: environment.id, name: 'environment.md', category: 'environment', size: environment.size }, changed: ['content'], source: 'feedback' },
      sim_t: null,
      wall_ts: '2026-10-04T12:00:00.000+00:00',
    })
    await settle()
    const area = $('[data-test="editor"] [data-test="text"]') as HTMLTextAreaElement
    expect(area.value).toContain('### Observer feedback (iteration 1)\n\nUse bars, not a pie.')
    expect(area.readOnly).toBe(true)
  })
})
