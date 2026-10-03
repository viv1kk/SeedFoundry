<script setup lang="ts">
// A chart card (treemap, bar, line or pie), drawn by ECharts from the panel's descriptor and data.
// Colours are read from the tokens when it paints, so a theme change repaints it with the other
// theme's values (seed-reuse-notes.md section 1.2); it paints again once the bundled fonts have
// loaded, because ECharts draws text to the canvas once (section 1.4). Clicking a cell or a bar
// drills. Keyboard path (NFR-6): the chart takes focus; the arrow keys, Home and End choose a
// drill target, the choice is read out under the chart, and Enter or Space drills into it.
// A panel that declares a latency (iteration 1's treemap, L-1, D-60) shows a spinner and waits
// that long before it draws, on first draw and at each new drill level (`level`), while every
// other panel draws at once; paging, sorting, a theme switch or the fonts arriving do not wait.
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { initChart, type Chart } from '../../dashboard/echarts'
import { format } from '../../dashboard/format'
import { wait } from '../../dashboard/latency'
import { chartOption } from '../../dashboard/options'
import { readTokens } from '../../dashboard/tokens'
import type { ClassInfo, Panel, PanelData, Step } from '../../dashboard/types'
import { theme } from '../../theme'

const props = defineProps<{ panel: Panel; data: PanelData; classes: ClassInfo[]; level?: string }>()
const emit = defineEmits<{ drill: [step: Step] }>()

const host = ref<HTMLElement | null>(null)
const chart = shallowRef<Chart | null>(null)
const chosen = ref(-1)
const focused = ref(false)
const waiting = ref(false)
let waits = 0

const targets = computed(() => (waiting.value ? [] : (props.data.targets ?? [])))
const readoutId = computed(() => `${props.panel.id}-readout`)
const legend = computed(() => {
  if (!props.panel.legend) return []
  const roles = new Map(props.classes.map((c) => [c.id, c.role]))
  return (props.data.legend ?? []).map((item) => {
    const role = roles.get(item.class) ?? 'muted'
    // The swatch shows the class as the chart draws it (a descriptor's own colour, V-3, D-60).
    return { ...item, swatch: props.panel.class_colours?.[item.class]?.colour ?? `var(--chart-${role})` }
  })
})

const readout = computed(() => {
  if (waiting.value) return `Loading ${props.panel.title}.`
  const target = targets.value[chosen.value]
  if (!target) {
    return targets.value.length
      ? `${targets.value.length} to drill into. Use the arrow keys to choose one.`
      : 'Nothing to drill into at this level.'
  }
  const measure = props.panel.value?.format ?? props.panel.format ?? 'count'
  const value = target.value === null ? 'withheld' : format(target.value, measure)
  return `${target.label}: ${value}. Press Enter to drill in.`
})

function paint(): void {
  if (!chart.value || waiting.value) return
  chart.value.setOption(chartOption(props.panel, props.data, { read: readTokens(), classes: props.classes }), { notMerge: true })
}

/** New data at a new level: draw it, after the panel's declared latency if it has one. */
async function arrive(): Promise<void> {
  const ms = props.panel.latency_ms ?? 0
  const mine = ++waits
  if (ms > 0) {
    waiting.value = true
    await wait(ms)
    if (mine !== waits) return
    waiting.value = false
  }
  paint()
}

function highlight(): void {
  if (!chart.value || props.panel.mark !== 'bar') return
  if (chosen.value >= 0) chart.value.dispatchAction({ type: 'showTip', seriesIndex: 0, dataIndex: chosen.value })
  else chart.value.dispatchAction({ type: 'hideTip' })
}

function choose(index: number): void {
  if (!targets.value.length) return
  chosen.value = (index + targets.value.length) % targets.value.length
  highlight()
}

function onKey(event: KeyboardEvent): void {
  const moves: Record<string, () => number> = {
    ArrowRight: () => chosen.value + 1,
    ArrowDown: () => chosen.value + 1,
    ArrowLeft: () => (chosen.value < 0 ? -1 : chosen.value - 1),
    ArrowUp: () => (chosen.value < 0 ? -1 : chosen.value - 1),
    Home: () => 0,
    End: () => targets.value.length - 1,
  }
  if (moves[event.key]) {
    event.preventDefault()
    choose(moves[event.key]())
  } else if ((event.key === 'Enter' || event.key === ' ') && targets.value[chosen.value]) {
    event.preventDefault()
    emit('drill', targets.value[chosen.value].step)
  }
}

function onBlur(): void {
  focused.value = false
  if (chart.value && props.panel.mark === 'bar') chart.value.dispatchAction({ type: 'hideTip' })
}

