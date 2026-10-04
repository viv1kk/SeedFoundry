<script setup lang="ts">
// Observer feedback into Knowledge (FR-RB-8, ui-spec.md section 3, D-83): on the Build page of
// iteration 2 on, where each segment of the feedback goes. One tile per Ensemble file (Person,
// Instrument Awareness, Environment, Music) and one for the segments kept in the feedback file. A
// tile lists its segments as soon as the routing decides, then the sections and lines its Update
// sub-step adds as it plays, so the panel fills in with the build and reads the same after a
// refresh. State shows by weight and colour, not motion (seed-reuse-notes.md 1.1).
import { computed, useId } from 'vue'
import type { FeedbackRouting, RoutedFile } from '../../stepper'
import BaseChip, { type ChipTone } from '../base/BaseChip.vue'

const props = defineProps<{ routing: FeedbackRouting }>()
const uid = useId()

const plural = (n: number, word: string) => `${n} ${n === 1 ? word : `${word}s`}`
const list = (numbers: number[]) => `${numbers.length === 1 ? 'Segment' : 'Segments'} ${numbers.join(', ')}`

const decided = computed(() => props.routing.state === 'done')

const lead = computed(() => {
  const r = props.routing
  if (r.state === 'pending') return `Waiting to read ${r.feedback}.`
  if (r.total === null) return `Reading ${r.feedback}.`
  if (!r.total) return `${r.feedback} has no segment to route.`
  const routed = r.placements.filter((p) => p.file).length
  const files = r.files.filter((f) => f.segments.length).length
  const kept = r.kept.length ? `, ${r.kept.length} kept in the feedback file` : ''
  const verb = decided.value ? '' : ' so far'
  return `${r.feedback}: ${plural(r.total, 'segment')}. ${routed} routed to ${plural(files, 'Ensemble file')}${kept}${verb}.`
})

function look(file: RoutedFile): { label: string; tone: ChipTone } {
  switch (file.state) {
    case 'active':
      return { label: 'Updating', tone: 'accent' }
    case 'done':
      return file.sections.length ? { label: 'Updated', tone: 'positive' } : { label: 'No change', tone: 'neutral' }
    case 'stopped':
      return { label: 'Stopped', tone: 'warning' }
    default:
      return { label: 'Waiting', tone: 'neutral' }
  }
}

function note(file: RoutedFile): string {
  if (file.segments.length) return `${list(file.segments)} routed here.`
  return decided.value ? 'No feedback for this file.' : 'Waiting for the routing.'
}

const lines = (n: number) => plural(n, 'line')
</script>

<template>
  <section class="routing" :aria-labelledby="`${uid}-title`" data-test="feedback-routing">
    <header class="routing__head">
      <h2 :id="`${uid}-title`" class="caps-label routing__title">Observer feedback into Knowledge</h2>
      <p class="routing__lead" data-test="routing-lead">{{ lead }}</p>
    </header>
    <ul class="routing__tiles">
      <li
        v-for="file in routing.files"
        :key="file.step"
        class="tile"
        :class="[`tile--${file.state}`, { 'tile--fed': file.segments.length }]"
        :data-state="file.state"
        :data-category="file.id"
        data-test="routing-file"
      >
        <div class="tile__head">
          <span class="tile__name">{{ file.name }}</span>
          <BaseChip :tone="look(file).tone" data-test="routing-state">{{ look(file).label }}</BaseChip>
        </div>
        <span class="caps-label">{{ file.category }}</span>
        <p class="tile__note" data-test="routing-segments">{{ note(file) }}</p>
        <ul v-if="file.sections.length" class="tile__sections" data-test="routing-sections">
          <li v-for="section in file.sections" :key="section.section">
            <span class="tile__lines">+{{ lines(section.lines) }}</span> in {{ section.section }}<template v-if="section.created"> (a new section)</template>
          </li>
        </ul>
      </li>
      <li class="tile tile--kept" :class="{ 'tile--fed': routing.kept.length }" data-test="routing-kept">
        <div class="tile__head">
          <span class="tile__name">{{ routing.feedback }}</span>
        </div>
        <span class="caps-label">Kept in the feedback file</span>
        <p class="tile__note">
          <template v-if="routing.kept.length">{{ list(routing.kept) }}: {{ routing.kept.length === 1 ? 'fits' : 'fit' }} no Ensemble file.</template>
          <template v-else-if="decided">Every segment found a file.</template>
          <template v-else>Waiting for the routing.</template>
        </p>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.routing {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.routing__head {
  display: grid;
  gap: var(--space-1);
}

.routing__title {
  margin: 0;
}

.routing__lead {
  font-size: var(--text-sm);
}

.routing__tiles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.tile {
  display: grid;
  align-content: start;
  gap: var(--space-1);
  padding: var(--space-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  background: var(--surface-sunken);
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.tile--fed {
  border-color: var(--border-default);
  background: var(--surface-raised);
  color: var(--text-primary);
}

.tile--active {
  border-color: var(--accent);
  box-shadow: inset 3px 0 0 var(--accent);
}

.tile--done.tile--fed {
  box-shadow: inset 3px 0 0 var(--status-positive);
}

.tile__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-1) var(--space-2);
}

.tile__name {
  font-family: var(--font-mono);
  font-weight: 600;
  overflow-wrap: anywhere;
}

.tile__note {
  margin: 0;
}

.tile__sections {
  display: grid;
  gap: 2px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.tile__lines {
  font-family: var(--font-mono);
  font-weight: 600;
}
</style>
