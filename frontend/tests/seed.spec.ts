// The Seed page and Approve (FR-F-1 to FR-F-5, FR-R-4, AC-4, AC-5, ui-spec.md section 7, D-73 to D-75),
// against tests/fake-server.ts, which serves the Seed page data the backend assembled for approving
// the sample's iteration 1 or iteration 2 (tests/fixtures/seed/). Both approval paths: every section of
// section 7; the feedback disclosure; Preview through the sanitiser; downloads as relative /api links;
// no text saying which Knowledge file fed which Seed file; the page before approval; Approve's rules
// on the reports; Reset; and the keyboard.

import { mount, type VueWrapper } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, type Router } from 'vue-router'
import App from '../src/App.vue'
import { createAppRouter } from '../src/router'
import type { SeedPackage } from '../src/seed'
import { useLabStore, type Build } from '../src/stores/lab'
import { buildRecord } from './build-script'
import { FakeServer, seedFixture } from './fake-server'

class FakeEventSource {
  static last: FakeEventSource | null = null
  listeners = new Map<string, (message: MessageEvent) => void>()
  onopen: (() => void) | null = null
  onerror: (() => void) | null = null
  constructor() {
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

const ONE = seedFixture(1) as unknown as SeedPackage
const TWO = seedFixture(2) as unknown as SeedPackage
const CATALOGUE = ['N-1', 'N-2', 'N-3', 'N-4', 'N-5', 'V-1', 'V-2', 'V-3', 'V-4', 'V-5', 'V-6', 'V-7', 'V-8', 'L-1']
const INTAKE_NAMES = ['person.md', 'instrument-awareness.md', 'environment.md', 'music.md', 'vendor-notes.md']
const HOSTILE = readFileSync(resolve(__dirname, 'fixtures/hostile.md'), 'utf8')

let server: FakeServer
let wrapper: VueWrapper | null = null
let router: Router

async function settle(times = 6): Promise<void> {
  for (let i = 0; i < times; i++) await new Promise((r) => setTimeout(r))
}

const completed = (iteration: number, status: Build['status'] = 'completed') => buildRecord({ id: `b-${iteration}`, iteration, status })

/** The lab after iteration 1, or after the rebuild and iteration 2. */
function builtTo(iteration: 1 | 2): void {
  server.builds = iteration === 1 ? [completed(1)] : [completed(1), completed(2)]
  server.iteration = iteration
}

beforeEach(() => {
  server = new FakeServer()
  vi.stubGlobal('fetch', (input: RequestInfo | URL, init?: RequestInit) => server.fetch(input, init))
  vi.stubGlobal('EventSource', FakeEventSource)
  FakeEventSource.last = null
})

afterEach(() => {
  wrapper?.unmount()
  wrapper = null
  vi.unstubAllGlobals()
  document.body.innerHTML = ''
})

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
const approveButton = () => $('[data-test="report-actions"] [data-action="approve"]')

/** Approve iteration `iteration` from its report, as a user does, and land on the Seed page. */
async function approveFromReport(iteration: 1 | 2): Promise<void> {
  builtTo(iteration)
  await open(`/review/${iteration}`)
  await click(approveButton())
  expect(router.currentRoute.value.fullPath).toBe('/seed')
}

describe('Approve on the report (FR-R-4, FR-F-1, D-73, D-75)', () => {
  it.each([1, 2] as const)('approves iteration %i, records it and opens the Seed page', async (iteration) => {
    await approveFromReport(iteration)
    expect(server.writes().map((c) => [c.path, c.body])).toEqual([['/api/seed/approve', { build_id: `b-${iteration}` }]])
    expect(useLabStore().snapshot?.approval).toMatchObject({ iteration, build_id: `b-${iteration}` })
    expect(text('[data-test="seed-name"]')).toBe('License Optimization')
    // The page came with the approval: no second request for it.
    expect(server.calls.filter((c) => c.path === '/api/seed')).toEqual([])
  })

  it("iteration 1's report offers no Approve once iteration 2 has started, and says why (D-73)", async () => {
    builtTo(2)
    await open('/review/1')
    const approve = approveButton()!
    expect(approve.getAttribute('aria-disabled')).toBe('true')
    const why = 'Iteration 2 was rebuilt from this report, so iteration 2 is the one to approve.'
    expect(text(document.getElementById(approve.getAttribute('aria-describedby')!))).toBe(why)
    await click(approve)
    expect(text('[data-test="report-status"]')).toBe(why)
    expect(server.writes()).toEqual([])
    expect(router.currentRoute.value.fullPath).toBe('/review/1')
  })

  it('says the server refusal and stays on the report', async () => {
    builtTo(1)
    await open('/review/1')
    server.refuseNext((c) => c.path === '/api/seed/approve', 409, 'build_running', 'A build is running. Approve once it has finished.')
    await click(approveButton())
    expect(text('[data-test="report-status"]')).toBe('A build is running. Approve once it has finished.')
    expect(router.currentRoute.value.fullPath).toBe('/review/1')
  })

  it('once approved, every report says so and links to the Seed instead of offering Approve', async () => {
    builtTo(2)
    server.approval = { iteration: 2, build_id: 'b-2', approved_at: '2026-10-04T12:00:00.000+00:00' }
    await open('/review/2')
    expect(approveButton()).toBeNull()
    expect(text('[data-test="report-approved"]')).toBe('This build is the approved Seed. Go to the Seed')
    await router.push('/review/1')
    await settle()
    expect(text('[data-test="report-approved"]')).toBe('The Seed was approved at iteration 2. Go to the Seed')
    await click($('[data-test="report-approved"] a'))
    expect(router.currentRoute.value.fullPath).toBe('/seed')
  })
})

describe('the Seed page, iteration 2 approved (AC-4, ui-spec.md section 7)', () => {
  beforeEach(async () => {
    await approveFromReport(2)
  })

  it('hero: the Seed name, Approved, the iteration and the date', () => {
    expect(text('[data-test="seed-name"]')).toBe('License Optimization')
    expect($('[data-test="seed-approved"]')?.className).toContain('chip--positive')
    expect(text('[data-test="seed-approval"]')).toBe(`Approved at iteration 2, on 4 October 2026. Intake fingerprint ${TWO.fingerprint}`)
  })

  it('what this Seed does: the Purpose, rendered', () => {
    const items = $$('[data-test="seed-purpose"] [data-test="preview"] li').map((li) => text(li))
    expect(items).toEqual(TWO.purpose.text.split('\n').map((line) => line.replace(/^- /, '')))
  })

  it('tests conducted: every phase with its tests and result', () => {
    expect(text('[data-test="seed-tests"] .seed__lead')).toBe('21 tests in 11 phases: 21 passed. Verdict Passed Read the full report')
    const rows = $$('[data-test="seed-phase"]')
    expect(rows.map((row) => text($('th', row)))).toEqual(TWO.phases.map((p) => `${p.index}. ${p.name}`))
    expect(rows.map((row) => text($('[data-test="seed-phase-result"]', row)))).toEqual(Array(11).fill('Passed'))
    expect(rows.flatMap((row) => $$('li', row).map((li) => text(li).split(' ')[0]))).toEqual(TWO.phases.flatMap((p) => p.tests.map((t) => t.id)))
  })

  it('iteration history: iteration 1, the observer feedback, then iteration 2 approved', () => {
    const items = $$('[data-test="history-item"]')
    expect(items.map((i) => i.dataset.kind)).toEqual(['iteration', 'feedback', 'iteration'])
    expect(text($('[data-test="history-detail"]', items[0]))).toBe('14 findings. Read its report')
    expect(text($('[data-test="history-verdict"]', items[0]))).toBe('Completed with findings')
    expect(text($('[data-test="history-detail"]', items[1]))).toBe('observer-feedback-iteration-1.md: 9 of 10 segments went into 4 Knowledge files.')
    expect(text($('[data-test="history-detail"]', items[2]))).toBe('0 findings; 14 of 14 iteration 1 findings resolved. Read its report')
    expect(text($('[data-test="history-approved"]', items[2]))).toBe('Approved')
    expect($('[data-test="history-approved"]', items[0])).toBeNull()
  })

  it('the observer feedback is a disclosure that expands and collapses (NFR-6)', async () => {
    const toggle = $('[data-test="feedback-toggle"]')!
    const panel = document.getElementById(toggle.getAttribute('aria-controls')!)!
    expect(toggle.tagName).toBe('BUTTON')
    expect([toggle.getAttribute('aria-expanded'), panel.style.display]).toEqual(['false', 'none'])
    await click(toggle)
    expect([toggle.getAttribute('aria-expanded'), panel.style.display, text(toggle)]).toEqual(['true', '', 'Hide the feedback'])
    expect(text(panel)).toContain('N-1 to N-5: the totals do not add up.')
    await click(toggle)
    expect([toggle.getAttribute('aria-expanded'), panel.style.display, text(toggle)]).toEqual(['false', 'none', 'Show the feedback'])
  })

  it('has no known issues', () => {
    expect($('[data-test="seed-known-issues"]')).toBeNull()
  })

  it('Seed files: three cards with a description, size, Preview and Download, then Download all (.zip)', () => {
    const cards = $$('[data-test="seed-file"]')
    expect(cards.map((c) => c.dataset.file)).toEqual(['core.md', 'adaptation.md', 'protection.md'])
    expect(cards.map((c) => text($('[data-test="seed-file-description"]', c)))).toEqual(TWO.files.map((f) => f.description))
    expect(cards.map((c) => text($('[data-test="seed-file-size"]', c)))).toEqual(TWO.files.map((f) => `${(f.bytes / 1024).toFixed(1)} KB`))
    for (const card of cards) {
      const name = card.dataset.file!
      expect(text($('[data-action="preview"]', card))).toBe('Preview')
      const download = $('a[data-action="download"]', card)!
      expect([download.getAttribute('href'), download.getAttribute('download')]).toEqual([`/api/seed/files/${name}`, name])
    }
    const zip = $('a[data-action="download-zip"]')!
    expect([text(zip), zip.getAttribute('href'), zip.getAttribute('download')]).toEqual(['Download all (.zip)', '/api/seed/zip', 'license-optimization-seed.zip'])
  })

  it('Preview opens the file in a modal; Escape closes it and puts focus back', async () => {
    const button = $('[data-file="protection.md"] [data-action="preview"]')!
    button.focus()
    await click(button)
    const dialog = $('[role="dialog"][data-modal="seed-preview"]')!
    expect(text($('h2', dialog))).toBe('Preview: protection.md')
    expect(text($('[data-test="preview"]', dialog))).toContain('Every part-to-whole chart must reconcile to its total.')
    dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await settle()
    expect($('[role="dialog"]')).toBeNull()
    expect(document.activeElement).toBe(button)
  })

  it('names no Knowledge file anywhere on the page, the feedback opened (D-9)', async () => {
    await click($('[data-test="feedback-toggle"]'))
    const page = text('[data-test="seed"]')
    for (const name of INTAKE_NAMES) expect(page).not.toContain(name)
    expect(page).not.toMatch(/built from|comes from|drawn from|mapped from/i)
  })

  it('every control is a button or a link the keyboard reaches', () => {
    const controls = $$('[data-test="seed"] button, [data-test="seed"] a')
    expect(controls.length).toBeGreaterThan(8)
    for (const control of controls) {
      expect(control.tagName === 'BUTTON' || control.hasAttribute('href')).toBe(true)
      expect(control.getAttribute('tabindex')).not.toBe('-1')
    }
  })
})

// D-81: the history runs through every iteration, each rejection's feedback between two of them.
describe('the Seed page, iteration 3 approved (D-80, D-81)', () => {
  beforeEach(async () => {
    const [first, feedback, second] = TWO.history
    const later = { ...feedback, rejected: 2, name: 'observer-feedback-iteration-2.md', content: 'Sort the candidates by saving.', segments: 6, routed: 5, files_updated: 4 }
    const history = [first, feedback, { ...second, approved: false }, later, { ...second, iteration: 3, build_id: 'b-3', resolved: 0, open: 0, prior_findings: 0, approved: true }]
    server.seedPatches.set(3, { history })
    server.builds = [completed(1), completed(2), completed(3)]
    server.iteration = 3
    await open('/review/3')
    await click(approveButton())
    expect(router.currentRoute.value.fullPath).toBe('/seed')
  })

  it('shows every iteration and each feedback, with no total, and its own disclosure for each feedback', async () => {
    expect(text('[data-test="seed-approval"]')).toContain('Approved at iteration 3,')
    const items = $$('[data-test="history-item"]')
    expect(items.map((i) => [i.dataset.kind, text($('.history__title', i))])).toEqual([
      ['iteration', 'Iteration 1'],
      ['feedback', 'Observer feedback'],
      ['iteration', 'Iteration 2'],
      ['feedback', 'Observer feedback'],
      ['iteration', 'Iteration 3'],
    ])
    expect(text($('[data-test="history-detail"]', items[3]))).toBe('observer-feedback-iteration-2.md: 5 of 6 segments went into 4 Knowledge files.')
    expect(text($('[data-test="history-detail"]', items[4]))).toBe('0 findings. Read its report')
    expect($$('[data-test="history-approved"]')).toHaveLength(1)
    const [firstToggle, secondToggle] = $$('[data-test="feedback-toggle"]')
    expect(firstToggle.getAttribute('aria-controls')).not.toBe(secondToggle.getAttribute('aria-controls'))
    await click(secondToggle)
    expect([firstToggle.getAttribute('aria-expanded'), secondToggle.getAttribute('aria-expanded')]).toEqual(['false', 'true'])
    expect(text(document.getElementById(secondToggle.getAttribute('aria-controls')!))).toBe('Sort the candidates by saving.')
  })
})

describe('the Seed page, iteration 1 approved (AC-5, FR-F-4)', () => {
  beforeEach(async () => {
    await approveFromReport(1)
  })

  it('lists every open finding as a known issue, and the history ends at iteration 1', () => {
    expect(text('[data-test="seed-approval"]')).toContain('Approved at iteration 1,')
    expect(text('[data-test="seed-known-issues"] .seed__lead')).toBe(
      'Approved at iteration 1 with 14 open findings. Each is also listed under Known issues in every Seed file.',
    )
    const rows = $$('[data-test="known-issue"]')
    expect(rows.map((r) => r.dataset.issue)).toEqual(CATALOGUE)
    expect(text($('th', rows[0]))).toBe(`N-1 ${ONE.known_issues[0].message}`)
    expect($$('[data-test="history-item"]').map((i) => i.dataset.kind)).toEqual(['iteration'])
    expect(text('[data-test="history-approved"]')).toBe('Approved')
    expect($('[data-test="feedback-toggle"]')).toBeNull()
  })

  it('tests conducted show the two phases with findings', () => {
    const results = $$('[data-test="seed-phase-result"]').map((chip) => text(chip))
    expect(results.filter((r) => r !== 'Passed')).toEqual(['Findings: 1', 'Findings: 13'])
    expect(text('[data-test="seed-tests"] .seed__lead')).toBe('21 tests in 11 phases: 15 passed, 5 warned, 1 failed. Verdict Completed with findings Read the full report')
  })

  it('each file in Preview has the Known issues section', async () => {
    for (const name of ['core.md', 'adaptation.md', 'protection.md']) {
      await click($(`[data-file="${name}"] [data-action="preview"]`))
      const preview = $('[role="dialog"] [data-test="preview"]')!
      expect($$('h2', preview).map((h) => text(h))).toContain('Known issues')
      await click($('[role="dialog"] .modal__close'))
    }
  })
})

describe('Preview is sanitised (D-40)', () => {
  it('a hostile file shows as text and loads or follows nothing', async () => {
    server.seedPatches.set(2, { files: TWO.files.map((f) => (f.name === 'core.md' ? { ...f, content: HOSTILE } : f)) })
    await approveFromReport(2)
    // The approval's own answer carries the page, so the patched file is what Preview shows.
    await click($('[data-file="core.md"] [data-action="preview"]'))
    const preview = $('[role="dialog"] [data-test="preview"]')!
    expect($$('script, iframe, object, embed, img, video, form, style, link, meta, base', preview)).toEqual([])
    expect($$('[src], [href], [style], [onerror], [onload]', preview)).toEqual([])
    expect(preview.textContent).toContain("<script>window.__hostile = 'script tag ran'</script>")
    expect((window as unknown as { __hostile?: string }).__hostile).toBeUndefined()
  })
})

describe('before approval, and Reset (D-46, D-75)', () => {
  it.each([
    ['no build', () => undefined, "Build the Seed from Knowledge first, then approve it from its report.", '/knowledge'],
    ['a running build', () => (server.builds = [completed(1, 'running')]), 'Iteration 1 is still building. Approve it from its report once it completes.', '/build/1'],
    ["iteration 1's report ready", () => builtTo(1), "Iteration 1's report is ready: approve it there to make it the Seed.", '/review/1'],
    ["iteration 2's report ready", () => builtTo(2), "Iteration 2's report is ready: approve it there to make it the Seed.", '/review/2'],
  ])('with %s, says there is no approved Seed and points the way', async (_, arrange, next, to) => {
    arrange()
    await open('/seed')
    expect(text('main h1')).toBe('Seed')
    expect(text('[data-test="seed-empty-reason"]')).toBe('No Seed is approved yet, so there are no Seed files to show.')
    expect(text('[data-test="seed-next"]')).toBe(next)
    expect($('[data-test="seed-next-link"]')?.getAttribute('href')).toBe(to)
    expect($('[data-test="seed-files"]')).toBeNull()
    expect(server.calls.filter((c) => c.path.startsWith('/api/seed'))).toEqual([])
  })

  it('Reset clears the approval: the page empties and the journey stops linking Seed', async () => {
    await approveFromReport(2)
    expect($$('nav[aria-label="Journey"] a').map((a) => text(a))).toEqual(['Knowledge', 'Seed'])
    await click($('nav[aria-label="Journey"] a[href="/seed"]'))
    await useLabStore().refresh()
    await settle()
    expect(text('[data-test="seed-name"]')).toBe('License Optimization')
    // Reset to start, as the demo controller sends it; the stream's demo.reset re-fetches the snapshot.
    await server.fetch('/api/demo/reset', { method: 'POST' })
    FakeEventSource.last!.emit({ type: 'demo.reset', seq: server.seq } as never)
    await settle()
    expect(text('[data-test="seed-empty-reason"]')).toBe('No Seed is approved yet, so there are no Seed files to show.')
    expect($$('nav[aria-label="Journey"] a').map((a) => text(a))).toEqual(['Knowledge'])
  })

  it('a reload of the Seed page loads the approved Seed from the server', async () => {
    builtTo(2)
    server.approval = { iteration: 2, build_id: 'b-2', approved_at: '2026-10-04T12:00:00.000+00:00' }
    await open('/seed')
    expect(server.calls.filter((c) => c.path === '/api/seed')).toHaveLength(1)
    expect(text('[data-test="seed-name"]')).toBe('License Optimization')
    expect($$('[data-test="seed-file"]')).toHaveLength(3)
  })
})
