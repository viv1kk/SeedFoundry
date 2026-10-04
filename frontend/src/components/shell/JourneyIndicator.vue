<script setup lang="ts">
// Knowledge, Build, Review, Seed (ui-spec.md section 1). Shows where you are. Knowledge is always a
// link; Seed follows the approval (D-75): once a Seed is approved it is a link to the Seed page and
// reads as reached. Build and Review are not links: which iteration they would open is the page's
// own choice.
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { JOURNEY, type JourneyStep } from '../../router'
import { useLabStore } from '../../stores/lab'

const LABELS: Record<JourneyStep, string> = {
  knowledge: 'Knowledge',
  build: 'Build',
  review: 'Review',
  seed: 'Seed',
}

const route = useRoute()
const lab = useLabStore()
const approved = computed(() => Boolean(lab.snapshot?.approval))
const linked = computed<ReadonlySet<JourneyStep>>(() => new Set(approved.value ? ['knowledge', 'seed'] : ['knowledge']))
const current = computed(() => (JOURNEY as readonly string[]).indexOf(String(route.name ?? '')))

const steps = computed(() =>
  JOURNEY.map((step, index) => ({
    step,
    label: LABELS[step],
    current: index === current.value,
    done: current.value > index || (step === 'seed' && approved.value && index !== current.value),
    linked: linked.value.has(step),
  })),
)
</script>

<template>
  <nav class="journey" aria-label="Journey">
    <ol class="journey__list">
      <li v-for="item in steps" :key="item.step" class="journey__item" :data-step="item.step">
        <RouterLink
          v-if="item.linked"
          :to="{ name: item.step }"
          class="journey__step journey__step--link"
          :class="{ 'journey__step--current': item.current, 'journey__step--done': item.done }"
          :aria-current="item.current ? 'step' : undefined"
        >
          {{ item.label }}
        </RouterLink>
        <span
          v-else
          class="journey__step"
          :class="{ 'journey__step--current': item.current, 'journey__step--done': item.done }"
          :aria-current="item.current ? 'step' : undefined"
        >
          {{ item.label }}
        </span>
      </li>
    </ol>
  </nav>
</template>

<style scoped>
.journey__list {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.journey__item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* A chevron between steps, drawn in CSS so no glyph sits in the text */
.journey__item + .journey__item::before {
  content: '';
  width: 6px;
  height: 6px;
  margin-right: var(--space-2);
  border-top: 1.5px solid var(--text-muted);
  border-right: 1.5px solid var(--text-muted);
  transform: rotate(45deg);
}

/* State by weight and colour, not motion */
.journey__step {
  display: inline-block;
  padding: var(--space-1) var(--space-2);
  border-bottom: 2px solid transparent;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
}

.journey__step--done {
  color: var(--text-secondary);
}

.journey__step--current {
  color: var(--text-primary);
  font-weight: 650;
  border-bottom-color: var(--accent);
}

.journey__step--link:hover {
  color: var(--text-primary);
  background: var(--surface-sunken);
}
</style>
