<script setup lang="ts">
// Build (ui-spec.md section 3). The stepper and console are M6's; until then the page says
// what the iteration's build is doing, from the live snapshot, which the lab store keeps
// current from build events without a re-fetch each time (M5).
import { computed } from 'vue'
import ScreenPlaceholder from '../components/ScreenPlaceholder.vue'
import { useLabStore } from '../stores/lab'

const props = defineProps<{ iteration: string }>()
const lab = useLabStore()

const LATER = 'The phase stepper and console arrive in M6.'

const build = computed(() => {
  const builds = lab.snapshot?.builds.filter((b) => b.iteration === Number(props.iteration)) ?? []
  return builds[builds.length - 1] ?? null
})

const note = computed(() => {
  const current = build.value
  if (!current) return lab.snapshot ? `No build for this iteration yet. ${LATER}` : LATER
  if (current.status === 'completed') return `Build completed. ${LATER} The report arrives in M9.`
  if (current.status === 'interrupted') return `This build stopped before it finished. Start it again from Knowledge. ${LATER}`
  const plan = current.plan ?? []
  const index = plan.findIndex((phase) => phase.id === current.phase)
  if (index < 0) return `Build running. ${LATER}`
  return `Build running: phase ${index + 1} of ${plan.length}, ${plan[index].name}. ${LATER}`
})
</script>

<template>
  <ScreenPlaceholder :title="`Build, iteration ${iteration}`" :note="note" />
</template>
