// Contrast test (NFR-6, D-21), ported from Seed v0.1's backend/tests/test_design.py rules
// (seed-reuse-notes.md section 1.5) and run over tokens.css in both themes, plus the console
// pairs (D-37). Since CR-3 the values are the ValueWise house style's: it checks that tokens.css
// holds them, read from the token table in docs/valuewise-style.md (D-96, D-102), and the rules
// that follow from the guide (D-97, D-98, D-100).

import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const ROOT = resolve(__dirname, '..', '..')
const CSS = readFileSync(resolve(ROOT, 'frontend/src/styles/tokens.css'), 'utf8')
const STYLE = readFileSync(resolve(ROOT, 'docs/valuewise-style.md'), 'utf8')

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
// Colours SeedFactory sets as text: the control colour, link blue, and each status's text colour.
const COLOURED_TEXT = ['--accent', '--link', '--status-positive-text', '--status-warning-text', '--status-negative-text', '--status-neutral']
const STATUSES = ['positive', 'warning', 'negative']
const SERIES = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => `series-${n}`)
// Every chart role but muted, which is drawn as a background (Unassigned).
const MARK_ROLES = [...SERIES, 'positive', 'warning', 'negative', 'anomaly', 'value', 'baseline']
const BANDS: Record<string, string> = {
  '--band-under-20': '#036715',
  '--band-20-50': '#17ae42',
  '--band-50-70': '#37eb67',
  '--band-70-100': '#e9973a',
  '--band-100': '#b50e05',
  '--band-150': '#7a0a02',
}
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

/** A role's label token: its own --chart-label-on-<role>, else --chart-label-on-fill (dashboard/tokens.ts labelOn). */
function labelFor(theme: ThemeName, role: string): string {
  return THEMES[theme][`--chart-label-on-${role}`] !== undefined ? `--chart-label-on-${role}` : '--chart-label-on-fill'
}

describe('tokens.css holds the ValueWise values (docs/valuewise-style.md)', () => {
  // Rows like: | `--surface-base` | `#ffffff` | `#020921` | Background |
  const section = STYLE.slice(STYLE.indexOf('### Tokens'))
  const rows = [...section.matchAll(/^\| `(--[\w-]+)` \| `(#[0-9a-f]{6})` \| `(#[0-9a-f]{6})` \|/gim)].map((m) => ({
    token: m[1],
    light: m[2].toLowerCase(),
    dark: m[3].toLowerCase(),
  }))

  it('reads every token from the style doc', () => {
    // 11 surface, line and text tokens; control, selection, link and gold; 3 status fills; 11 chart tokens; 2 console
    expect(rows).toHaveLength(31)
  })

  it.each(rows)('$token', ({ token, light, dark }) => {
    expect(colour('light', token)).toBe(light)
    expect(colour('dark', token)).toBe(dark)
  })

  it("holds the guide's data scale, the same in both themes", () => {
    for (const [token, hex] of Object.entries(BANDS)) {
      expect(colour('light', token)).toBe(hex)
      expect(colour('dark', token)).toBe(hex)
    }
  })

  it('is flat and square: no radius, no shadow (guide section 5)', () => {
    for (const theme of BOTH) {
      for (const token of ['--radius-sm', '--radius-md', '--radius-lg']) expect(THEMES[theme][token]).toBe('0')
      for (const token of ['--shadow-sm', '--shadow-md']) expect(THEMES[theme][token]).toBe('none')
    }
  })

  it('sets IBM Plex Sans, and IBM Plex Mono for code (D-101)', () => {
    expect(THEMES.light['--font-sans']).toMatch(/^'IBM Plex Sans Variable'/)
    expect(THEMES.light['--font-mono']).toMatch(/^'IBM Plex Mono'/)
  })
})

