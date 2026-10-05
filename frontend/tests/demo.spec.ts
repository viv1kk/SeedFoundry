// The demo controller on the page (ui-spec.md section 8, FR-DC-1, FR-DC-2, D-46, D-47, OQ-17),
// against tests/fake-server.ts, whose Load sample serves the real sample files.

import type { VueWrapper } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Router } from 'vue-router'
import { SHORTCUTS } from '../src/demo/shortcuts'
import { useDemoStore } from '../src/stores/demo'
import { useIntakeStore } from '../src/stores/intake'
import { useLabStore } from '../src/stores/lab'
import { applyTheme, THEME_KEY } from '../src/theme'
import { FakeServer, SAMPLE } from './fake-server'
import { mountApp } from './helpers'

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

/** A Shift shortcut, pressed wherever focus is (or on `target`). */
async function shift(key: string, code: string, target: Element | null = document.activeElement): Promise<KeyboardEvent> {
  const event = new KeyboardEvent('keydown', { key, code, shiftKey: true, bubbles: true, cancelable: true })
  ;(target ?? document.body).dispatchEvent(event)
  await settle()
  return event
}

const letter = (l: string) => shift(l, `Key${l}`)

async function click(selector: string): Promise<void> {
  const el = $(selector)
  if (!el) throw new Error(`nothing to click: ${selector}`)
  el.click()
  await settle()
}

const panel = () => $('[data-test="demo-panel"]')
const status = () => $('[data-test="demo-status"]')?.textContent?.trim() ?? ''
const confirmText = () => $('[data-test="demo-confirm"]')?.textContent?.trim() ?? null
const names = () => $$('[data-test="file-panel"] .file__name').map((el) => el.textContent)
const theme = () => document.documentElement.getAttribute('data-theme')
const action = (name: string) => $(`[data-test="demo-panel"] [data-action="${name}"]`)
const demoWrites = () => server.writes().filter((c) => c.path.startsWith('/api/demo/'))

function startBuildEnabled(): boolean {
  const button = $('[data-test="start-build"]')!
  return !button.hasAttribute('disabled') && button.getAttribute('aria-disabled') !== 'true'
}

beforeEach(() => {
  server = new FakeServer()
  vi.stubGlobal('fetch', server.fetch)
  localStorage.clear()
  applyTheme('light')
})

afterEach(async () => {
  await useIntakeStore().flushAll()
  wrapper?.unmount()
  vi.unstubAllGlobals()
  document.body.innerHTML = ''
  document.documentElement.removeAttribute('data-theme')
  localStorage.clear()
})

describe('Shift+O: the panel (FR-DC-1)', () => {
  it('is hidden by default and Shift+O shows and hides it', async () => {
    await open()
    expect(panel()).toBeNull()
    await letter('O')
    expect(panel()).not.toBeNull()
    expect(panel()!.textContent).toContain('Demo')
    await letter('O')
    expect(panel()).toBeNull()
  })

  it('takes focus when it opens, and Escape closes it and puts focus back', async () => {
    await open()
    const toggle = $('[data-test="theme-toggle"]')!
    toggle.focus()
    await letter('O')
    expect(document.activeElement).toBe(panel())
    panel()!.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }))
    await settle()
    expect(panel()).toBeNull()
    expect(document.activeElement).toBe(toggle)
  })

  it('Shift+O from inside the panel closes it and puts focus back', async () => {
    await open()
    const toggle = $('[data-test="theme-toggle"]')!
    toggle.focus()
    await letter('O')
    action('theme')!.focus()
    await letter('O')
    expect(panel()).toBeNull()
    expect(document.activeElement).toBe(toggle)
  })

  it('the close button hides it', async () => {
    await open()
    await letter('O')
    await click('[data-test="demo-close"]')
    expect(panel()).toBeNull()
  })

  it('has a button for every action, each listing its shortcut', async () => {
    await open()
    await letter('O')
    for (const shortcut of SHORTCUTS.filter((s) => s.action !== 'toggle')) {
      const button = action(shortcut.action)
      expect(button?.tagName, shortcut.action).toBe('BUTTON')
      expect(button!.querySelector('kbd')?.textContent).toBe(shortcut.label)
    }
    expect(panel()!.textContent).toContain('Shift+O shows or hides this panel.')
  })

  it('every button is reachable from the keyboard (NFR-6)', async () => {
    await open()
    await letter('O')
    const buttons = $$('[data-test="demo-panel"] button')
    expect(buttons.length).toBe(12)
    for (const button of buttons) {
      expect(button.getAttribute('tabindex')).toBeNull()
      expect(button.hasAttribute('disabled')).toBe(false)
    }
  })
})

