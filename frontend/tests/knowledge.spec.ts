// The Knowledge page (ui-spec.md section 2): FR-IN-1 to FR-IN-11, FR-B-8, NFR-6.
// The page runs against tests/fake-server.ts, which keeps the intake API's rules.

import type { VueWrapper } from '@vue/test-utils'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Router } from 'vue-router'
import { nextTick } from 'vue'
import { AUTOSAVE_MS, useIntakeStore } from '../src/stores/intake'
import { useLabStore } from '../src/stores/lab'
import { FakeServer } from './fake-server'
import { mountApp } from './helpers'

const FIXTURES = resolve(__dirname, 'fixtures')
const fixture = (name: string) => readFileSync(resolve(FIXTURES, name), 'utf8')
const CORE_FIXTURES = ['person.md', 'instrument-awareness.md', 'environment.md', 'music.md']

let server: FakeServer
let wrapper: VueWrapper
let router: Router

async function settle(times = 4): Promise<void> {
  for (let i = 0; i < times; i++) await new Promise((r) => setTimeout(r))
}

async function open(path = '/knowledge'): Promise<void> {
  const mounted = await mountApp(path, server.snapshot())
  wrapper = mounted.wrapper
  router = mounted.router
  await settle()
}

const $ = <T extends Element = HTMLElement>(selector: string) => document.querySelector<T>(selector)
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

async function click(selector: string | Element | null): Promise<void> {
  const el = typeof selector === 'string' ? $(selector) : selector
  if (!el) throw new Error(`nothing to click: ${String(selector)}`)
  ;(el as HTMLElement).click()
  await settle()
}

async function press(key: string, target: Element | null = document.activeElement): Promise<void> {
  target?.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }))
  await settle()
}

async function type(selector: string, value: string): Promise<void> {
  const el = $<HTMLInputElement | HTMLTextAreaElement>(selector)!
  el.value = value
  el.dispatchEvent(new Event('input', { bubbles: true }))
  await settle(1)
}

async function choose(selector: string, value: string): Promise<void> {
  const el = $<HTMLSelectElement>(selector)!
  el.value = value
  el.dispatchEvent(new Event('change', { bubbles: true }))
  await settle(1)
}

async function pick(files: { name: string; content: string | Uint8Array<ArrayBuffer> }[]): Promise<void> {
  const input = $<HTMLInputElement>('[data-test="import-input"]')!
  const chosen = files.map((f) => new File([f.content], f.name))
  Object.defineProperty(input, 'files', { value: chosen, configurable: true })
  input.dispatchEvent(new Event('change', { bubbles: true }))
  await settle()
}

function fileButton(name: string): HTMLElement | undefined {
  return $$('[data-test="file-panel"] .file').find((b) => b.querySelector('.file__name')?.textContent === name)
}

function groupNames(category: string): string[] {
  return $$(`[data-category="${category}"] .file__name`).map((el) => el.textContent ?? '')
}

beforeEach(() => {
  server = new FakeServer()
  vi.stubGlobal('fetch', server.fetch)
})

afterEach(async () => {
  // Send any autosave still due to this test's server, so no timer outlives the test.
  vi.useRealTimers()
  await useIntakeStore().flushAll()
  wrapper?.unmount()
  vi.useRealTimers()
  vi.unstubAllGlobals()
  document.body.innerHTML = ''
})

describe('FR-IN-1: layout', () => {
  it('has the editor on the left and the file panel on the right', async () => {
    server.add('music.md', 'music', '# Tune')
    await open()
    const layout = $('.knowledge__layout')!
    expect(layout.children[0].querySelector('[data-test="editor"]')).not.toBeNull()
    expect(layout.children[1].matches('[data-test="file-panel"]')).toBe(true)
  })

  it('shows the name field and category picker above the toolbar', async () => {
    server.add('music.md', 'music', '# Tune')
    await open()
    const editor = $('[data-test="editor"]')!
    const parts = Array.from(editor.children).map((el) => el.className)
    expect(parts.indexOf('editor__meta')).toBeLessThan(parts.indexOf('editor__toolbar'))
    expect($<HTMLInputElement>('[data-test="name"]')?.value).toBe('music.md')
    expect(text('[data-test="category"] .menu-trigger')).toBe('Music')
  })
})

