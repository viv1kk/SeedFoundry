// The build report on screen and its finding links (FR-R-1, FR-R-2, FR-R-4, AC-2, ui-spec.md
// sections 4 and 5, D-64, D-65), against tests/fake-server.ts, which serves the reports the backend
// assembled for the sample's two builds (tests/fixtures/reports/), and a recorder in place of
// ECharts. Clicking a dashboard finding opens the dashboard at All products with its panels
// outlined; iteration 1's "N findings" link goes back to the report.

import { mount, type VueWrapper } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, type Router } from 'vue-router'
import App from '../src/App.vue'
import { consoleLines } from '../src/stepper'
import type { Report } from '../src/report'
import { createAppRouter } from '../src/router'
import { useLabStore, type Build } from '../src/stores/lab'
import { applyTheme } from '../src/theme'
import { buildRecord } from './build-script'
import { charts } from './fake-echarts'
import { FakeServer, reportFixture, sampleBuildEvents } from './fake-server'

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
const TWO = reportFixture(2) as unknown as Report
const ROOT = resolve(__dirname, '..')
const TOKENS_CSS = readFileSync(resolve(ROOT, 'src/styles/tokens.css'), 'utf8')
const CATALOGUE = ['N-1', 'N-2', 'N-3', 'N-4', 'N-5', 'V-1', 'V-2', 'V-3', 'V-4', 'V-5', 'V-6', 'V-7', 'V-8', 'L-1']

let server: FakeServer
let wrapper: VueWrapper | null = null
let router: Router
let history: ReturnType<typeof createMemoryHistory>

async function settle(times = 6): Promise<void> {
  for (let i = 0; i < times; i++) await new Promise((r) => setTimeout(r))
}

function completed(iteration = 1, status: Build['status'] = 'completed'): Build {
  return buildRecord({ id: `b-${iteration}`, iteration, status })
}