describe('Shift+P: Load sample Seed (FR-DC-2, FR-DC-3)', () => {
  it('fills an empty intake at once: the four core slots complete and Start Build enabled', async () => {
    await open()
    expect(startBuildEnabled()).toBe(false)
    await letter('P')
    expect(confirmText()).toBeNull()
    expect(demoWrites()).toEqual([expect.objectContaining({ method: 'POST', path: '/api/demo/sample', body: { replace: false } })])
    expect(names()).toEqual(SAMPLE.map((f) => f.name))
    expect($$('[data-test="checklist"] [data-complete="true"]').length).toBe(4)
    expect(startBuildEnabled()).toBe(true)
    // The editor opens the first file in Ensemble order, with the sample's text.
    expect($<HTMLInputElement>('[data-test="name"]')?.value).toBe('Identity.md')
    expect($<HTMLTextAreaElement>('[data-test="editor"] textarea')?.value).toBe(SAMPLE[0].content)
  })

  it('the panel button does the same and says what it did', async () => {
    await open()
    await letter('O')
    await click('[data-action="sample"]')
    expect(names()).toEqual(SAMPLE.map((f) => f.name))
    expect(status()).toBe('Sample Seed loaded: 4 files.')
  })

  it('asks before replacing files (OQ-17)', async () => {
    server.add('person.md', 'person', 'mine')
    server.add('my-notes.md', 'environment', 'notes')
    await open()
    await letter('P')
    expect(confirmText()).toBe('This replaces all 2 knowledge files with the sample Seed. Unsaved changes are lost.')
    expect(demoWrites()).toEqual([])
    await click('[data-test="confirm-ok"]')
    expect(demoWrites()).toEqual([expect.objectContaining({ path: '/api/demo/sample', body: { replace: true } })])
    expect(names()).toEqual(SAMPLE.map((f) => f.name))
  })

  it('Cancel keeps the files as they are', async () => {
    server.add('my-notes.md', 'environment', 'notes')
    await open()
    await letter('P')
    await click('[data-test="confirm-cancel"]')
    expect(confirmText()).toBeNull()
    expect(demoWrites()).toEqual([])
    expect(names()).toEqual(['my-notes.md'])
  })

  it('drops the unsaved text of the files it replaces, selected or not', async () => {
    server.add('person.md', 'person', 'p')
    const notes = server.add('notes.md', 'misc_context', 'n')
    await open()
    // person.md is open in the editor; notes.md has unsaved text with its autosave still due.
    const textarea = $<HTMLTextAreaElement>('[data-test="editor"] textarea')!
    textarea.value = 'p, edited'
    textarea.dispatchEvent(new Event('input', { bubbles: true }))
    useIntakeStore().edit(notes.id, 'n, edited')
    await settle(1)
    expect(useIntakeStore().isDirty(notes.id)).toBe(true)
    $('[data-test="theme-toggle"]')!.focus()
    await letter('P')
    await click('[data-test="confirm-ok"]')
    expect(useIntakeStore().anyDirty).toBe(false)
    await useIntakeStore().flushAll()
    expect(server.writes().filter((c) => c.method === 'PATCH')).toEqual([])
  })

  it('is refused while a build runs, and says why', async () => {
    server.builds = [{ id: 'b-1', iteration: 1, status: 'running' }]
    await open()
    await letter('O')
    await letter('P')
    expect(demoWrites()).toEqual([])
    expect(status()).toBe('A build is running. Knowledge files are read-only until it finishes.')
    expect(action('sample')!.getAttribute('aria-disabled')).toBe('true')
  })

  it('opens the Knowledge page from another screen', async () => {
    await open('/seed')
    await letter('P')
    expect(router.currentRoute.value.name).toBe('knowledge')
    expect(names()).toEqual(SAMPLE.map((f) => f.name))
  })
})