describe('FR-IN-2: every file has a name and one category', () => {
  it('groups files under their category in Ensemble order, from the server', async () => {
    server.add('vendor-notes.md', 'misc_context', 'v')
    server.add('music.md', 'music', 'm')
    server.add('person.md', 'person', 'p')
    await open()
    expect($$('[data-test="file-panel"] .group__title').map((el) => el.textContent)).toEqual([
      'Person',
      'Instrument Awareness',
      'Environment',
      'Music',
      'Misc Context',
    ])
    expect(groupNames('person')).toEqual(['person.md'])
    expect(groupNames('music')).toEqual(['music.md'])
    expect(groupNames('misc_context')).toEqual(['vendor-notes.md'])
  })

  it('offers exactly the five categories in the picker, with the current one checked', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await click('[data-test="category"] .menu-trigger')
    const items = $$('[role="menuitemradio"]')
    expect(items.map((i) => i.textContent?.trim())).toEqual(['Person', 'Instrument Awareness', 'Environment', 'Music', 'Misc Context'])
    expect(items.filter((i) => i.getAttribute('aria-checked') === 'true').map((i) => i.textContent?.trim())).toEqual(['Music'])
  })

  it('shows a muted "Add file" link in each empty category', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    expect($$('[data-add]').map((el) => el.getAttribute('data-add'))).toEqual(['person', 'instrument_awareness', 'environment', 'misc_context'])
  })
})

describe('FR-IN-3: one file per core category', () => {
  it('a new file in a filled core slot asks "Replace it?", naming the file, then replaces', async () => {
    server.add('person.md', 'person', 'old person')
    await open()
    await click('[data-test="new-file"]')
    await choose('[data-test="new-category"]', 'person')
    expect(text('[data-test="new-replace-warning"]')).toBe('Replaces existing person.md')
    await type('[data-test="new-name"]', 'player.md')
    await click('[data-test="new-create"]')
    expect(text('.modal__title')).toBe('Replace it?')
    expect(text('[data-test="new-confirm"]')).toBe('Person already has person.md. Replace it with player.md? person.md will be deleted.')
    expect(server.writes()).toEqual([])
    await click('[data-test="new-create"]')
    expect(server.writes().map((c) => c.body)).toEqual([{ name: 'player.md', category: 'person', content: '', replace: true }])
    expect(groupNames('person')).toEqual(['player.md'])
    expect(router.currentRoute.value.query.file).toBe('f-2')
  })

  it('a category change into a filled core slot asks first, then sends replace', async () => {
    server.add('person.md', 'person', 'p')
    server.add('draft.md', 'misc_context', 'd')
    await open('/knowledge?file=f-2')
    await click('[data-test="category"] .menu-trigger')
    await click('[data-item="person"]')
    expect(text('.modal__title')).toBe('Replace it?')
    expect(text('[data-test="confirm-body"]')).toBe('Person already has person.md. Replace it with draft.md? person.md will be deleted.')
    await click('[data-test="confirm-ok"]')
    expect(server.writes().map((c) => c.body)).toEqual([{ category: 'person', replace: true }])
    expect(groupNames('person')).toEqual(['draft.md'])
    expect(groupNames('misc_context')).toEqual([])
  })

  it("cancelling the question changes nothing", async () => {
    server.add('person.md', 'person', 'p')
    server.add('draft.md', 'misc_context', 'd')
    await open('/knowledge?file=f-2')
    await click('[data-test="category"] .menu-trigger')
    await click('[data-item="person"]')
    await click('[data-test="confirm-cancel"]')
    expect(server.writes()).toEqual([])
    expect(groupNames('person')).toEqual(['person.md'])
  })

  it("the server's 409 core_slot_taken is the backstop: it asks with the server's message", async () => {
    await open()
    server.add('music.md', 'music', 'added elsewhere') // the snapshot here has not heard of it
    await click('[data-test="new-file"]')
    await choose('[data-test="new-category"]', 'music')
    await click('[data-test="new-create"]')
    expect(server.writes()).toHaveLength(1)
    expect(text('[data-test="new-confirm"]')).toBe('Music already has music.md. Replace it with music.md? music.md will be deleted.')
    await click('[data-test="new-create"]')
    expect(server.writes()[1].body).toMatchObject({ category: 'music', replace: true })
  })

  it('Misc Context takes any number of files without asking', async () => {
    server.add('a.md', 'misc_context', 'a')
    await open()
    await click('[data-test="new-file"]')
    await choose('[data-test="new-category"]', 'misc_context')
    await type('[data-test="new-name"]', 'b.md')
    await click('[data-test="new-create"]')
    expect(server.writes().map((c) => c.body)).toEqual([{ name: 'b.md', category: 'misc_context', content: '', replace: false }])
    expect(groupNames('misc_context')).toEqual(['a.md', 'b.md'])
  })
})

