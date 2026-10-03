<script setup lang="ts">
// The hand-off when a build completes (FR-B-9, ui-spec.md sections 3 and 4, D-54): until M9
// assembles the report, a summary of `build.completed` data, with no verdict (D-51), above
// the stepper, and the report's three actions in a footer. Each action is present and
// focusable but not yet available: pressing it says which milestone brings it, as the demo
// controller's stubs did (D-47).
import { computed, ref } from 'vue'
import type { LabEvent } from '../../events'
import { clock } from '../../stepper'
import BaseButton from '../base/BaseButton.vue'

const props = defineProps<{ iteration: number; completed: LabEvent; phases: number }>()

interface Counts {
  pass: number
  warn: number
  fail: number
  not_run: number
}

const data = computed(() => props.completed.data)

const counts = computed<Counts>(() => {
  const raw = (data.value.counts ?? {}) as Partial<Counts>
  return { pass: raw.pass ?? 0, warn: raw.warn ?? 0, fail: raw.fail ?? 0, not_run: raw.not_run ?? 0 }
})

const list = (key: string) => (Array.isArray(data.value[key]) ? (data.value[key] as unknown[]).length : 0)

const tests = computed(() => {
  const c = counts.value
  const parts = [`${c.pass + c.warn} passed`]
  if (c.not_run) parts.push(`${c.not_run} not run`)
  if (c.fail) parts.push(`${c.fail} failed`)
  return `${c.pass + c.warn + c.fail + c.not_run}: ${parts.join(', ')}`
})

const facts = computed(() => [
  { label: 'Duration', value: `${clock(Number(data.value.sim_seconds ?? props.completed.sim_t ?? 0))} simulated` },
  { label: 'Phases', value: String(props.phases) },
  { label: 'Tests', value: tests.value },
  { label: 'Findings', value: String(list('findings')) },
  { label: 'Boundary advisories', value: String(list('advisories')) },
  { label: 'Gates auto-resolved', value: String(list('gates')) },
])

type Action = 'dashboard' | 'rebuild' | 'approve'

const WHY: Record<Action, string> = {
  dashboard: 'View Dashboard opens the License Optimization dashboard, which arrives in M7.',
  rebuild: 'Rebuild opens the observer feedback editor, which arrives in M10.',
  approve: 'Approve arrives with the Seed page in M11.',
}

const said = ref('')
</script>

<template>
  <section class="summary" aria-labelledby="summary-title" data-test="build-summary">
    <h2 id="summary-title" class="summary__title">Build completed</h2>
    <dl class="summary__facts">
      <div v-for="fact in facts" :key="fact.label" class="summary__fact">
        <dt>{{ fact.label }}</dt>
        <dd data-test="summary-fact">{{ fact.value }}</dd>
      </div>
    </dl>
    <p class="summary__note">The build report, with its verdict, findings and tests, arrives in M9.</p>
    <footer class="summary__actions" data-test="summary-actions">
      <BaseButton aria-disabled="true" aria-describedby="why-dashboard" data-action="dashboard" @click="said = WHY.dashboard">View Dashboard</BaseButton>
      <BaseButton v-if="iteration === 1" aria-disabled="true" aria-describedby="why-rebuild" data-action="rebuild" @click="said = WHY.rebuild">
        Rebuild
      </BaseButton>
      <BaseButton variant="primary" aria-disabled="true" aria-describedby="why-approve" data-action="approve" @click="said = WHY.approve">Approve</BaseButton>
      <span id="why-dashboard" class="visually-hidden">{{ WHY.dashboard }}</span>
      <span id="why-rebuild" class="visually-hidden">{{ WHY.rebuild }}</span>
      <span id="why-approve" class="visually-hidden">{{ WHY.approve }}</span>
      <p class="summary__said" role="status" data-test="summary-status">{{ said }}</p>
    </footer>
  </section>
</template>

<style scoped>
.summary {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface-raised);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
}

.summary__title {
  font-size: var(--text-lg);
  font-weight: 600;
}

.summary__facts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: var(--space-3) var(--space-6);
  margin: 0;
}

.summary__fact dt {
  color: var(--text-secondary);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
}

.summary__fact dd {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.summary__note {
  color: var(--text-secondary);
  font-size: var(--text-sm);
}

.summary__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border-subtle);
}

.summary__said {
  flex-basis: 100%;
  min-height: 1.5em;
  color: var(--text-secondary);
  font-size: var(--text-sm);
}
</style>
