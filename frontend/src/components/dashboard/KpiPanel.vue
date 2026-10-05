<script setup lang="ts">
// A KPI tile: a small-capitals label over the figure, in tabular figures. The primary KPI is the
// number the room must read first: one per dashboard, in gold and larger (ValueWise sections 1
// and 6, D-99). No coloured rule: colour is never decoration.
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


.kpi__label {
  color: var(--text-secondary);
}

.kpi__figure {
  font-family: var(--font-sans);
  font-size: var(--text-xl);
  font-weight: 600;
  line-height: 1.2;
}

.kpi--primary .kpi__figure {
  color: var(--gold);
  font-size: var(--text-figure);
  font-weight: 700;
  line-height: 1.1;
}

.kpi__note {
  font-size: var(--text-sm);
}
</style>