describe('Shift+C: Clear Knowledge', () => {
  it('asks first, then deletes every file', async () => {
    server.add('person.md', 'person', 'p')
    server.add('notes.md', 'misc_context', 'n')
    await open()
    await letter('C')
    expect(confirmText()).toBe('This deletes all 2 knowledge files. It cannot be undone.')
    await click('[data-test="confirm-ok"]')
    expect(demoWrites()).toEqual([expect.objectContaining({ path: '/api/demo/clear' })])
    expect(names()).toEqual([])
    expect(useLabStore().files).toEqual([])
  })

  it('Cancel deletes nothing', async () => {
    server.add('notes.md', 'environment', 'n')
    await open()
    await letter('C')
    await click('[data-test="confirm-cancel"]')
    expect(demoWrites()).toEqual([])
    expect(names()).toEqual(['notes.md'])
  })

  it('on an empty intake, says so and asks nothing', async () => {
    await open()
    await letter('O')
    await letter('C')
    expect(confirmText()).toBeNull()
    expect(status()).toBe('Knowledge is already empty.')
  })
})

describe('Shift+R: Reset to start', () => {
  it('asks first, then clears everything and returns to Knowledge, keeping speed and theme', async () => {
    server.add('notes.md', 'misc_context', 'n')
    server.builds = [{ id: 'b-1', iteration: 1, status: 'completed' }]
    await open('/review/1')
    await shift('$', 'Digit4')
    await letter('D')
    await letter('R')
    expect(confirmText()).toBe(
      'This deletes all knowledge files and builds and returns to the Knowledge page. Speed and theme stay as they are.',
    )
    await click('[data-test="confirm-ok"]')
    // D-53: the speed set before Reset now goes to the server too.
    expect(demoWrites().map((c) => c.path)).toEqual(['/api/demo/speed', '/api/demo/reset'])
    expect(router.currentRoute.value.fullPath).toBe('/knowledge')
    expect(useLabStore().snapshot?.builds).toEqual([])
    expect(useLabStore().files).toEqual([])
    expect(useDemoStore().speed).toBe(4)
    expect(theme()).toBe('dark')
  })

  it('works while a build runs', async () => {
    server.builds = [{ id: 'b-1', iteration: 1, status: 'running' }]
    await open()
    await letter('R')
    await click('[data-test="confirm-ok"]')
    expect(demoWrites()).toEqual([expect.objectContaining({ path: '/api/demo/reset' })])
    expect(useLabStore().runningBuild).toBeNull()
  })
})

