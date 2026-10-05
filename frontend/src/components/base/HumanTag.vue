<script setup lang="ts">
// The "Human" tag (D-90): an iteration after the first exists only because a person rejected the
// one before it and wrote the feedback it was rebuilt from, so wherever such an iteration is named
// on screen, this tag sits beside it. Iteration 1 has none. Neutral, as a state of knowledge
// (seed-reuse-notes.md section 1.1), not a status.
import { isHuman } from '../../builds'
import BaseChip from './BaseChip.vue'

defineProps<{ iteration: number }>()
</script>

<template>
  <span v-if="isHuman(iteration)" class="human" title="Rebuilt from human feedback" data-test="human-tag"
    ><span class="visually-hidden">, </span><BaseChip>Human</BaseChip></span
  >
</template>

<style scoped>
.human {
  display: inline-flex;
  margin-left: var(--space-2);
  vertical-align: middle;
}
</style>
