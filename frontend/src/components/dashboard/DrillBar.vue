<script setup lang="ts">
// The drill bar (FR-D-6, seed-reuse-notes.md section 5.3): Back pops one step, and the breadcrumb
// shows the path, All products first. A crumb is one step, so a treemap leaf's crumb names its
// three levels. Earlier crumbs are buttons that go back to that step; the last is where you are.
import type { Crumb } from '../../dashboard/types'
import BaseButton from '../base/BaseButton.vue'

defineProps<{ crumbs: Crumb[] }>()
const emit = defineEmits<{ back: []; go: [path: string] }>()
</script>

<template>
  <div class="drill-bar" data-test="drill-bar">
    <BaseButton :disabled="crumbs.length <= 1" explain-disabled aria-label="Back one drill step" data-test="drill-back" @click="emit('back')">
      Back
    </BaseButton>
    <nav class="drill-bar__crumbs" aria-label="Drill path">
      <ol>
        <li v-for="(crumb, i) in crumbs" :key="crumb.path" data-test="crumb">
          <span v-if="i > 0" class="drill-bar__sep" aria-hidden="true">&#8250;</span>
          <span v-if="i === crumbs.length - 1" class="drill-bar__here" aria-current="location">{{ crumb.label }}</span>
          <button v-else type="button" class="drill-bar__crumb" @click="emit('go', crumb.path)">{{ crumb.label }}</button>
        </li>
      </ol>
    </nav>
  </div>
</template>

<style scoped>
.drill-bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 44px;
  padding: var(--space-1) var(--space-3);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.drill-bar__crumbs ol {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-1) var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--text-sm);
}

.drill-bar__crumbs li {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.drill-bar__sep {
  color: var(--text-muted);
}

.drill-bar__crumb {
  padding: 0;
  border: 0;
  background: none;
  color: var(--accent);
  font: inherit;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.drill-bar__here {
  color: var(--text-primary);
  font-weight: 600;
}
</style>
