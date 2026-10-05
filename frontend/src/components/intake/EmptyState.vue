<script setup lang="ts">
// No files yet (ui-spec.md section 2): one line on each initiation file, from the server's
// category descriptions, and the two ways to start. There is no other category (D-84).
import { useIntakeStore } from '../../stores/intake'
import BaseButton from '../base/BaseButton.vue'

defineProps<{ readOnly: boolean }>()
const emit = defineEmits<{ new: []; import: [] }>()

const intake = useIntakeStore()
</script>

<template>
  <section class="empty" aria-labelledby="empty-heading" data-test="empty-state">
    <h1 id="empty-heading" class="empty__title">Add your knowledge files</h1>
    <p class="empty__lead">A Seed is built from four initiation files, one of each:</p>
    <dl class="empty__list">
      <div v-for="c in intake.coreCategories" :key="c.id" class="empty__item">
        <dt>{{ c.label }}</dt>
        <dd>{{ c.description }}</dd>
      </div>
    </dl>
    <div class="empty__actions">
      <BaseButton variant="primary" :disabled="readOnly" data-test="empty-new" @click="emit('new')">New file</BaseButton>
      <BaseButton :disabled="readOnly" data-test="empty-import" @click="emit('import')">Import</BaseButton>
    </div>
  </section>
</template>

<style scoped>
.empty {
  display: grid;
  align-content: start;
  gap: var(--space-4);
  max-width: 640px;
  padding: var(--space-12) var(--space-8);
}

.empty__title {
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.2;
}

.empty__lead {
  color: var(--text-secondary);
}

.empty__list {
  display: grid;
  gap: var(--space-3);
  margin: 0;
}

.empty__item {
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-raised);
}

.empty__item dt {
  font-weight: 600;
}

.empty__item dd {
  margin: 0;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.empty__actions {
  display: flex;
  gap: var(--space-2);
}
</style>