beforeEach(() => {
  server = new FakeServer()
  server.builds = [completed(1), completed(2)]
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

const $ = (selector: string, root: ParentNode = document) => root.querySelector<HTMLElement>(selector)
const $$ = (selector: string, root: ParentNode = document) => Array.from(root.querySelectorAll<HTMLElement>(selector))
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
const reportCalls = () => server.calls.filter((c) => /\/report$/.test(c.path))
const highlighted = () => $$('[data-highlight="finding"] > [data-panel]').map((el) => el.dataset.panel)
const findingRow = (id: string) => $(`[data-test="finding"][data-finding="${id}"]`)!

describe('the report (FR-R-1, ui-spec.md section 4)', () => {
  it('shows the verdict, iteration, duration and counts; findings are a caution, not a fault (D-64)', async () => {
    await open('/review/1')
    expect(text('main h1')).toBe('Review, iteration 1')
    expect(text('[data-test="build-report"] h2')).toBe('Build Report')
    const verdict = $('[data-test="report-verdict"]')!
    expect([text(verdict), verdict.className.match(/chip--(\w+)/)?.[1]]).toEqual(['Completed with findings', 'warning'])
    expect($$('[data-test="report-fact"]').map((d) => d.textContent)).toEqual([
      '1 of 2',
      '01:15 simulated',
      '11, 2 with findings',
      '21: 15 passed, 5 warned, 1 failed',
      '14',
      '0',
      '3',
    ])
  })

  it('groups the findings Numeric, Visual, Latency, Boundary, each with expected and shown (FR-R-2, AC-2)', async () => {
    await open('/review/1')
    expect($$('[data-test="finding-group"]').map((g) => [g.dataset.group, $$('[data-test="finding"]', g).map((r) => r.dataset.finding)])).toEqual([
      ['Numeric', CATALOGUE.slice(0, 5)],
      ['Visual', CATALOGUE.slice(5, 13)],
      ['Latency', ['L-1']],
      ['Boundary', []],
    ])
    expect(text('[data-group="Boundary"] [data-test="group-none"]')).toBe('None.')
    for (const finding of ONE.groups.flatMap((g) => g.findings)) {
      const row = findingRow(finding.id)
      expect(text($('[data-test="finding-expected"]', row))).toBe(finding.expected)
      expect(text($('[data-test="finding-shown"]', row))).toBe(finding.shown)
      expect(text($('[data-test="finding-where"]', row))).toBe(finding.panel_titles!.join(', '))
      expect(text(row)).toContain(finding.message!)
    }
    const n1 = findingRow('N-1')
    expect(text($('[data-test="finding-expected"]', n1))).toBe('13,050')
    expect(text($('[data-test="finding-shown"]', n1))).toBe('15,660')
    expect(text(n1)).toContain('Harvest Validation')
    expect(text(findingRow('L-1'))).toContain('Stress & Probe')
  })

  it('marks severity: high in the negative status, medium in the warning status', async () => {
    await open('/review/1')
    const chip = (id: string) => $('[data-test="finding-severity"]', findingRow(id))!
    expect([text(chip('N-1')), chip('N-1').className.match(/chip--(\w+)/)?.[1]]).toEqual(['High', 'negative'])
    expect([text(chip('V-8')), chip('V-8').className.match(/chip--(\w+)/)?.[1]]).toEqual(['Medium', 'warning'])
    expect([text(chip('L-1')), chip('L-1').className.match(/chip--(\w+)/)?.[1]]).toEqual(['Medium', 'warning'])
  })

  it('lists every test with its phase, name and result', async () => {
    await open('/review/1')
    const rows = $$('[data-test="test-row"]')
    expect(rows.map((r) => r.dataset.testId)).toEqual(ONE.tests.map((t) => t.id))
    expect(rows).toHaveLength(21)
    const results = Object.fromEntries(rows.map((r) => [r.dataset.testId, text($('[data-test="test-result"]', r))]))
    expect(Object.entries(results).filter(([, r]) => r !== 'Passed')).toEqual([
      ['T-15', 'Warned'],
      ['T-16', 'Failed'],
      ['T-17', 'Warned'],
      ['T-18', 'Warned'],
      ['T-19', 'Warned'],
      ['T-20', 'Warned'],
    ])
    expect(text(rows[12])).toContain('Stress & Probe')
    expect(text(rows[12])).toContain('Protection probes')
  })

  it('lists the auto-resolved gates and the simulated usage, labelled as simulated', async () => {
    await open('/review/1')
    expect($$('[data-test="gate"]').map((g) => text(g))).toEqual(
      ONE.gates.map((g) => `${g.id} ${g.kind}, ${g.stage} Resolved: ${g.resolution}. Basis: ${g.basis!.file}, ${g.basis!.section}`),
    )
    const u = ONE.usage
    expect($$('[data-test="usage-fact"]').map((d) => d.textContent)).toEqual([
      String(u.llm_calls),
      u.tokens_in.toLocaleString('en-US'),
      u.tokens_out.toLocaleString('en-US'),
      String(u.api_calls),
      `${u.sandbox_seconds.toFixed(1)} s`,
    ])
    expect(text('[data-test="usage-note"]')).toBe('Simulated: no model, Seed API or sandbox was called.')
  })

  it('iteration 2 passes with no findings and no Rebuild (D-6)', async () => {
    await open('/review/2')
    const verdict = $('[data-test="report-verdict"]')!
    expect([text(verdict), verdict.className.match(/chip--(\w+)/)?.[1]]).toEqual(['Passed', 'positive'])
    expect($$('[data-test="group-none"]')).toHaveLength(4)
    expect($$('[data-test="test-row"] [data-test="test-result"]').every((c) => text(c) === 'Passed')).toBe(true)
    expect($$('[data-test="report-actions"] button').map((b) => text(b))).toEqual(['View Dashboard', 'Approve'])
    expect(TWO.counts.findings).toBe(0)
  })

  it('is the same on the Build page, loaded once per build', async () => {
    server.buildEvents.set('b-1', sampleBuildEvents())
    await open('/review/1')
    const onReview = text('[data-test="build-report"]')
    await router.push('/build/1')
    await settle()
    expect(text('[data-test="build-report"]')).toBe(onReview)
    expect(reportCalls()).toHaveLength(1)
  })

  it('says why when the report cannot be loaded, and tries again', async () => {
    server.refuseNext((c) => /\/report$/.test(c.path), 409, 'report_not_ready', 'Build b-1 has not completed, so it has no report.')
    await open('/review/1')
    expect(text('[data-test="report-error"]')).toContain('Build b-1 has not completed, so it has no report.')
    await click($('[data-test="report-error"] button'))
    expect(text('[data-test="report-verdict"]')).toBe('Completed with findings')
  })
})

describe('the sample build on the Build page (FR-B-4, build-simulation.md section 4)', () => {
  it('writes each finding into the log in phases 9 and 10, as it is found', async () => {
    const events = sampleBuildEvents()
    server.buildEvents.set('b-1', events)
    await open('/build/1')
    const findings = events.filter((e) => e.type === 'finding.raised')
    expect(findings.map((e) => e.code)).toEqual(['L-1', 'N-1', 'N-2', 'N-3', 'N-4', 'N-5', 'V-1', 'V-4', 'V-5', 'V-2', 'V-3', 'V-6', 'V-7', 'V-8'])
    expect(new Set(findings.map((e) => e.phase))).toEqual(new Set(['probe', 'harvest']))
    const shown = $$('[data-test="console-line"] .line__message').map((el) => el.textContent ?? '')
    expect(shown).toEqual(consoleLines(events).map((l) => l.message))
    expect(shown).toContain('L-1 Panel "Seats by vendor and product" responds in 4.5 s (budget 1.0 s)')
    expect(shown).toContain('N-1 Entitled seats: KPI shows 13,050, product chart sums to 15,660; 18 problems in all')
    const chips = $$('[data-test="phase-chip"]').map((c) => text(c))
    expect([chips[8], chips[9]]).toEqual(['Findings: 1', 'Findings: 13'])
  })
})

describe('finding links and the highlight (ui-spec.md sections 4 and 5, D-65)', () => {
  it('each dashboard finding is a link to the dashboard at All products with that finding', async () => {
    await open('/review/1')
    const links = $$('[data-test="finding-link"]')
    expect(links.map((a) => a.tagName)).toEqual(Array(14).fill('A'))
    expect(links.map((a) => a.getAttribute('href'))).toEqual(CATALOGUE.map((id) => `/review/1?dashboard=license-optimization&finding=${id}`))
    expect(text(links[0])).toBe('N-1: show on the dashboard')
  })

  it('clicking N-1 opens the dashboard with the product chart outlined and says which finding it is', async () => {
    await open('/review/1')
    await click($('[data-finding="N-1"] [data-test="finding-link"]'))
    expect(router.currentRoute.value.fullPath).toBe('/review/1?dashboard=license-optimization&finding=N-1')
    expect(highlighted()).toEqual(['entitlement'])
    expect(text('[data-test="finding-note"]')).toBe(
      'Showing N-1 on Entitled, assigned and active by product. Entitled seats: KPI shows 13,050, product chart sums to 15,660; 18 problems in all Clear highlight',
    )
    expect(document.activeElement).toBe($('[data-test="finding-note"]'))
  })

  it.each([
    ['V-3', ['seats-treemap', 'entitlement'], 'Seats by vendor and product and Entitled, assigned and active by product'],
    ['V-6', ['k-assigned', 'k-active', 'k-idle', 'seats-treemap', 'seats'], 'Assigned, Active, Unused or underused, Seats by vendor and product and Seats'],
    ['V-8', ['candidates'], 'Optimisation candidates'],
  ])('a finding on several panels outlines them all: %s', async (id, panels, names) => {
    await open(`/review/1?dashboard=license-optimization&finding=${id}`)
    expect(highlighted().sort()).toEqual([...panels].sort())
    expect(text('[data-test="finding-note"]')).toContain(`Showing ${id} on ${names}.`)
  })

  it("L-1 outlines the treemap's card while it still waits, spinner inside", async () => {
    await open('/review/1?dashboard=license-optimization&finding=L-1')
    expect(latency.waits).toHaveLength(1)
    expect(highlighted()).toEqual(['seats-treemap'])
    expect($('[data-highlight="finding"] [data-test="chart-waiting"]')).not.toBeNull()
    latency.waits[0].release()
    await settle()
    expect(highlighted()).toEqual(['seats-treemap'])
  })

  it('a reload keeps the highlight; a drill drops it', async () => {
    await open('/review/1?dashboard=license-optimization&finding=N-5')
    await open(router.currentRoute.value.fullPath, true)
    expect(highlighted()).toEqual(['candidates'])
    await click($$('[data-panel="candidates"] [data-test="drill-row"]').find((b) => text(b) === 'Microsoft 365 E3')!)
    expect(router.currentRoute.value.query.finding).toBeUndefined()
    expect(router.currentRoute.value.query.drill).toBeTruthy()
    expect(highlighted()).toEqual([])
    expect($('[data-test="finding-note"]')).toBeNull()
  })

  it('Clear highlight removes it; an unknown finding highlights nothing and says so', async () => {
    await open('/review/1?dashboard=license-optimization&finding=V-2')
    expect(highlighted()).toEqual(['trend'])
    await click($('[data-test="clear-highlight"]'))
    expect(router.currentRoute.value.fullPath).toBe('/review/1?dashboard=license-optimization')
    expect(highlighted()).toEqual([])
    await open('/review/1?dashboard=license-optimization&finding=V-99')
    expect(highlighted()).toEqual([])
    expect(text('[data-test="finding-note"]')).toBe("No finding V-99 in this build's report, so nothing is highlighted.")
  })

  it('the outline is SeedFoundry\'s own accent, outside the defect overlay\'s sheet (NFR-5, R-1)', () => {
    const renderer = readFileSync(resolve(ROOT, 'src/components/dashboard/DashboardRenderer.vue'), 'utf8')
    expect(renderer).toMatch(/\.renderer__cell--finding > \[data-panel\] \{\s*outline: 2px solid var\(--accent\);/)
    const defects = readFileSync(resolve(ROOT, 'src/styles/defects.css'), 'utf8')
    expect(defects).not.toMatch(/highlight|finding|outline/)
  })
})

describe('"N findings" in the dashboard frame (ui-spec.md section 5)', () => {
  it('iteration 1 links its real count back to the report', async () => {
    await open('/review/1?dashboard=license-optimization')
    const link = $('[data-test="findings-link"]')!
    expect([text(link), link.getAttribute('href')]).toEqual([`${ONE.counts.findings} findings`, '/review/1'])
    expect(text(link)).toBe('14 findings')
    await click(link)
    expect(router.currentRoute.value.fullPath).toBe('/review/1')
    expect(text('[data-test="report-verdict"]')).toBe('Completed with findings')
  })

  it('iteration 2 has none', async () => {
    await open('/review/2?dashboard=license-optimization')
    expect($('[data-test="findings-link"]')).toBeNull()
  })
})

describe('keyboard and screen readers (NFR-6)', () => {
  it('every finding link and action is a link or a button; tables have captions and column headers', async () => {
    await open('/review/1')
    const report = $('[data-test="build-report"]')!
    for (const control of $$('a, button', report)) {
      expect(['A', 'BUTTON']).toContain(control.tagName)
      expect(control.getAttribute('tabindex')).not.toBe('-1')
    }
    const tables = $$('table', report)
    expect(tables).toHaveLength(4) // three groups with findings, and the tests
    for (const table of tables) {
      expect(text($('caption', table))).not.toBe('')
      expect($$('thead th', table).every((th) => th.getAttribute('scope') === 'col')).toBe(true)
      expect($$('tbody th', table).every((th) => th.getAttribute('scope') === 'row')).toBe(true)
    }
    for (const section of $$('section', report)) {
      const label = section.getAttribute('aria-labelledby')
      expect(label && document.getElementById(label)?.textContent?.trim()).toBeTruthy()
    }
  })
})
