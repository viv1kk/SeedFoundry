<script setup lang="ts">
// A small status label. Colour carries meaning (seed-reuse-notes.md section 1.1):
// accent for work in progress, positive for done, warning for caution,
// negative only for a fault, neutral for a state of knowledge.
export type ChipTone = 'neutral' | 'accent' | 'positive' | 'warning' | 'negative'

withDefaults(defineProps<{ tone?: ChipTone }>(), { tone: 'neutral' })
</script>

<template>
  <span class="chip" :class="`chip--${tone}`"><slot /></span>
</template>

<style scoped>
.chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 1px var(--space-2);
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.6;
  white-space: nowrap;
}

.chip--neutral {
  color: var(--status-neutral);
}

.chip--accent {
  color: var(--accent);
  background: var(--accent-subtle);
}

.chip--positive {
  color: var(--status-positive);
}

.chip--warning {
  color: var(--status-warning);
}

.chip--negative {
  color: var(--status-negative);
}
</style>
