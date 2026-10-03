<script setup lang="ts">
// The generic renderer (seed-reuse-notes.md section 2.5): bands in the descriptor's order, each a
// twelve-column grid with one gutter, each panel drawn by its mark at its span. Nothing here is
// specific to License Optimization; the descriptor says what to draw and the payload what with.
// A highlighted panel (a finding opened from the report, D-65) is outlined in the accent, the
// selection colour: SeedFoundry's own style, outside the defect overlay's sheet, on the panel's
// own `[data-panel]` element so the outline follows a card the overlay moved.
import { computed } from 'vue'
import type { Descriptor, Payload, SortDirection, Step } from '../../dashboard/types'
import ChartPanel from './ChartPanel.vue'
import KpiPanel from './KpiPanel.vue'
import TablePanel from './TablePanel.vue'

const props = defineProps<{ descriptor: Descriptor; payload: Payload; busy?: boolean; highlight?: string[] }>()
const emit = defineEmits<{
  drill: [step: Step]
  page: [page: number]
  sort: [column: string, direction: SortDirection]
}>()

const bands = computed(() =>
  props.descriptor.bands
    .map((band) => ({ ...band, panels: props.descriptor.panels.filter((p) => p.band === band.id) }))
    .filter((band) => band.panels.length),
)
</script>

<template>
  <div class="renderer" :style="{ '--grid-columns': descriptor.grid.columns, '--grid-gutter': `var(--${descriptor.grid.gutter})` }">
    <section v-for="band in bands" :key="band.id" class="renderer__band" :aria-label="band.title" :data-band="band.id" data-test="band">
      <div
        v-for="panel in band.panels"
        :key="panel.id"
        class="renderer__cell"
        :class="{ 'renderer__cell--finding': highlight?.includes(panel.id) }"
        :style="{ gridColumn: `span ${panel.span}` }"
        :data-highlight="highlight?.includes(panel.id) ? 'finding' : undefined"
        data-test="cell"
      >
        <KpiPanel v-if="panel.mark === 'kpi'" :panel="panel" :data="payload.panels[panel.id]" />
        <TablePanel
          v-else-if="panel.mark === 'table'"
          :panel="panel"
          :data="payload.panels[panel.id]"
          :classes="descriptor.classes"
          :busy="busy"
          @drill="emit('drill', $event)"
          @page="emit('page', $event)"
          @sort="(column, direction) => emit('sort', column, direction)"
        />
        <ChartPanel
          v-else
          :panel="panel"
          :data="payload.panels[panel.id]"
          :classes="descriptor.classes"
          :level="payload.drill.path"
          @drill="emit('drill', $event)"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
.renderer {
  display: grid;
  gap: var(--grid-gutter);
}

.renderer__band {
  display: grid;
  grid-template-columns: repeat(var(--grid-columns), minmax(0, 1fr));
  gap: var(--grid-gutter);
}

.renderer__cell {
  display: grid;
  min-width: 0;
}

.renderer__cell--finding > [data-panel] {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
}
</style>
