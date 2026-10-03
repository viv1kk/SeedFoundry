<script setup lang="ts">
// A bordered panel on the raised surface. Borders separate surfaces; no shadow by default.
defineProps<{ title?: string }>()
</script>

<template>
  <section class="card">
    <header v-if="title || $slots.header" class="card__header">
      <slot name="header">
        <h2 class="card__title">{{ title }}</h2>
      </slot>
    </header>
    <div class="card__body"><slot /></div>
  </section>
</template>

<style scoped>
.card {
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.card__header {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}

.card__title {
  font-size: var(--text-sm);
  font-weight: 600;
}

.card__body {
  padding: var(--space-4);
}
</style>