let resizer: ResizeObserver | null = null
let fontsLoaded: (() => void) | null = null

onMounted(() => {
  if (!host.value) return
  chart.value = initChart(host.value)
  chart.value.on('click', (params) => {
    const step = (params.data as { step?: Step | null } | undefined)?.step
    if (step?.length) emit('drill', step)
  })
  void arrive()
  if (typeof ResizeObserver !== 'undefined') {
    resizer = new ResizeObserver(() => chart.value?.resize())
    resizer.observe(host.value)
  }
  const fonts = document.fonts
  if (fonts) {
    fontsLoaded = () => paint()
    void fonts.ready.then(() => fontsLoaded?.())
    fonts.addEventListener?.('loadingdone', fontsLoaded)
  }
})

onBeforeUnmount(() => {
  waits++
  resizer?.disconnect()
  if (fontsLoaded) document.fonts?.removeEventListener?.('loadingdone', fontsLoaded)
  fontsLoaded = null
  chart.value?.dispose()
  chart.value = null
})

watch(
  () => [props.data, props.level] as const,
  ([, level], [, before]) => {
    chosen.value = -1
    if (level !== before) void arrive()
    else paint()
  },
)
watch(theme, () => paint())
</script>

<template>
  <article class="chart-panel" :class="`chart-panel--${panel.mark}`" :data-panel="panel.id" data-test="chart-panel">
    <header class="chart-panel__head">
      <h3 class="chart-panel__title">{{ panel.title }}</h3>
      <p v-if="panel.subtitle" class="chart-panel__subtitle">{{ panel.subtitle }}</p>
    </header>
    <div
      class="chart-panel__frame"
      tabindex="0"
      role="group"
      aria-roledescription="chart"
      :aria-label="`${panel.title}. ${targets.length ? 'Arrow keys choose, Enter drills in.' : 'Nothing to drill into at this level.'}`"
      :aria-describedby="readoutId"
      data-test="chart-frame"
      @keydown="onKey"
      @focus="focused = true"
      @blur="onBlur"
    >
      <div
        ref="host"
        class="chart-panel__canvas"
        :class="{ 'chart-panel__canvas--waiting': waiting }"
        :style="{ height: `${panel.height ?? 320}px` }"
        data-test="chart-canvas"
      ></div>
      <div v-if="waiting" class="chart-panel__waiting" role="status" data-test="chart-waiting">
        <span class="chart-panel__spinner" aria-hidden="true"></span>
        Loading {{ panel.title }}
      </div>
    </div>
    <p :id="readoutId" class="chart-panel__readout" :class="{ 'chart-panel__readout--shown': focused }" aria-live="polite" data-test="chart-readout">
      {{ focused ? readout : '' }}
    </p>
    <ul v-if="legend.length && !waiting" class="chart-panel__legend" :aria-label="`Share of ${panel.legend?.of}`" data-test="treemap-legend">
      <li v-for="item in legend" :key="item.class" class="chart-panel__legend-item" data-test="legend-item">
        <span class="chart-panel__swatch" :style="{ background: item.swatch }" aria-hidden="true"></span>
        <span class="chart-panel__legend-label">{{ item.label }}</span>
        <span class="chart-panel__legend-figure">{{ format(item.share, panel.legend!.format) }}</span>
        <span class="chart-panel__legend-count">{{ format(item.count, 'count') }}</span>
      </li>
    </ul>
  </article>
</template>

<style scoped>
.chart-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
  padding: var(--space-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.chart-panel__title {
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: 1.3;
}

.chart-panel__subtitle {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.chart-panel__frame {
  position: relative;
  border-radius: var(--radius-sm);
}

.chart-panel__canvas {
  width: 100%;
}

.chart-panel__canvas--waiting {
  visibility: hidden;
}

.chart-panel__waiting {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.chart-panel__spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-default);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: chart-panel-spin 0.9s linear infinite;
}

@keyframes chart-panel-spin {
  to {
    transform: rotate(360deg);
  }
}

.chart-panel__readout {
  min-height: 1.5em;
  color: var(--text-secondary);
  font-size: var(--text-sm);
  visibility: hidden;
}

.chart-panel__readout--shown {
  visibility: visible;
}

.chart-panel__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-6);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--text-sm);
}

.chart-panel__legend-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.chart-panel__swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.chart-panel__legend-label {
  color: var(--text-secondary);
}

.chart-panel__legend-figure {
  font-family: var(--font-mono);
  font-weight: 600;
}

.chart-panel__legend-count {
  color: var(--text-muted);
  font-family: var(--font-mono);
}
</style>
