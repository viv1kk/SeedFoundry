<script setup lang="ts">
// The thin SeedFactory frame around the dashboard (FR-D-5, ui-spec.md section 5): Back to report,
// the iteration badge, iteration 1's "N findings" link back to the report, and the dashboard. The
// drill path lives in the URL (FR-D-6, D-29), so a reload keeps it and the browser's Back pops one
// step: each drill is one history entry. The drill bar's Back goes back in history when the entry
// before is the parent level, and otherwise (after a reload, or a crumb) opens the parent as a new
// entry. Iteration 1's dashboard carries the defect overlay (D-60); the frame around it is
// SeedFactory's own and stays outside it.
//
// A finding opened from the report is in the URL too (`finding=<id>`, D-65): every panel it names
// is outlined, the frame says which, and focus moves to that line. A reload keeps it; a drill, a
// crumb or Back drops it, as the finding was measured at All products.
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DASHBOARD_ID } from '../../dashboard/api'
import { drillOf } from '../../dashboard/drill'
import { dashboardFindings } from '../../report'
import type { Build } from '../../stores/lab'
import { useReportsStore } from '../../stores/reports'
import BaseChip from '../base/BaseChip.vue'
import HumanTag from '../base/HumanTag.vue'
import DashboardView from './DashboardView.vue'

const props = defineProps<{ iteration: number; build: Build }>()
const route = useRoute()
const router = useRouter()
const reports = useReportsStore()

watch(
  () => props.build.id,
  (id) => void reports.load(id),
  { immediate: true },
)

const drill = computed(() => drillOf(route.query.drill))
const notice = ref('')

const report = computed(() => reports.reports.get(props.build.id) ?? null)
const findingCount = computed(() => (report.value ? dashboardFindings(report.value).length : 0))
const findingId = computed(() => (typeof route.query.finding === 'string' ? route.query.finding : ''))
const finding = computed(() => (report.value && findingId.value ? (dashboardFindings(report.value).find((f) => f.id === findingId.value) ?? null) : null))
const highlight = computed(() => finding.value?.panels ?? [])

function joined(names: string[]): string {
  return names.length < 2 ? (names[0] ?? '') : `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`
}

const findingNote = ref<HTMLElement | null>(null)
watch(
  () => [finding.value?.id, findingNote.value] as const,
  async ([id, note]) => {
    if (!id || !note) return
    await nextTick()
    note.focus({ preventScroll: true })  // the dashboard scrolls to the panel itself
  },
)

function location(path: string, keep: Record<string, string> = {}) {
  return { name: 'review', params: { iteration: String(props.iteration) }, query: { dashboard: DASHBOARD_ID, ...(path ? { drill: path } : {}), ...keep } }
}

function navigate(path: string): void {
  notice.value = ''
  void router.push(location(path))
}

function back(path: string): void {
  notice.value = ''
  const target = router.resolve(location(path)).fullPath
  if (router.options.history.state?.back === target) router.back()
  else void router.push(target)
}

function invalidDrill(): void {
  notice.value = 'The drill path in the address is not in the data, so the dashboard opened at All products.'
  void router.replace(location('', findingId.value ? { finding: findingId.value } : {}))
}

function clearHighlight(): void {
  const path = typeof route.query.drill === 'string' ? route.query.drill : ''
  void router.replace(location(path))
}
</script>

<template>
  <section class="frame" data-test="dashboard-frame">
    <div class="frame__bar">
      <RouterLink :to="`/review/${iteration}`" class="frame__back" data-test="back-to-report">Back to report</RouterLink>
      <div class="frame__side">
        <RouterLink v-if="iteration === 1 && findingCount" :to="`/review/${iteration}`" class="frame__findings" data-test="findings-link">
          {{ findingCount }} {{ findingCount === 1 ? 'finding' : 'findings' }}
        </RouterLink>
        <BaseChip tone="accent" class="frame__badge" data-test="frame-iteration">Iteration {{ iteration }}</BaseChip>
        <HumanTag :iteration="iteration" />
      </div>
    </div>
    <p v-if="notice" class="frame__note" role="status" data-test="drill-notice">{{ notice }}</p>
    <div v-if="finding" ref="findingNote" class="frame__finding" tabindex="-1" role="status" data-test="finding-note">
      <p>
        Showing <span class="frame__id">{{ finding.id }}</span> on {{ joined(finding.panel_titles ?? []) }}.
        <span class="frame__message">{{ finding.message }}</span>
      </p>
      <button type="button" class="frame__clear" data-test="clear-highlight" @click="clearHighlight">Clear highlight</button>
    </div>
    <p v-else-if="findingId && report" class="frame__note" role="status" data-test="finding-note">
      No finding {{ findingId }} in this build's report, so nothing is highlighted.
    </p>
    <DashboardView
      :dashboard-id="DASHBOARD_ID"
      :iteration="iteration"
      :drill="drill"
      :highlight="highlight"
      @navigate="navigate"
      @back="back"
      @invalid-drill="invalidDrill"
    />
  </section>
</template>

<style scoped>
.frame {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6) var(--space-8);
}

.frame__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border-subtle);
}

.frame__side {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.frame__back,
.frame__findings {
  font-size: var(--text-sm);
  font-weight: 600;
}

.frame__badge {
  font-family: var(--font-mono);
}

.frame__note {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.frame__finding {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2) var(--space-4);
  padding: var(--space-2) var(--space-3);
  background: var(--accent-subtle);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.frame__id {
  font-family: var(--font-mono);
  font-weight: 600;
}

.frame__message {
  color: var(--text-secondary);
}

.frame__clear {
  padding: 0;
  border: 0;
  background: none;
  color: var(--accent);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
</style>
