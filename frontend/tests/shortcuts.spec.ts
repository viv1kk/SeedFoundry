// The demo controller's shortcut rules (seed-reuse-notes.md section 6.2, FR-DC-1, D-47), unit
// level. The page-level tests are in demo.spec.ts.

import { afterEach, describe, expect, it } from 'vitest'
import { activatesOnEnter, matchShortcut, openModal, SHORTCUTS, shortcutAction, takesTyping } from '../src/demo/shortcuts'

function keydown(init: KeyboardEventInit): KeyboardEvent {
  return new KeyboardEvent('keydown', { bubbles: true, cancelable: true, shiftKey: true, ...init })
}

/** Dispatch on an element so the event has a target, and return what the rules make of it. */
function actionOn(target: Element, init: KeyboardEventInit) {
  let action: ReturnType<typeof shortcutAction> = null
  target.addEventListener('keydown', (event) => (action = shortcutAction(event as KeyboardEvent)), { once: true })
  target.dispatchEvent(keydown(init))
  return action
}

function add<K extends keyof HTMLElementTagNameMap>(tag: K, attributes: Record<string, string> = {}): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag)
  for (const [name, value] of Object.entries(attributes)) el.setAttribute(name, value)
  document.body.appendChild(el)
  return el
}

afterEach(() => {
  document.body.innerHTML = ''
})

describe('the map (seed-reuse-notes.md section 6.2)', () => {
  it('has one shortcut per action, as the operator guide lists them', () => {
    expect(SHORTCUTS.map((s) => [s.action, s.label])).toEqual([
      ['toggle', 'Shift+O'],
      ['sample', 'Shift+P'],
      ['start', 'Shift+Enter'],
      ['speed1', 'Shift+1'],
      ['speed2', 'Shift+2'],
      ['speed4', 'Shift+4'],
      ['skipPhase', 'Shift+S'],
      ['skipEnd', 'Shift+E'],
      ['prefill', 'Shift+F'],
      ['clear', 'Shift+C'],
      ['reset', 'Shift+R'],
      ['theme', 'Shift+D'],
    ])
  })

  it.each([
    ['O', 'KeyO', 'toggle'],
    ['P', 'KeyP', 'sample'],
    ['Enter', 'Enter', 'start'],
    ['S', 'KeyS', 'skipPhase'],
    ['E', 'KeyE', 'skipEnd'],
    ['F', 'KeyF', 'prefill'],
    ['C', 'KeyC', 'clear'],
    ['R', 'KeyR', 'reset'],
    ['D', 'KeyD', 'theme'],
  ])('Shift+%s is %s', (key, code, action) => {
    expect(matchShortcut(keydown({ key, code }))?.action).toBe(action)
  })

  it('matches letters case-insensitively, so Caps Lock does not matter', () => {
    expect(matchShortcut(keydown({ key: 'p', code: 'KeyP' }))?.action).toBe('sample')
  })

  it('matches digits by code, whatever character the layout types', () => {
    // US: Shift+1 types "!"; French: Shift+& key types "1"; both are Digit1.
    for (const key of ['!', '1', '&']) expect(matchShortcut(keydown({ key, code: 'Digit1' }))?.action).toBe('speed1')
    expect(matchShortcut(keydown({ key: '@', code: 'Digit2' }))?.action).toBe('speed2')
    expect(matchShortcut(keydown({ key: '$', code: 'Digit4' }))?.action).toBe('speed4')
    // The character alone is not enough.
    expect(matchShortcut(keydown({ key: '1', code: 'Numpad1' }))).toBeNull()
    expect(matchShortcut(keydown({ key: '!', code: 'Digit3' }))).toBeNull()
  })

  it('needs Shift and no other modifier, and ignores held-down repeats', () => {
    expect(matchShortcut(keydown({ key: 'p', code: 'KeyP', shiftKey: false }))).toBeNull()
    expect(matchShortcut(keydown({ key: 'P', code: 'KeyP', ctrlKey: true }))).toBeNull()
    expect(matchShortcut(keydown({ key: 'P', code: 'KeyP', altKey: true }))).toBeNull()
    expect(matchShortcut(keydown({ key: 'P', code: 'KeyP', metaKey: true }))).toBeNull()
    expect(matchShortcut(keydown({ key: 'P', code: 'KeyP', repeat: true }))).toBeNull()
  })

  it('ignores keys that are not on the map', () => {
    expect(matchShortcut(keydown({ key: 'Q', code: 'KeyQ' }))).toBeNull()
  })
})

describe('where text is typed (FR-DC-1)', () => {
  it.each([
    ['input', () => add('input')],
    ['textarea', () => add('textarea')],
    ['select', () => add('select')],
    ['contenteditable', () => add('div', { contenteditable: 'true' })],
    ['inside contenteditable', () => add('div', { contenteditable: '' }).appendChild(document.createElement('span'))],
    ['data-no-shortcuts', () => add('div', { 'data-no-shortcuts': '' }).appendChild(document.createElement('button'))],
  ])('a shortcut in a %s is text, not a shortcut', (_, make) => {
    const target = make()
    expect(takesTyping(target)).toBe(true)
    for (const [key, code] of [['P', 'KeyP'], ['C', 'KeyC'], ['R', 'KeyR'], ['D', 'KeyD'], ['O', 'KeyO']]) {
      expect(actionOn(target, { key, code })).toBeNull()
    }
  })

  it('a shortcut on a button or the page body runs', () => {
    expect(takesTyping(add('button'))).toBe(false)
    expect(takesTyping(add('div', { contenteditable: 'false' }))).toBe(false)
    expect(actionOn(document.body, { key: 'D', code: 'KeyD' })).toBe('theme')
    expect(actionOn(add('button'), { key: 'D', code: 'KeyD' })).toBe('theme')
  })

  it('Shift+Enter on a button or link is that control, not Start Build', () => {
    for (const target of [add('button'), add('a', { href: '#x' }), add('div', { role: 'menuitem' })]) {
      expect(activatesOnEnter(target)).toBe(true)
      expect(actionOn(target, { key: 'Enter', code: 'Enter' })).toBeNull()
    }
    expect(actionOn(document.body, { key: 'Enter', code: 'Enter' })).toBe('start')
  })
})

describe('while a modal is open', () => {
  it("ignores every shortcut but the modal's own", () => {
    add('div', { role: 'dialog', 'aria-modal': 'true' })
    expect(openModal()).toBe('')
    expect(actionOn(document.body, { key: 'D', code: 'KeyD' })).toBeNull()
    expect(actionOn(document.body, { key: 'O', code: 'KeyO' })).toBeNull()
    expect(actionOn(document.body, { key: 'F', code: 'KeyF' })).toBeNull()
  })

  it('Shift+F belongs to the rebuild modal and fires only while it is open', () => {
    expect(openModal()).toBeNull()
    expect(actionOn(document.body, { key: 'F', code: 'KeyF' })).toBeNull()
    add('div', { role: 'dialog', 'aria-modal': 'true', 'data-modal': 'rebuild' })
    expect(openModal()).toBe('rebuild')
    expect(actionOn(document.body, { key: 'F', code: 'KeyF' })).toBe('prefill')
    expect(actionOn(document.body, { key: 'D', code: 'KeyD' })).toBeNull()
  })

  it('a dialog that is not modal does not count', () => {
    add('div', { role: 'dialog' })
    expect(openModal()).toBeNull()
    expect(actionOn(document.body, { key: 'D', code: 'KeyD' })).toBe('theme')
  })
})