describe('FR-IN-4: Edit and Preview', () => {
  beforeEach(() => {
    server.add('environment.md', 'environment', fixture('environment.md'))
  })

  it('Edit is the raw markdown in a monospace textarea', async () => {
    await open()
    const area = $<HTMLTextAreaElement>('[data-test="text"]')!
    expect(area.value).toBe(fixture('environment.md'))
    expect(area.classList.contains('editor__text')).toBe(true)
    expect($('[data-test="mode-edit"]')?.getAttribute('aria-pressed')).toBe('true')
  })

  it('Preview renders the markdown, tables included', async () => {
    await open()
    await click('[data-test="mode-preview"]')
    expect($('[data-test="text"]')).toBeNull()
    expect($('[data-test="mode-preview"]')?.getAttribute('aria-pressed')).toBe('true')
    expect(text('[data-test="preview"] h1')).toBe('Environment (test fixture)')
    expect($$('[data-test="preview"] th').map((th) => th.textContent)).toEqual(['Table', 'Rows', 'Owner'])
    expect(text('[data-test="preview"] strong')).toBe('No')
    await click('[data-test="mode-edit"]')
    expect($('[data-test="text"]')).not.toBeNull()
  })

  it('Preview shows the text being typed, before it is saved', async () => {
    await open()
    await type('[data-test="text"]', '# Changed')
    await click('[data-test="mode-preview"]')
    expect(text('[data-test="preview"] h1')).toBe('Changed')
  })

  it('Preview of the hostile sample holds nothing executable (R-7)', async () => {
    server.add('hostile.md', 'misc_context', fixture('hostile.md'))
    await open('/knowledge?file=f-2')
    await click('[data-test="mode-preview"]')
    const preview = $('[data-test="preview"]')!
    expect(preview.querySelectorAll('script, iframe, img, svg, a, style, link, object, embed, video, form')).toHaveLength(0)
    expect(Array.from(preview.querySelectorAll('*')).flatMap((el) => el.getAttributeNames()).filter((n) => n !== 'class' && n !== 'start')).toEqual([])
    expect(server.calls.filter((c) => c.path.includes('evil'))).toEqual([])
  })
})

describe('FR-IN-5: mic icon', () => {
  it('shows a "Voice input" tooltip and does nothing when pressed (D-8a)', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    const mic = $<HTMLButtonElement>('[data-test="mic"]')!
    expect(mic.getAttribute('aria-label')).toBe('Voice input')
    const tip = document.getElementById(mic.getAttribute('aria-describedby')!)
    expect(tip?.textContent?.trim()).toBe('Voice input')
    const before = server.calls.length
    await click(mic)
    expect(server.calls.length).toBe(before)
    expect($('[role="dialog"]')).toBeNull()
  })
})

