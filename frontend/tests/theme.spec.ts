// Light and dark (seed-reuse-notes.md section 1.2): a first visit is dark whatever the OS
// prefers (D-96), the toggle switches and remembers under seedfoundry.theme, and storage
// failures are tolerated.

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ThemeToggle from '../src/components/shell/ThemeToggle.vue'
import { applyTheme, initialTheme, initTheme, theme, THEME_KEY, toggleTheme } from '../src/theme'

function osPrefers(dark: boolean) {
  vi.stubGlobal(
    'matchMedia',
    vi.fn((query: string) => ({ matches: dark && query === '(prefers-color-scheme: dark)', media: query })),
  )
}

const html = () => document.documentElement.getAttribute('data-theme')

beforeEach(() => {
  localStorage.clear()
  document.documentElement.removeAttribute('data-theme')
  osPrefers(false)
})

afterEach(() => {
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('first visit', () => {
  it('is dark with a dark OS preference', () => {
    osPrefers(true)
    initTheme()
    expect(html()).toBe('dark')
    expect(theme.value).toBe('dark')
  })

  it('is dark with a light OS preference too (D-96)', () => {
    osPrefers(false)
    initTheme()
    expect(html()).toBe('dark')
  })

  it('ignores a stored value that is not a theme', () => {
    localStorage.setItem(THEME_KEY, 'purple')
    osPrefers(true)
    expect(initialTheme()).toBe('dark')
  })
})

describe('the toggle', () => {
  it('switches both ways and remembers each choice', () => {
    applyTheme('light')
    expect(toggleTheme()).toBe('dark')
    expect(html()).toBe('dark')
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    expect(toggleTheme()).toBe('light')
    expect(html()).toBe('light')
    expect(localStorage.getItem(THEME_KEY)).toBe('light')
  })

  it('a remembered choice wins over the OS on the next load', () => {
    localStorage.setItem(THEME_KEY, 'light')
    osPrefers(true)
    initTheme()
    expect(html()).toBe('light')
  })

  it('works when storage throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    osPrefers(true)
    expect(() => initTheme()).not.toThrow()
    expect(html()).toBe('dark')
    expect(() => toggleTheme()).not.toThrow()
    expect(html()).toBe('light')
  })

  it('works when matchMedia is missing', () => {
    vi.stubGlobal('matchMedia', undefined)
    expect(initialTheme()).toBe('dark')
  })

  it('is a labelled button that flips the theme on click', async () => {
    applyTheme('light')
    const wrapper = mount(ThemeToggle, { attachTo: document.body })
    const button = wrapper.find('button[data-test="theme-toggle"]')
    expect(button.attributes('aria-label')).toBe('Switch to dark theme')
    await button.trigger('click')
    expect(html()).toBe('dark')
    expect(button.attributes('aria-label')).toBe('Switch to light theme')
    wrapper.unmount()
  })
})

describe('index.html sets the theme before first paint', () => {
  const page = readFileSync(resolve(__dirname, '..', 'index.html'), 'utf8')
  const boot = page.match(/<script>([\s\S]*?)<\/script>/)?.[1] ?? ''

  function runBoot(): void {
    new Function(boot)()
  }

  it('uses the same storage key', () => {
    expect(boot).toContain(`'${THEME_KEY}'`)
  })

  it('applies a stored choice, else dark (D-96)', () => {
    osPrefers(false)
    runBoot()
    expect(html()).toBe('dark')
    localStorage.setItem(THEME_KEY, 'light')
    runBoot()
    expect(html()).toBe('light')
  })

  it('survives storage that throws', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('blocked')
    })
    osPrefers(false)
    expect(runBoot).not.toThrow()
    expect(html()).toBe('dark')
  })
})
