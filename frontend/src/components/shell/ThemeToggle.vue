<script setup lang="ts">
// Switches light and dark and remembers the choice (seed-reuse-notes.md section 1.2).
import { computed } from 'vue'
import { theme, toggleTheme } from '../../theme'
import BaseTooltip from '../base/BaseTooltip.vue'

const label = computed(() => (theme.value === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'))
</script>

<template>
  <BaseTooltip :text="label" align="end">
    <button type="button" class="theme-toggle" :aria-label="label" data-test="theme-toggle" @click="toggleTheme">
      <!-- A sun in dark (go light), a moon in light (go dark) -->
      <svg v-if="theme === 'dark'" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
        <circle cx="8" cy="8" r="3" fill="none" stroke="currentColor" stroke-width="1.5" />
        <path
          d="M8 1.5v1.5M8 13v1.5M1.5 8H3M13 8h1.5M3.4 3.4l1.1 1.1M11.5 11.5l1.1 1.1M3.4 12.6l1.1-1.1M11.5 4.5l1.1-1.1"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
        />
      </svg>
      <svg v-else viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
        <path
          d="M13.5 9.5A5.5 5.5 0 0 1 6.5 2.5a5.5 5.5 0 1 0 7 7z"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linejoin="round"
        />
      </svg>
    </button>
  </BaseTooltip>
</template>

<style scoped>
.theme-toggle {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-sm);
  background: var(--surface-raised);
  color: var(--text-secondary);
  cursor: pointer;
}

.theme-toggle:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}
</style>