describe('FR-IN-6: new, rename, change category, delete, unsaved dot, autosave', () => {
  it('creates a new file and opens it', async () => {
    await open()
    await click('[data-test="empty-new"]')
    expect($<HTMLInputElement>('[data-test="new-name"]')?.value).toBe('person.md')
    await click('[data-test="new-create"]')
    expect(server.writes().map((c) => c.body)).toEqual([{ name: 'person.md', category: 'person', content: '', replace: false }])
    expect(router.currentRoute.value.query.file).toBe('f-1')
    expect($<HTMLInputElement>('[data-test="name"]')?.value).toBe('person.md')
  })

  it('"Add file" opens New file on that category with its suggested name', async () => {
    server.add('person.md', 'person', 'p')
    await open()
    await click('[data-add="environment"]')
    expect($<HTMLSelectElement>('[data-test="new-category"]')?.value).toBe('environment')
    expect($<HTMLInputElement>('[data-test="new-name"]')?.value).toBe('environment.md')
  })

  it('shows the server message for a bad name', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await type('[data-test="name"]', 'a/b.md')
    await press('Enter', $('[data-test="name"]'))
    expect(text('[data-test="name-error"]')).toBe('A file name cannot contain / or \\.')
    await press('Escape', $('[data-test="name"]'))
    expect($<HTMLInputElement>('[data-test="name"]')?.value).toBe('music.md')
    expect($('[data-test="name-error"]')).toBeNull()
  })

  it('renames on Enter', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await type('[data-test="name"]', '  tune.md ')
    await press('Enter', $('[data-test="name"]'))
    expect(server.writes().map((c) => c.body)).toEqual([{ name: '  tune.md ' }])
    expect($<HTMLInputElement>('[data-test="name"]')?.value).toBe('tune.md')
    expect(groupNames('music')).toEqual(['tune.md'])
  })

  it('Rename in the overflow menu focuses the name field', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await click('[data-test="overflow"] .menu-trigger')
    await click('[data-item="rename"]')
    expect(document.activeElement).toBe($('[data-test="name"]'))
  })

  it('changes category through the picker', async () => {
    server.add('notes.md', 'misc_context', 'n')
    await open()
    await click('[data-test="overflow"] .menu-trigger')
    await click('[data-item="category"]')
    expect(document.activeElement?.getAttribute('data-item')).toBe('misc_context')
    await click('[data-item="environment"]')
    expect(server.writes().map((c) => c.body)).toEqual([{ category: 'environment', replace: false }])
    expect(groupNames('environment')).toEqual(['notes.md'])
  })

  it('deletes only after confirmation', async () => {
    server.add('music.md', 'music', 'm')
    server.add('notes.md', 'misc_context', 'n')
    await open()
    await click('[data-test="overflow"] .menu-trigger')
    await click('[data-item="delete"]')
    expect(text('.modal__title')).toBe('Delete music.md?')
    await click('[data-test="confirm-cancel"]')
    expect(server.writes()).toEqual([])
    await click('[data-test="overflow"] .menu-trigger')
    await click('[data-item="delete"]')
    await click('[data-test="confirm-ok"]')
    expect(server.writes().map((c) => [c.method, c.path])).toEqual([['DELETE', '/api/intake/files/f-1']])
    expect(groupNames('music')).toEqual([])
    expect(router.currentRoute.value.query.file).toBe('f-2')
  })

  it('shows the unsaved dot while typing and clears it after the autosave', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    vi.useFakeTimers()
    const area = $<HTMLTextAreaElement>('[data-test="text"]')!
    area.value = 'm, edited'
    area.dispatchEvent(new Event('input', { bubbles: true }))
    await nextTick()
    expect(fileButton('music.md')?.querySelector('[data-test="unsaved-dot"]')).not.toBeNull()
    expect(fileButton('music.md')?.textContent).toContain('Unsaved changes')
    await vi.advanceTimersByTimeAsync(AUTOSAVE_MS - 100)
    expect(server.writes()).toEqual([])
    await vi.advanceTimersByTimeAsync(100)
    await vi.advanceTimersByTimeAsync(10)
    expect(server.writes().map((c) => c.body)).toEqual([{ content: 'm, edited' }])
    expect(fileButton('music.md')?.querySelector('[data-test="unsaved-dot"]')).toBeNull()
  })

  it('saves at once when switching files', async () => {
    server.add('music.md', 'music', 'm')
    server.add('notes.md', 'misc_context', 'n')
    await open()
    await type('[data-test="text"]', 'switching')
    await click(fileButton('notes.md')!)
    expect(server.writes().map((c) => [c.path, c.body])).toEqual([['/api/intake/files/f-1', { content: 'switching' }]])
    expect($<HTMLTextAreaElement>('[data-test="text"]')?.value).toBe('n')
    expect(fileButton('notes.md')?.getAttribute('aria-current')).toBe('true')
  })

  it('saves when leaving the page', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await type('[data-test="text"]', 'leaving')
    await router.push('/seed')
    await settle()
    expect(server.writes().map((c) => c.body)).toEqual([{ content: 'leaving' }])
  })

  it('on unload, sends a small draft with keepalive', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await type('[data-test="text"]', 'closing the tab')
    const unload = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(unload)
    expect(unload.defaultPrevented).toBe(false)
    const [, init] = server.fetch.mock.calls.find(([, i]) => i?.method === 'PATCH')!
    expect(init?.keepalive).toBe(true)
  })

  it('on unload, asks before leaving when a draft is too large to send', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await type('[data-test="text"]', 'x'.repeat(70_000))
    const unload = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(unload)
    expect(unload.defaultPrevented).toBe(true)
  })
})

