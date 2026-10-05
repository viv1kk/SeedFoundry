<script setup lang="ts">
// The phase stepper (ui-spec.md section 3, FR-B-3, D-54). The active phase is open on its
// sub-steps; a finished phase is one line with its duration and result chip, and opens on
// click or Enter. State shows by weight and colour, not motion (seed-reuse-notes.md 1.1).
// Iteration 2's first five Assay sub-steps sit under "Apply observer feedback" (FR-RB-8).
import { computed, ref } from 'vue'
import { duration, type PhaseView, type StepView } from '../../stepper'
import BaseChip, { type ChipTone } from '../base/BaseChip.vue'

const props = defineProps<{ phases: PhaseView[] }>()

const opened = ref(new Set<string>())

function isOpen(phase: PhaseView): boolean {
  return phase.state === 'active' || phase.state === 'stopped' || opened.value.has(phase.id)
}

function toggle(id: string): void {
  const next = new Set(opened.value)
  if (!next.delete(id)) next.add(id)
  opened.value = next
}

/** The phase's mark and chip: one look per state and result. */
function look(phase: PhaseView): { mark: string; tone: ChipTone; chip: string | null } {
  if (phase.state === 'pending') return { mark: 'pending', tone: 'neutral', chip: null }
  if (phase.state === 'active') return { mark: 'active', tone: 'accent', chip: 'Running' }
  if (phase.state === 'stopped') return { mark: 'stopped', tone: 'warning', chip: 'Stopped' }
  switch (phase.result) {
    case 'passed':
      return { mark: 'passed', tone: 'positive', chip: 'Passed' }
    case 'findings':
      return { mark: 'findings', tone: 'warning', chip: `Findings: ${phase.findings}` }
    case 'failed':
      return { mark: 'failed', tone: 'negative', chip: phase.failedTests.length ? `Failed: ${phase.failedTests.join(', ')}` : 'Failed' }
    case 'incomplete':
      // A test that did not run (D-51): neither a pass nor a fault, so neutral, and it says why.
      return { mark: 'incomplete', tone: 'neutral', chip: `Incomplete: ${phase.notRun} of ${phase.tests} not run` }
    default:
      return { mark: 'unknown', tone: 'neutral', chip: 'Result not kept' }
  }
}

interface Group {
  label: string | null
  steps: StepView[]
}

function groups(phase: PhaseView): Group[] {
  const feedback = phase.steps.filter((step) => step.feedback)
  const rest = phase.steps.filter((step) => !step.feedback)
  return feedback.length ? [{ label: 'Apply observer feedback', steps: feedback }, { label: null, steps: rest }] : [{ label: null, steps: rest }]
}

const STEP_LABEL = { pending: 'pending', active: 'active', done: 'done', stopped: 'stopped' } as const

const looks = computed(() => props.phases.map(look))
</script>

<template>
  <ol class="stepper" aria-label="Phases" data-test="stepper">
    <li
      v-for="(phase, i) in phases"
      :key="phase.id"
      class="phase"
      :class="[`phase--${phase.state}`, `mark--${looks[i].mark}`]"
      :data-state="phase.state"
      :data-result="phase.result ?? undefined"
      data-test="phase"
    >
      <component
        :is="phase.state === 'done' ? 'button' : 'div'"
        :type="phase.state === 'done' ? 'button' : undefined"
        class="phase__row"
        :aria-expanded="phase.state === 'done' ? isOpen(phase) : undefined"
        :aria-controls="phase.state === 'done' && isOpen(phase) ? `steps-${phase.id}` : undefined"
        data-test="phase-row"
        @click="phase.state === 'done' && toggle(phase.id)"
      >
        <span class="phase__mark" aria-hidden="true" />
        <span class="phase__index">{{ phase.index }}</span>
        <span class="phase__name">{{ phase.name }}</span>
        <span v-if="phase.state === 'pending'" class="visually-hidden">pending</span>
        <span class="phase__meta">
          <span v-if="phase.duration !== null" class="phase__duration" data-test="phase-duration">{{ duration(phase.duration) }}</span>
          <BaseChip v-if="looks[i].chip" :tone="looks[i].tone" data-test="phase-chip">{{ looks[i].chip }}</BaseChip>
        </span>
      </component>
      <div v-if="isOpen(phase) && phase.steps.length" :id="`steps-${phase.id}`" class="phase__steps">
        <template v-for="group in groups(phase)" :key="group.label ?? 'steps'">
          <p v-if="group.label" class="group__label caps-label" data-test="step-group">{{ group.label }}</p>
          <ul class="steps" :class="{ 'steps--grouped': group.label }">
            <li v-for="step in group.steps" :key="step.id" class="step" :class="`step--${step.state}`" :data-state="step.state" data-test="step">
              <span class="step__mark" aria-hidden="true" />
              <span class="step__name">{{ step.name }}</span>
              <span class="step__state" data-test="step-state">{{ step.state === 'done' && step.summary ? step.summary : STEP_LABEL[step.state] }}</span>
            </li>
          </ul>
        </template>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.stepper {
  display: grid;
  gap: var(--space-1);
  margin: 0;
  padding: 0;
  list-style: none;
}