describe('contrast, both themes (WCAG 2.1)', () => {
  it('every text token on every surface and on the selected-row tint, at 4.5:1', () => {
    expect(failures(every(TEXT, [...SURFACES, SELECTED_ROW], 4.5))).toEqual([])
  })

  it('control, link and status text colours, on every surface and the selected-row tint, at 4.5:1', () => {
    expect(failures(every(COLOURED_TEXT, [...SURFACES, SELECTED_ROW], 4.5))).toEqual([])
  })

  it('each status label on its fill, at 4.5:1 (D-98)', () => {
    const pairs = BOTH.flatMap((theme) => STATUSES.map((s) => ({ theme, fg: `--on-status-${s}`, bg: `--status-${s}`, min: 4.5 })))
    expect(failures(pairs)).toEqual([])
  })

  it('the primary button label on the control colour, at 4.5:1', () => {
    expect(failures(every(['--text-inverse'], ['--accent'], 4.5))).toEqual([])
  })

  it('the control colour as an outline (focus, the finding highlight) against every surface, at 3:1 (D-65)', () => {
    expect(failures(every(['--accent'], SURFACES, 3))).toEqual([])
  })

  it('gold, used only for a large headline figure, on every surface, at 3:1 (D-97)', () => {
    expect(failures(every(['--gold'], SURFACES, 3))).toEqual([])
  })

  it('the chart outline against the panel surface, at 3:1 (D-100)', () => {
    expect(failures(every(['--chart-outline'], ['--surface-raised'], 3))).toEqual([])
  })

  it('every chart role except muted holds a 3:1 edge on the panel surface: its fill or its outline (D-100)', () => {
    const weak = BOTH.flatMap((theme) => {
      const panel = colour(theme, '--surface-raised')
      const edge = contrast(colour(theme, '--chart-outline'), panel)
      return MARK_ROLES.filter((r) => Math.max(contrast(colour(theme, `--chart-${r}`), panel), edge) < 3).map((r) => `${theme}: ${r}`)
    })
    expect(weak).toEqual([])
  })

  it('every chart label on its fill, at 4.5:1 (D-100)', () => {
    const pairs = BOTH.flatMap((theme) => [...MARK_ROLES, 'muted'].map((r) => ({ theme, fg: labelFor(theme, r), bg: `--chart-${r}`, min: 4.5 })))
    expect(failures(pairs)).toEqual([])
  })

  it("follows the guide's light-theme tile labels: navy on green and orange, white on red", () => {
    expect(colour('light', labelFor('light', 'positive'))).toBe('#0b1f3a')
    expect(colour('light', labelFor('light', 'warning'))).toBe('#0b1f3a')
    expect(colour('light', labelFor('light', 'anomaly'))).toBe('#ffffff')
    expect(colour('light', labelFor('light', 'negative'))).toBe('#ffffff')
  })
})

describe('console (D-37)', () => {
  it('every console text colour on the console surfaces, at 4.5:1', () => {
    expect(failures(every(CONSOLE_TEXT, CONSOLE_SURFACES, 4.5))).toEqual([])
  })

  it("a FAIL level's text on its red mark, at 4.5:1 (D-98)", () => {
    expect(failures(every(['--console-fail'], ['--console-fail-mark'], 4.5))).toEqual([])
  })

  it('is a dark surface in both themes: no console token changes with the theme', () => {
    expect(Object.keys(DARK_OVERRIDES).filter((name) => name.startsWith('--console-'))).toEqual([])
    expect(luminance(colour('light', '--console-surface'))).toBeLessThan(0.05)
  })

  it('draws LLM and API lines in white and grey, not a band or link colour (ValueWise section 1)', () => {
    expect([colour('light', '--console-llm'), colour('light', '--console-api')]).toEqual([
      colour('dark', '--text-primary'),
      colour('dark', '--text-secondary'),
    ])
  })
})

describe('the contrast arithmetic', () => {
  it('matches WCAG reference values', () => {
    expect(contrast('#000000', '#ffffff')).toBeCloseTo(21, 5)
    expect(contrast('#ffffff', '#ffffff')).toBeCloseTo(1, 5)
    expect(contrast('#767676', '#ffffff')).toBeCloseTo(4.54, 2)
  })
})
