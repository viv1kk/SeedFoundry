<script setup lang="ts">
// The build console (ui-spec.md section 3, FR-B-4, build-simulation.md section 4, D-54):
// `mm:ss.s  LEVEL  message` on the console surface, the same in both themes (D-37), coloured
// by level with red only for FAIL. It follows new lines unless paused; scrolling up pauses it,
// and Resume jumps back to the latest line. The filter keeps one level (TEST includes PASS).
// A full build is a few hundred lines, so the list is plain (Seed v0.1 needed no
// virtualisation for its log either, seed-reuse-notes.md 2.2).
import { computed, nextTick, ref, watch } from 'vue'
import { FILTERS, filterLines, type ConsoleLine, type FilterId } from '../../stepper'

const props = withDefaults(defineProps<{ lines: ConsoleLine[]; collapsible?: boolean }>(), { collapsible: false })
const emit = defineEmits<{ collapse: [] }>()

const filter = ref<FilterId>('all')
const paused = ref(false)
/** Lines held when the console paused, to say how many arrived since. */
const heldAt = ref(0)
const body = ref<HTMLElement | null>(null)

const shown = computed(() => filterLines(props.lines, filter.value))
const unseen = computed(() => (paused.value ? Math.max(0, props.lines.length - heldAt.value) : 0))

function toBottom(): void {
  const el = body.value
  if (el) el.scrollTop = el.scrollHeight
}

function pause(): void {
  if (paused.value) return
  paused.value = true
  heldAt.value = props.lines.length
}

function resume(): void {
  paused.value = false
  void nextTick(toBottom)
}

function onScroll(): void {
  const el = body.value
  if (!el || paused.value) return
  // Only a person scrolls away from the bottom: following always lands on it.
  if (el.scrollHeight - el.scrollTop - el.clientHeight > 4) pause()
}

watch(
  () => [shown.value.length, filter.value],
  () => {
    if (!paused.value) void nextTick(toBottom)
  },
  { immediate: true, flush: 'post' },
)

const EMPTY: Record<FilterId, string> = {
  all: 'No log lines yet.',
  LLM: 'No LLM lines yet.',
  API: 'No API lines yet.',
  TEST: 'No TEST or PASS lines yet.',
  WARN: 'No WARN lines.',
  FAIL: 'No FAIL lines.',
}
</script>

<template>
  <section class="console" aria-label="Console" data-test="console">
    <header class="console__bar">
      <h2 class="console__title caps-label">Console</h2>
      <div class="console__filter" role="group" aria-label="Show levels" data-test="console-filter">
        <button
          v-for="option in FILTERS"
          :key="option.id"
          type="button"
          class="console__button"
          :aria-pressed="filter === option.id"
          :data-filter="option.id"
          @click="filter = option.id"
        >
          {{ option.label }}
        </button>
      </div>
      <button
        type="button"
        class="console__button"
        :aria-pressed="paused"
        data-test="console-pause"
        @click="paused ? resume() : pause()"
      >
        {{ paused ? 'Resume' : 'Pause' }}
      </button>
      <button v-if="collapsible" type="button" class="console__button" data-test="console-hide" @click="emit('collapse')">Hide</button>
    </header>
    <p v-if="paused" class="console__paused" role="status" data-test="console-paused">
      Paused<template v-if="unseen">: {{ unseen }} new {{ unseen === 1 ? 'line' : 'lines' }} below</template>
    </p>
    <div ref="body" class="console__body" tabindex="0" aria-label="Build log" data-test="console-body" @scroll="onScroll">
      <ol v-if="shown.length" class="console__lines">
        <li v-for="line in shown" :key="line.seq" class="line" :class="`line--${line.level}`" :data-level="line.level" data-test="console-line">
          <span class="line__time">{{ `${line.time}  ` }}</span><span class="line__level">{{ line.level.padEnd(7) }}</span><span class="line__message">{{ line.message }}</span>
        </li>
      </ol>
      <p v-else class="console__empty">{{ EMPTY[filter] }}</p>
    </div>
  </section>
</template>

<style scoped>
.console {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  background: var(--console-surface);
  color: var(--console-text);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.console__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--console-border);
  background: var(--console-surface-raised);
}

.console__title {
  margin-right: auto;
  color: var(--console-text-secondary);
  font-family: var(--font-sans);
}

.console__filter {
  display: inline-flex;
  border: 1px solid var(--console-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.console__filter .console__button {
  border: 0;
  border-radius: 0;
}

.console__filter .console__button + .console__button {
  border-left: 1px solid var(--console-border);
}

.console__button {
  min-height: 26px;
  padding: 0 var(--space-2);
  border: 1px solid var(--console-border);
  border-radius: var(--radius-sm);
  background: var(--console-surface);
  color: var(--console-text-secondary);
  font: inherit;
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
}

.console__button:hover {
  color: var(--console-text);
}

.console__button[aria-pressed='true'] {
  background: var(--console-surface-raised);
  color: var(--console-text);
  box-shadow: inset 0 -2px 0 var(--console-llm);
}

.console__button:focus-visible {
  outline-color: var(--console-llm);
  outline-offset: -2px;
}

.console__paused {
  padding: var(--space-1) var(--space-4);
  border-bottom: 1px solid var(--console-border);
  color: var(--console-warn);
  font-size: var(--text-xs);
}

.console__body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--space-3) var(--space-4);
  scrollbar-color: var(--console-border) transparent;
}

.console__body:focus-visible {
  outline-color: var(--console-llm);
  outline-offset: -2px;
}

.console__lines {
  margin: 0;
  padding: 0;
  list-style: none;
}

.line {
  display: grid;
  grid-template-columns: auto auto minmax(0, 1fr);
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.line__time {
  color: var(--console-text-muted);
}

.console__empty {
  color: var(--console-text-muted);
}

/* Level colours (build-simulation.md section 4, D-37). Red only for FAIL. */
.line--INFO {
  color: var(--console-text-secondary);
}

.line--LLM {
  color: var(--console-llm);
}

.line--API {
  color: var(--console-api);
}

.line--TEST {
  color: var(--console-text);
}

.line--PASS {
  color: var(--console-pass);
}

.line--WARN {
  color: var(--console-warn);
}

.line--FAIL {
  color: var(--console-fail);
}
</style>
