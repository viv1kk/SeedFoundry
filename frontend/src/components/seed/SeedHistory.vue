<script setup lang="ts">
// The Seed page's iteration history (ui-spec.md section 7, OQ-9, D-75, D-81): Iteration 1 (n findings),
// then each observer feedback and the iteration it started, up to the approved one, as a timeline; it
// ends at iteration 1 when iteration 1 is the Seed. Each feedback is a real disclosure (a button with
// aria-expanded, NFR-6), closed at first, and renders through the Knowledge Preview's sanitiser (D-40),
// so nothing in it loads or navigates.
import { computed, ref, useId } from 'vue'
import type { HistoryItem } from '../../seed'
import BaseChip from '../base/BaseChip.vue'
import HumanTag from '../base/HumanTag.vue'
import MarkdownPreview from '../intake/MarkdownPreview.vue'

const props = defineProps<{ items: HistoryItem[] }>()

const opened = ref(new Set<string>())
const uid = useId()

function toggle(key: string): void {
  const next = new Set(opened.value)
  if (!next.delete(key)) next.add(key)
  opened.value = next
}

const plural = (n: number, word: string) => `${n} ${n === 1 ? word : `${word}s`}`

const entries = computed(() =>
  props.items.map((item) => {
    if (item.kind === 'feedback') {
      const routed = `${item.routed} of ${plural(item.segments, 'segment')} went into ${plural(item.files_updated, 'Knowledge file')}`
      return { item, key: `feedback-${item.rejected ?? 1}`, title: 'Observer feedback', detail: `${item.name}: ${routed}.` }
    }
    const parts = [plural(item.findings, 'finding')]
    if (item.prior_findings) parts.push(`${item.resolved} of ${item.prior_findings} iteration ${item.iteration - 1} findings resolved`)
    return { item, key: `iteration-${item.iteration}`, title: `Iteration ${item.iteration}`, detail: `${parts.join('; ')}.` }
  }),
)
</script>

<template>
  <ol class="history" data-test="seed-history">
    <li v-for="entry in entries" :key="entry.key" class="history__item" :data-kind="entry.item.kind" data-test="history-item">
      <span class="history__mark" aria-hidden="true" />
      <div class="history__body">
        <p class="history__head">
          <strong class="history__title">{{ entry.title }}</strong>
          <HumanTag v-if="entry.item.kind === 'iteration'" :iteration="entry.item.iteration" />
          <template v-if="entry.item.kind === 'iteration'">
            <BaseChip :tone="entry.item.verdict.tone" data-test="history-verdict">{{ entry.item.verdict.label }}</BaseChip>
            <BaseChip v-if="entry.item.approved" tone="positive" data-test="history-approved">Approved</BaseChip>
          </template>
        </p>
        <p class="history__detail" data-test="history-detail">
          {{ entry.detail }}
          <RouterLink v-if="entry.item.kind === 'iteration'" :to="`/review/${entry.item.iteration}`">Read its report</RouterLink>
        </p>
        <template v-if="entry.item.kind === 'feedback'">
          <button
            type="button"
            class="history__toggle"
            :aria-expanded="opened.has(entry.key) ? 'true' : 'false'"
            :aria-controls="`${uid}-${entry.key}`"
            data-test="feedback-toggle"
            @click="toggle(entry.key)"
          >
            {{ opened.has(entry.key) ? 'Hide the feedback' : 'Show the feedback' }}
          </button>
          <blockquote v-show="opened.has(entry.key)" :id="`${uid}-${entry.key}`" class="history__quote" data-test="feedback-text">
            <MarkdownPreview compact :text="entry.item.content" :label="`Observer feedback, ${entry.item.name}`" />
          </blockquote>
        </template>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.history {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}

.history__item {
  position: relative;
  display: grid;
  grid-template-columns: var(--space-4) minmax(0, 1fr);
  gap: var(--space-3);
  padding-bottom: var(--space-5);
}

/* The line joining one step to the next, drawn behind the marks */
.history__item:not(:last-child)::before {
  content: '';
  position: absolute;
  top: var(--space-4);
  bottom: 0;
  left: calc(var(--space-2) - 1px);
  border-left: 2px solid var(--border-default);
}

.history__mark {
  position: relative;
  width: var(--space-4);
  height: var(--space-4);
  margin-top: 2px;
  border: 2px solid var(--border-strong);
  border-radius: 50%;
  background: var(--surface-raised);
}

.history__item[data-kind='feedback'] .history__mark {
  border-color: var(--accent);
}

.history__body {
  display: grid;
  gap: var(--space-1);
  justify-items: start;
  min-width: 0;
}

.history__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.history__title {
  font-weight: 600;
}

.history__detail {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.history__toggle {
  padding: 0;
  border: 0;
  background: none;
  color: var(--accent);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 2px;
  cursor: pointer;
}

.history__quote {
  justify-self: stretch;
  margin: var(--space-2) 0 0;
  padding: var(--space-2) var(--space-4);
  border-left: 3px solid var(--border-strong);
  background: var(--surface-sunken);
}
</style>
