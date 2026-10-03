// A recorder in place of src/dashboard/echarts.ts: jsdom has no canvas, and the tests need to see
// what each chart was given (its options, in the colours read at paint time), to click its marks
// and to see the actions the keyboard path sends. Use with
//   vi.mock('../src/dashboard/echarts', () => import('./fake-echarts'))

import type { Chart, ClickParams } from '../src/dashboard/echarts'

export class FakeChart implements Chart {
  options: object[] = []
  actions: object[] = []
  clicks: ((params: ClickParams) => void)[] = []
  resized = 0
  disposed = false

  constructor(readonly element: HTMLElement) {}

  setOption(option: object): void {
    this.options.push(option)
  }

  on(_event: 'click', handler: (params: ClickParams) => void): void {
    this.clicks.push(handler)
  }

  dispatchAction(action: object): void {
    this.actions.push(action)
  }

  resize(): void {
    this.resized++
  }

  dispose(): void {
    this.disposed = true
  }

  /** The latest options, typed loosely for reading. */
  get option(): Record<string, any> {
    return this.options[this.options.length - 1] as Record<string, any>
  }

  /** Click a mark as ECharts would, with its data item. */
  click(data: unknown): void {
    this.clicks.forEach((handler) => handler({ data }))
  }
}

export const charts: FakeChart[] = []

export function initChart(element: HTMLElement): Chart {
  const chart = new FakeChart(element)
  charts.push(chart)
  return chart
}

/** The live chart drawn for a panel id. */
export function chartFor(panelId: string): FakeChart {
  const found = [...charts].reverse().find((c) => !c.disposed && c.element.closest(`[data-panel="${panelId}"]`))
  if (!found) throw new Error(`no live chart for ${panelId}`)
  return found
}
