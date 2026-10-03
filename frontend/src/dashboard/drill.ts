// The drill path in the URL (FR-D-6, D-29, D-56): steps joined by "/", a step's level ids joined
// by ".". A treemap leaf is one step of three levels ("microsoft.microsoft-365-e3.unused"), so
// after a reload its crumb still names all three, and Back still pops it as one step.

import type { Step } from './types'

export function steps(path: string): string[] {
  return path ? path.split('/') : []
}

/** The path after one more step. */
export function deeper(path: string, step: Step): string {
  return [...steps(path), step.join('.')].join('/')
}

/** The path one step up, or null at All products. */
export function parent(path: string): string | null {
  const all = steps(path)
  return all.length ? all.slice(0, -1).join('/') : null
}

/** The drill query value as a string; anything else (missing, repeated) reads as All products. */
export function drillOf(value: unknown): string {
  return typeof value === 'string' ? value : ''
}
