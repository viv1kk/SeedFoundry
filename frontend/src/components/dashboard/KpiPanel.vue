<script setup lang="ts">
// A KPI tile: a small-capitals label over the figure, in the figures' face (seed-reuse-notes.md
// section 1.4). The primary KPI carries a top rule in its chart role, Seed v0.1's convention.
// A note's placeholders ("{withheld_seats}") are filled from the panel's data, formatted as counts.
import { computed } from 'vue'
import { count, format } from '../../dashboard/format'
import type { Panel, PanelData } from '../../dashboard/types'

const props = defineProps<{ panel: Panel; data: PanelData }>()

const figure = computed(() => format(props.data.value ?? 0, props.panel.format ?? 'count'))
const note = computed(() =>
  props.panel.note?.text.replace(/\{(\w+)\}/g, (_, key: string) => count(Number((props.data as Record<string, unknown>)[key] ?? 0))),
)
</script>

<template>
  <article
    class="kpi"
    :class="{ 'kpi--primary': panel.emphasis === 'primary' }"
    :style="panel.rule_role ? { '--kpi-rule': `var(--chart-${panel.rule_role})` } : undefined"
    :data-panel="panel.id"
    data-test="kpi"
  >
    <h3 class="kpi__label caps-label">{{ panel.title }}</h3>
    <p class="kpi__figure" data-test="kpi-figure">{{ figure }}</p>
    <p v-if="note" class="kpi__note" :style="{ color: `var(--${panel.note!.role})` }" data-test="kpi-note">{{ note }}</p>
  </article>
</template>

<style scoped>
.kpi {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
  padding: var(--space-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.kpi--primary {
  border-top: 3px solid var(--kpi-rule);
  padding-top: calc(var(--space-4) - 2px);
}

.kpi__label {
  color: var(--text-secondary);
}

.kpi__figure {
  font-family: var(--font-mono);
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.2;
}

.kpi__note {
  font-size: var(--text-sm);
}
</style>