describe('FR-IN-7: import', () => {
  it('pre-selects each category from the filename and imports one raw request per file', async () => {
    await open()
    await pick([...CORE_FIXTURES, 'vendor-notes.md'].map((name) => ({ name, content: fixture(name) })))
    expect($$('[data-test="row-category"]').map((s) => (s as HTMLSelectElement).value)).toEqual([
      'person',
      'instrument_awareness',
      'environment',
      'music',
      'misc_context',
    ])
    await click('[data-test="import-confirm"]')
    const imports = server.writes()
    expect(imports.map((c) => [c.path, c.query.filename, c.query.category, c.query.replace])).toEqual([
      ['/api/intake/import', 'person.md', 'person', 'false'],
      ['/api/intake/import', 'instrument-awareness.md', 'instrument_awareness', 'false'],
      ['/api/intake/import', 'environment.md', 'environment', 'false'],
      ['/api/intake/import', 'music.md', 'music', 'false'],
      ['/api/intake/import', 'vendor-notes.md', 'misc_context', 'false'],
    ])
    expect(imports[0].body).toBe(fixture('person.md'))
    expect($('[data-test="import-rows"]')).toBeNull()
    expect(router.currentRoute.value.query.file).toBe('f-1')
  })

  it.each([
    ['player.md', 'person'],
    ['instrument_awareness.md', 'instrument_awareness'],
    ['Music.md', 'music'],
    ['readme.md', 'misc_context'],
  ])('pre-selects %s as %s', async (name, category) => {
    await open()
    await pick([{ name, content: 'x' }])
    expect(($('[data-test="row-category"]') as HTMLSelectElement).value).toBe(category)
  })

  it('warns "Replaces existing person.md" and sends replace for that row', async () => {
    server.add('person.md', 'person', 'old')
    await open()
    await pick([{ name: 'player.md', content: 'new' }])
    expect(text('[data-test="row-replace"]')).toBe('Replaces existing person.md')
    await click('[data-test="import-confirm"]')
    expect(server.writes()[0].query).toMatchObject({ filename: 'player.md', category: 'person', replace: 'true' })
    expect(groupNames('person')).toEqual(['player.md'])
  })

  it('the category can be changed before import, and the warning follows it', async () => {
    server.add('person.md', 'person', 'old')
    await open()
    await pick([{ name: 'player.md', content: 'new' }])
    await choose('[data-test="row-category"]', 'misc_context')
    expect($('[data-test="row-replace"]')).toBeNull()
    await click('[data-test="import-confirm"]')
    expect(server.writes()[0].query).toMatchObject({ category: 'misc_context', replace: 'false' })
  })

  it('two files for the same core category block Import until one changes (D-42)', async () => {
    await open()
    await pick([
      { name: 'person.md', content: 'a' },
      { name: 'player.md', content: 'b' },
    ])
    expect($$('[data-test="row-clash"]').map((el) => el.textContent?.trim())).toEqual([
      'Only one Person file: player.md is also set to it.',
      'Only one Person file: person.md is also set to it.',
    ])
    expect($<HTMLButtonElement>('[data-test="import-confirm"]')?.disabled).toBe(true)
    const selects = $$('[data-test="row-category"]') as HTMLSelectElement[]
    selects[1].value = 'misc_context'
    selects[1].dispatchEvent(new Event('change', { bubbles: true }))
    await settle()
    expect($$('[data-test="row-clash"]')).toEqual([])
    expect($<HTMLButtonElement>('[data-test="import-confirm"]')?.disabled).toBe(false)
  })

  it('Cancel imports nothing', async () => {
    await open()
    await pick([{ name: 'music.md', content: 'x' }])
    await click('[data-test="import-cancel"]')
    expect(server.writes()).toEqual([])
  })
})

