<script setup lang="ts">
// Build (ui-spec.md section 3, FR-B-3 to FR-B-9, D-54). `/build/<n>` shows that iteration's latest
// build: the header and stepper left, the console right. Everything on
// the page comes from the build record in the snapshot and the build's events
// (stores/buildLog.ts), and every time from sim_t, so it reads the same at any speed and after
// a refresh (FR-B-7). On completion the build report (FR-B-9, D-65) sits above the collapsed
// stepper, with its actions, and the console can be hidden. The page stays on `/build/<n>` (OQ-21).
// From iteration 2 on, a panel above the stepper shows the observer feedback going into the four
// Knowledge files as the routing and Update sub-steps play (D-83).
import { computed, ref, watch } from 'vue'
import BaseChip from '../components/base/BaseChip.vue'
import BuildConsole from '../components/build/BuildConsole.vue'
import FeedbackRouting from '../components/build/FeedbackRouting.vue'
import PhaseStepper from '../components/build/PhaseStepper.vue'
import BuildReport from '../components/report/BuildReport.vue'
import type { LabEvent } from '../events'
import { clock, consoleLines, derivePhases, elapsed, feedbackRouting, progress } from '../stepper'
import { useBuildLogStore } from '../stores/buildLog'
import { useLabStore } from '../stores/lab'

const props = defineProps<{ iteration: string }>()
const lab = useLabStore()
const log = useBuildLogStore()

const iteration = computed(() => Number(props.iteration))

const build = computed(() => {
  const builds = lab.snapshot?.builds.filter((b) => b.iteration === iteration.value) ?? []
  return builds[builds.length - 1] ?? null
})

watch(
  () => build.value?.id ?? null,
  (id) => log.follow(id),
  { immediate: true },
)

const ready = computed(() => build.value !== null && log.loaded && log.buildId === build.value.id)
const phases = computed(() => (build.value ? derivePhases(build.value, log.events) : []))
const lines = computed(() => consoleLines(log.events))
const routing = computed(() => (build.value ? feedbackRouting(build.value, log.events) : null))
const seconds = computed(() => elapsed(log.events))
const percent = computed(() => (build.value ? Math.floor(progress(build.value, phases.value, seconds.value) * 100) : 0))

const lastOf = (type: LabEvent['type']) => [...log.events].reverse().find((event) => event.type === type) ?? null
const completedEvent = computed(() => lastOf('build.completed'))
const interruptedEvent = computed(() => lastOf('build.interrupted'))

const status = computed(() => {
  const current = build.value
  if (!current) return ''
  if (current.status === 'completed') return 'Completed'
  if (current.status === 'interrupted') return 'Stopped'
  const active = phases.value.find((phase) => phase.state === 'active')
  return active ? `Phase ${active.index} of ${phases.value.length}: ${active.name}` : 'Starting'
})

const consoleHidden = ref(false)
watch(
  () => build.value?.id,
  () => {
    consoleHidden.value = false
  },
)

const previousBuild = computed(() => lab.snapshot?.builds.find((b) => b.iteration === iteration.value - 1) ?? null)
</script>

