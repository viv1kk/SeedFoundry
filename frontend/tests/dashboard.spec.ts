// The License Optimization dashboard on the review route (FR-D-1 to FR-D-6, ui-spec.md section 5,
// D-59, OQ-22, OQ-23), against tests/fake-server.ts, which replays the backend's own responses,
// and a recorder in place of ECharts (tests/fake-echarts.ts).

import { mount, type VueWrapper } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, type Router } from 'vue-router'
import App from '../src/App.vue'
import type { DashboardResponse } from '../src/dashboard/types'
import { createAppRouter } from '../src/router'
import { useLabStore, type Build } from '../src/stores/lab'
import { applyTheme } from '../src/theme'
import { buildRecord, script } from './build-script'
import { chartFor, charts } from './fake-echarts'
import { dashboardFixture, FakeServer } from './fake-server'

vi.mock('../src/dashboard/echarts', () => import('./fake-echarts'))

class FakeEventSource {
  addEventListener() {}
  close() {}
  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
}

const DASHBOARD = '/review/1?dashboard=license-optimization'
const ROOT = dashboardFixture('root.json') as unknown as DashboardResponse
const TOKENS_CSS = readFileSync(resolve(__dirname, '../src/styles/tokens.css'), 'utf8')

let server: FakeServer
let wrapper: VueWrapper | null = null
let router: Router
let history: ReturnType<typeof createMemoryHistory>
/** Dashboard requests wait here while `holding` is set. */
let holding = false
let held: (() => void)[] = []

async function settle(times = 6): Promise<void> {
  for (let i = 0; i < times; i++) await new Promise((r) => setTimeout(r))
}

function completed(iteration = 1, status: Build['status'] = 'completed'): Build {
  return buildRecord({ id: `b-${iteration}`, iteration, status })
}