describe('FR-IN-8 and FR-IN-9: core checklist and Start Build', () => {
  it('Start Build is disabled until all four core files have content, with a tooltip of what is missing', async () => {
    server.add('person.md', 'person', 'p')
    server.add('music.md', 'music', '   ')
    await open()
    expect($$('[data-slot]').map((li) => [li.getAttribute('data-slot'), li.getAttribute('data-complete')])).toEqual([
      ['person', 'true'],
      ['instrument_awareness', 'false'],
      ['environment', 'false'],
      ['music', 'false'],
    ])
    const button = $<HTMLButtonElement>('[data-test="start-build"]')!
    expect(button.getAttribute('aria-disabled')).toBe('true')
    expect(button.disabled).toBe(false) // focusable, so the tooltip is reachable (D-42)
    const tip = document.getElementById(button.getAttribute('aria-describedby')!)
    expect(tip?.textContent?.trim()).toBe('Missing: Instrument Awareness, Environment, Music')
  })

  it('importing the four fixture files completes the checklist and enables Start Build', async () => {
    await open()
    await pick(CORE_FIXTURES.map((name) => ({ name, content: fixture(name) })))
    await click('[data-test="import-confirm"]')
    expect($$('[data-slot]').every((li) => li.getAttribute('data-complete') === 'true')).toBe(true)
    const button = $<HTMLButtonElement>('[data-test="start-build"]')!
    expect(button.getAttribute('aria-disabled')).toBeNull()
    expect(button.disabled).toBe(false)
  })

  it('a disabled Start Build does nothing when pressed', async () => {
    await open()
    await click('[data-test="start-build"]')
    expect(text('[data-test="build-note"]')).toBe('')
    expect(server.writes()).toEqual([])
  })

  it('in M3, an enabled Start Build saves every draft and starts nothing (D-42)', async () => {
    for (const name of CORE_FIXTURES) server.add(name, useIntakeCategory(name), fixture(name))
    await open()
    await type('[data-test="text"]', '# Person, edited')
    await click('[data-test="start-build"]')
    expect(server.writes().map((c) => [c.method, c.body])).toEqual([['PATCH', { content: '# Person, edited' }]])
    expect(text('[data-test="build-note"]')).toBe('Files saved. Builds arrive in M5, so nothing starts yet.')
    expect(router.currentRoute.value.name).toBe('knowledge')
  })
})

function useIntakeCategory(name: string): string {
  return { 'person.md': 'person', 'instrument-awareness.md': 'instrument_awareness', 'environment.md': 'environment', 'music.md': 'music' }[name]!
}

describe('FR-IN-10: persistence across refresh', () => {
  it('keeps the selected file in the URL, so a refresh opens it again (D-42)', async () => {
    server.add('music.md', 'music', 'm')
    server.add('notes.md', 'misc_context', 'n')
    await open()
    expect(router.currentRoute.value.fullPath).toBe('/knowledge?file=f-1')
    await click(fileButton('notes.md')!)
    expect(router.currentRoute.value.fullPath).toBe('/knowledge?file=f-2')
    wrapper.unmount()
    await open('/knowledge?file=f-2')
    expect($<HTMLInputElement>('[data-test="name"]')?.value).toBe('notes.md')
  })

  it('a refresh shows what was saved, from the server', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    await type('[data-test="text"]', 'saved before refresh')
    await useIntakeStore().flushAll()
    wrapper.unmount()
    await open('/knowledge?file=f-1')
    expect($<HTMLTextAreaElement>('[data-test="text"]')?.value).toBe('saved before refresh')
  })

  it('an unknown file in the URL falls back to the first file', async () => {
    server.add('music.md', 'music', 'm')
    await open('/knowledge?file=f-99')
    expect(router.currentRoute.value.query.file).toBe('f-1')
  })
})

