// Apache ECharts, bundled from npm (D-38, NFR-2): only the charts and components the dashboard
// uses, drawn to canvas. Tests replace this module with a recorder.

import { BarChart, LineChart, PieChart, TreemapChart } from 'echarts/charts'
import { AriaComponent, GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([BarChart, LineChart, PieChart, TreemapChart, AriaComponent, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer])

export interface ClickParams {
  data?: unknown
  dataIndex?: number
  seriesIndex?: number
}

/** The part of an ECharts instance the dashboard uses. */
export interface Chart {
  setOption(option: object, opts?: { notMerge?: boolean }): void
  on(event: 'click', handler: (params: ClickParams) => void): void
  dispatchAction(action: object): void
  resize(): void
  dispose(): void
}

export function initChart(element: HTMLElement): Chart {
  return echarts.init(element, undefined, { renderer: 'canvas' }) as unknown as Chart
}