beforeEach(() => {
  server = new FakeServer()
  server.builds = [completed()]
  holding = false
  held = []
  charts.length = 0
  vi.stubGlobal('fetch', async (input: RequestInfo | URL, init?: RequestInit) => {
    if (holding && String(input).includes('/api/dashboards/')) await new Promise<void>((go) => held.push(go))
    return server.fetch(input, init)
  })
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

/** Open a page as main.ts does. `keepHistory` reopens on the same history, as a reload keeps the address. */
async function open(path: string, keepHistory = false): Promise<void> {
  wrapper?.unmount()
  const pinia = createPinia()
  setActivePinia(pinia)
  if (!keepHistory) history = createMemoryHistory()
  router = createAppRouter(history)
  await router.push(path)
  await router.isReady()
  wrapper = mount(App, { global: { plugins: [pinia, router] }, attachTo: document.body })
  await useLabStore().connect()
  await settle()
}

const $ = (selector: string) => document.querySelector<HTMLElement>(selector)
const $$ = (selector: string) => Array.from(document.querySelectorAll<HTMLElement>(selector))
/** Visible text, with a space between elements, as a reader would see it. */
function text(selector: string | HTMLElement | null): string {
  const el = typeof selector === 'string' ? $(selector) : selector
  if (!el) return ''
  const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
  const parts: string[] = []
  for (let node = walker.nextNode(); node; node = walker.nextNode()) parts.push(node.textContent ?? '')
  return parts.join(' ').replace(/\s+/g, ' ').replace(/\s+([?.,:])/g, '$1').trim()
}
async function click(el: Element | null): Promise<void> {
  if (!el) throw new Error('nothing to click')
  ;(el as HTMLElement).click()
  await settle()
}
async function key(el: Element | null, name: string): Promise<void> {
  if (!el) throw new Error('nothing to press')
  el.dispatchEvent(new KeyboardEvent('keydown', { key: name, bubbles: true, cancelable: true }))
  await settle()
}
const crumbs = () => $$('[data-test="crumb"]').map((li) => text(li).replace(/^› /, ''))
const drillQuery = () => router.currentRoute.value.query.drill ?? ''
const dashboardCalls = () => server.calls.filter((c) => c.path === '/api/dashboards/license-optimization')
const kpi = (id: string) => text(`[data-panel="${id}"] [data-test="kpi-figure"]`)

describe('opening the dashboard (OQ-22, OQ-23)', () => {
  it('View Dashboard on a completed build opens it over the review route', async () => {
    const build = completed()
    server.buildEvents.set(build.id, script({ build }))
    server.builds = [build]
    await open('/build/1')
    await click($('[data-test="summary-actions"] [data-action="dashboard"]'))
    expect(router.currentRoute.value.fullPath).toBe(DASHBOARD)
    expect($('[data-test="dashboard-frame"]')).not.toBeNull()
    expect(text('main h1')).toBe('License Optimization')
  })

  it('shows the frame: Back to report, the iteration badge, and for iteration 1 a line on the overlay', async () => {
    await open(DASHBOARD)
    expect(text('[data-test="back-to-report"]')).toBe('Back to report')
    expect(text('[data-test="frame-iteration"]')).toBe('Iteration 1 of 2')
    expect(text('[data-test="overlay-note"]')).toBe("Iteration 1's defect overlay arrives in M8, so until then this is the polished dashboard.")
    expect(text('[data-test="dashboard-source"]')).toBe('Primary estate, 13,050 seats; monthly usage Oct 2025 to Sep 2026, snapshot 2026-09-30')
  })

  it('iteration 2 has no overlay line', async () => {
    server.builds = [completed(1), completed(2)]
    await open('/review/2?dashboard=license-optimization')
    expect(text('[data-test="frame-iteration"]')).toBe('Iteration 2 of 2')
    expect($('[data-test="overlay-note"]')).toBeNull()
    expect(dashboardCalls()[0].query.iteration).toBe('2')
  })

  it('Back to report closes the dashboard and shows the report stand-in', async () => {
    await open(DASHBOARD)
    await click($('[data-test="back-to-report"]'))
    expect(router.currentRoute.value.fullPath).toBe('/review/1')
    expect($('[data-test="dashboard-frame"]')).toBeNull()
    expect(text('main h1')).toBe('Review, iteration 1')
    expect(text('[data-test="review-state"]')).toBe(
      "The build report, with its verdict, findings and tests, arrives in M9. Until then the build's summary is on its Build page.",
    )
    await click($('[data-test="view-dashboard"]'))
    expect(router.currentRoute.value.fullPath).toBe(DASHBOARD)
  })

  it.each([
    [[] as Build[], 'No build for iteration 1 yet, so there is nothing to review.'],
    [[completed(1, 'running')], 'Iteration 1 is still building. Its report and dashboard open here when it completes.'],
    [[completed(1, 'interrupted')], 'This build stopped before it finished, so it has no report or dashboard.'],
  ])('does not open without a completed build: %#', async (builds, message) => {
    server.builds = builds
    await open(DASHBOARD)
    expect($('[data-test="dashboard-frame"]')).toBeNull()
    expect(text('[data-test="review-state"]')).toBe(message)
    expect(dashboardCalls()).toHaveLength(0)
  })
})

describe('the panels (seed-reuse-notes.md section 5.3 and 5.4, FR-D-3)', () => {
  it('draws the four bands and eleven panels at their spans on a twelve-column grid', async () => {
    await open(DASHBOARD)
    expect($$('[data-test="band"]').map((b) => b.dataset.band)).toEqual(['kpis', 'charts', 'focus', 'records'])
    expect($$('[data-panel]').map((p) => p.dataset.panel)).toEqual(ROOT.descriptor.panels.map((p) => p.id))
    expect($$('[data-test="cell"]').map((c) => c.style.gridColumn)).toEqual(ROOT.descriptor.panels.map((p) => `span ${p.span}`))
    expect($$('[data-test="chart-panel"] h3').map((h) => text(h))).toEqual([
      'Seats by vendor and product',
      'Entitled, assigned and active by product',
      'Assigned and in use, by month',
      'Recoverable cost by product',
    ])
  })

  it('formats every KPI from the payload, with the withheld seats beside the recoverable cost', async () => {
    await open(DASHBOARD)
    const panels = ROOT.payload.panels
    expect([kpi('k-entitled'), kpi('k-assigned'), kpi('k-active'), kpi('k-idle'), kpi('k-recoverable')]).toEqual([
      panels['k-entitled'].value!.toLocaleString('en-US'),
      panels['k-assigned'].value!.toLocaleString('en-US'),
      panels['k-active'].value!.toLocaleString('en-US'),
      panels['k-idle'].value!.toLocaleString('en-US'),
      '$1.0M',
    ])
    expect(text('[data-panel="k-recoverable"] [data-test="kpi-note"]')).toBe(`priced products only, ${panels['k-recoverable'].withheld_seats} seats withheld`)
    expect($$('[data-test="kpi"] h3').map((h) => text(h))).toEqual(['Entitled', 'Assigned', 'Active', 'Unused or underused', 'Recoverable a year'])
  })

  it("lists the five classes under the treemap with each one's share of entitled seats", async () => {
    await open(DASHBOARD)
    const items = $$('[data-test="legend-item"]').map((li) => text(li))
    expect(items).toEqual(ROOT.payload.panels['seats-treemap'].legend!.map((l) => `${l.label} ${l.share.toFixed(1)}% ${l.count.toLocaleString('en-US')}`))
  })

  it('gives the candidates a total row and the Seats table its class counts, total and pages', async () => {
    await open(DASHBOARD)
    const total = text('[data-panel="candidates"] [data-test="total-row"]')
    expect(total.startsWith('Total')).toBe(true)
    expect(total).toContain('$1,035,384')
    expect($$('[data-panel="candidates"] [data-test="row"]')).toHaveLength(17)
    expect($$('[data-panel="seats"] [data-test="row"]')).toHaveLength(25)
    expect(text('[data-test="footer-total"]')).toBe('13,050')
    expect(text('[data-test="page-range"]')).toBe('Seats 1 to 25 of 13,050, page 1 of 522')
    const withheld = $$('[data-panel="candidates"] [data-test="row"]').filter((r) => text(r).endsWith('Withheld'))
    expect(withheld.length).toBe(5)
  })

  it('pages and sorts the Seats table through the server, from the keyboard-reachable buttons', async () => {
    await open(DASHBOARD)
    const next = $('[data-test="page-next"]')!
    expect(next.tagName).toBe('BUTTON')
    expect($('[data-test="page-previous"]')!.getAttribute('aria-disabled')).toBe('true')
    await click(next)
    expect(dashboardCalls().at(-1)!.query.page).toBe('2')
    expect(text('[data-test="page-range"]')).toBe('Seats 26 to 50 of 13,050, page 2 of 522')
    expect($('[data-test="page-previous"]')!.getAttribute('aria-disabled')).toBeNull()
    await click($('[data-test="sort"][data-column="days_idle"]'))
    await click($('[data-test="sort"][data-column="days_idle"]'))
    expect(dashboardCalls().at(-1)!.query).toMatchObject({ sort: 'days_idle', direction: 'desc' })
    expect($('[data-test="sort"][data-column="days_idle"]')!.closest('th')!.getAttribute('aria-sort')).toBe('descending')
    expect(router.currentRoute.value.query.page).toBeUndefined() // page and sort are not in the URL
  })
})

describe('drill-down (FR-D-6, D-29)', () => {
  it('a treemap leaf drills vendor, product and class in one step, named in one crumb', async () => {
    await open(DASHBOARD)
    const leaf = ROOT.payload.panels['seats-treemap'].nodes![0].children![0].children!.find((n) => n.id === 'unused')!
    chartFor('seats-treemap').click({ step: leaf.step })
    await settle()
    expect(drillQuery()).toBe('microsoft.microsoft-365-e3.unused')
    expect(dashboardCalls().at(-1)!.query.drill).toBe('microsoft.microsoft-365-e3.unused')
    expect(crumbs()).toEqual(['All products', 'Microsoft › Microsoft 365 E3 › Unused'])
    // The deepest level: the Seats table lists that product's Unused seats only.
    const classes = $$('[data-panel="seats"] [data-test="row"]').map((r) => text(r.querySelectorAll('td')[6] as HTMLElement))
    expect(new Set(classes)).toEqual(new Set(['Unused']))
  })

  it('a bar drills to its product, and the drill bar Back pops one step', async () => {
    await open(DASHBOARD)
    const bar = ROOT.payload.panels.entitlement.categories!.find((c) => c.id === 'microsoft-365-e3')!
    chartFor('entitlement').click({ step: bar.step })
    await settle()
    expect(drillQuery()).toBe('microsoft.microsoft-365-e3')
    expect(crumbs()).toEqual(['All products', 'Microsoft › Microsoft 365 E3'])
    await click($('[data-test="drill-back"]'))
    expect(drillQuery()).toBe('')
    expect(crumbs()).toEqual(['All products'])
    expect($('[data-test="drill-back"]')!.getAttribute('aria-disabled')).toBe('true')
  })

  it("every panel follows the drill: the KPIs, the treemap and the tables are that level's", async () => {
    await open(DASHBOARD)
    await click($$('[data-panel="candidates"] [data-test="drill-row"]').find((b) => text(b) === 'Microsoft 365 E3')!)
    const level = dashboardFixture('product-step.json') as unknown as DashboardResponse
    expect(kpi('k-entitled')).toBe(level.payload.panels['k-entitled'].value!.toLocaleString('en-US'))
    expect(chartFor('seats-treemap').option.series[0].data.map((n: { id: string }) => n.id)).toEqual(
      level.payload.panels['seats-treemap'].nodes!.map((n) => n.id),
    )
    expect($$('[data-panel="candidates"] [data-test="row"]')).toHaveLength(1)
    expect(text('[data-test="page-range"]')).toBe(`Seats 1 to 25 of ${level.payload.panels.seats.total!.toLocaleString('en-US')}, page 1 of ${level.payload.panels.seats.pages}`)
  })

  it('reload keeps the drill path, crumbs included', async () => {
    await open(`${DASHBOARD}&drill=microsoft.microsoft-365-e3.unused`)
    await open(router.currentRoute.value.fullPath, true)
    expect(drillQuery()).toBe('microsoft.microsoft-365-e3.unused')
    expect(crumbs()).toEqual(['All products', 'Microsoft › Microsoft 365 E3 › Unused'])
    expect(dashboardCalls().at(-1)!.query.drill).toBe('microsoft.microsoft-365-e3.unused')
  })

  it("the browser's Back pops one step at a time", async () => {
    await open(DASHBOARD)
    chartFor('seats-treemap').click({ step: ['microsoft'] })
    await settle()
    chartFor('seats-treemap').click({ step: ['microsoft-365-e3'] })
    await settle()
    chartFor('seats-treemap').click({ step: ['unused'] })
    await settle()
    expect(drillQuery()).toBe('microsoft/microsoft-365-e3/unused')
    expect(crumbs()).toEqual(['All products', 'Microsoft', 'Microsoft 365 E3', 'Unused'])
    for (const [path, shown] of [
      ['microsoft/microsoft-365-e3', ['All products', 'Microsoft', 'Microsoft 365 E3']],
      ['microsoft', ['All products', 'Microsoft']],
      ['', ['All products']],
    ] as const) {
      router.back()
      await settle()
      expect(drillQuery()).toBe(path)
      expect(crumbs()).toEqual(shown)
    }
  })

  it('a crumb goes back to its step', async () => {
    await open(`${DASHBOARD}&drill=microsoft/microsoft-365-e3/unused`)
    await click($$('[data-test="crumb"] button').find((b) => text(b) === 'Microsoft')!)
    expect(drillQuery()).toBe('microsoft')
    expect(crumbs()).toEqual(['All products', 'Microsoft'])
  })

  it('a drill path the data does not have reopens at All products and says so', async () => {
    await open(`${DASHBOARD}&drill=nobody`)
    expect(drillQuery()).toBe('')
    expect(text('[data-test="drill-notice"]')).toBe('The drill path in the address is not in the data, so the dashboard opened at All products.')
    expect(crumbs()).toEqual(['All products'])
  })

  it('an answer to an older request never replaces a newer one', async () => {
    await open(DASHBOARD)
    holding = true
    // Two quick clicks on what is still on screen: a vendor, then a leaf.
    chartFor('seats-treemap').click({ step: ['microsoft'] })
    await settle()
    chartFor('seats-treemap').click({ step: ['microsoft', 'microsoft-365-e3', 'unused'] })
    await settle()
    expect(held).toHaveLength(2)
    expect(drillQuery()).toBe('microsoft.microsoft-365-e3.unused')
    held[1]()
    await settle()
    held[0]()
    await settle()
    expect(crumbs()).toEqual(['All products', 'Microsoft › Microsoft 365 E3 › Unused'])
  })
})

describe('keyboard (NFR-6)', () => {
  it('a chart takes focus; the arrow keys choose a target, read out under it; Enter drills', async () => {
    await open(DASHBOARD)
    const frame = $('[data-panel="entitlement"] [data-test="chart-frame"]')!
    expect(frame.tabIndex).toBe(0)
    frame.focus()
    await settle()
    const targets = ROOT.payload.panels.entitlement.targets!
    expect(text('[data-panel="entitlement"] [data-test="chart-readout"]')).toBe(`${targets.length} to drill into. Use the arrow keys to choose one.`)
    await key(frame, 'ArrowDown')
    await key(frame, 'ArrowDown')
    expect(text('[data-panel="entitlement"] [data-test="chart-readout"]')).toBe(
      `${targets[1].label}: ${targets[1].value!.toLocaleString('en-US')}. Press Enter to drill in.`,
    )
    expect(chartFor('entitlement').actions.at(-1)).toEqual({ type: 'showTip', seriesIndex: 0, dataIndex: 1 })
    await key(frame, 'End')
    await key(frame, 'ArrowDown') // wraps to the first
    await key(frame, 'Enter')
    expect(drillQuery()).toBe(targets[0].step.join('.'))
  })

  it('the treemap drills one level at a time from the keyboard', async () => {
    await open(DASHBOARD)
    const frame = $('[data-panel="seats-treemap"] [data-test="chart-frame"]')!
    frame.focus()
    await key(frame, 'ArrowRight')
    await key(frame, ' ')
    expect(drillQuery()).toBe(ROOT.payload.panels['seats-treemap'].targets![0].step.join('.'))
  })

  it('Back, crumbs, product cells, sort headers and pages are buttons', async () => {
    await open(`${DASHBOARD}&drill=microsoft/microsoft-365-e3`)
    expect($('[data-test="drill-back"]')!.tagName).toBe('BUTTON')
    expect($$('[data-test="crumb"] button').map((b) => text(b))).toEqual(['All products', 'Microsoft'])
    expect($$('[data-test="sort"]').every((b) => b.tagName === 'BUTTON')).toBe(true)
    expect($$('[data-test="pagination"] button').map((b) => text(b))).toEqual(['First', 'Previous', 'Next', 'Last'])
    expect($$('[tabindex="-1"]').filter((el) => el.closest('[data-test="dashboard"]'))).toEqual([])
  })
})

describe('theme and fonts (seed-reuse-notes.md section 1.2 and 1.4)', () => {
  it('a theme switch with the dashboard open repaints every chart in the other theme', async () => {
    await open(DASHBOARD)
    const bars = chartFor('entitlement')
    const before = bars.options.length
    const light = bars.option.series[1].itemStyle.color
    applyTheme('dark')
    await settle()
    expect(bars.options.length).toBe(before + 1)
    expect(bars.option.series[1].itemStyle.color).not.toBe(light)
    expect(bars.option.series[1].itemStyle.color).toBe('#5b8cff') // dark --chart-series-1
    for (const id of ['seats-treemap', 'trend', 'recoverable']) expect(chartFor(id).options.length).toBeGreaterThan(1)
  })

  it('repaints once the bundled fonts have loaded', async () => {
    let loaded!: () => void
    const ready = new Promise<void>((r) => (loaded = r))
    vi.stubGlobal('document', document)
    Object.defineProperty(document, 'fonts', { value: { ready, addEventListener() {}, removeEventListener() {} }, configurable: true })
    try {
      await open(DASHBOARD)
      const painted = chartFor('trend').options.length
      loaded()
      await settle()
      expect(chartFor('trend').options.length).toBe(painted + 1)
    } finally {
      delete (document as { fonts?: unknown }).fonts
    }
  })

  it('disposes its charts when it closes', async () => {
    await open(DASHBOARD)
    const live = charts.filter((c) => !c.disposed)
    expect(live).toHaveLength(4)
    await click($('[data-test="back-to-report"]'))
    expect(live.every((c) => c.disposed)).toBe(true)
  })
})