describe('FR-IN-11: size and encoding errors show inline', () => {
  it.each([
    [413, 'file_too_large', 'big.md is 2,000,000 bytes. Files are limited to 1 MB (1,048,576 bytes).'],
    [415, 'not_utf8_text', 'latin.md is not UTF-8 text. Only markdown or plain text files can be added.'],
    [415, 'not_markdown', 'notes.txt is not a .md file. Import accepts markdown files only.'],
  ])('shows %s %s on its row, as the server wrote it', async (status, code, message) => {
    await open()
    server.refuseNext((c) => c.path === '/api/intake/import' && c.query.filename === 'bad.md', status, code, message)
    await pick([
      { name: 'bad.md', content: new Uint8Array([0xe9, 0x74, 0xe9]) },
      { name: 'good.md', content: 'fine' },
    ])
    await click('[data-test="import-confirm"]')
    const rows = $$('[data-row]')
    expect(rows[0].querySelector('[data-test="row-error"]')?.textContent?.trim()).toBe(message)
    expect(rows[1].querySelector('[data-test="row-done"]')?.textContent?.trim()).toBe('Imported')
    expect(text('[data-test="import-cancel"]')).toBe('Close')
    expect($<HTMLButtonElement>('[data-test="import-confirm"]')?.disabled).toBe(true)
  })

  it('shows a refused autosave next to the editor', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    server.refuseNext((c) => c.method === 'PATCH', 413, 'file_too_large', 'music.md is 1,048,600 bytes. Files are limited to 1 MB (1,048,576 bytes).')
    await type('[data-test="text"]', 'too much')
    await useIntakeStore().flushAll()
    await settle()
    expect(text('[data-test="save-error"]')).toBe('music.md is 1,048,600 bytes. Files are limited to 1 MB (1,048,576 bytes).')
    expect(fileButton('music.md')?.querySelector('[data-test="unsaved-dot"]')).not.toBeNull()
  })
})

describe('Empty state', () => {
  it('explains the four Ensemble files, one line each, with New file and Import', async () => {
    await open()
    expect(text('[data-test="empty-state"] h1')).toBe('Add your knowledge files')
    expect($$('[data-test="empty-state"] dt').map((el) => el.textContent)).toEqual(['Person', 'Instrument Awareness', 'Environment', 'Music'])
    expect($$('[data-test="empty-state"] dd').map((el) => el.textContent)).toEqual([
      'Who does the work.',
      'Which tool it uses.',
      'Where the work happens.',
      'Why the work exists.',
    ])
    expect(text('[data-test="empty-new"]')).toBe('New file')
    expect(text('[data-test="empty-import"]')).toBe('Import')
  })

  it('Import opens the file picker for .md files', async () => {
    await open()
    const input = $<HTMLInputElement>('[data-test="import-input"]')!
    const opened = vi.fn()
    input.addEventListener('click', opened)
    await click('[data-test="empty-import"]')
    expect(opened).toHaveBeenCalled()
    expect(input.accept).toBe('.md,text/markdown')
    expect(input.multiple).toBe(true)
  })
})