<template>
  <div class="build" data-test="build">
    <p v-if="!lab.snapshot" class="build__note">Loading the build</p>

    <section v-else-if="!build" class="build__empty" data-test="no-build">
      <h1>Build, iteration {{ iteration }}</h1>
      <template v-if="iteration === 1">
        <p>No build for iteration 1 yet. Start Build is on the Knowledge page once the four core files are in.</p>
        <RouterLink to="/knowledge" class="build__link">Go to Knowledge</RouterLink>
      </template>
      <template v-else>
        <p>No build for iteration {{ iteration }} yet. Iteration {{ iteration }} starts when you reject iteration {{ iteration - 1 }} from its report.</p>
        <RouterLink v-if="previousBuild" :to="`/build/${iteration - 1}`" class="build__link">Go to iteration {{ iteration - 1 }}</RouterLink>
        <RouterLink v-else to="/knowledge" class="build__link">Go to Knowledge</RouterLink>
      </template>
    </section>

    <template v-else>
      <div v-if="build.status === 'interrupted'" class="banner" role="status" data-test="interrupted-banner">
        <span>
          This build stopped before it finished.
          <template v-if="interruptedEvent">{{ interruptedEvent.message }}</template>
          <template v-else>Start it again from Knowledge.</template>
        </span>
        <RouterLink to="/knowledge" class="build__link">Go to Knowledge</RouterLink>
      </div>
      <div class="build__layout" :class="{ 'build__layout--wide': consoleHidden }">
        <div class="build__main">
          <header class="build__header" data-test="build-header">
            <div class="build__heading">
              <BaseChip tone="accent" class="build__iteration" data-test="build-iteration">Iteration {{ iteration }}</BaseChip>
              <h1 class="build__title">{{ build.seed_name || 'Untitled Seed' }}</h1>
              <span class="build__elapsed">
                <span class="caps-label">Elapsed</span>
                <span class="build__clock" data-test="build-elapsed">{{ clock(seconds) }}</span>
              </span>
            </div>
            <div class="build__progress">
              <div
                class="progress"
                role="progressbar"
                aria-label="Build progress"
                aria-valuemin="0"
                aria-valuemax="100"
                :aria-valuenow="percent"
                data-test="build-progress"
              >
                <div class="progress__bar" :class="`progress__bar--${build.status}`" :style="{ width: `${percent}%` }" />
              </div>
              <span class="build__percent">{{ percent }}%</span>
            </div>
            <p class="build__status" data-test="build-status">
              {{ status }}
              <button v-if="consoleHidden" type="button" class="build__show" data-test="console-show" @click="consoleHidden = false">Show console</button>
            </p>
          </header>
          <p v-if="!ready" class="build__note">Loading the build log</p>
          <template v-else>
            <BuildReport v-if="build.status === 'completed' && completedEvent" :build="build" />
            <FeedbackRouting v-if="routing" :routing="routing" />
            <PhaseStepper :phases="phases" />
          </template>
        </div>
        <BuildConsole v-if="!consoleHidden" class="build__console" :lines="ready ? lines : []" :collapsible="build.status === 'completed'" @collapse="consoleHidden = true" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.build {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--top-bar-height));
}

.build__note {
  padding: var(--space-12) var(--space-8);
  color: var(--text-secondary);
}

.build__empty {
  display: grid;
  justify-items: start;
  gap: var(--space-3);
  padding: var(--space-12) var(--space-8);
}

.build__empty h1 {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.2;
}

.build__empty p {
  color: var(--text-secondary);
}

.build__link {
  font-weight: 600;
}

.banner {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-2) var(--space-6);
  background: var(--surface-raised);
  border-bottom: 1px solid var(--status-warning);
  color: var(--text-primary);
  font-size: var(--text-sm);
}

.build__layout {
  display: grid;
  grid-template-columns: minmax(0, 55fr) minmax(320px, 45fr);
  flex: 1;
  min-height: 0;
}

.build__layout--wide {
  grid-template-columns: minmax(0, 1fr);
}

.build__main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-6) var(--space-8);
}

.build__console {
  min-width: 0;
}

.build__header {
  display: grid;
  gap: var(--space-2);
}

.build__heading {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.build__iteration {
  font-family: var(--font-mono);
}

.build__title {
  flex: 1;
  min-width: 0;
  font-size: var(--text-lg);
  font-weight: 600;
}

.build__elapsed {
  display: inline-flex;
  align-items: baseline;
  gap: var(--space-2);
  color: var(--text-secondary);
}

.build__clock {
  font-family: var(--font-mono);
  font-size: var(--text-lg);
  color: var(--text-primary);
}

.build__progress {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.progress {
  flex: 1;
  height: 6px;
  overflow: hidden;
  background: var(--surface-sunken);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
}

.progress__bar {
  height: 100%;
  background: var(--accent);
}

.progress__bar--completed {
  background: var(--status-positive);
}

.progress__bar--interrupted {
  background: var(--status-warning);
}

.build__percent {
  min-width: 4ch;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  text-align: right;
}

.build__status {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.build__show {
  margin-left: auto;
  padding: 0;
  border: 0;
  background: none;
  color: var(--accent);
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}
</style>