.phase__row {
  display: grid;
  grid-template-columns: 12px 2ch minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 36px;
  padding: var(--space-1) var(--space-3);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--text-secondary);
  font: inherit;
  font-size: var(--text-md);
  text-align: left;
}

button.phase__row {
  cursor: pointer;
}

button.phase__row:hover {
  background: var(--surface-sunken);
}

.phase__index {
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--text-muted);
  text-align: right;
}

.phase__name {
  min-width: 0;
}

.phase__meta {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
}

.phase__duration {
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  color: var(--text-muted);
}

/* Weight, not motion, shows state. */
.phase--pending .phase__row {
  color: var(--text-muted);
}

.phase--active .phase__row,
.phase--stopped .phase__row {
  color: var(--text-primary);
  font-weight: 600;
  background: var(--surface-raised);
  border-color: var(--border-default);
}

.phase--done .phase__row {
  color: var(--text-primary);
}

.phase__mark,
.step__mark {
  width: 10px;
  height: 10px;
  border: 2px solid var(--border-default);
  /* Square, like every other mark (ValueWise section 5) */
  border-radius: 0;
}

.mark--active .phase__mark {
  border-color: var(--accent);
  background: var(--accent);
}

.mark--passed .phase__mark {
  border-color: var(--status-positive);
  background: var(--status-positive);
}

.mark--findings .phase__mark,
.mark--stopped .phase__mark {
  border-color: var(--status-warning);
  background: var(--status-warning);
}

.mark--failed .phase__mark {
  border-color: var(--status-negative);
  background: var(--status-negative);
}

/* Incomplete: a ring in the neutral colour, neither the pass fill nor a fault. */
.mark--incomplete .phase__mark,
.mark--unknown .phase__mark {
  border-color: var(--status-neutral);
}

.phase__steps {
  padding: var(--space-1) 0 var(--space-3) calc(var(--space-3) + 12px + var(--space-3));
}

.group__label {
  margin: var(--space-2) 0 var(--space-1);
  color: var(--text-secondary);
}

.steps {
  display: grid;
  gap: 2px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.steps--grouped {
  margin-bottom: var(--space-2);
  padding-left: var(--space-3);
  border-left: 1px solid var(--border-default);
}

.step {
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) auto;
  align-items: baseline;
  gap: var(--space-3);
  padding: 2px 0;
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.step__mark {
  width: 8px;
  height: 8px;
  border-width: 1px;
  align-self: center;
}

.step__state {
  max-width: 28ch;
  overflow: hidden;
  font-family: var(--font-sans);
  font-size: var(--text-xs);
  color: var(--text-muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step--pending {
  color: var(--text-muted);
}

.step--active {
  color: var(--text-primary);
  font-weight: 600;
}

.step--active .step__mark {
  border-color: var(--accent);
  background: var(--accent);
}

.step--active .step__state {
  color: var(--accent);
  font-weight: 600;
}

.step--done .step__mark {
  border-color: var(--status-positive);
  background: var(--status-positive);
}

.step--stopped .step__mark {
  border-color: var(--status-warning);
}

.step--stopped .step__state {
  /* A status in words: tested text colour, marked with the status fill (D-98) */
  color: var(--status-warning-text);
  border-left: 3px solid var(--status-warning);
  padding-left: var(--space-2);
}
</style>
