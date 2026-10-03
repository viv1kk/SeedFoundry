<script setup lang="ts">
// The thin SeedFoundry frame around the dashboard (FR-D-5, ui-spec.md section 5): Back to report,
// the iteration badge, and the dashboard. The drill path lives in the URL (FR-D-6, D-29), so a
// reload keeps it and the browser's Back pops one step: each drill is one history entry. The
// drill bar's Back goes back in history when the entry before is the parent level, and otherwise
// (after a reload, or a crumb) opens the parent as a new entry. Iteration 1's dashboard carries the
// defect overlay (D-60); the frame around it is SeedFoundry's own and stays outside it.
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DASHBOARD_ID } from '../../dashboard/api'
import { drillOf } from '../../dashboard/drill'
import { ITERATIONS } from '../../stores/lab'
import BaseChip from '../base/BaseChip.vue'
import DashboardView from './DashboardView.vue'

const props = defineProps<{ iteration: number }>()
const route = useRoute()
const router = useRouter()

const drill = computed(() => drillOf(route.query.drill))
const notice = ref('')

function location(path: string) {
  return { name: 'review', params: { iteration: String(props.iteration) }, query: { dashboard: DASHBOARD_ID, ...(path ? { drill: path } : {}) } }
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
  void router.replace(location(''))
}
</script>

<template>
  <section class="frame" data-test="dashboard-frame">
    <div class="frame__bar">
      <RouterLink :to="`/review/${iteration}`" class="frame__back" data-test="back-to-report">Back to report</RouterLink>
      <BaseChip tone="accent" class="frame__badge" data-test="frame-iteration">Iteration {{ iteration }} of {{ ITERATIONS }}</BaseChip>
    </div>
    <p v-if="notice" class="frame__note" role="status" data-test="drill-notice">{{ notice }}</p>
    <DashboardView :dashboard-id="DASHBOARD_ID" :iteration="iteration" :drill="drill" @navigate="navigate" @back="back" @invalid-drill="invalidDrill" />
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

.frame__back {
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
</style>
