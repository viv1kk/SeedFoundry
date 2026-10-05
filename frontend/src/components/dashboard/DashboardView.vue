<script setup lang="ts">
// One dashboard at one drill level, embeddable (the review route's frame, and the rebuild modal's
// Feedback + Dashboard view). It asks the server for the descriptor and payload whenever the drill
// path, page or sort changes (D-56) and renders the drill bar over the bands. It never changes the URL itself:
// a drill, a crumb or Back is emitted as the path to show, so the host decides where the path
// lives. An answer to an older request is dropped, so a fast click never shows a stale level.
// A descriptor that names a scoped stylesheet (iteration 1's defect overlay, D-60) has it loaded
// before its answer renders, and its root class goes on this element, so the overlay's styles
// reach this dashboard and nothing around it (R-1). `highlight` names panels to outline (a finding
// opened from the report, D-65); the first is scrolled into view once drawn.
import { computed, nextTick, ref, shallowRef, watch } from 'vue'
import { ApiError, messageOf } from '../../api'
import { dashboardApi } from '../../dashboard/api'
import { deeper, parent } from '../../dashboard/drill'
import { count, month } from '../../dashboard/format'
import { loadStylesheet } from '../../dashboard/stylesheets'
import type { DashboardResponse, SortDirection, Step } from '../../dashboard/types'
import BaseButton from '../base/BaseButton.vue'
import DashboardRenderer from './DashboardRenderer.vue'
import DrillBar from './DrillBar.vue'

const props = withDefaults(defineProps<{ dashboardId: string; iteration: number; drill: string; headingLevel?: 1 | 2 | 3; highlight?: string[] }>(), {
  headingLevel: 1,
  highlight: () => [],
})
const emit = defineEmits<{
  navigate: [path: string]
  back: [path: string]
  'invalid-drill': [message: string]
}>()

const response = shallowRef<DashboardResponse | null>(null)
const loading = ref(false)
const error = ref('')
const page = ref(1)
const sort = ref<{ column: string; direction: SortDirection } | null>(null)
let latest = 0

async function load(): Promise<void> {
  const mine = ++latest
  loading.value = true
  try {
    const answer = await dashboardApi.get(props.dashboardId, {
      iteration: props.iteration,
      drill: props.drill,
      page: page.value,
      sort: sort.value?.column,
      direction: sort.value?.direction,
    })
    if (mine !== latest) return
    if (answer.descriptor.styles) await loadStylesheet(answer.descriptor.styles.sheet)
    if (mine !== latest) return
    response.value = answer
    error.value = ''
  } catch (failure) {
    if (mine !== latest) return
    if (failure instanceof ApiError && failure.code === 'drill_not_found') emit('invalid-drill', failure.message)
    else error.value = messageOf(failure)
  } finally {
    if (mine === latest) loading.value = false
  }
}

watch(
  () => [props.dashboardId, props.iteration, props.drill] as const,
  () => {
    page.value = 1
    void load()
  },
  { immediate: true },
)

const shownPath = computed(() => response.value?.payload.drill.path ?? props.drill)

const root = ref<HTMLElement | null>(null)
watch(
  () => [props.highlight[0], response.value] as const,
  async ([first, answer]) => {
    if (!first || !answer) return
    await nextTick()
    root.value?.querySelector(`[data-panel="${first}"]`)?.scrollIntoView?.({ block: 'center' })
  },
)

function drillInto(step: Step): void {
  emit('navigate', deeper(shownPath.value, step))
}

function back(): void {
  const up = parent(shownPath.value)
  if (up !== null) emit('back', up)
}

function toPage(next: number): void {
  page.value = next
  void load()
}

function sortBy(column: string, direction: SortDirection): void {
  sort.value = { column, direction }
  page.value = 1
  void load()
}

const source = computed(() => {
  const dataset = response.value?.payload.dataset
  if (!dataset) return ''
  return `${dataset.title}, ${count(dataset.seats)} seats; monthly usage ${month(dataset.period.from)} to ${month(dataset.period.to)}, snapshot ${dataset.snapshot_date}`
})
</script>

<template>
  <div
    ref="root"
    class="dashboard"
    :class="response?.descriptor.styles?.root_class"
    :aria-busy="loading ? 'true' : 'false'"
    :data-variant="response?.variant"
    data-test="dashboard"
  >
    <header class="dashboard__head">
      <component :is="`h${headingLevel}`" class="dashboard__title">{{ response?.descriptor.title ?? 'License Optimization' }}</component>
      <p v-if="source" class="dashboard__source" data-test="dashboard-source">{{ source }}</p>
    </header>
    <p v-if="!response && !error" class="dashboard__note" data-test="dashboard-loading">Loading the dashboard</p>
    <p v-if="error" class="dashboard__error" role="alert" data-test="dashboard-error">
      {{ error }}
      <BaseButton @click="load">Try again</BaseButton>
    </p>
    <template v-if="response">
      <DrillBar :crumbs="response.payload.drill.crumbs" @back="back" @go="emit('navigate', $event)" />
      <DashboardRenderer
        :descriptor="response.descriptor"
        :payload="response.payload"
        :busy="loading"
        :highlight="highlight"
        @drill="drillInto"
        @page="toPage"
        @sort="sortBy"
      />
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  display: grid;
  gap: var(--space-4);
}

.dashboard__head {
  display: grid;
  gap: var(--space-1);
}

.dashboard__title {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.2;
}

.dashboard__source,
.dashboard__note {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.dashboard__error {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  /* A status in words: tested text colour, marked with the status fill (D-98) */
  color: var(--status-negative-text);
  border-left: 3px solid var(--status-negative);
  padding-left: var(--space-2);
}
</style>