describe('Shift+Enter: Start Build (FR-B-1)', () => {
  it('with files missing, says what is missing and does nothing', async () => {
    server.add('music.md', 'music', '# Tune')
    await open()
    await letter('O')
    await shift('Enter', 'Enter', document.body)
    expect(status()).toBe('Start Build needs every initiation file. Missing: Identity.md, Tools_and_Skills.md, Environment.md.')
    expect(server.writes()).toEqual([])
  })

  // D-53: in M4 this said builds arrive in M5; it now does what the button does from M5.
  it('with all four, does what the Start Build button does: starts the build and opens its page', async () => {
    await open()
    await letter('P')
    await letter('O')
    await shift('Enter', 'Enter', document.body)
    expect(server.writes().filter((c) => c.path === '/api/builds')).toHaveLength(1)
    expect(router.currentRoute.value.fullPath).toBe('/build/1')
    expect(status()).toBe('Build started: iteration 1.')
    // D-54 (h): the Build page replaced the placeholder's "Build running" line.
    expect($('main [data-test="build-iteration"]')?.textContent?.trim()).toBe('Iteration 1')
    expect($('main [data-test="build-status"]')?.textContent?.trim()).toBe('Starting')
  })

  it('on a focused button, Shift+Enter belongs to that button', async () => {
    await open()
    await letter('P')
    await shift('Enter', 'Enter', $('[data-test="theme-toggle"]'))
    expect($('[data-test="build-note"]')?.textContent).toBe('')
  })
})

describe('Speed: Shift+1, Shift+2, Shift+4 by key code', () => {
  it('sets the speed whatever character the layout types, and the panel shows it', async () => {
    await open()
    await letter('O')
    const pressed = () => $$('[data-test="demo-panel"] [aria-pressed="true"]').map((b) => b.dataset.action)
    expect(pressed()).toEqual(['speed1'])
    await shift('@', 'Digit2')
    expect(useDemoStore().speed).toBe(2)
    expect(pressed()).toEqual(['speed2'])
    await shift('$', 'Digit4')
    expect(useDemoStore().speed).toBe(4)
    await shift('1', 'Digit1')
    expect(useDemoStore().speed).toBe(1)
    // D-53: speed is now kept on the server (D-48), so each press is sent there.
    expect(status()).toBe('Speed 1x.')
    expect(server.writes().map((c) => c.body)).toEqual([{ speed: 2 }, { speed: 4 }, { speed: 1 }])
    expect(server.speed).toBe(1)
  })

  it("shows the server's speed when it loads, as it survives Reset and reloads", async () => {
    server.speed = 4
    await open()
    await letter('O')
    expect($$('[data-test="demo-panel"] [aria-pressed="true"]').map((b) => b.dataset.action)).toEqual(['speed4'])
  })

  it('a refused speed goes back and says why', async () => {
    server.refuseNext((c) => c.path === '/api/demo/speed' && c.method === 'POST', 409, 'nope', 'Speed cannot change now.')
    await open()
    await letter('O')
    await shift('@', 'Digit2')
    expect(useDemoStore().speed).toBe(1)
    expect(status()).toBe('Speed cannot change now.')
  })

  it('the speed buttons set it too', async () => {
    await open()
    await letter('O')
    await click('[data-action="speed2"]')
    expect(useDemoStore().speed).toBe(2)
  })
})

describe('Shift+S and Shift+E: skip (D-48)', () => {
  // D-53: in M4 these said builds arrive in M5; without a build they now say there is none.
  it('without a running build, say there is nothing to skip and send nothing', async () => {
    await open()
    await letter('O')
    for (const key of ['S', 'E']) {
      await letter(key)
      expect(status()).toBe('No build is running, so there is nothing to skip.')
    }
    expect(server.writes()).toEqual([])
    for (const name of ['skipPhase', 'skipEnd']) {
      const button = action(name)!
      expect(button.getAttribute('aria-disabled')).toBe('true')
      expect(document.getElementById(button.getAttribute('aria-describedby')!)?.textContent?.trim()).toBe(
        'No build is running, so there is nothing to skip.',
      )
    }
  })

  it('while a build runs, skip the phase or the build', async () => {
    server.builds = [{ id: 'b-1', iteration: 1, status: 'running' }]
    await open('/build/1')
    await letter('O')
    expect(action('skipPhase')!.getAttribute('aria-disabled')).toBeNull()
    await letter('S')
    expect(status()).toBe('Skipping to the end of Assay.')
    await click('[data-action="skipEnd"]')
    expect(status()).toBe('Skipping to the end of the build.')
    expect(demoWrites().map((c) => c.body)).toEqual([{ to: 'phase' }, { to: 'build' }])
  })
})

