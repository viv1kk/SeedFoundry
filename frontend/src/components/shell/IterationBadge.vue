<script setup lang="ts">
// "Iteration 1", shown once a build exists (ui-spec.md section 1). No total: iterations go on while
// the observer rejects them (D-80).
import { useLabStore } from '../../stores/lab'
import BaseChip from '../base/BaseChip.vue'

const lab = useLabStore()
</script>

<template>
  <BaseChip v-if="lab.currentIteration !== null" tone="accent" class="iteration-badge" data-test="iteration-badge">
    Iteration {{ lab.currentIteration }}
  </BaseChip>
</template>

<style scoped>
.iteration-badge {
  font-family: var(--font-mono);
}
</style>
