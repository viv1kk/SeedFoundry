// Token values at paint time (D-5, D-37). A descriptor names a role ("positive", "series-1") and
// the chart reads `--chart-<role>` from the document when it draws, so a theme change is a redraw
// with freshly read values, and no colour is written anywhere but tokens.css.

import type { ClassInfo, Panel } from './types'

export type TokenReader = (name: string) => string

export function readTokens(element: Element = document.documentElement): TokenReader {
  const style = getComputedStyle(element)
  const read = (name: string, seen: string[] = []): string => {
    const token = name.startsWith('--') ? name : `--${name}`
    const value = style.getPropertyValue(token).trim()
    // Browsers substitute var() in a custom property's computed value; follow it where they do not.
    const reference = value.match(/^var\((--[\w-]+)\)$/)
    return reference && !seen.includes(reference[1]) ? read(reference[1], [...seen, token]) : value
  }
  return (name) => read(name)
}

/** A chart role's colour ("positive" reads --chart-positive). */
export function role(read: TokenReader, name: string): string {
  return read(`--chart-${name}`)
}

/** A class's colour on a panel: its role's token, unless the panel's descriptor gives the class a
 * colour value of its own (iteration 1's V-3, D-60), which is drawn as given. SeedFactory's code
 * writes no colour; such a value only ever comes from the descriptor. */
export function classColour(read: TokenReader, panel: Panel, cls: ClassInfo): string {
  return panel.class_colours?.[cls.id]?.colour ?? role(read, cls.role)
}

/** The label colour on a role's fill (D-100): the role's own --chart-label-on-<role> where
 * tokens.css gives one (navy on the light fills, white on the dark ones), else --chart-label-on-fill. */
export function labelOn(read: TokenReader, fill: string): string {
  return read(`--chart-label-on-${fill}`) || read('--chart-label-on-fill')
}