describe('Shift+F: Prefill (FR-DC-2, D-70)', () => {
  // D-71: until M10 the button said Prefill arrives in M10. It still does nothing without the modal,
  // and now says the modal must be open; inside the modal, rebuild-modal.spec.ts shows it filling it.
  // D-81: Rebuild is Reject on screen, on any iteration's report.
  it('Shift+F does nothing without the rebuild modal; its button says to open Reject first', async () => {
    await open()
    await letter('O')
    await letter('F')
    expect(status()).toBe('')
    await click('[data-action="prefill"]')
    expect(status()).toBe('Prefill fills the rebuild modal. Open Reject from the current report first.')
    expect(server.writes()).toEqual([])
    expect(server.calls.filter((c) => c.path === '/api/demo/feedback')).toEqual([])
  })
})

describe('Shift+D: theme', () => {
  it('toggles light and dark', async () => {
    await open()
    await letter('D')
    expect(theme()).toBe('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    await letter('D')
    expect(theme()).toBe('light')
  })
})

describe('ignored where text is typed (FR-DC-1, seed-reuse-notes.md section 6.2)', () => {
  async function typeCapitals(target: HTMLInputElement | HTMLTextAreaElement): Promise<void> {
    target.focus()
    for (const l of ['P', 'C', 'R', 'D', 'O', 'S', 'E', 'F']) {
      const event = await shift(l, `Key${l}`, target)
      expect(event.defaultPrevented).toBe(false)
    }
    await shift('!', 'Digit1', target)
    await shift('Enter', 'Enter', target)
  }

  function nothingHappened(): void {
    expect(panel()).toBeNull()
    expect(confirmText()).toBeNull()
    expect(demoWrites()).toEqual([])
    expect(theme()).toBe('light')
    expect(useDemoStore().status).toBe('')
  }

  it('in the editor: capital P, C, R and D (and the rest) do nothing', async () => {
    await open()
    await letter('P')
    const writes = demoWrites().length
    await typeCapitals($<HTMLTextAreaElement>('[data-test="editor"] textarea')!)
    expect(panel()).toBeNull()
    expect(confirmText()).toBeNull()
    expect(demoWrites().length).toBe(writes)
    expect(theme()).toBe('light')
    expect($('[data-test="build-note"]')?.textContent).toBe('')
  })

  it('in the name field', async () => {
    server.add('music.md', 'music', '# Tune')
    await open()
    await typeCapitals($<HTMLInputElement>('[data-test="name"]')!)
    nothingHappened()
  })

  it('in a select and a contenteditable element', async () => {
    await open()
    const select = document.body.appendChild(document.createElement('select'))
    select.focus()
    await letter('D')
    await letter('P')
    const editable = document.body.appendChild(document.createElement('div'))
    editable.setAttribute('contenteditable', 'true')
    await shift('D', 'KeyD', editable)
    await shift('C', 'KeyC', editable)
    nothingHappened()
  })
})

describe('while a modal is open', () => {
  it('shortcuts do nothing until it closes, then Escape returns focus', async () => {
    server.add('notes.md', 'misc_context', 'n')
    await open()
    await letter('O')
    const clear = action('clear')!
    clear.focus()
    await letter('C')
    expect(confirmText()).not.toBeNull()
    await letter('D')
    await letter('P')
    await letter('O')
    expect(theme()).toBe('light')
    expect(panel()).not.toBeNull()
    expect(demoWrites()).toEqual([])
    document.activeElement!.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true, cancelable: true }))
    await settle()
    expect(confirmText()).toBeNull()
    expect(document.activeElement).toBe(clear)
    // Escape in the confirm does not also close the panel.
    expect(panel()).not.toBeNull()
  })
})
