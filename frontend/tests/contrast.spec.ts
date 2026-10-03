// Contrast test (NFR-6, D-21), ported from Seed v0.1's backend/tests/test_design.py rules
// (seed-reuse-notes.md section 1.5) and run over tokens.css in both themes, plus the console
// pairs (D-37). It also checks that tokens.css still holds Seed v0.1's values exactly, read
// from the tables in seed-reuse-notes.md section 1.3 (D-38).

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const ROOT = resolve(__dirname, '..', '..')
const CSS = readFileSync(resolve(ROOT, 'frontend/src/styles/tokens.css'), 'utf8')
const NOTES = readFileSync(resolve(ROOT, 'docs/seed-reuse-notes.md'), 'utf8')

type Tokens = Record<string, string>
type ThemeName = 'light' | 'dark'

function declarations(block: string): Tokens {
  const tokens: Tokens = {}
  for (const match of block.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) tokens[match[1]] = match[2].trim()
  return tokens
}

function block(selector: string): string {
  const css = CSS.replace(/\/\*[\s\S]*?\*\//g, '')
  const start = css.indexOf(`${selector} {`)
  if (start < 0) throw new Error(`no ${selector} block in tokens.css`)
  return css.slice(start, css.indexOf('}', start))
}

const LIGHT = declarations(block(':root'))
const DARK_OVERRIDES = declarations(block("[data-theme='dark']"))
const THEMES: Record<ThemeName, Tokens> = { light: LIGHT, dark: { ...LIGHT, ...DARK_OVERRIDES } }

/** A token's colour in a theme, following var() references as the browser does. */
function colour(theme: ThemeName, name: string, seen: string[] = []): string {
  const value = THEMES[theme][name]
  if (value === undefined) throw new Error(`${name} is not defined in the ${theme} theme`)
  const reference = value.match(/^var\((--[\w-]+)\)$/)
  if (reference) {
    if (seen.includes(reference[1])) throw new Error(`var() cycle at ${name}`)
    return colour(theme, reference[1], [...seen, name])
  }
  if (!/^#[0-9a-f]{6}$/i.test(value)) throw new Error(`${name} in ${theme} is not a #rrggbb colour: ${value}`)
  return value.toLowerCase()
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** WCAG 2.1 contrast ratio. */
export function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

interface Pair {
  theme: ThemeName
  fg: string
  bg: string
  min: number
}

function failures(pairs: Pair[]): string[] {
  return pairs
    .map((p) => ({ ...p, ratio: contrast(colour(p.theme, p.fg), colour(p.theme, p.bg)) }))
    .filter((p) => p.ratio < p.min)
    .map((p) => `${p.theme}: ${p.fg} on ${p.bg} is ${p.ratio.toFixed(2)}:1, needs ${p.min}:1`)
}

const BOTH: ThemeName[] = ['light', 'dark']
const SURFACES = ['--surface-base', '--surface-raised', '--surface-sunken', '--surface-overlay']
const SELECTED_ROW = '--accent-subtle'
const TEXT = ['--text-primary', '--text-secondary', '--text-muted']
// SeedFoundry also sets status and accent colours as text (chips, links, the iteration badge).
const COLOURED_TEXT = ['--accent', '--status-positive', '--status-warning', '--status-negative', '--status-neutral']
const FILLED_ROLES = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => `--chart-series-${n}`).concat(
  ['positive', 'warning', 'negative', 'anomaly'].map((role) => `--chart-${role}`),
)
const CONSOLE_SURFACES = ['--console-surface', '--console-surface-raised']
const CONSOLE_TEXT = [
  '--console-text',
  '--console-text-secondary',
  '--console-text-muted',
  '--console-llm',
  '--console-api',
  '--console-pass',
  '--console-warn',
  '--console-fail',
]

function every(fgs: string[], bgs: string[], min: number, themes: ThemeName[] = BOTH): Pair[] {
  return themes.flatMap((theme) => fgs.flatMap((fg) => bgs.map((bg) => ({ theme, fg, bg, min }))))
}

describe("tokens.css holds Seed v0.1's values unchanged", () => {
  // Rows like: | `--surface-base` | `#f7f8fa` | `#0e1116` | ... and | `series-1` | `#1e61f5` | `#5b8cff` | ...
  const section = NOTES.slice(NOTES.indexOf('### 1.3 Colour tokens'), NOTES.indexOf('### 1.4'))
  const rows = [...section.matchAll(/^\| `([\w-]+)` \| `(#[0-9a-f]{6})` \| `(#[0-9a-f]{6})` \|/gim)].map((m) => ({
    token: m[1].startsWith('--') ? m[1] : `--chart-${m[1]}`,
    light: m[2].toLowerCase(),
    dark: m[3].toLowerCase(),
  }))

  it('reads every Seed token from the reuse notes', () => {
    // 11 surface, line and text tokens, 6 accent and status, 14 chart roles
    expect(rows).toHaveLength(31)
  })

  it.each(rows)('$token', ({ token, light, dark }) => {
    expect(THEMES.light[token]?.toLowerCase()).toBe(light)
    expect(THEMES.dark[token]?.toLowerCase()).toBe(dark)
  })
})

describe('contrast, both themes (WCAG 2.1)', () => {
  it('every text token on every surface and on the selected-row tint, at 4.5:1', () => {
    expect(failures(every(TEXT, [...SURFACES, SELECTED_ROW], 4.5))).toEqual([])
  })

  it('accent and status colours used as text, on every surface and the selected-row tint, at 4.5:1', () => {
    expect(failures(every(COLOURED_TEXT, [...SURFACES, SELECTED_ROW], 4.5))).toEqual([])
  })

  it('the primary button label on the accent, at 4.5:1', () => {
    expect(failures(every(['--text-inverse'], ['--accent'], 4.5))).toEqual([])
  })

  it('every chart role except muted against the panel surface, at 3:1', () => {
    expect(failures(every([...FILLED_ROLES, '--chart-baseline'], ['--surface-raised'], 3))).toEqual([])
  })

  it('every chart label on its fill, at 4.5:1', () => {
    const pairs = [
      ...every(['--chart-label-on-fill'], FILLED_ROLES, 4.5),
      ...every(['--chart-label-on-baseline'], ['--chart-baseline'], 4.5),
      ...every(['--chart-label-on-muted'], ['--chart-muted'], 4.5),
    ]
    expect(failures(pairs)).toEqual([])
  })

  it('chart labels: light on filled roles in light, dark in dark; the reverse on baseline and muted', () => {
    const isLight = (theme: ThemeName, token: string) => luminance(colour(theme, token)) > 0.5
    expect(isLight('light', '--chart-label-on-fill')).toBe(true)
    expect(isLight('dark', '--chart-label-on-fill')).toBe(false)
    expect(isLight('light', '--chart-label-on-baseline')).toBe(false)
    expect(isLight('dark', '--chart-label-on-baseline')).toBe(true)
    expect(isLight('light', '--chart-label-on-muted')).toBe(false)
    expect(isLight('dark', '--chart-label-on-muted')).toBe(true)
  })
})

describe('console (D-37)', () => {
  it('every console text colour on the console surfaces, at 4.5:1', () => {
    expect(failures(every(CONSOLE_TEXT, CONSOLE_SURFACES, 4.5))).toEqual([])
  })

  it('is a dark surface in both themes: no console token changes with the theme', () => {
    expect(Object.keys(DARK_OVERRIDES).filter((name) => name.startsWith('--console-'))).toEqual([])
    expect(luminance(colour('light', '--console-surface'))).toBeLessThan(0.05)
  })

  it('has an API line colour', () => {
    expect(colour('light', '--console-api')).toBe(colour('dark', '--chart-series-3'))
  })
})

describe('the contrast arithmetic', () => {
  it('matches WCAG reference values', () => {
    expect(contrast('#000000', '#ffffff')).toBeCloseTo(21, 5)
    expect(contrast('#ffffff', '#ffffff')).toBeCloseTo(1, 5)
    expect(contrast('#767676', '#ffffff')).toBeCloseTo(4.54, 2)
  })
})