describe('FR-B-8: read-only while a build runs', () => {
  beforeEach(() => {
    server.add('music.md', 'music', 'm')
    server.builds = [{ id: 'b-1', iteration: 1, status: 'running' }]
  })

  it('shows a banner linking to the running build, and locks every control', async () => {
    await open()
    expect(text('[data-test="read-only-banner"]')).toBe(
      'A build is running. Knowledge files are read-only until it finishes. Go to the build',
    )
    expect($('[data-test="read-only-banner"] a')?.getAttribute('href')).toBe('/build/1')
    expect($<HTMLTextAreaElement>('[data-test="text"]')?.readOnly).toBe(true)
    expect($<HTMLInputElement>('[data-test="name"]')?.readOnly).toBe(true)
    expect($<HTMLButtonElement>('[data-test="category"] .menu-trigger')?.disabled).toBe(true)
    expect($<HTMLButtonElement>('[data-test="new-file"]')?.disabled).toBe(true)
    expect($<HTMLButtonElement>('[data-test="import"]')?.disabled).toBe(true)
    expect($$('[data-add]')).toEqual([])
    await click('[data-test="overflow"] .menu-trigger')
    expect($$('[role="menuitem"]').map((i) => i.getAttribute('aria-disabled'))).toEqual(['true', 'true', 'true'])
  })

  it('Preview still works', async () => {
    await open()
    await click('[data-test="mode-preview"]')
    expect(text('[data-test="preview"]')).toBe('m')
  })

  it('handles a 409 intake_locked from a save started before the lock was seen', async () => {
    server.builds = []
    await open()
    server.builds = [{ id: 'b-1', iteration: 1, status: 'running' }]
    await type('[data-test="text"]', 'typed as the build started')
    await useIntakeStore().flushAll()
    await settle()
    expect(text('[data-test="save-error"]')).toBe('Knowledge files are read-only while a build runs.')
    expect($<HTMLTextAreaElement>('[data-test="text"]')?.value).toBe('typed as the build started')
  })
})

describe('NFR-6: keyboard', () => {
  it('the category menu opens on ArrowDown, moves with arrows, and Escape returns focus', async () => {
    server.add('notes.md', 'misc_context', 'n')
    await open()
    const trigger = $<HTMLButtonElement>('[data-test="category"] .menu-trigger')!
    trigger.focus()
    await press('ArrowDown')
    expect(document.activeElement?.getAttribute('data-item')).toBe('misc_context')
    await press('ArrowDown')
    expect(document.activeElement?.getAttribute('data-item')).toBe('person')
    await press('End')
    expect(document.activeElement?.getAttribute('data-item')).toBe('misc_context')
    await press('ArrowUp')
    expect(document.activeElement?.getAttribute('data-item')).toBe('music')
    await press('Escape')
    expect($('[role="menu"]')).toBeNull()
    expect(document.activeElement).toBe(trigger)
    expect(server.writes()).toEqual([])
  })

  it('Delete from the overflow menu by keyboard, then Escape closes the dialog and focus returns', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    const trigger = $<HTMLButtonElement>('[data-test="overflow"] .menu-trigger')!
    trigger.focus()
    await press('ArrowUp')
    expect(document.activeElement?.getAttribute('data-item')).toBe('delete')
    await click(document.activeElement)
    expect(text('.modal__title')).toBe('Delete music.md?')
    expect($('[role="dialog"]')?.contains(document.activeElement)).toBe(true)
    await press('Escape')
    expect($('[role="dialog"]')).toBeNull()
    expect(document.activeElement).toBe(trigger)
    expect(server.writes()).toEqual([])
  })

  it('every control on the page is a native control, reachable with Tab', async () => {
    server.add('music.md', 'music', 'm')
    await open()
    const controls = $$('[data-test="knowledge"] button, [data-test="knowledge"] input, [data-test="knowledge"] textarea, [data-test="knowledge"] a')
    const reachable = controls.filter((el) => el.getAttribute('tabindex') !== '-1')
    const skipped = controls.filter((el) => el.getAttribute('tabindex') === '-1').map((el) => el.getAttribute('data-test'))
    expect(skipped).toEqual(['import-input']) // reached through the Import button instead
    expect(reachable.length).toBeGreaterThan(8)
  })
})

describe('store wiring', () => {
  it('the page reads categories from the server, once', async () => {
    await open()
    expect(server.calls.filter((c) => c.path === '/api/intake/categories')).toHaveLength(1)
    expect(useLabStore().snapshot).not.toBeNull()
  })
})
