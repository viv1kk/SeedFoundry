<script setup lang="ts">
// Review (ui-spec.md sections 4 and 5). `/review/<n>` is the report; the dashboard opens over it
// at `/review/<n>?dashboard=license-optimization&drill=...` (OQ-4) and Back to report closes it.
// A completed build's report is the same component the Build page shows (D-65, OQ-22); a finding
// opens the dashboard with `&finding=<id>`. The dashboard is the build's output, so it opens once
// the iteration has a completed build.
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DashboardFrame from '../components/dashboard/DashboardFrame.vue'
import BuildReport from '../components/report/BuildReport.vue'
import { DASHBOARD_ID } from '../dashboard/api'
import { useLabStore } from '../stores/lab'

const props = defineProps<{ iteration: string }>()
const lab = useLabStore()
const route = useRoute()

const iteration = computed(() => Number(props.iteration))
const build = computed(() => {
  const builds = lab.snapshot?.builds.filter((b) => b.iteration === iteration.value) ?? []
  return builds[builds.length - 1] ?? null
})
const completed = computed(() => build.value?.status === 'completed')
const dashboardOpen = computed(() => route.query.dashboard === DASHBOARD_ID && completed.value)
</script>

<template>
  <div class="review" data-test="review">
    <DashboardFrame v-if="dashboardOpen && build" :iteration="iteration" :build="build" />
    <section v-else class="review__report" data-test="review-report">
      <h1>Review, iteration {{ iteration }}</h1>
      <p v-if="!lab.snapshot" class="review__note">Loading the review</p>
      <template v-else-if="!build">
        <p class="review__note" data-test="review-state">No build for iteration {{ iteration }} yet, so there is nothing to review.</p>
        <RouterLink v-if="iteration > 1" :to="`/build/${iteration - 1}`" class="review__link">Go to iteration {{ iteration - 1 }}</RouterLink>
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
        <RouterLink :to="`/build/${iteration}`" class="review__link" data-test="go-to-build">Go to the build</RouterLink>
        <BuildReport class="review__body" :build="build" />
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

.review__body {
  justify-self: stretch;
  max-width: 1200px;
}

.review__link {
  font-size: var(--text-sm);
  font-weight: 600;
}
</style>
