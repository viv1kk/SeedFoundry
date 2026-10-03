<script setup lang="ts">
// Review (ui-spec.md sections 4 and 5). `/review/<n>` is the report; the dashboard opens over it
// at `/review/<n>?dashboard=license-optimization&drill=...` (OQ-4) and Back to report closes it.
// The report is M9's: until then the route shows a short stand-in for the iteration's completed
// build, with View Dashboard and a way to the build's summary (OQ-22). The dashboard is the
// build's output, so it opens once the iteration has a completed build.
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../components/base/BaseButton.vue'
import DashboardFrame from '../components/dashboard/DashboardFrame.vue'
import { DASHBOARD_ID } from '../dashboard/api'
import { useLabStore } from '../stores/lab'

const props = defineProps<{ iteration: string }>()
const lab = useLabStore()
const route = useRoute()
const router = useRouter()

const iteration = computed(() => Number(props.iteration))
const build = computed(() => {
  const builds = lab.snapshot?.builds.filter((b) => b.iteration === iteration.value) ?? []
  return builds[builds.length - 1] ?? null
})
const completed = computed(() => build.value?.status === 'completed')
const dashboardOpen = computed(() => route.query.dashboard === DASHBOARD_ID && completed.value)

function viewDashboard(): void {
  void router.push({ name: 'review', params: { iteration: props.iteration }, query: { dashboard: DASHBOARD_ID } })
}
</script>

<template>
  <div class="review" data-test="review">
    <DashboardFrame v-if="dashboardOpen" :iteration="iteration" />
    <section v-else class="review__report" data-test="review-report">
      <h1>Review, iteration {{ iteration }}</h1>
      <p v-if="!lab.snapshot" class="review__note">Loading the review</p>
      <template v-else-if="!build">
        <p class="review__note" data-test="review-state">No build for iteration {{ iteration }} yet, so there is nothing to review.</p>
        <RouterLink v-if="iteration === 2" to="/build/1" class="review__link">Go to iteration 1</RouterLink>
        <RouterLink v-else to="/knowledge" class="review__link">Go to Knowledge</RouterLink>
      </template>
      <template v-else-if="build.status === 'running'">
        <p class="review__note" data-test="review-state">Iteration {{ iteration }} is still building. Its report and dashboard open here when it completes.</p>
        <RouterLink :to="`/build/${iteration}`" class="review__link">Go to the build</RouterLink>
      </template>
      <template v-else-if="build.status === 'interrupted'">
        <p class="review__note" data-test="review-state">This build stopped before it finished, so it has no report or dashboard.</p>
        <RouterLink to="/knowledge" class="review__link">Go to Knowledge</RouterLink>
      </template>
      <template v-else>
        <p class="review__note" data-test="review-state">
          The build report, with its verdict, findings and tests, arrives in M9. Until then the build's summary is on its Build page.
        </p>
        <div class="review__actions">
          <BaseButton data-test="view-dashboard" @click="viewDashboard">View Dashboard</BaseButton>
          <RouterLink :to="`/build/${iteration}`" class="review__link">Go to the build summary</RouterLink>
        </div>
      </template>
    </section>
  </div>
</template>

<style scoped>
.review__report {
  display: grid;
  gap: var(--space-3);
  justify-items: start;
  padding: var(--space-12) var(--space-8);
}

h1 {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.2;
}

.review__note {
  max-width: 60ch;
  color: var(--text-secondary);
}

.review__actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.review__link {
  font-size: var(--text-sm);
  font-weight: 600;
}
</style>
