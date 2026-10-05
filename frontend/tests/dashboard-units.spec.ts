// The dashboard's pure parts (D-56, D-59): formats, the drill path in the URL, and the ECharts
// options built from descriptor, payload and token values, in both themes. Payloads are the
// backend's own (tests/fixtures/dashboard): the polished checks read iteration 2's (D-61), and
// iteration 1's defect overlay has its own tests (D-60).

import { readdirSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { dashboardUrl } from '../src/dashboard/api'
import { deeper, drillOf, parent, steps } from '../src/dashboard/drill'
import { axisTitle, compact, count, format, month, percent, plain, usd, usdCompact } from '../src/dashboard/format'
import { barOption, chartOption, lineOption, pieOption, treemapOption } from '../src/dashboard/options'
import { readTokens } from '../src/dashboard/tokens'
import type { DashboardResponse, Panel } from '../src/dashboard/types'
import { dashboardFixture } from './fake-server'

const SRC = resolve(__dirname, '../src')
const TOKENS_CSS = readFileSync(join(SRC, 'styles/tokens.css'), 'utf8')
const root = dashboardFixture(2, 'root.json') as unknown as DashboardResponse
const panel = (id: string) => root.descriptor.panels.find((p) => p.id === id) as Panel
const data = (id: string) => root.payload.panels[id]
const rough = dashboardFixture(1, 'root.json') as unknown as DashboardResponse
const roughPanel = (id: string) => rough.descriptor.panels.find((p) => p.id === id) as Panel
const roughData = (id: string) => rough.payload.panels[id]
const DEFECTS_CSS = readFileSync(join(SRC, 'styles/defects.css'), 'utf8')

let style: HTMLStyleElement
beforeAll(() => {
  style = document.createElement('style')
  style.textContent = TOKENS_CSS
  document.head.append(style)
})
afterAll(() => {
  style.remove()
  document.documentElement.removeAttribute('data-theme')
})

function paint(theme: 'light' | 'dark') {
  document.documentElement.setAttribute('data-theme', theme)
  return { read: readTokens(), classes: root.descriptor.classes }
}

/** A token's declared value in a theme, straight from tokens.css. */
function declared(theme: 'light' | 'dark', name: string): string {
  const css = TOKENS_CSS.replace(/\/\*[\s\S]*?\*\//g, '')
  const block = (selector: string) => {
    const start = css.indexOf(`${selector} {`)
    return Object.fromEntries([...css.slice(start, css.indexOf('}', start)).matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]))
  }
  const values = theme === 'light' ? block(':root') : { ...block(':root'), ...block("[data-theme='dark']") }
  let value = values[name]
  while (value?.startsWith('var(')) value = values[value.slice(4, -1)]
  return value
}

describe('formats (one per measure, environment.md Styling)', () => {
  it('counts carry thousands separators', () => {
    expect([count(13050), count(0), count(1200)]).toEqual(['13,050', '0', '1,200'])
  })

  it('money is in dollars: compact on charts and KPIs, whole dollars in tables', () => {
    expect([usdCompact(850), usdCompact(45120), usdCompact(1035384), usdCompact(999_600)]).toEqual(['$850', '$45k', '$1.0M', '$1.0M'])
    expect([usd(36), usd(247500)]).toEqual(['$36', '$247,500'])
  })

  it('shares have one decimal place; months read as words; units join axis names', () => {
    expect([percent(63.5), percent(100), month('2025-10'), month('2026-09')]).toEqual(['63.5%', '100.0%', 'Oct 2025', 'Sep 2026'])
    expect(format(null, 'count')).toBe('')
    expect(axisTitle({ name: 'Seats', unit: 'seats' })).toBe('Seats')
    expect(axisTitle({ name: 'Recoverable a year', unit: 'USD' })).toBe('Recoverable a year (USD)')
    expect(axisTitle({ name: 'Product', unit: null })).toBe('Product')
  })
})

describe('the drill path in the URL (D-56)', () => {
  it('appends a step, keeping a multi-level step as one', () => {
    expect(deeper('', ['microsoft', 'microsoft-365-e3', 'unused'])).toBe('microsoft.microsoft-365-e3.unused')
    expect(deeper('microsoft', ['microsoft-365-e3'])).toBe('microsoft/microsoft-365-e3')
    expect(steps('microsoft/microsoft-365-e3.unused')).toEqual(['microsoft', 'microsoft-365-e3.unused'])
  })

  it('pops one step at a time, and none at All products', () => {
    expect(parent('microsoft.microsoft-365-e3.unused')).toBe('')
    expect(parent('microsoft/microsoft-365-e3/unused')).toBe('microsoft/microsoft-365-e3')
    expect(parent('')).toBeNull()
    expect([drillOf('microsoft'), drillOf(undefined), drillOf(['a', 'b'])]).toEqual(['microsoft', '', ''])
  })

  it('asks the server for the level, page and sort', () => {
    expect(dashboardUrl('license-optimization', { iteration: 1, drill: 'microsoft/microsoft-365-e3', page: 1 })).toBe(
      '/api/dashboards/license-optimization?iteration=1&drill=microsoft%2Fmicrosoft-365-e3',
    )
    expect(dashboardUrl('license-optimization', { iteration: 2, drill: '', page: 3, sort: 'days_idle', direction: 'desc' })).toBe(
      '/api/dashboards/license-optimization?iteration=2&page=3&sort=days_idle&direction=desc',
    )
  })
})

describe('chart options (colours from tokens at paint time, D-37)', () => {
  it.each(['light', 'dark'] as const)('binds each class and series to its role, read from tokens.css (%s)', (theme) => {
    const tree = treemapOption(panel('seats-treemap'), data('seats-treemap'), paint(theme)) as any
    const leaves = tree.series[0].data[0].children[0].children
    for (const leaf of leaves) {
      const role = root.descriptor.classes.find((c) => c.id === leaf.id)!.role
      expect(leaf.itemStyle.color).toBe(declared(theme, `--chart-${role}`))
      // Each role's own label token where tokens.css gives one, else the default (D-100).
      const own = `--chart-label-on-${role}`
      expect(leaf.label.color).toBe(declared(theme, declared(theme, own) ? own : '--chart-label-on-fill'))
      expect(leaf.itemStyle.borderColor).toBe(declared(theme, '--chart-outline'))
    }
    const bars = barOption(panel('entitlement'), data('entitlement'), paint(theme)) as any
    expect(bars.series.map((s: any) => s.itemStyle.color)).toEqual(['--chart-baseline', '--chart-series-1', '--chart-positive'].map((t) => declared(theme, t)))
    const lines = lineOption(panel('trend'), data('trend'), paint(theme)) as any
    // ValueWise roles (D-99): In use is a grey count, cost the gold Value lens.
    expect(lines.series.map((s: any) => s.lineStyle.color)).toEqual(['--chart-series-1', '--chart-series-2'].map((t) => declared(theme, t)))
    const cost = barOption(panel('recoverable'), data('recoverable'), paint(theme)) as any
    expect(cost.series[0].itemStyle.color).toBe(declared(theme, '--chart-value'))
    expect(cost.series[0].itemStyle.borderColor).toBe(declared(theme, '--chart-outline'))
  })

  it('repaints in the other theme with the other values', () => {
    const light = JSON.stringify(chartOption(panel('entitlement'), data('entitlement'), paint('light')))
    const dark = JSON.stringify(chartOption(panel('entitlement'), data('entitlement'), paint('dark')))
    expect(light).not.toBe(dark)
    expect(dark).toContain(declared('dark', '--chart-series-1'))
    expect(light).toContain(declared('light', '--chart-series-1'))
  })

  // jsdom writes rgba() without spaces; compare colours without them.
  const canonical = (colour: string) => colour.toLowerCase().replace(/\s+/g, '')

  it('every colour in an option is a token value of the theme it was painted in', () => {
    for (const theme of ['light', 'dark'] as const) {
      const values = new Set(
        TOKENS_CSS.match(/#[0-9a-f]{6}\b|rgba\([^)]*\)/gi)!.map(canonical).concat(['transparent']),
      )
      for (const p of root.descriptor.panels.filter((x) => ['treemap', 'bar', 'line'].includes(x.mark))) {
        const text = JSON.stringify(chartOption(p, data(p.id), paint(theme)))
        for (const colour of text.match(/#[0-9a-f]{3,8}\b|rgba?\([^)]*\)/gi) ?? []) {
          expect(values.has(canonical(colour)), `${p.id}: ${colour}`).toBe(true)
        }
      }
    }
  })

  it('names every axis and its unit, and formats axis figures as the descriptor says', () => {
    const bars = barOption(panel('recoverable'), data('recoverable'), paint('light')) as any
    expect([bars.xAxis.name, bars.yAxis.name]).toEqual(['Recoverable a year (USD)', 'Product'])
    expect(bars.xAxis.axisLabel.formatter(250000)).toBe('$250k')
    const lines = lineOption(panel('trend'), data('trend'), paint('light')) as any
    expect([lines.xAxis.name, lines.yAxis.name]).toEqual(['Month', 'Seats'])
    expect(lines.xAxis.axisLabel.formatter('2025-10')).toBe('Oct 2025')
    expect(lines.yAxis.axisLabel.formatter(12000)).toBe('12,000')
  })

  it('shows unpriced products as Withheld, never as a zero bar', () => {
    const recoverable = data('recoverable')
    const bars = barOption(panel('recoverable'), recoverable, paint('light')) as any
    const withheld = recoverable.withheld!.map((w, i) => (w ? i : -1)).filter((i) => i >= 0)
    expect(withheld.length).toBeGreaterThan(0)
    for (const i of withheld) {
      const item = bars.series[0].data[i]
      expect(item.itemStyle.color).toBe('transparent')
      expect(item.label.formatter).toBe('Withheld')
    }
    expect(bars.tooltip.formatter([{ dataIndex: withheld[0], seriesName: 'Recoverable a year', value: 0 }])).toContain('Withheld: no unit price,')
  })

  it('treemap levels: vendors and products carry upper labels, leaves fill by class; ECharts does not drill itself', () => {
    const tree = treemapOption(panel('seats-treemap'), data('seats-treemap'), paint('light')) as any
    const series = tree.series[0]
    expect(series.nodeClick).toBe(false)
    expect(series.breadcrumb.show).toBe(false)
    expect(series.levels).toHaveLength(4) // the virtual root, vendor, product, class
    expect([series.levels[1].upperLabel?.show, series.levels[2].upperLabel?.show, series.levels[3].upperLabel]).toEqual([true, true, undefined])
    const leaf = series.data[0].children[0].children[0]
    expect(leaf.step).toEqual([series.data[0].id, series.data[0].children[0].id, leaf.id])
  })
})

function files(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => (e.isDirectory() ? files(join(dir, e.name)) : [join(dir, e.name)]))
}

describe('source', () => {
  it('the dashboard writes no colour value of its own: chart and status tokens only (D-37)', () => {
    const sources = [...files(join(SRC, 'dashboard')), ...files(join(SRC, 'components/dashboard'))]
    expect(sources.length).toBeGreaterThan(8)
    for (const file of sources) {
      const text = readFileSync(file, 'utf8')
      // A colour literal; an HTML character reference such as &#8250; is not one.
      expect(text.match(/(?<!&)#[0-9a-fA-F]{3,8}\b(?![\w-])|rgba?\(|hsla?\(/g), file).toBeNull()
    }
  })
})

describe("iteration 1's overlay in the options (D-60)", () => {
  it('names the three V-4 formats: no separators, compact, and grouped without a currency', () => {
    expect([plain(13050), plain(12.6), compact(8286), compact(950), compact(1_191_396)]).toEqual(['13050', '13', '8.3k', '950', '1.2M'])
    expect([format(13050, 'plain'), format(8286, 'compact'), format(1267800, 'number')]).toEqual(['13050', '8.3k', '1,267,800'])
  })

  it.each(['light', 'dark'] as const)('draws the recoverable cost as a pie, one slice per priced product, in token colours (V-1, %s)', (theme) => {
    const values = roughData('recoverable').values!
    const pie = pieOption(roughPanel('recoverable'), roughData('recoverable'), paint(theme)) as any
    const slices = pie.series[0].data
    expect(slices).toHaveLength(values.filter((v) => v !== null).length)
    expect(slices.length).toBeGreaterThan(8)
    const roles = roughPanel('recoverable').slice_roles!
    expect(slices.map((s: any) => s.itemStyle.color)).toEqual(slices.map((_: unknown, n: number) => declared(theme, `--chart-${roles[n % roles.length]}`)))
    const priced = roughData('recoverable').categories!.filter((_, i) => values[i] !== null)
    expect(slices.map((s: any) => s.step)).toEqual(priced.map((c) => c.step))
    expect((chartOption(roughPanel('recoverable'), roughData('recoverable'), paint(theme)) as any).series).toEqual(pie.series)
    expect(pie.tooltip.formatter({ name: priced[0].name, value: slices[0].value })).toContain(usdCompact(slices[0].value))
  })

  it("draws Unused in the descriptor's own colour on the treemap, and every other colour from tokens (V-3)", () => {
    for (const theme of ['light', 'dark'] as const) {
      const own = roughPanel('seats-treemap').class_colours!.unused.colour
      const tree = treemapOption(roughPanel('seats-treemap'), roughData('seats-treemap'), paint(theme)) as any
      const leaves = tree.series[0].data.flatMap((v: any) => v.children.flatMap((p: any) => p.children))
      expect(leaves.filter((l: any) => l.id === 'unused').every((l: any) => l.itemStyle.color === own)).toBe(true)
      expect(leaves.filter((l: any) => l.id === 'active').every((l: any) => l.itemStyle.color === declared(theme, '--chart-positive'))).toBe(true)
      const tokenValues = new Set(TOKENS_CSS.match(/#[0-9a-f]{6}\b|rgba\([^)]*\)/gi)!.map((c) => c.toLowerCase().replace(/\s+/g, '')).concat(['transparent']))
      for (const p of rough.descriptor.panels.filter((x) => ['treemap', 'bar', 'line', 'pie'].includes(x.mark))) {
        const colours = JSON.stringify(chartOption(p, roughData(p.id), paint(theme))).match(/#[0-9a-f]{3,8}\b|rgba?\([^)]*\)/gi) ?? []
        const strays = colours.filter((c) => !tokenValues.has(c.toLowerCase().replace(/\s+/g, '')))
        expect(new Set(strays), `${p.id} ${theme}`).toEqual(p.id === 'seats-treemap' ? new Set([own]) : new Set())
      }
    }
  })
})

describe('defects.css stays inside the iteration 1 dashboard (R-1)', () => {
  const css = DEFECTS_CSS.replace(/\/\*[\s\S]*?\*\//g, '')
  const selectors = [...css.matchAll(/([^{}]+)\{[^{}]*\}/g)].flatMap((m) => m[1].split(',').map((x) => x.trim().replace(/\s+/g, ' ')))

  it('scopes every selector under .defects-overlay, with no sibling combinator to step outside it', () => {
    expect(selectors.length).toBeGreaterThan(8)
    for (const selector of selectors) {
      expect(selector.startsWith('.defects-overlay '), selector).toBe(true)
      expect(selector.replace(/\([^)]*\)/g, ''), selector).not.toMatch(/[~+]/)
    }
    expect(css).not.toMatch(/@import|@font-face|:root|\bhtml\b|\bbody\b/)
    expect(css).not.toMatch(/--[\w-]+\s*:/) // defines no token
  })

  it('writes no colour value: its grey is a token used as text (V-8)', () => {
    expect(css.match(/#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(/g)).toBeNull()
    expect(css).toContain('var(--border-default)')
  })

  it('names a defect for every rule: V-6, V-7 and V-8 only', () => {
    expect([...new Set([...DEFECTS_CSS.matchAll(/\/\* (V-\d+):/g)].map((m) => m[1]))]).toEqual(['V-6', 'V-7', 'V-8'])
  })

  it("is loaded only through a descriptor's named sheet, and nothing imports it at start", () => {
    const main = readFileSync(join(SRC, 'main.ts'), 'utf8')
    expect(main).not.toContain('defects')
    const importers = files(SRC).filter((f) => !f.endsWith('defects.css') && readFileSync(f, 'utf8').includes('defects.css'))
    expect(importers.map((f) => f.slice(SRC.length + 1).replace(/\\/g, '/'))).toEqual(['dashboard/stylesheets.ts'])
  })
})
