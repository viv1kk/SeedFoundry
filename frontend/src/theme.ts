// Light and dark theme (seed-reuse-notes.md section 1.2). The theme is the data-theme
// attribute on <html>; tokens.css does the rest. A first visit is dark, the ValueWise
// presentation default (D-96); light is for print and bright rooms. index.html runs the
// same first-visit rule before the page paints, so there is no flash of the wrong theme.

import { ref } from 'vue'

export type Theme = 'light' | 'dark'

export const THEME_KEY = 'seedfoundry.theme'

function isTheme(value: unknown): value is Theme {
  return value === 'light' || value === 'dark'
}

// Storage can be missing or throw (private windows, blocked site data); the theme still works.
export function storedTheme(): Theme | null {
  try {
    const value = window.localStorage.getItem(THEME_KEY)
    return isTheme(value) ? value : null
  } catch {
    return null
  }
}

function storeTheme(theme: Theme): void {
  try {
    window.localStorage.setItem(THEME_KEY, theme)
  } catch {
    // Not remembered across reloads, but the switch itself still happens.
  }
}

/** A remembered choice wins; a first visit is dark, whatever the operating system prefers. */
export function initialTheme(): Theme {
  return storedTheme() ?? 'dark'
}

export const theme = ref<Theme>('dark')

export function applyTheme(next: Theme): void {
  theme.value = next
  document.documentElement.setAttribute('data-theme', next)
}

export function initTheme(): void {
  applyTheme(initialTheme())
}

/** The toggle: switch and remember. */
export function toggleTheme(): Theme {
  const next: Theme = theme.value === 'dark' ? 'light' : 'dark'
  applyTheme(next)
  storeTheme(next)
  return next
}
