<script setup lang="ts">
// "Iteration 1", shown once a build exists (ui-spec.md section 1). No total: iterations go on while
// the observer rejects them (D-80). From iteration 2 on, the Human tag sits beside it (D-90).
import { useLabStore } from '../../stores/lab'
import BaseChip from '../base/BaseChip.vue'
import HumanTag from '../base/HumanTag.vue'

const lab = useLabStore()
</script>

<template>
  <span v-if="lab.currentIteration !== null" class="iteration">
    <BaseChip tone="accent" class="iteration-badge" data-test="iteration-badge">Iteration {{ lab.currentIteration }}</BaseChip>
    <HumanTag :iteration="lab.currentIteration" />
  </span>
</template>

<style scoped>
.iteration {
  display: inline-flex;
  align-items: center;
}

.iteration-badge {
  font-family: var(--font-mono);
}
</style>
