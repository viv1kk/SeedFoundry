<script setup lang="ts">
// A small status label (ValueWise section 1, the mood board's status chips). A status that comes
// out of the data is a filled chip in the data scale, its label in the tested colour on that fill:
// positive green for done or within target, warning amber for caution, negative red only for a
// fault. Neutral and accent are not statuses: an outline in grey, or in the control colour
// (white in dark, navy in light) for the iteration.
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
  padding: 0 var(--space-2);
  border: 1px solid currentColor;
  border-radius: var(--radius-sm);
  background: transparent;
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.5;
  white-space: nowrap;
}

.chip--neutral {
  color: var(--text-secondary);
  border-color: var(--border-strong);
}

.chip--accent {
  color: var(--accent);
}

.chip--positive {
  border-color: var(--status-positive);
  background: var(--status-positive);
  color: var(--on-status-positive);
}

.chip--warning {
  border-color: var(--status-warning);
  background: var(--status-warning);
  color: var(--on-status-warning);
}

.chip--negative {
  border-color: var(--status-negative);
  background: var(--status-negative);
  color: var(--on-status-negative);
}
</style>
