// ECharts options for the chart marks (treemap, bar, line, pie), from a panel's descriptor, its data
// and the token values read at paint time. Pure, so a theme change or the fonts arriving is a
// rebuild (seed-reuse-notes.md section 1.2 and 1.4). Every colour is a token's value, or a value the
// descriptor itself gives (iteration 1's V-3, D-60); none is written here. ValueWise house style
// (D-99, D-100): flat, square, 14 px text and 16 px tile labels with the count in brackets, and
// every filled mark outlined in --chart-outline so it holds a 3:1 edge on the card whatever its fill.

import { axisTitle, count, format } from './format'
import { classColour, labelOn, role, type TokenReader } from './tokens'
import type { ClassInfo, Panel, PanelData, TreeNode } from './types'

export interface Paint {
  read: TokenReader
  classes: ClassInfo[]
}

const CRUMB_JOIN = ' › '
const MIN_LABELLED_SHARE = 0.01

function escape(text: string): string {
  return text.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`)
}

function fonts(read: TokenReader) {
  return { sans: read('--font-sans'), mono: read('--font-mono') }
}

const TEXT_SIZE = 14
const TILE_LABEL_SIZE = 16

function textStyle(read: TokenReader) {
  return { fontFamily: fonts(read).sans, fontSize: TEXT_SIZE, color: read('--text-secondary') }
}

/** The 1 px outline every filled mark carries (D-100). */
function outline(read: TokenReader) {
  return { borderColor: read('--chart-outline'), borderWidth: 1 }
}

function tooltip(read: TokenReader, trigger: 'item' | 'axis') {
  return {
    trigger,
    confine: true,
    backgroundColor: read('--surface-overlay'),
    borderColor: read('--border-default'),
    borderWidth: 1,
    padding: [6, 10],
    textStyle: { fontFamily: fonts(read).sans, fontSize: TEXT_SIZE, color: read('--text-primary') },
    extraCssText: 'box-shadow: none; border-radius: 0;',
    axisPointer: { type: 'shadow', shadowStyle: { color: read('--chart-brush') } },
  }
}

/** A tooltip line: a label, then the figure in bold. */
function line(label: string, figure: string): string {
  return `${escape(label)} <span style="font-weight: 600">${escape(figure)}</span>`
}

function legend(read: TokenReader) {
  return {
    top: 0,
    left: 0,
    icon: 'rect',
    itemWidth: 12,
    itemHeight: 12,
    itemGap: 16,
    textStyle: textStyle(read),
  }
}

/** `vertical`: the value axis stands on the left (a line chart, a column chart), so its name clears
 * the tick labels, which at 14 px are wider than they are tall. */
function valueAxis(panel: Panel, read: TokenReader, vertical: boolean) {
  const value = panel.value!
  return {
    type: 'value',
    name: axisTitle(value.axis),
    nameLocation: 'middle',
    nameGap: vertical ? 56 : 30,
    nameTextStyle: { ...textStyle(read), color: read('--text-muted') },
    axisLabel: { ...textStyle(read), formatter: (v: number) => format(v, value.format) },
    splitLine: { lineStyle: { color: read('--chart-grid') } },
    axisLine: { show: false },
  }
}

function categoryAxis(panel: Panel, read: TokenReader, labels: string[], horizontal: boolean) {
  const category = panel.category!
  return {
    type: 'category',
    data: labels,
    inverse: horizontal,
    name: axisTitle(category.axis),
    nameLocation: horizontal ? 'start' : 'middle',
    nameGap: horizontal ? 8 : 28,
    nameTextStyle: { ...textStyle(read), color: read('--text-muted'), align: horizontal ? 'right' : 'center' },
    axisLabel: {
      ...textStyle(read),
      width: horizontal ? 132 : undefined,
      overflow: horizontal ? 'truncate' : undefined,
      formatter: category.format ? (v: string) => format(v, category.format!) : undefined,
    },
    axisLine: { lineStyle: { color: read('--border-default') } },
    axisTick: { show: false },
  }
}

/** Room on top for a legend at 14 px and, on a horizontal bar chart, the category axis's name. */
function grid(horizontal: boolean, legend: boolean) {
  return { left: horizontal ? 4 : 24, right: 24, top: legend ? 56 : 40, bottom: 40, containLabel: true }
}

export function treemapOption(panel: Panel, data: PanelData, paint: Paint) {
  const { read, classes } = paint
  const byClass = new Map(classes.map((c) => [c.id, c]))
  const total = data.legend?.reduce((sum, item) => sum + item.count, 0) ?? 0

  const node = (n: TreeNode): object => {
    const cls = n.class ? byClass.get(n.class) : undefined
    return {
      id: n.id,
      name: n.name,
      value: n.value,
      step: n.step,
      level: n.level,
      itemStyle: cls ? { color: classColour(read, panel, cls), ...outline(read) } : { color: read('--surface-sunken'), borderColor: read('--border-default') },
      // A leaf too small for its name shows none rather than a stub; its tooltip still names it.
      // A label is the name with the count in brackets, as on the ValueWise dashboard.
      label: cls
        ? {
            color: labelOn(read, cls.role),
            show: total > 0 && n.value / total >= MIN_LABELLED_SHARE,
            formatter: `${n.name} (${format(n.value, panel.format ?? 'count')})`,
          }
        : undefined,
      children: n.children?.map(node),
    }
  }

  // levels[0] is ECharts' virtual root; levels[1] the first level of data. A level's gapWidth is
  // the gap between its children. Parents (vendor, product) carry their name in an upper label;
  // leaves (classes) are filled with their class's role.
  const depth = (nodes: TreeNode[] | undefined): number => (nodes?.length ? 1 + Math.max(...nodes.map((n) => depth(n.children))) : 0)
  const deepest = depth(data.nodes)
  const levels = [
    { itemStyle: { borderWidth: 0, gapWidth: 3 } },
    ...Array.from({ length: deepest }, (_, i) =>
      i === deepest - 1
        ? { itemStyle: { ...outline(read), gapWidth: 0 } }
        : {
            itemStyle: { borderWidth: 2, borderColor: read('--surface-raised'), gapWidth: 2 },
            upperLabel: {
              show: true,
              height: 22,
              color: read('--text-primary'),
              fontFamily: fonts(read).sans,
              fontSize: TEXT_SIZE,
              fontWeight: i === 0 ? 600 : 500,
            },
          },
    ),
  ]

  return {
    aria: { enabled: true, label: { description: `${panel.title}: ${count(total)} seats` } },
    textStyle: textStyle(read),
    tooltip: {
      ...tooltip(read, 'item'),
      formatter: (info: { treePathInfo?: { name: string }[]; value?: number; data?: { level?: string } }) => {
        const path = (info.treePathInfo ?? []).slice(1).map((p) => p.name)
        const value = Number(info.value ?? 0)
        const share = total ? `, ${((100 * value) / total).toFixed(1)}%` : ''
        return line(path.join(CRUMB_JOIN), `${count(value)} seats${share}`)
      },
    },
    series: [
      {
        type: 'treemap',
        name: panel.title,
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        left: 0,
        right: 0,
        top: 0,
        bottom: 0,
        label: { show: true, fontFamily: fonts(read).sans, fontSize: TILE_LABEL_SIZE, overflow: 'truncate' },
        emphasis: { itemStyle: { borderColor: read('--text-primary') } },
        levels,
        data: (data.nodes ?? []).map(node),
      },
    ],
  }
}

export function barOption(panel: Panel, data: PanelData, paint: Paint) {
  const { read } = paint
  const horizontal = panel.orientation !== 'vertical'
  const categories = data.categories ?? []
  const valueFormat = panel.value!.format
  const series = panel.series ?? []
  const withheld = data.withheld ?? []

  const bars = series.map((s) => {
    const values = data.series ? data.series[s.id] : data.values
    return {
      type: 'bar',
      name: s.label,
      barGap: '12%',
      barCategoryGap: series.length > 1 ? '28%' : '36%',
      itemStyle: { color: role(read, s.role), ...outline(read) },
      emphasis: { focus: 'none', itemStyle: { color: role(read, s.role), ...outline(read) } },
      data: (values ?? []).map((v, i) =>
        withheld[i]
          ? {
              value: 0,
              step: categories[i]?.step,
              itemStyle: { color: 'transparent', borderWidth: 0 },
              label: {
                show: true,
                position: horizontal ? 'right' : 'top',
                formatter: panel.withheld!.label,
                color: read(`--${panel.withheld!.role}`),
                fontFamily: fonts(read).sans,
                fontSize: TEXT_SIZE,
              },
            }
          : { value: v, step: categories[i]?.step },
      ),
    }
  })

  const axes = [valueAxis(panel, read, !horizontal), categoryAxis(panel, read, categories.map((c) => c.name), horizontal)]

  return {
    aria: { enabled: true, label: { description: `${panel.title}, one bar per product` } },
    textStyle: textStyle(read),
    grid: grid(horizontal, series.length > 1),
    legend: series.length > 1 ? legend(read) : undefined,
    tooltip: {
      ...tooltip(read, 'axis'),
      formatter: (items: { dataIndex: number; seriesName: string; value: number }[]) => {
        const i = items[0]?.dataIndex ?? 0
        const head = `<strong>${escape(categories[i]?.name ?? '')}</strong>`
        if (withheld[i]) return `${head}<br>${line('Withheld: no unit price,', `${count(data.seats?.[i] ?? 0)} recoverable seats`)}`
        return [head, ...items.map((item) => line(`${item.seriesName}:`, format(item.value, valueFormat)))].join('<br>')
      },
    },
    xAxis: horizontal ? axes[0] : axes[1],
    yAxis: horizontal ? axes[1] : axes[0],
    series: bars,
  }
}

export function lineOption(panel: Panel, data: PanelData, paint: Paint) {
  const { read } = paint
  const months = data.months ?? []
  const valueFormat = panel.value!.format
  return {
    aria: { enabled: true, label: { description: `${panel.title}, ${months.length} months` } },
    textStyle: textStyle(read),
    grid: grid(false, true),
    legend: legend(read),
    tooltip: {
      ...tooltip(read, 'axis'),
      axisPointer: { type: 'line', lineStyle: { color: read('--border-strong') } },
      formatter: (items: { dataIndex: number; seriesName: string; value: number }[]) =>
        [`<strong>${escape(format(months[items[0]?.dataIndex ?? 0], 'month'))}</strong>`, ...items.map((item) => line(`${item.seriesName}:`, format(item.value, valueFormat)))].join(
          '<br>',
        ),
    },
    xAxis: { ...categoryAxis(panel, read, months, false), boundaryGap: false },
    yAxis: valueAxis(panel, read, true),
    series: (panel.series ?? []).map((s) => ({
      type: 'line',
      name: s.label,
      data: data.series?.[s.id] ?? [],
      // Square points, outlined like every filled mark, so each month holds its edge (D-100).
      symbol: 'rect',
      symbolSize: 7,
      lineStyle: { width: 2, color: role(read, s.role) },
      itemStyle: { color: role(read, s.role), ...outline(read) },
      emphasis: { focus: 'none' },
    })),
  }
}

/** A pie over a bar's data: one slice per category with a value (a withheld one has none), in the
 * descriptor's slice roles, cycled. The polished descriptor draws no pie; iteration 1's V-1 does. */
export function pieOption(panel: Panel, data: PanelData, paint: Paint) {
  const { read } = paint
  const categories = data.categories ?? []
  const values = data.values ?? []
  const roles = panel.slice_roles?.length ? panel.slice_roles : (panel.series ?? []).map((s) => s.role)
  const valueFormat = panel.value!.format
  const slices = categories.flatMap((category, i) => (values[i] === null || values[i] === undefined ? [] : [{ category, value: values[i] as number }]))
  return {
    aria: { enabled: true, label: { description: `${panel.title}, one slice per product` } },
    textStyle: textStyle(read),
    tooltip: {
      ...tooltip(read, 'item'),
      formatter: (info: { name: string; value: number }) => line(`${info.name}:`, format(info.value, valueFormat)),
    },
    series: [
      {
        type: 'pie',
        name: panel.title,
        radius: '58%',
        center: ['50%', '52%'],
        label: { ...textStyle(read), formatter: '{b}' },
        labelLine: { lineStyle: { color: read('--border-strong') } },
        itemStyle: outline(read),
        emphasis: { scale: false },
        data: slices.map((slice, n) => ({
          name: slice.category.name,
          value: slice.value,
          step: slice.category.step,
          itemStyle: { color: role(read, roles[n % roles.length]) },
        })),
      },
    ],
  }
}

export function chartOption(panel: Panel, data: PanelData, paint: Paint): object {
  if (panel.mark === 'treemap') return treemapOption(panel, data, paint)
  if (panel.mark === 'line') return lineOption(panel, data, paint)
  if (panel.mark === 'pie') return pieOption(panel, data, paint)
  return barOption(panel, data, paint)
}
