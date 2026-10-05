<script setup lang="ts">
// Three columns, as in Seed v0.1's top bar: the outer two share the leftover width equally,
// so the journey indicator stays centred whatever the widths of the left and right groups.
import IterationBadge from './IterationBadge.vue'
import JourneyIndicator from './JourneyIndicator.vue'
import ThemeToggle from './ThemeToggle.vue'
</script>

<template>
  <header class="top-bar">
    <div class="top-bar__start">
      <span class="wordmark" data-test="wordmark">SeedFactory</span>
    </div>
    <JourneyIndicator />
    <div class="top-bar__end">
      <IterationBadge />
      <ThemeToggle />
    </div>
  </header>
</template>

<style scoped>
.top-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: var(--space-4);
  height: var(--top-bar-height);
  padding: 0 var(--space-4);
  background: var(--surface-raised);
  border-bottom: 1px solid var(--border-default);
}

.top-bar__start {
  justify-self: start;
  min-width: 0;
}

.top-bar__end {
  display: flex;
  justify-self: end;
  align-items: center;
  gap: var(--space-3);
}

.wordmark {
  color: var(--text-primary);
  font-size: var(--text-md);
  font-weight: 700;
  letter-spacing: -0.01em;
  white-space: nowrap;
}
</style>
