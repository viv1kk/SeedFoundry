<script setup lang="ts">
// Placeholder body for a screen whose content arrives in a later milestone.
defineProps<{ title: string; note: string }>()
</script>

<template>
  <section class="placeholder" data-test="placeholder">
    <h1>{{ title }}</h1>
    <p>{{ note }}</p>
  </section>
</template>

<style scoped>
.placeholder {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-12) var(--space-8);
}

h1 {
  font-size: var(--text-2xl);
  font-weight: 600;
  line-height: 1.2;
}

p {
  color: var(--text-secondary);
}
</style>
