<script setup lang="ts">
// "Iteration 1 of 2", shown once a build exists (ui-spec.md section 1).
import { ITERATIONS, useLabStore } from '../../stores/lab'
import BaseChip from '../base/BaseChip.vue'

const lab = useLabStore()
</script>

<template>
  <BaseChip v-if="lab.currentIteration !== null" tone="accent" class="iteration-badge" data-test="iteration-badge">
    Iteration {{ lab.currentIteration }} of {{ ITERATIONS }}
  </BaseChip>
</template>

<style scoped>
.iteration-badge {
  font-family: var(--font-mono);
}
</style>
